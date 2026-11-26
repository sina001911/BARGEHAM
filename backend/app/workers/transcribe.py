"""Transcription worker: audio → timestamped segments (Whisper-like, graceful).

Uses faster-whisper when available, then openai-whisper, then a no-op fallback
that marks the file READY without a transcript. Speaker diarization is a stub
that labels a single speaker when the engine cannot separate speakers.
"""
from __future__ import annotations

import asyncio
import logging
import uuid

from sqlalchemy import delete, func

from app.audio.models import AudioFile, AudioStatus, TranscriptionSegment
from app.celery import celery_app
from app.storage import get_storage
from app.workers._db import run_async, worker_session

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.workers.transcribe.transcribe_audio",
    bind=True,
    max_retries=3,
    default_retry_delay=15,
)
def transcribe_audio(self, audio_id: str) -> dict:
    return run_async(_transcribe(uuid.UUID(audio_id)))


def _load_transcriber():
    """Return (engine_name, transcribe_callable) or (None, None)."""
    try:
        from faster_whisper import WhisperModel

        model = WhisperModel("base", device="cpu", compute_type="int8")
        return "faster-whisper", model
    except Exception as exc:  # pragma: no cover - optional dependency
        logger.debug("faster-whisper unavailable: %s", exc)

    try:
        import whisper  # type: ignore

        model = whisper.load_model("base")
        return "whisper", model
    except Exception as exc:  # pragma: no cover - optional dependency
        logger.debug("openai-whisper unavailable: %s", exc)

    return None, None


def _extract_metadata(data: bytes, file_name: str) -> dict:
    """Best-effort audio metadata via mutagen; empty dict when unavailable."""
    import io

    try:
        from mutagen import File as MutagenFile

        mf = MutagenFile(io.BytesIO(data))
        if mf is None or mf.info is None:
            return {}
        info = mf.info
        meta = {}
        if getattr(info, "length", None):
            meta["duration_seconds"] = float(info.length)
        if getattr(info, "bitrate", None):
            meta["bitrate"] = int(info.bitrate)
        if getattr(info, "sample_rate", None):
            meta["sample_rate"] = int(info.sample_rate)
        if getattr(info, "channels", None):
            meta["channels"] = int(info.channels)
        if getattr(mf, "mime", None):
            meta["codec"] = str(mf.mime[0]) if mf.mime else None
        return meta
    except Exception as exc:  # pragma: no cover - optional dependency
        logger.debug("mutagen unavailable: %s", exc)
        return {}


async def _transcribe(audio_id: uuid.UUID) -> dict:
    async with worker_session() as session:
        audio = await session.get(AudioFile, audio_id)
        if audio is None:
            return {"audio_id": str(audio_id), "status": "not_found"}

        try:
            data = get_storage().get_object(audio.storage_path)
        except Exception as exc:
            logger.warning("Transcribe: cannot read %s: %s", audio_id, exc)
            audio.status = AudioStatus.FAILED
            session.add(audio)
            await session.commit()
            return {"audio_id": str(audio_id), "status": "read_failed"}

        # Metadata extraction (always attempted)
        meta = _extract_metadata(data, audio.file_name)
        for key in ("duration_seconds", "bitrate", "sample_rate", "channels", "codec"):
            if key in meta and meta[key] is not None:
                setattr(audio, key, meta[key])

        engine_name, engine = _load_transcriber()
        if engine is None:
            # No STT engine — mark READY so playback works, no transcript.
            audio.status = AudioStatus.READY
            session.add(audio)
            await session.commit()
            logger.info("Transcribe: no engine for %s — READY without transcript", audio_id)
            return {"audio_id": str(audio_id), "status": "ready_no_engine", "metadata": meta}

        # Clear previous segments (re-transcription)
        await session.execute(
            delete(TranscriptionSegment).where(
                TranscriptionSegment.audio_id == audio_id
            )
        )

        import tempfile
        import os

        segments: list[dict] = []
        language = None
        confidences: list[float] = []
        with tempfile.NamedTemporaryFile(delete=False, suffix=".audio") as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        try:
            loop = asyncio.get_running_loop()
            segments, language, confidences = await loop.run_in_executor(
                None, _run_engine, engine_name, engine, tmp_path
            )
        except Exception as exc:
            logger.warning("Transcribe engine failed for %s: %s", audio_id, exc)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

        for idx, seg in enumerate(segments):
            session.add(
                TranscriptionSegment(
                    audio_id=audio_id,
                    segment_index=idx,
                    start_seconds=seg["start"],
                    end_seconds=seg["end"],
                    text=seg["text"],
                    speaker=seg.get("speaker"),
                    confidence=seg.get("confidence"),
                    tsv=func.to_tsvector("simple", seg["text"]),
                )
            )

        audio.has_transcript = bool(segments)
        audio.language = language
        if confidences:
            audio.transcript_confidence = sum(confidences) / len(confidences)
        audio.status = AudioStatus.TRANSCRIBED if segments else AudioStatus.READY
        session.add(audio)
        await session.commit()

        logger.info(
            "Transcribe: %s → %d segments (lang=%s)",
            audio_id,
            len(segments),
            language,
        )
        return {
            "audio_id": str(audio_id),
            "status": audio.status.value,
            "segments": len(segments),
            "language": language,
        }


def _run_engine(engine_name: str, engine, path: str) -> tuple[list[dict], str | None, list[float]]:
    """Run the STT engine synchronously; returns (segments, language, confidences)."""
    segments: list[dict] = []
    language: str | None = None
    confidences: list[float] = []

    if engine_name == "faster-whisper":
        seg_iter, info = engine.transcribe(path, vad_filter=True)
        language = getattr(info, "language", None)
        for seg in seg_iter:
            segments.append(
                {
                    "start": float(seg.start),
                    "end": float(seg.end),
                    "text": seg.text.strip(),
                    "confidence": float(getattr(seg, "avg_logprob", 0.0) or 0.0),
                    "speaker": None,
                }
            )
            confidences.append(float(getattr(seg, "avg_logprob", 0.0) or 0.0))
    elif engine_name == "whisper":
        result = engine.transcribe(path)
        language = result.get("language")
        for seg in result.get("segments", []):
            segments.append(
                {
                    "start": float(seg["start"]),
                    "end": float(seg["end"]),
                    "text": seg["text"].strip(),
                    "confidence": None,
                    "speaker": None,
                }
            )
    return segments, language, confidences