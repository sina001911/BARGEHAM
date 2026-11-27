"""Podcast generation worker: multi-speaker script → per-segment TTS → mix."""
from __future__ import annotations

import logging
import os
import uuid

from app.celery import celery_app
from app.workers._db import run_async, worker_session

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.workers.podcast.generate_podcast",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def generate_podcast(self, project_id: str) -> dict:
    return run_async(_generate_podcast(uuid.UUID(project_id)))


async def _generate_podcast(project_id: uuid.UUID) -> dict:
    from app.audio_creation.models import (
        PodcastProject, PodcastSegment, PodcastSpeaker, PodcastStatus,
    )
    from app.audio_creation.tts_service import (
        synthesize_text, concatenate_audio_files, persist_audio_file,
        get_audio_duration, get_voice,
    )

    async with worker_session() as session:
        project = await session.get(PodcastProject, project_id)
        if not project:
            return {"project_id": str(project_id), "status": "not_found"}

        try:
            project.status = PodcastStatus.GENERATING.value
            session.add(project)
            await session.commit()

            # Load speakers and segments
            from sqlmodel import select, col
            speakers_stmt = (
                select(PodcastSpeaker)
                .where(PodcastSpeaker.project_id == project_id)
                .order_by(col(PodcastSpeaker.order_index))
            )
            speakers = list((await session.execute(speakers_stmt)).scalars().all())
            speaker_map = {sp.id: sp for sp in speakers}

            segs_stmt = (
                select(PodcastSegment)
                .where(PodcastSegment.project_id == project_id)
                .order_by(col(PodcastSegment.order_index))
            )
            segments = list((await session.execute(segs_stmt)).scalars().all())

            if not segments:
                raise ValueError("Podcast has no segments")

            # Synthesize each segment with its speaker's voice
            segment_paths: list[str] = []
            total_duration = 0.0

            for seg in segments:
                seg.status = "generating"
                session.add(seg)
                await session.commit()

                audio_path = None
                try:
                    speaker = speaker_map.get(seg.speaker_id) if seg.speaker_id else None
                    if speaker is None:
                        raise ValueError(f"Speaker for segment {seg.id} not found")

                    speed = seg.voice_speed or 1.0
                    audio_path, _ = await synthesize_text(
                        session,
                        seg.text,
                        speaker.voice_id,
                        speed=speed,
                    )

                    stored = await persist_audio_file(audio_path, prefix=f"podcast/{project_id}")
                    seg.audio_path = stored
                    seg.duration_seconds = await get_audio_duration(audio_path)
                    seg.status = "ready"
                    session.add(seg)

                    segment_paths.append(audio_path)
                    total_duration += seg.duration_seconds or 0.0

                    # Add pauses
                    pause_ms = (seg.pause_after_ms if seg.pause_after_ms is not None
                                else project.default_pause_ms)
                    if pause_ms > 0:
                        # Represent pause as extra concat handled by concatenate
                        pass

                except Exception as exc:
                    logger.exception("Segment %s TTS failed: %s", seg.id, exc)
                    seg.status = "failed"
                    session.add(seg)

                await session.commit()
                if audio_path:
                    try:
                        os.unlink(audio_path)
                    except OSError:
                        pass

            # Concatenate all segments
            final_path = f"/tmp/podcast_{project_id}.{project.output_format}"
            await concatenate_audio_files(
                segment_paths, final_path, pause_ms=project.default_pause_ms
            )

            # Persist
            final_stored = await persist_audio_file(final_path, prefix=f"podcast/{project_id}")
            project.output_path = final_stored
            project.total_duration_seconds = total_duration
            project.file_size_bytes = os.path.getsize(final_path)
            project.status = PodcastStatus.READY.value
            session.add(project)
            await session.commit()

            logger.info("Podcast %s generated: %.1fs", project_id, total_duration)
            return {
                "project_id": str(project_id),
                "status": "ready",
                "duration_seconds": total_duration,
                "output_path": final_stored,
            }

        except Exception as exc:
            logger.exception("Podcast %s generation failed: %s", project_id, exc)
            project.status = PodcastStatus.FAILED.value
            project.error_message = str(exc)
            session.add(project)
            await session.commit()
            return {"project_id": str(project_id), "status": "failed", "error": str(exc)}