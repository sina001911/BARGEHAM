"""Audio Library models: audio files, chapters, transcription segments, playlists."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, Index
from sqlalchemy.dialects import postgresql
from sqlmodel import Field, SQLModel

from app.config import settings

from pgvector.sqlalchemy import Vector as _Vector


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AudioStatus(str, enum.Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    TRANSCRIBED = "transcribed"
    FAILED = "failed"


class AudioFile(SQLModel, table=True):
    """An imported audio file with metadata and optional transcription."""
    __tablename__ = "audiofile"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(max_length=500)
    file_name: str = Field(max_length=500)
    file_size: int = Field(default=0)
    mime_type: str = Field(max_length=100)
    storage_path: str = Field(max_length=1024)
    owner_id: uuid.UUID | None = Field(default=None, foreign_key="user.id", index=True)
    folder_id: uuid.UUID | None = Field(default=None, foreign_key="folder.id")

    # --- Metadata (filled by the import worker) ---
    duration_seconds: float | None = Field(default=None)
    bitrate: int | None = Field(default=None)
    sample_rate: int | None = Field(default=None)
    channels: int | None = Field(default=None)
    codec: str | None = Field(default=None, max_length=50)

    # --- Transcription state ---
    status: AudioStatus = Field(default=AudioStatus.UPLOADING)
    language: str | None = Field(default=None, max_length=10)
    has_transcript: bool = Field(default=False)
    transcript_confidence: float | None = Field(default=None)

    # --- Summary / Q&A support ---
    summary: str | None = Field(default=None, max_length=4096)

    is_deleted: bool = Field(default=False)
    deleted_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class AudioChapter(SQLModel, table=True):
    """A named chapter / bookmark within an audio file."""
    __tablename__ = "audiochapter"
    __table_args__ = (
        Index("ix_audiochapter_audio_id", "audio_id"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    audio_id: uuid.UUID = Field(foreign_key="audiofile.id", index=True)
    title: str = Field(max_length=500)
    start_seconds: float = Field(default=0.0)
    end_seconds: float | None = Field(default=None)
    order_index: int = Field(default=0)
    created_at: datetime = Field(default_factory=_utcnow)


class TranscriptionSegment(SQLModel, table=True):
    """A timestamped segment of a transcription with optional speaker label."""
    __tablename__ = "transcriptionsegment"
    __table_args__ = (
        Index("ix_transcriptionsegment_audio_id", "audio_id"),
        Index(
            "ix_transcriptionsegment_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        Index("ix_transcriptionsegment_tsv", "tsv", postgresql_using="gin"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    audio_id: uuid.UUID = Field(foreign_key="audiofile.id", index=True)
    segment_index: int = Field(default=0)
    start_seconds: float = Field(default=0.0)
    end_seconds: float = Field(default=0.0)
    text: str = Field(max_length=65535)
    speaker: str | None = Field(default=None, max_length=50)  # diarization label
    confidence: float | None = Field(default=None)
    embedding: list[float] | None = Field(
        default=None,
        sa_column=Column(_Vector(settings.embedding_dim), nullable=True),
    )
    tsv: str | None = Field(
        default=None,
        sa_column=Column(postgresql.TSVECTOR(), nullable=True),
    )
    created_at: datetime = Field(default_factory=_utcnow)


class AudioPlaylist(SQLModel, table=True):
    """A user-defined playlist of audio files."""
    __tablename__ = "audioplaylist"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255, index=True)
    description: str | None = Field(default=None, max_length=1000)
    owner_id: uuid.UUID | None = Field(default=None, foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class AudioPlaylistItem(SQLModel, table=True):
    """An entry in a playlist, ordered."""
    __tablename__ = "audioplaylistitem"
    __table_args__ = (
        Index("ix_audioplaylistitem_playlist_id", "playlist_id"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    playlist_id: uuid.UUID = Field(foreign_key="audioplaylist.id", index=True)
    audio_id: uuid.UUID = Field(foreign_key="audiofile.id", index=True)
    order_index: int = Field(default=0)
    created_at: datetime = Field(default_factory=_utcnow)


AudioFile.model_rebuild()
AudioChapter.model_rebuild()
TranscriptionSegment.model_rebuild()
AudioPlaylist.model_rebuild()
AudioPlaylistItem.model_rebuild()