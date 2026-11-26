"""Audio Library service: import, metadata, chapters, playlists, search."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from app.audio.models import (
    AudioChapter,
    AudioFile,
    AudioPlaylist,
    AudioPlaylistItem,
    AudioStatus,
    TranscriptionSegment,
)
from app.config import settings
from app.exceptions import NotFoundError, ValidationFailedError
from app.storage import get_storage

logger = logging.getLogger(__name__)

_ALLOWED_AUDIO_MIME = {
    "audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav", "audio/wave",
    "audio/ogg", "audio/opus", "audio/webm", "audio/flac", "audio/x-flac",
    "audio/aac", "audio/mp4", "audio/x-m4a", "video/mp4", "video/webm",
}
_ALLOWED_AUDIO_EXT = {
    ".mp3", ".wav", ".ogg", ".opus", ".flac", ".aac", ".m4a",
    ".webm", ".mp4", ".wma",
}
_MAX_AUDIO_SIZE = settings.max_upload_size_mb * 1024 * 1024


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _is_allowed(mime_type: str, file_name: str) -> bool:
    if mime_type in _ALLOWED_AUDIO_MIME:
        return True
    ext = "." + file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
    return ext in _ALLOWED_AUDIO_EXT


# --------------------------------------------------------------------------- #
# Import
# --------------------------------------------------------------------------- #

async def create_audio_from_upload(
    session: AsyncSession,
    *,
    title: str | None,
    file_name: str,
    mime_type: str,
    data: bytes,
    owner_id: uuid.UUID | None = None,
    folder_id: uuid.UUID | None = None,
) -> AudioFile:
    if not _is_allowed(mime_type, file_name):
        raise ValidationFailedError(f"Unsupported audio type: {mime_type or file_name}")
    if len(data) > _MAX_AUDIO_SIZE:
        raise ValidationFailedError(
            f"Audio exceeds max size ({settings.max_upload_size_mb} MB)"
        )
    if not data:
        raise ValidationFailedError("Uploaded file is empty")

    audio_id = uuid.uuid4()
    storage = get_storage()
    object_name = storage.generate_object_name(file_name, audio_id)
    storage_path = storage.put_object(
        object_name, data, content_type=mime_type, length=len(data)
    )

    audio = AudioFile(
        id=audio_id,
        title=title or file_name,
        file_name=file_name,
        file_size=len(data),
        mime_type=mime_type,
        storage_path=storage_path,
        owner_id=owner_id,
        folder_id=folder_id,
        status=AudioStatus.PROCESSING,
    )
    session.add(audio)
    await session.commit()
    await session.refresh(audio)

    _dispatch_transcribe(audio.id)
    return audio


def _dispatch_transcribe(audio_id: uuid.UUID) -> None:
    """Best-effort background transcription without requiring Celery/Redis."""
    try:
        import asyncio

        from app.workers.transcribe import _transcribe

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop is not None:
            loop.create_task(_transcribe(audio_id))
        else:
            from app.workers._db import run_async

            run_async(_transcribe(audio_id))
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Transcription dispatch failed for %s: %s", audio_id, exc)


# --------------------------------------------------------------------------- #
# CRUD
# --------------------------------------------------------------------------- #

async def list_audio(
    session: AsyncSession,
    *,
    owner_id: uuid.UUID | None = None,
    folder_id: uuid.UUID | None = None,
    q: str | None = None,
    skip: int = 0,
    limit: int = 50,
    include_deleted: bool = False,
) -> tuple[list[AudioFile], int]:
    conditions = []
    if not include_deleted:
        conditions.append(AudioFile.is_deleted == False)  # noqa: E712
    if owner_id is not None:
        conditions.append(AudioFile.owner_id == owner_id)
    if folder_id is not None:
        conditions.append(AudioFile.folder_id == folder_id)
    if q:
        conditions.append(
            or_(
                col(AudioFile.title).ilike(f"%{q}%"),
                col(AudioFile.file_name).ilike(f"%{q}%"),
            )
        )

    base = select(AudioFile)
    if conditions:
        base = base.where(*conditions)

    total = (
        await session.execute(
            select(func.count()).select_from(base.subquery())
        )
    ).scalar_one()
    stmt = (
        base.order_by(col(AudioFile.created_at).desc()).offset(skip).limit(limit)
    )
    items = list((await session.execute(stmt)).scalars().all())
    return items, total


async def get_audio(session: AsyncSession, audio_id: uuid.UUID) -> AudioFile:
    audio = await session.get(AudioFile, audio_id)
    if audio is None or audio.is_deleted:
        raise NotFoundError("Audio not found")
    return audio


async def update_audio(
    session: AsyncSession,
    audio_id: uuid.UUID,
    *,
    title: str | None = None,
    folder_id: uuid.UUID | None = None,
) -> AudioFile:
    audio = await get_audio(session, audio_id)
    if title is not None:
        audio.title = title
    if folder_id is not None:
        audio.folder_id = folder_id
    audio.updated_at = _utcnow()
    session.add(audio)
    await session.commit()
    await session.refresh(audio)
    return audio


async def soft_delete_audio(session: AsyncSession, audio_id: uuid.UUID) -> None:
    audio = await get_audio(session, audio_id)
    audio.is_deleted = True
    audio.deleted_at = _utcnow()
    session.add(audio)
    await session.commit()


async def get_audio_bytes(session: AsyncSession, audio_id: uuid.UUID) -> tuple[bytes, str]:
    audio = await get_audio(session, audio_id)
    data = get_storage().get_object(audio.storage_path)
    return data, audio.mime_type


# --------------------------------------------------------------------------- #
# Chapters
# --------------------------------------------------------------------------- #

async def list_chapters(
    session: AsyncSession, audio_id: uuid.UUID
) -> list[AudioChapter]:
    stmt = (
        select(AudioChapter)
        .where(AudioChapter.audio_id == audio_id)
        .order_by(col(AudioChapter.order_index), col(AudioChapter.start_seconds))
    )
    return list((await session.execute(stmt)).scalars().all())


async def create_chapter(
    session: AsyncSession,
    *,
    audio_id: uuid.UUID,
    title: str,
    start_seconds: float,
    end_seconds: float | None = None,
) -> AudioChapter:
    chapter = AudioChapter(
        audio_id=audio_id,
        title=title,
        start_seconds=start_seconds,
        end_seconds=end_seconds,
        order_index=(await _chapter_count(session, audio_id)),
    )
    session.add(chapter)
    await session.commit()
    await session.refresh(chapter)
    return chapter


async def _chapter_count(session: AsyncSession, audio_id: uuid.UUID) -> int:
    return (
        await session.execute(
            select(func.count())
            .select_from(AudioChapter)
            .where(AudioChapter.audio_id == audio_id)
        )
    ).scalar_one()


async def delete_chapter(
    session: AsyncSession, chapter_id: uuid.UUID
) -> bool:
    chapter = await session.get(AudioChapter, chapter_id)
    if chapter is None:
        return False
    await session.delete(chapter)
    await session.commit()
    return True


# --------------------------------------------------------------------------- #
# Transcription segments + search
# --------------------------------------------------------------------------- #

async def list_segments(
    session: AsyncSession,
    audio_id: uuid.UUID,
    *,
    skip: int = 0,
    limit: int = 1000,
) -> list[TranscriptionSegment]:
    stmt = (
        select(TranscriptionSegment)
        .where(TranscriptionSegment.audio_id == audio_id)
        .order_by(col(TranscriptionSegment.segment_index))
        .offset(skip)
        .limit(limit)
    )
    return list((await session.execute(stmt)).scalars().all())


async def search_transcripts(
    session: AsyncSession,
    *,
    query: str,
    limit: int = 30,
) -> list[tuple[TranscriptionSegment, float]]:
    """Full-text search across all transcription segments."""
    if not query.strip():
        return []
    ts_query = func.plainto_tsquery("simple", query)
    stmt = (
        select(
            TranscriptionSegment,
            func.ts_rank(TranscriptionSegment.tsv, ts_query).label("rank"),
        )
        .where(TranscriptionSegment.tsv.op("@@")(ts_query))
        .order_by(func.ts_rank(TranscriptionSegment.tsv, ts_query).desc())
        .limit(limit)
    )
    rows = (await session.execute(stmt)).all()
    return [(seg, float(rank)) for seg, rank in rows]


# --------------------------------------------------------------------------- #
# Playlists
# --------------------------------------------------------------------------- #

async def create_playlist(
    session: AsyncSession,
    *,
    name: str,
    description: str | None = None,
    owner_id: uuid.UUID | None = None,
) -> AudioPlaylist:
    pl = AudioPlaylist(name=name, description=description, owner_id=owner_id)
    session.add(pl)
    await session.commit()
    await session.refresh(pl)
    return pl


async def list_playlists(
    session: AsyncSession, owner_id: uuid.UUID | None = None
) -> list[AudioPlaylist]:
    stmt = select(AudioPlaylist)
    if owner_id is not None:
        stmt = stmt.where(AudioPlaylist.owner_id == owner_id)
    stmt = stmt.order_by(col(AudioPlaylist.name))
    return list((await session.execute(stmt)).scalars().all())


async def add_to_playlist(
    session: AsyncSession, playlist_id: uuid.UUID, audio_id: uuid.UUID
) -> AudioPlaylistItem:
    count = (
        await session.execute(
            select(func.count())
            .select_from(AudioPlaylistItem)
            .where(AudioPlaylistItem.playlist_id == playlist_id)
        )
    ).scalar_one()
    item = AudioPlaylistItem(
        playlist_id=playlist_id, audio_id=audio_id, order_index=count
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


async def list_playlist_items(
    session: AsyncSession, playlist_id: uuid.UUID
) -> list[AudioPlaylistItem]:
    stmt = (
        select(AudioPlaylistItem)
        .where(AudioPlaylistItem.playlist_id == playlist_id)
        .order_by(col(AudioPlaylistItem.order_index))
    )
    return list((await session.execute(stmt)).scalars().all())