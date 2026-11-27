"""Audio Creation Studio HTTP endpoints: voices, pronunciation, audiobooks, podcasts, versions."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from app.audio_creation import service
from app.audio_creation.models import (
    AudiobookProject,
    AudiobookStatus,
    PodcastProject,
    PodcastStatus,
    TTSVoice,
)
from app.auth.router import get_current_user
from app.database import get_session
from app.users.models import User
from app.users.schemas import Message

router = APIRouter(prefix="/creation", tags=["audio-creation"])


# --------------------------------------------------------------------------- #
# Schemas
# --------------------------------------------------------------------------- #

class VoiceRead(SQLModel):
    id: uuid.UUID
    name: str
    display_name: str
    provider: str
    language: str
    gender: str
    sample_rate: int
    is_default_for_lang: bool


class AudiobookCreate(SQLModel):
    title: str
    source_document_id: uuid.UUID
    voice_id: uuid.UUID
    speed: float = 1.0
    pause_between_paragraphs_ms: int = 500
    pause_between_sentences_ms: int = 200
    output_format: str = "mp3"


class AudiobookRead(SQLModel):
    id: uuid.UUID
    title: str
    source_document_id: uuid.UUID
    voice_id: uuid.UUID
    speed: float
    status: str
    output_path: str | None
    output_format: str
    total_duration_seconds: float | None
    file_size_bytes: int | None
    version: int
    error_message: str | None
    created_at: str


class PodcastCreate(SQLModel):
    title: str
    description: str | None = None
    intro_music_path: str | None = None
    outro_music_path: str | None = None
    default_pause_ms: int = 300
    output_format: str = "mp3"


class PodcastRead(SQLModel):
    id: uuid.UUID
    title: str
    description: str | None
    status: str
    output_path: str | None
    output_format: str
    total_duration_seconds: float | None
    file_size_bytes: int | None
    version: int
    error_message: str | None
    created_at: str


class SpeakerCreate(SQLModel):
    name: str
    voice_id: uuid.UUID
    color: str | None = None


class SegmentCreate(SQLModel):
    speaker_id: uuid.UUID | None = None
    text: str
    voice_speed: float | None = None
    pause_before_ms: int | None = None
    pause_after_ms: int | None = None
    emotion: str | None = None


def _audiobook_read(p: AudiobookProject) -> AudiobookRead:
    return AudiobookRead(
        id=p.id,
        title=p.title,
        source_document_id=p.source_document_id,
        voice_id=p.voice_id,
        speed=p.speed,
        status=p.status,
        output_path=p.output_path,
        output_format=p.output_format,
        total_duration_seconds=p.total_duration_seconds,
        file_size_bytes=p.file_size_bytes,
        version=p.version,
        error_message=p.error_message,
        created_at=p.created_at.isoformat(),
    )


def _podcast_read(p: PodcastProject) -> PodcastRead:
    return PodcastRead(
        id=p.id,
        title=p.title,
        description=p.description,
        status=p.status,
        output_path=p.output_path,
        output_format=p.output_format,
        total_duration_seconds=p.total_duration_seconds,
        file_size_bytes=p.file_size_bytes,
        version=p.version,
        error_message=p.error_message,
        created_at=p.created_at.isoformat(),
    )


# --------------------------------------------------------------------------- #
# Voices
# --------------------------------------------------------------------------- #

@router.get("/voices", response_model=list[VoiceRead])
async def list_voices(
    language: str | None = Query(default=None),
    provider: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[VoiceRead]:
    voices = await service.list_voices(session, language=language, provider=provider)
    return [
        VoiceRead(
            id=v.id,
            name=v.name,
            display_name=v.display_name,
            provider=v.provider,
            language=v.language,
            gender=v.gender,
            sample_rate=v.sample_rate,
            is_default_for_lang=v.is_default_for_lang,
        )
        for v in voices
    ]


# --------------------------------------------------------------------------- #
# Pronunciation rules
# --------------------------------------------------------------------------- #

@router.get("/pronunciation", response_model=list[dict])
async def list_pronunciation(
    language: str = Query(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    rules = await service.list_pronunciation_rules(session, language=language)
    return [
        {
            "id": str(r.id),
            "word": r.word,
            "replacement": r.replacement,
            "rule_type": r.rule_type,
            "is_active": r.is_active,
        }
        for r in rules
    ]


@router.post("/pronunciation", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_pronunciation(
    body: dict,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    rule = await service.create_pronunciation_rule(
        session,
        language=body["language"],
        word=body["word"],
        replacement=body["replacement"],
        rule_type=body.get("rule_type", "replace"),
        case_sensitive=body.get("case_sensitive", False),
    )
    return {
        "id": str(rule.id),
        "word": rule.word,
        "replacement": rule.replacement,
        "rule_type": rule.rule_type,
    }


# --------------------------------------------------------------------------- #
# Audiobooks
# --------------------------------------------------------------------------- #

@router.post("/audiobooks", response_model=AudiobookRead, status_code=status.HTTP_201_CREATED)
async def create_audiobook(
    body: AudiobookCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AudiobookRead:
    project = await service.create_audiobook_project(
        session,
        title=body.title,
        source_document_id=body.source_document_id,
        voice_id=body.voice_id,
        owner_id=current_user.id,
        speed=body.speed,
        pause_between_paragraphs_ms=body.pause_between_paragraphs_ms,
        pause_between_sentences_ms=body.pause_between_sentences_ms,
        output_format=body.output_format,
    )
    return _audiobook_read(project)


@router.get("/audiobooks", response_model=list[AudiobookRead])
async def list_audiobooks(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[AudiobookRead]:
    projects = await service.list_audiobook_projects(
        session, owner_id=current_user.id, skip=skip, limit=limit
    )
    return [_audiobook_read(p) for p in projects]


@router.get("/audiobooks/{project_id}", response_model=AudiobookRead)
async def get_audiobook(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AudiobookRead:
    project = await service.get_audiobook_project(session, project_id)
    return _audiobook_read(project)


@router.post("/audiobooks/{project_id}/generate", response_model=Message)
async def generate_audiobook_endpoint(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Message:
    await service.dispatch_audiobook_generation(project_id)
    return Message(message="Audiobook generation started")


@router.get("/audiobooks/{project_id}/chapters", response_model=list[dict])
async def list_audiobook_chapters(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    chapters = await service.list_audiobook_chapters(session, project_id)
    return [
        {
            "id": str(c.id),
            "title": c.title,
            "order_index": c.order_index,
            "status": c.status,
            "duration_seconds": c.duration_seconds,
            "audio_path": c.audio_path,
        }
        for c in chapters
    ]


# --------------------------------------------------------------------------- #
# Podcasts
# --------------------------------------------------------------------------- #

@router.post("/podcasts", response_model=PodcastRead, status_code=status.HTTP_201_CREATED)
async def create_podcast(
    body: PodcastCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> PodcastRead:
    project = await service.create_podcast_project(
        session,
        title=body.title,
        description=body.description,
        owner_id=current_user.id,
        intro_music_path=body.intro_music_path,
        outro_music_path=body.outro_music_path,
        default_pause_ms=body.default_pause_ms,
        output_format=body.output_format,
    )
    return _podcast_read(project)


@router.get("/podcasts", response_model=list[PodcastRead])
async def list_podcasts(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[PodcastRead]:
    projects = await service.list_podcast_projects(
        session, owner_id=current_user.id, skip=skip, limit=limit
    )
    return [_podcast_read(p) for p in projects]


@router.get("/podcasts/{project_id}", response_model=PodcastRead)
async def get_podcast(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> PodcastRead:
    project = await service.get_podcast_project(session, project_id)
    return _podcast_read(project)


@router.post("/podcasts/{project_id}/generate", response_model=Message)
async def generate_podcast_endpoint(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Message:
    await service.dispatch_podcast_generation(project_id)
    return Message(message="Podcast generation started")


@router.get("/podcasts/{project_id}/speakers", response_model=list[dict])
async def list_podcast_speakers(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    speakers = await service.list_podcast_speakers(session, project_id)
    return [
        {
            "id": str(s.id),
            "name": s.name,
            "voice_id": str(s.voice_id),
            "color": s.color,
            "order_index": s.order_index,
        }
        for s in speakers
    ]


@router.post("/podcasts/{project_id}/speakers", response_model=dict, status_code=status.HTTP_201_CREATED)
async def add_podcast_speaker(
    project_id: uuid.UUID,
    body: SpeakerCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    sp = await service.add_podcast_speaker(
        session,
        project_id=project_id,
        name=body.name,
        voice_id=body.voice_id,
        color=body.color,
    )
    return {
        "id": str(sp.id),
        "name": sp.name,
        "voice_id": str(sp.voice_id),
        "color": sp.color,
    }


@router.get("/podcasts/{project_id}/segments", response_model=list[dict])
async def list_podcast_segments(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    segments = await service.list_podcast_segments(session, project_id)
    return [
        {
            "id": str(s.id),
            "speaker_id": str(s.speaker_id) if s.speaker_id else None,
            "text": s.text,
            "order_index": s.order_index,
            "voice_speed": s.voice_speed,
            "pause_before_ms": s.pause_before_ms,
            "pause_after_ms": s.pause_after_ms,
            "emotion": s.emotion,
            "status": s.status,
            "duration_seconds": s.duration_seconds,
        }
        for s in segments
    ]


@router.post("/podcasts/{project_id}/segments", response_model=dict, status_code=status.HTTP_201_CREATED)
async def add_podcast_segment(
    project_id: uuid.UUID,
    body: SegmentCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    seg = await service.add_podcast_segment(
        session,
        project_id=project_id,
        speaker_id=body.speaker_id,
        text=body.text,
        voice_speed=body.voice_speed,
        pause_before_ms=body.pause_before_ms,
        pause_after_ms=body.pause_after_ms,
        emotion=body.emotion,
    )
    return {
        "id": str(seg.id),
        "speaker_id": str(seg.speaker_id) if seg.speaker_id else None,
        "text": seg.text,
        "order_index": seg.order_index,
    }


# --------------------------------------------------------------------------- #
# Versions
# --------------------------------------------------------------------------- #

@router.get("/versions", response_model=list[dict])
async def list_versions(
    project_type: str = Query(...),
    project_id: uuid.UUID = Query(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    versions = await service.list_project_versions(
        session, project_type=project_type, project_id=project_id
    )
    return [
        {
            "id": str(v.id),
            "version_number": v.version_number,
            "label": v.label,
            "change_summary": v.change_summary,
            "created_at": v.created_at.isoformat(),
        }
        for v in versions
    ]