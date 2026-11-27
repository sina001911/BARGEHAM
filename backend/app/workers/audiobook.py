"""Audiobook generation worker: document → chapters → TTS → concatenate."""
from __future__ import annotations

import logging
import os
import uuid

from app.celery import celery_app
from app.workers._db import run_async, worker_session

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.workers.audiobook.generate_audiobook",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def generate_audiobook(self, project_id: str) -> dict:
    return run_async(_generate_audiobook(uuid.UUID(project_id)))


async def _generate_audiobook(project_id: uuid.UUID) -> dict:
    from app.audio_creation.models import AudiobookProject, AudiobookChapter, AudiobookStatus
    from app.audio_creation.tts_service import (
        synthesize_text,
        concatenate_audio_files,
        convert_audio_format,
        get_audio_duration,
        persist_audio_file,
        get_voice,
    )
    from app.documents.models import Document
    from app.ocr import chunk_pages, extract_document
    from app.storage import get_storage

    async with worker_session() as session:
        project = await session.get(AudiobookProject, project_id)
        if not project:
            return {"project_id": str(project_id), "status": "not_found"}

        try:
            project.status = AudiobookStatus.GENERATING.value
            session.add(project)
            await session.commit()

            # Get source document text
            doc = await session.get(Document, project.source_document_id)
            if not doc:
                raise ValueError("Source document not found")

            data = get_storage().get_object(doc.storage_path)
            result = extract_document(data, doc.mime_type, doc.file_name)

            # Chunk into chapters (reuse OCR chunking logic)
            pages = [(p.page_number, p.text) for p in result.pages if p.text.strip()]
            pieces = chunk_pages(pages, chunk_size=2000, overlap=200)

            if not pieces:
                raise ValueError("Document has no extractable text")

            # Create chapter records
            chapters: list = []
            for idx, piece in enumerate(pieces):
                chapter = AudiobookChapter(
                    project_id=project_id,
                    title=f"بخش {idx + 1}" if piece.direction == "rtl" else f"Section {idx + 1}",
                    source_text=piece.text,
                    order_index=idx,
                    status="pending",
                )
                session.add(chapter)
                chapters.append(chapter)

            await session.commit()
            for ch in chapters:
                await session.refresh(ch)

            # Get voice for language
            voice = await get_voice(session, project.voice_id)
            if not voice:
                raise ValueError("TTS voice not found")

            # Generate TTS for each chapter
            chapter_audio_paths: list[str] = []
            total_duration = 0.0

            for ch in chapters:
                ch.status = "generating"
                session.add(ch)
                await session.commit()

                audio_path = None
                try:
                    audio_path, _ = await synthesize_text(
                        session,
                        ch.source_text,
                        project.voice_id,
                        speed=project.speed,
                        language=voice.language,
                    )

                    # Persist chapter audio
                    stored = await persist_audio_file(audio_path, prefix=f"audiobook/{project_id}")
                    ch.audio_path = stored
                    ch.duration_seconds = await get_audio_duration(audio_path)
                    ch.status = "ready"
                    session.add(ch)

                    chapter_audio_paths.append(audio_path)
                    total_duration += ch.duration_seconds or 0.0

                except Exception as exc:
                    logger.exception("Chapter %s TTS failed: %s", ch.id, exc)
                    ch.status = "failed"
                    session.add(ch)

                await session.commit()
                # Cleanup temp file
                if audio_path:
                    try:
                        os.unlink(audio_path)
                    except OSError:
                        pass

            # Concatenate all chapters
            final_path = f"/tmp/audiobook_{project_id}.{project.output_format}"
            await concatenate_audio_files(
                chapter_audio_paths,
                final_path,
                pause_ms=project.pause_between_paragraphs_ms,
            )

            # Convert to target format if needed
            if project.output_format != "mp3":
                converted_path = f"/tmp/audiobook_{project_id}_conv.{project.output_format}"
                await convert_audio_format(final_path, converted_path, project.output_format)
                final_path = converted_path

            # Persist final audiobook
            final_stored = await persist_audio_file(final_path, prefix=f"audiobook/{project_id}")
            project.output_path = final_stored
            project.total_duration_seconds = total_duration
            project.file_size_bytes = os.path.getsize(final_path)
            project.status = AudiobookStatus.READY.value
            session.add(project)
            await session.commit()

            logger.info("Audiobook %s generated: %.1fs", project_id, total_duration)
            return {
                "project_id": str(project_id),
                "status": "ready",
                "duration_seconds": total_duration,
                "output_path": final_stored,
            }

        except Exception as exc:
            logger.exception("Audiobook %s generation failed: %s", project_id, exc)
            project.status = AudiobookStatus.FAILED.value
            project.error_message = str(exc)
            session.add(project)
            await session.commit()
            return {"project_id": str(project_id), "status": "failed", "error": str(exc)}