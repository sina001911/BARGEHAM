"""TTS (Text-to-Speech) service with Piper primary, edge-tts fallback, and pronunciation rules."""
from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from app.audio_creation.models import PronunciationRule, TTSVoice
from app.config import settings
from app.storage import get_storage

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Piper / edge-tts availability
# --------------------------------------------------------------------------- #

def _has_piper() -> bool:
    try:
        import piper  # noqa: F401
        return True
    except Exception:
        return False


def _has_edge_tts() -> bool:
    try:
        import edge_tts  # noqa: F401
        return True
    except Exception:
        return False


# --------------------------------------------------------------------------- #
# Pronunciation preprocessing
# --------------------------------------------------------------------------- #

async def apply_pronunciation_rules(
    session: AsyncSession,
    text: str,
    language: str,
) -> str:
    """Apply user-defined pronunciation rules to text."""
    stmt = (
        select(PronunciationRule)
        .where(
            PronunciationRule.language == language,
            PronunciationRule.is_active == True,  # noqa: E712
        )
        .order_by(col(PronunciationRule.word).desc())  # longer words first
    )
    rules = list((await session.execute(stmt)).scalars().all())
    if not rules:
        return text

    for rule in rules:
        word = rule.word
        repl = rule.replacement
        if rule.case_sensitive:
            text = text.replace(word, repl)
        else:
            import re
            text = re.sub(re.escape(word), repl, text, flags=re.IGNORECASE)
    return text


# --------------------------------------------------------------------------- #
# Voice management
# --------------------------------------------------------------------------- #

async def list_voices(
    session: AsyncSession,
    language: str | None = None,
    provider: str | None = None,
) -> list[TTSVoice]:
    stmt = select(TTSVoice).where(TTSVoice.is_active == True)  # noqa: E712
    if language:
        stmt = stmt.where(TTSVoice.language == language)
    if provider:
        stmt = stmt.where(TTSVoice.provider == provider)
    stmt = stmt.order_by(col(TTSVoice.language), col(TTSVoice.is_default_for_lang).desc())
    return list((await session.execute(stmt)).scalars().all())


async def get_voice(session: AsyncSession, voice_id: uuid.UUID) -> TTSVoice | None:
    return await session.get(TTSVoice, voice_id)


async def get_default_voice(
    session: AsyncSession, language: str
) -> TTSVoice | None:
    stmt = (
        select(TTSVoice)
        .where(
            TTSVoice.language == language,
            TTSVoice.is_default_for_lang == True,  # noqa: E712
            TTSVoice.is_active == True,  # noqa: E712
        )
        .limit(1)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_any_voice(session: AsyncSession, language: str) -> TTSVoice | None:
    stmt = (
        select(TTSVoice)
        .where(
            TTSVoice.language == language,
            TTSVoice.is_active == True,  # noqa: E712
        )
        .limit(1)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


# --------------------------------------------------------------------------- #
# Synthesis
# --------------------------------------------------------------------------- #

async def synthesize_piper(
    text: str,
    voice: TTSVoice,
    speed: float = 1.0,
    output_path: Optional[str] = None,
) -> str:
    """Run Piper TTS synchronously, return output file path."""
    if not voice.model_path or not os.path.exists(voice.model_path):
        raise RuntimeError(f"Piper model not found: {voice.model_path}")

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        out_wav = tmp.name

    try:
        # Piper command line
        cmd = [
            "piper",
            "--model", voice.model_path,
            "--output_file", out_wav,
        ]
        if voice.config_path and os.path.exists(voice.config_path):
            cmd.extend(["--config", voice.config_path])

        # Speed adjustment via length_scale (inverse of speed)
        if speed != 1.0:
            length_scale = max(0.1, min(2.0, 1.0 / speed))
            cmd.extend(["--length_scale", str(length_scale)])

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            input=text.encode("utf-8"),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"Piper failed: {stderr.decode()}")

        return out_wav

    except Exception as exc:
        if os.path.exists(out_wav):
            os.unlink(out_wav)
        raise


async def synthesize_edge_tts(
    text: str,
    voice: TTSVoice,
    speed: float = 1.0,
    output_path: Optional[str] = None,
) -> str:
    """Run edge-tts via Python API."""
    import edge_tts

    # Map our voice name to edge-tts voice
    # edge-tts voices: https://github.com/rany2/edge-tts/blob/master/edge_tts/voices.py
    edge_voice = voice.name
    if not edge_voice.startswith(("fa-", "en-", "ar-")):
        # Try to map to standard edge voices
        if voice.language == "fa":
            edge_voice = "fa-IR-DilaraNeural" if voice.gender == "female" else "fa-IR-FaridNeural"
        elif voice.language == "en":
            edge_voice = "en-US-AriaNeural" if voice.gender == "female" else "en-US-GuyNeural"
        else:
            edge_voice = "en-US-AriaNeural"

    rate = f"+{int((speed - 1) * 100)}%" if speed != 1.0 else "+0%"

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        out_mp3 = tmp.name

    try:
        communicate = edge_tts.Communicate(text, edge_voice, rate=rate)
        await communicate.save(out_mp3)
        return out_mp3
    except Exception as exc:
        if os.path.exists(out_mp3):
            os.unlink(out_mp3)
        raise


async def synthesize_text(
    session: AsyncSession,
    text: str,
    voice_id: uuid.UUID,
    speed: float = 1.0,
    language: str | None = None,
) -> tuple[str, TTSVoice]:
    """High-level synthesis: picks best engine, applies pronunciation rules."""
    voice = await get_voice(session, voice_id)
    if not voice:
        raise ValueError(f"Voice {voice_id} not found")

    # Apply pronunciation rules
    lang = language or voice.language
    processed_text = await apply_pronunciation_rules(session, text, lang)

    # Try Piper first (local, higher quality for Persian)
    if _has_piper() and voice.provider == "piper" and voice.model_path:
        try:
            path = await synthesize_piper(processed_text, voice, speed)
            return path, voice
        except Exception as exc:
            logger.warning("Piper synthesis failed for %s: %s", voice_id, exc)

    # Fallback to edge-tts
    if _has_edge_tts():
        try:
            path = await synthesize_edge_tts(processed_text, voice, speed)
            return path, voice
        except Exception as exc:
            logger.warning("edge-tts synthesis failed for %s: %s", voice_id, exc)

    # Last resort: no TTS engine available
    raise RuntimeError("No TTS engine available (Piper or edge-tts required)")


# --------------------------------------------------------------------------- #
# Audio concatenation utilities
# --------------------------------------------------------------------------- #

async def concatenate_audio_files(
    input_paths: list[str],
    output_path: str,
    pause_ms: int = 0,
) -> None:
    """Concatenate multiple audio files using ffmpeg."""
    if not input_paths:
        raise ValueError("No input files to concatenate")

    if len(input_paths) == 1 and pause_ms == 0:
        import shutil
        shutil.copy2(input_paths[0], output_path)
        return

    # Build ffmpeg filter complex
    filter_parts = []
    for i, _ in enumerate(input_paths):
        filter_parts.append(f"[{i}:a]")

    if pause_ms > 0:
        # Insert silence between tracks
        silence_duration = pause_ms / 1000.0
        concat_parts = []
        for i in range(len(input_paths)):
            concat_parts.append(f"[{i}:a]")
            if i < len(input_paths) - 1:
                concat_parts.append(f"aevalsrc=0:d={silence_duration}[sil{i}];")
        filter_str = "".join(concat_parts) + f"concat=n={len(input_paths)*2-1}:v=0:a=1"
    else:
        filter_str = "".join(filter_parts) + f"concat=n={len(input_paths)}:v=0:a=1"

    cmd = ["ffmpeg", "-y"]
    for p in input_paths:
        cmd.extend(["-i", p])
    cmd.extend(["-filter_complex", filter_str, "-c:a", "libmp3lame", output_path])

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg concatenation failed: {stderr.decode()}")


async def convert_audio_format(
    input_path: str,
    output_path: str,
    format: str = "mp3",  # mp3 | wav | opus | flac
) -> None:
    """Convert audio to target format."""
    codecs = {"mp3": "libmp3lame", "opus": "libopus", "flac": "flac", "wav": "pcm_s16le"}
    codec = codecs.get(format, "libmp3lame")
    cmd = ["ffmpeg", "-y", "-i", input_path, "-c:a", codec, output_path]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg conversion failed: {stderr.decode()}")


async def get_audio_duration(path: str) -> float:
    """Get audio duration in seconds using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    try:
        return float(stdout.decode().strip())
    except ValueError:
        return 0.0


# --------------------------------------------------------------------------- #
# Persist generated audio to storage
# --------------------------------------------------------------------------- #

async def persist_audio_file(
    local_path: str,
    prefix: str = "tts",
) -> str:
    """Move generated audio to object storage and return storage path."""
    import aiofiles

    storage = get_storage()
    ext = Path(local_path).suffix or ".mp3"
    object_name = f"{prefix}/{uuid.uuid4()}{ext}"

    async with aiofiles.open(local_path, "rb") as f:
        data = await f.read()

    stored_path = storage.put_object(object_name, data)
    return stored_path