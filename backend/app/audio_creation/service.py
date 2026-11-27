"""Audio Creation Studio service layer."""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from app.audio_creation.models import (
    AudiobookChapter,
    AudiobookProject,
    AudiobookStatus,
    PodcastProject,
    PodcastSegment,
    PodcastSpeaker,
    PodcastStatus,
    ProjectVersion,
    PronunciationRule,
    TTSVoice,
    VoiceGender,
    VoiceProvider,
)
from app.exceptions import NotFoundError

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------- #
# Voice management
# --------------------------------------------------------------------------- #

async def list_voices(
    session: AsyncSession,
    language: str | None = None,
    provider: str | None = None,
) -> list[TTSVoice]:
    conditions = [TTSVoice.is_active == True]  # noqa: E712
    if language:
        conditions.append(TTSVoice.language == language)
    if provider:
        conditions.append(TTSVoice.provider == provider)
    stmt = (
        select(TTSVoice)
        .where(*conditions)
        .order_by(col(TTSVoice.language), col(TTSVoice.is_default_for_lang).desc())
    )
    return list((await session.execute(stmt)).scalars().all())


# --------------------------------------------------------------------------- #
# Pronunciation rules
# --------------------------------------------------------------------------- #

async def list_pronunciation_rules(
    session: AsyncSession, language: str
) -> list[PronunciationRule]:
    stmt = (
        select(PronunciationRule)
        .where(
            PronunciationRule.language == language,
            PronunciationRule.is_active == True,  # noqa: E712
        )
        .order_by(col(PronunciationRule.word))
    )
    return list((await session.execute(stmt)).scalars().all())


async def create_pronunciation_rule(
    session: AsyncSession,
    *,
    language: str,
    word: str,
    replacement: str,
    rule_type: str = "replace",
    case_sensitive: bool = False,
) -> PronunciationRule:
    rule = PronunciationRule(
        language=language,
        word=word,
        replacement=replacement,
        rule_type=rule_type,
        case_sensitive=case_sensitive,
    )
    session.add(rule)
    await session.commit()
    await session.refresh(rule)
    return rule


# --------------------------------------------------------------------------- #
# Audiobook projects
# --------------------------------------------------------------------------- #

async def create_audiobook_project(
    session: AsyncSession,
    *,
    title: str,
    source_document_id: uuid.UUID,
    voice_id: uuid.UUID,
    owner_id: uuid.UUID | None = None,
    speed: float = 1.0,
    pause_between_paragraphs_ms: int = 500,
    pause_between_sentences_ms: int = 200,
    output_format: str = "mp3",
) -> AudiobookProject:
    project = AudiobookProject(
        title=title,
        source_document_id=source_document_id,
        voice_id=voice_id,
        owner_id=owner_id,
        speed=speed,
        pause_between_paragraphs_ms=pause_between_paragraphs_ms,
        pause_between_sentences_ms=pause_between_sentences_ms,
        output_format=output_format,
        status=AudiobookStatus.DRAFT.value,
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


async def list_audiobook_projects(
    session: AsyncSession,
    *,
    owner_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[AudiobookProject]:
    conditions = []
    if owner_id:
        conditions.append(AudiobookProject.owner_id == owner_id)
    stmt = select(AudiobookProject)
    if conditions:
        stmt = stmt.where(*conditions)
    stmt = stmt.order_by(col(AudiobookProject.created_at).desc()).offset(skip).limit(limit)
    return list((await session.execute(stmt)).scalars().all())


async def get_audiobook_project(
    session: AsyncSession, project_id: uuid.UUID
) -> AudiobookProject:
    project = await session.get(AudiobookProject, project_id)
    if not project:
        raise NotFoundError("Audiobook project not found")
    return project


async def list_audiobook_chapters(
    session: AsyncSession, project_id: uuid.UUID
) -> list[AudiobookChapter]:
    stmt = (
        select(AudiobookChapter)
        .where(AudiobookChapter.project_id == project_id)
        .order_by(col(AudiobookChapter.order_index))
    )
    return list((await session.execute(stmt)).scalars().all())


async def dispatch_audiobook_generation(project_id: uuid.UUID) -> None:
    try:
        import asyncio

        from app.workers.audiobook import _generate_audiobook

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop is not None:
            loop.create_task(_generate_audiobook(project_id))
        else:
            from app.workers._db import run_async
            run_async(_generate_audiobook(project_id))
    except Exception as exc:
        logger.warning("Audiobook dispatch failed for %s: %s", project_id, exc)


# --------------------------------------------------------------------------- #
# Podcast projects
# --------------------------------------------------------------------------- #

async def create_podcast_project(
    session: AsyncSession,
    *,
    title: str,
    description: str | None = None,
    owner_id: uuid.UUID | None = None,
    intro_music_path: str | None = None,
    outro_music_path: str | None = None,
    default_pause_ms: int = 300,
    output_format: str = "mp3",
) -> PodcastProject:
    project = PodcastProject(
        title=title,
        description=description,
        owner_id=owner_id,
        intro_music_path=intro_music_path,
        outro_music_path=outro_music_path,
        default_pause_ms=default_pause_ms,
        output_format=output_format,
        status=PodcastStatus.DRAFT.value,
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


async def list_podcast_projects(
    session: AsyncSession,
    *,
    owner_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[PodcastProject]:
    conditions = []
    if owner_id:
        conditions.append(PodcastProject.owner_id == owner_id)
    stmt = select(PodcastProject)
    if conditions:
        stmt = stmt.where(*conditions)
    stmt = stmt.order_by(col(PodcastProject.created_at).desc()).offset(skip).limit(limit)
    return list((await session.execute(stmt)).scalars().all())


async def get_podcast_project(
    session: AsyncSession, project_id: uuid.UUID
) -> PodcastProject:
    project = await session.get(PodcastProject, project_id)
    if not project:
        raise NotFoundError("Podcast project not found")
    return project


async def list_podcast_speakers(
    session: AsyncSession, project_id: uuid.UUID
) -> list[PodcastSpeaker]:
    stmt = (
        select(PodcastSpeaker)
        .where(PodcastSpeaker.project_id == project_id)
        .order_by(col(PodcastSpeaker.order_index))
    )
    return list((await session.execute(stmt)).scalars().all())


async def add_podcast_speaker(
    session: AsyncSession,
    *,
    project_id: uuid.UUID,
    name: str,
    voice_id: uuid.UUID,
    color: str | None = None,
) -> PodcastSpeaker:
    count = (
        await session.execute(
            select(func.count())
            .select_from(PodcastSpeaker)
            .where(PodcastSpeaker.project_id == project_id)
        )
    ).scalar_one()
    sp = PodcastSpeaker(
        project_id=project_id,
        name=name,
        voice_id=voice_id,
        color=color,
        order_index=count,
    )
    session.add(sp)
    await session.commit()
    await session.refresh(sp)
    return sp


async def list_podcast_segments(
    session: AsyncSession, project_id: uuid.UUID
) -> list[PodcastSegment]:
    stmt = (
        select(PodcastSegment)
        .where(PodcastSegment.project_id == project_id)
        .order_by(col(PodcastSegment.order_index))
    )
    return list((await session.execute(stmt)).scalars().all())


async def add_podcast_segment(
    session: AsyncSession,
    *,
    project_id: uuid.UUID,
    speaker_id: uuid.UUID | None = None,
    text: str,
    voice_speed: float | None = None,
    pause_before_ms: int | None = None,
    pause_after_ms: int | None = None,
    emotion: str | None = None,
) -> PodcastSegment:
    count = (
        await session.execute(
            select(func.count())
            .select_from(PodcastSegment)
            .where(PodcastSegment.project_id == project_id)
        )
    ).scalar_one()
    seg = PodcastSegment(
        project_id=project_id,
        speaker_id=speaker_id,
        text=text,
        order_index=count,
        voice_speed=voice_speed,
        pause_before_ms=pause_before_ms,
        pause_after_ms=pause_after_ms,
        emotion=emotion,
    )
    session.add(seg)
    await session.commit()
    await session.refresh(seg)
    return seg


async def dispatch_podcast_generation(project_id: uuid.UUID) -> None:
    try:
        import asyncio

        from app.workers.podcast import _generate_podcast

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop is not None:
            loop.create_task(_generate_podcast(project_id))
        else:
            from app.workers._db import run_async
            run_async(_generate_podcast(project_id))
    except Exception as exc:
        logger.warning("Podcast dispatch failed for %s: %s", project_id, exc)


# --------------------------------------------------------------------------- #
# Versions
# --------------------------------------------------------------------------- #

async def list_project_versions(
    session: AsyncSession,
    *,
    project_type: str,
    project_id: uuid.UUID,
) -> list[ProjectVersion]:
    stmt = (
        select(ProjectVersion)
        .where(
            ProjectVersion.project_type == project_type,
            ProjectVersion.project_id == project_id,
        )
        .order_by(col(ProjectVersion.version_number).desc())
    )
    return list((await session.execute(stmt)).scalars().all())