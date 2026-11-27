"""Cross-module integration: unified search, audio→KB, audio→Academy, workspace aggregates."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from app.documents.models import Document, TextChunk
from app.audio.models import AudioFile, TranscriptionSegment
from app.knowledge.models import KnowledgeBase, KnowledgeEntry
from app.academy.models import Course, CourseFolderLink
from app.exceptions import NotFoundError

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------- #
# Unified cross-module search
# --------------------------------------------------------------------------- #

async def unified_search(
    session: AsyncSession,
    *,
    query: str,
    owner_id: uuid.UUID | None = None,
    limit_per_module: int = 10,
) -> dict:
    """Search across documents, audio transcriptions, and knowledge entries."""
    if not query.strip():
        return {"documents": [], "audio": [], "knowledge": []}

    results: dict = {"documents": [], "audio": [], "knowledge": []}

    # 1. Document chunks (FTS)
    try:
        ts_query = func.plainto_tsquery("simple", query)
        doc_stmt = (
            select(
                TextChunk,
                func.ts_rank(TextChunk.tsv, ts_query).label("rank"),
            )
            .where(TextChunk.tsv.op("@@")(ts_query))
            .order_by(func.ts_rank(TextChunk.tsv, ts_query).desc())
            .limit(limit_per_module)
        )
        if owner_id:
            doc_stmt = doc_stmt.join(Document).where(Document.owner_id == owner_id)
        doc_rows = (await session.execute(doc_stmt)).all()
        for chunk, rank in doc_rows:
            results["documents"].append({
                "chunk_id": str(chunk.id),
                "document_id": str(chunk.document_id),
                "page": chunk.page_number,
                "text": chunk.text[:300],
                "score": round(float(rank), 4),
                "type": "document",
            })
    except Exception as exc:
        logger.warning("Unified search documents failed: %s", exc)

    # 2. Audio transcriptions (FTS)
    try:
        ts_query = func.plainto_tsquery("simple", query)
        audio_stmt = (
            select(
                TranscriptionSegment,
                func.ts_rank(TranscriptionSegment.tsv, ts_query).label("rank"),
            )
            .where(TranscriptionSegment.tsv.op("@@")(ts_query))
            .order_by(func.ts_rank(TranscriptionSegment.tsv, ts_query).desc())
            .limit(limit_per_module)
        )
        audio_rows = (await session.execute(audio_stmt)).all()
        for seg, rank in audio_rows:
            results["audio"].append({
                "segment_id": str(seg.id),
                "audio_id": str(seg.audio_id),
                "start_seconds": seg.start_seconds,
                "text": seg.text[:300],
                "speaker": seg.speaker,
                "score": round(float(rank), 4),
                "type": "audio_transcript",
            })
    except Exception as exc:
        logger.warning("Unified search audio failed: %s", exc)

    # 3. Knowledge entries (FTS)
    try:
        ts_query = func.plainto_tsquery("simple", query)
        kb_stmt = (
            select(
                KnowledgeEntry,
                func.ts_rank(KnowledgeEntry.tsv, ts_query).label("rank"),
            )
            .where(KnowledgeEntry.tsv.op("@@")(ts_query))
            .order_by(func.ts_rank(KnowledgeEntry.tsv, ts_query).desc())
            .limit(limit_per_module)
        )
        if owner_id:
            kb_stmt = kb_stmt.join(KnowledgeBase).where(
                KnowledgeBase.owner_id == owner_id
            )
        kb_rows = (await session.execute(kb_stmt)).all()
        for entry, rank in kb_rows:
            results["knowledge"].append({
                "entry_id": str(entry.id),
                "kb_id": str(entry.kb_id),
                "text": entry.text[:300],
                "section": entry.section,
                "score": round(float(rank), 4),
                "type": "knowledge_entry",
            })
    except Exception as exc:
        logger.warning("Unified search knowledge failed: %s", exc)

    return results


# --------------------------------------------------------------------------- #
# Audio → Knowledge: add transcript segments as KB entries
# --------------------------------------------------------------------------- #

async def audio_transcript_to_knowledge(
    session: AsyncSession,
    *,
    audio_id: uuid.UUID,
    kb_id: uuid.UUID,
    owner_id: uuid.UUID | None = None,
) -> dict:
    """Import audio transcript segments into a knowledge base."""
    from app.audio.models import AudioFile
    from app.ai.embeddings import embed_texts

    audio = await session.get(AudioFile, audio_id)
    if not audio:
        raise NotFoundError("Audio not found")

    kb = await session.get(KnowledgeBase, kb_id)
    if not kb:
        raise NotFoundError("Knowledge base not found")

    segments = list(
        (await session.execute(
            select(TranscriptionSegment)
            .where(TranscriptionSegment.audio_id == audio_id)
            .order_by(col(TranscriptionSegment.segment_index))
        )).scalars().all()
    )

    if not segments:
        return {"audio_id": str(audio_id), "entries_created": 0, "message": "No transcript segments"}

    # Batch embed
    texts = [seg.text for seg in segments]
    try:
        vectors = embed_texts(texts)
    except Exception:
        vectors = [None] * len(segments)

    created = 0
    for seg, vec in zip(segments, vectors):
        entry = KnowledgeEntry(
            kb_id=kb_id,
            chunk_index=seg.segment_index,
            text=seg.text,
            page_number=1,
            section=f"Audio: {audio.title} [{seg.start_seconds:.0f}s]",
            direction="ltr",
            embedding=vec,
            tsv=func.to_tsvector("simple", seg.text),
        )
        session.add(entry)
        created += 1

    await session.commit()
    logger.info("Imported %d audio segments into KB %s", created, kb_id)
    return {
        "audio_id": str(audio_id),
        "kb_id": str(kb_id),
        "entries_created": created,
    }


# --------------------------------------------------------------------------- #
# Audio → Academy: create a lesson from audio transcript
# --------------------------------------------------------------------------- #

async def audio_to_academy_lesson(
    session: AsyncSession,
    *,
    audio_id: uuid.UUID,
    course_id: uuid.UUID,
    topic: str | None = None,
    owner_id: uuid.UUID | None = None,
) -> dict:
    """Create an Academy lesson from an audio file's transcript."""
    from app.audio.models import AudioFile
    from app.academy.intelligence_models import Lesson, LessonType, LessonStatus

    audio = await session.get(AudioFile, audio_id)
    if not audio:
        raise NotFoundError("Audio not found")

    course = await session.get(Course, course_id)
    if not course:
        raise NotFoundError("Course not found")

    segments = list(
        (await session.execute(
            select(TranscriptionSegment)
            .where(TranscriptionSegment.audio_id == audio_id)
            .order_by(col(TranscriptionSegment.segment_index))
        )).scalars().all()
    )

    # Build lesson content from transcript
    if segments:
        content = "\n\n".join(
            f"[{seg.start_seconds:.0f}s] {seg.text}" for seg in segments
        )
    else:
        content = audio.summary or f"Audio file: {audio.title}"

    lesson = Lesson(
        course_id=course_id,
        topic=topic or audio.title,
        title=topic or audio.title,
        content=content[:50000],
        lesson_type=LessonType.CONCEPT,
        status=LessonStatus.DRAFT,
        order_index=0,
        estimated_minutes=int((audio.duration_seconds or 0) / 60) or None,
        ai_generated=False,
    )
    session.add(lesson)
    await session.commit()
    await session.refresh(lesson)

    logger.info("Created lesson %s from audio %s", lesson.id, audio_id)
    return {
        "lesson_id": str(lesson.id),
        "course_id": str(course_id),
        "audio_id": str(audio_id),
        "title": lesson.title,
    }


# --------------------------------------------------------------------------- #
# Workspace aggregates (unified dashboard)
# --------------------------------------------------------------------------- #

async def get_workspace_stats(
    session: AsyncSession,
    owner_id: uuid.UUID | None = None,
) -> dict:
    """Return aggregate counts across all modules for the Workspace dashboard."""
    stats: dict = {}

    # Documents
    doc_stmt = select(func.count()).select_from(Document)
    if owner_id:
        doc_stmt = doc_stmt.where(Document.owner_id == owner_id)
    stats["documents_total"] = (await session.execute(doc_stmt)).scalar_one()
    stats["documents_ready"] = (
        await session.execute(
            doc_stmt.where(Document.status == "ready")
        )
    ).scalar_one()

    # Audio
    audio_stmt = select(func.count()).select_from(AudioFile)
    if owner_id:
        audio_stmt = audio_stmt.where(AudioFile.owner_id == owner_id)
    stats["audio_total"] = (await session.execute(audio_stmt)).scalar_one()
    stats["audio_transcribed"] = (
        await session.execute(audio_stmt.where(AudioFile.has_transcript == True))  # noqa: E712
    ).scalar_one()

    # Knowledge bases
    kb_stmt = select(func.count()).select_from(KnowledgeBase)
    if owner_id:
        kb_stmt = kb_stmt.where(KnowledgeBase.owner_id == owner_id)
    stats["knowledge_bases"] = (await session.execute(kb_stmt)).scalar_one()

    # Academy courses
    course_stmt = select(func.count()).select_from(Course)
    if owner_id:
        course_stmt = course_stmt.where(Course.owner_id == owner_id)
    stats["academy_courses"] = (await session.execute(course_stmt)).scalar_one()

    # Recent activity (last 5 items across modules)
    recent: list[dict] = []

    # Recent documents
    doc_items = list(
        (await session.execute(
            select(Document)
            .order_by(col(Document.created_at).desc())
            .limit(3)
        )).scalars().all()
    )
    for d in doc_items:
        recent.append({"type": "document", "id": str(d.id), "title": d.title, "at": d.created_at.isoformat()})

    # Recent audio
    audio_items = list(
        (await session.execute(
            select(AudioFile)
            .order_by(col(AudioFile.created_at).desc())
            .limit(2)
        )).scalars().all()
    )
    for a in audio_items:
        recent.append({"type": "audio", "id": str(a.id), "title": a.title, "at": a.created_at.isoformat()})

    stats["recent"] = recent
    return stats