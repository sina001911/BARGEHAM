"""Audio Library HTTP endpoints: upload, CRUD, stream, chapters, segments, playlists."""
from __future__ import annotations

import uuid
from urllib.parse import quote

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from app.audio import service
from app.audio.models import AudioStatus
from app.auth.router import get_current_user
from app.database import get_session
from app.users.models import User
from app.users.schemas import Message

router = APIRouter(prefix="/audio", tags=["audio"])


# --------------------------------------------------------------------------- #
# Schemas
# --------------------------------------------------------------------------- #

class AudioRead(SQLModel):
    id: uuid.UUID
    title: str
    file_name: str
    file_size: int
    mime_type: str
    duration_seconds: float | None = None
    bitrate: int | None = None
    sample_rate: int | None = None
    channels: int | None = None
    codec: str | None = None
    status: str
    language: str | None = None
    has_transcript: bool = False
    transcript_confidence: float | None = None
    summary: str | None = None
    created_at: str


class AudioListResponse(SQLModel):
    items: list[AudioRead]
    total: int
    skip: int
    limit: int


class UploadAudioResponse(SQLModel):
    audio_id: uuid.UUID
    message: str
    status: str


class ChapterCreate(SQLModel):
    title: str
    start_seconds: float
    end_seconds: float | None = None


class ChapterRead(SQLModel):
    id: uuid.UUID
    audio_id: uuid.UUID
    title: str
    start_seconds: float
    end_seconds: float | None = None
    order_index: int


class SegmentRead(SQLModel):
    id: uuid.UUID
    audio_id: uuid.UUID
    segment_index: int
    start_seconds: float
    end_seconds: float
    text: str
    speaker: str | None = None
    confidence: float | None = None


class PlaylistCreate(SQLModel):
    name: str
    description: str | None = None


def _to_read(a: service.AudioFile) -> AudioRead:
    return AudioRead(
        id=a.id,
        title=a.title,
        file_name=a.file_name,
        file_size=a.file_size,
        mime_type=a.mime_type,
        duration_seconds=a.duration_seconds,
        bitrate=a.bitrate,
        sample_rate=a.sample_rate,
        channels=a.channels,
        codec=a.codec,
        status=a.status.value if isinstance(a.status, AudioStatus) else str(a.status),
        language=a.language,
        has_transcript=a.has_transcript,
        transcript_confidence=a.transcript_confidence,
        summary=a.summary,
        created_at=a.created_at.isoformat(),
    )


# --------------------------------------------------------------------------- #
# Upload + CRUD
# --------------------------------------------------------------------------- #

@router.post("", response_model=UploadAudioResponse, status_code=status.HTTP_201_CREATED)
async def upload_audio(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    folder_id: uuid.UUID | None = Form(default=None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UploadAudioResponse:
    data = await file.read()
    audio = await service.create_audio_from_upload(
        session,
        title=title,
        file_name=file.filename or "audio",
        mime_type=file.content_type or "application/octet-stream",
        data=data,
        owner_id=current_user.id,
        folder_id=folder_id,
    )
    return UploadAudioResponse(
        audio_id=audio.id,
        message="Audio uploaded and queued for transcription",
        status=audio.status.value,
    )


@router.get("", response_model=AudioListResponse)
async def list_audio(
    q: str | None = Query(default=None),
    folder_id: uuid.UUID | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    include_deleted: bool = Query(default=False),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AudioListResponse:
    items, total = await service.list_audio(
        session,
        owner_id=current_user.id,
        folder_id=folder_id,
        q=q,
        skip=skip,
        limit=limit,
        include_deleted=include_deleted,
    )
    return AudioListResponse(
        items=[_to_read(a) for a in items], total=total, skip=skip, limit=limit
    )


@router.get("/{audio_id}", response_model=AudioRead)
async def get_audio(
    audio_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AudioRead:
    return _to_read(await service.get_audio(session, audio_id))


@router.patch("/{audio_id}", response_model=AudioRead)
async def update_audio(
    audio_id: uuid.UUID,
    title: str | None = Form(default=None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> AudioRead:
    audio = await service.update_audio(session, audio_id, title=title)
    return _to_read(audio)


@router.delete("/{audio_id}", response_model=Message)
async def delete_audio(
    audio_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Message:
    await service.soft_delete_audio(session, audio_id)
    return Message(message="Audio moved to trash")


@router.get("/{audio_id}/stream")
async def stream_audio(
    audio_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Response:
    data, mime_type = await service.get_audio_bytes(session, audio_id)
    audio = await service.get_audio(session, audio_id)
    filename = quote(audio.file_name)
    return Response(
        content=data,
        media_type=mime_type,
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{filename}",
            "Accept-Ranges": "bytes",
            "X-Content-Type-Options": "nosniff",
        },
    )


# --------------------------------------------------------------------------- #
# Chapters
# --------------------------------------------------------------------------- #

@router.get("/{audio_id}/chapters", response_model=list[ChapterRead])
async def list_chapters(
    audio_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[ChapterRead]:
    chapters = await service.list_chapters(session, audio_id)
    return [
        ChapterRead(
            id=c.id,
            audio_id=c.audio_id,
            title=c.title,
            start_seconds=c.start_seconds,
            end_seconds=c.end_seconds,
            order_index=c.order_index,
        )
        for c in chapters
    ]


@router.post(
    "/{audio_id}/chapters",
    response_model=ChapterRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_chapter(
    audio_id: uuid.UUID,
    body: ChapterCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ChapterRead:
    chapter = await service.create_chapter(
        session,
        audio_id=audio_id,
        title=body.title,
        start_seconds=body.start_seconds,
        end_seconds=body.end_seconds,
    )
    return ChapterRead(
        id=chapter.id,
        audio_id=chapter.audio_id,
        title=chapter.title,
        start_seconds=chapter.start_seconds,
        end_seconds=chapter.end_seconds,
        order_index=chapter.order_index,
    )


# --------------------------------------------------------------------------- #
# Transcription
# --------------------------------------------------------------------------- #

@router.get("/{audio_id}/segments", response_model=list[SegmentRead])
async def list_segments(
    audio_id: uuid.UUID,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=1000, ge=1, le=5000),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[SegmentRead]:
    segments = await service.list_segments(
        session, audio_id, skip=skip, limit=limit
    )
    return [
        SegmentRead(
            id=s.id,
            audio_id=s.audio_id,
            segment_index=s.segment_index,
            start_seconds=s.start_seconds,
            end_seconds=s.end_seconds,
            text=s.text,
            speaker=s.speaker,
            confidence=s.confidence,
        )
        for s in segments
    ]


@router.get("/search/transcripts")
async def search_transcripts(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=30, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    results = await service.search_transcripts(session, query=q, limit=limit)
    return [
        {
            "segment_id": str(seg.id),
            "audio_id": str(seg.audio_id),
            "start_seconds": seg.start_seconds,
            "text": seg.text,
            "speaker": seg.speaker,
            "score": round(score, 4),
        }
        for seg, score in results
    ]


# --------------------------------------------------------------------------- #
# Playlists
# --------------------------------------------------------------------------- #

playlists_router = APIRouter(prefix="/audio/playlists", tags=["audio"])


@playlists_router.get("", response_model=list[dict])
async def list_playlists(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    pls = await service.list_playlists(session, owner_id=current_user.id)
    return [
        {
            "id": str(p.id),
            "name": p.name,
            "description": p.description,
            "created_at": p.created_at.isoformat(),
        }
        for p in pls
    ]


@playlists_router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_playlist(
    body: PlaylistCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    pl = await service.create_playlist(
        session, name=body.name, description=body.description, owner_id=current_user.id
    )
    return {
        "id": str(pl.id),
        "name": pl.name,
        "description": pl.description,
        "created_at": pl.created_at.isoformat(),
    }


@playlists_router.get("/{playlist_id}/items", response_model=list[dict])
async def list_playlist_items(
    playlist_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    items = await service.list_playlist_items(session, playlist_id)
    out = []
    for it in items:
        audio = await session.get(service.AudioFile, it.audio_id)
        out.append(
            {
                "item_id": str(it.id),
                "audio_id": str(it.audio_id),
                "order_index": it.order_index,
                "title": audio.title if audio else None,
            }
        )
    return out


@playlists_router.post(
    "/{playlist_id}/items", response_model=dict, status_code=status.HTTP_201_CREATED
)
async def add_playlist_item(
    playlist_id: uuid.UUID,
    audio_id: uuid.UUID = Query(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    item = await service.add_to_playlist(session, playlist_id, audio_id)
    return {"item_id": str(item.id), "order_index": item.order_index}