"""Audio Creation Studio models: TTS voices, Audiobooks, Podcasts, Scripts, Versions."""
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


# --------------------------------------------------------------------------- #
# TTS Voices
# --------------------------------------------------------------------------- #

class VoiceProvider(str, enum.Enum):
    PIPER = "piper"
    COQUI = "coqui"
    EDGETTS = "edge_tts"
    CUSTOM = "custom"


class VoiceGender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"


class TTSVoice(SQLModel, table=True):
    """A TTS voice available for synthesis."""
    __tablename__ = "tts_voice"
    __table_args__ = (
        Index("ix_tts_voice_lang", "language"),
        Index("ix_tts_voice_provider", "provider"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=100, index=True)  # e.g., "fa-ir-male-1"
    display_name: str = Field(max_length=200)  # e.g., "Farsi Male (Piper)"
    provider: str = Field(default=VoiceProvider.PIPER.value, max_length=30)
    language: str = Field(max_length=10, index=True)  # "fa", "en", "fa-en"
    gender: str = Field(default=VoiceGender.NEUTRAL.value, max_length=10)
    sample_rate: int = Field(default=22050)
    model_path: str | None = Field(default=None, max_length=500)  # local model file
    config_path: str | None = Field(default=None, max_length=500)
    is_default_for_lang: bool = Field(default=False)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


# --------------------------------------------------------------------------- #
# Pronunciation Dictionary
# --------------------------------------------------------------------------- #

class PronunciationRule(SQLModel, table=True):
    """Custom pronunciation overrides (word → phoneme or replacement)."""
    __tablename__ = "pronunciation_rule"
    __table_args__ = (
        Index("ix_pronunciation_rule_lang", "language"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    language: str = Field(max_length=10, index=True)
    word: str = Field(max_length=200, index=True)
    replacement: str = Field(max_length=500)  # IPA, SSML, or simple replacement
    rule_type: str = Field(default="replace", max_length=20)  # replace | ipa | ssml
    case_sensitive: bool = Field(default=False)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=_utcnow)


# --------------------------------------------------------------------------- #
# Audiobook Projects
# --------------------------------------------------------------------------- #

class AudiobookStatus(str, enum.Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


class AudiobookProject(SQLModel, table=True):
    """An audiobook generation project from a source document."""
    __tablename__ = "audiobook_project"
    __table_args__ = (
        Index("ix_audiobook_project_doc", "source_document_id"),
        Index("ix_audiobook_project_owner", "owner_id"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(max_length=500)
    source_document_id: uuid.UUID = Field(foreign_key="document.id", index=True)
    owner_id: uuid.UUID | None = Field(default=None, foreign_key="user.id", index=True)

    # Generation settings
    voice_id: uuid.UUID = Field(foreign_key="tts_voice.id")
    speed: float = Field(default=1.0)
    pause_between_paragraphs_ms: int = Field(default=500)
    pause_between_sentences_ms: int = Field(default=200)

    # Output
    status: str = Field(default=AudiobookStatus.DRAFT.value, max_length=20)
    output_path: str | None = Field(default=None, max_length=1024)
    output_format: str = Field(default="mp3", max_length=10)  # mp3 | wav
    total_duration_seconds: float | None = Field(default=None)
    file_size_bytes: int | None = Field(default=None)
    error_message: str | None = Field(default=None, max_length=2000)

    # Versioning
    version: int = Field(default=1)
    parent_version_id: uuid.UUID | None = Field(default=None, foreign_key="audiobook_project.id")

    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class AudiobookChapter(SQLModel, table=True):
    """A chapter/section within an audiobook project."""
    __tablename__ = "audiobook_chapter"
    __table_args__ = (
        Index("ix_audiobook_chapter_project", "project_id"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(foreign_key="audiobook_project.id", index=True)
    title: str = Field(max_length=500)
    source_text: str = Field(max_length=65535)  # The text for this chapter
    order_index: int = Field(default=0)
    start_offset_seconds: float | None = Field(default=None)
    end_offset_seconds: float | None = Field(default=None)
    audio_path: str | None = Field(default=None, max_length=1024)  # Generated audio for this chapter
    duration_seconds: float | None = Field(default=None)
    status: str = Field(default="pending", max_length=20)  # pending | generating | ready | failed
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


# --------------------------------------------------------------------------- #
# Podcast Projects
# --------------------------------------------------------------------------- #

class PodcastStatus(str, enum.Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    READY = "ready"
    FAILED = "failed"


class PodcastProject(SQLModel, table=True):
    """A multi-speaker podcast generation project."""
    __tablename__ = "podcast_project"
    __table_args__ = (
        Index("ix_podcast_project_owner", "owner_id"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(max_length=500)
    description: str | None = Field(default=None, max_length=2000)
    owner_id: uuid.UUID | None = Field(default=None, foreign_key="user.id", index=True)

    # Global settings
    intro_music_path: str | None = Field(default=None, max_length=1024)
    outro_music_path: str | None = Field(default=None, max_length=1024)
    default_pause_ms: int = Field(default=300)

    # Output
    status: str = Field(default=PodcastStatus.DRAFT.value, max_length=20)
    output_path: str | None = Field(default=None, max_length=1024)
    output_format: str = Field(default="mp3", max_length=10)
    total_duration_seconds: float | None = Field(default=None)
    file_size_bytes: int | None = Field(default=None)
    error_message: str | None = Field(default=None, max_length=2000)

    # Versioning
    version: int = Field(default=1)
    parent_version_id: uuid.UUID | None = Field(default=None, foreign_key="podcast_project.id")

    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class PodcastSpeaker(SQLModel, table=True):
    """A speaker/voice character in a podcast."""
    __tablename__ = "podcast_speaker"
    __table_args__ = (
        Index("ix_podcast_speaker_project", "project_id"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(foreign_key="podcast_project.id", index=True)
    name: str = Field(max_length=100)  # Display name in script
    voice_id: uuid.UUID = Field(foreign_key="tts_voice.id")
    color: str | None = Field(default=None, max_length=7)  # Hex color for UI
    order_index: int = Field(default=0)
    created_at: datetime = Field(default_factory=_utcnow)


class PodcastSegment(SQLModel, table=True):
    """A single segment/line in a podcast script."""
    __tablename__ = "podcast_segment"
    __table_args__ = (
        Index("ix_podcast_segment_project", "project_id"),
        Index("ix_podcast_segment_speaker", "speaker_id"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(foreign_key="podcast_project.id", index=True)
    speaker_id: uuid.UUID | None = Field(default=None, foreign_key="podcast_speaker.id")
    text: str = Field(max_length=10000)
    order_index: int = Field(default=0)

    # Per-segment overrides
    voice_speed: float | None = Field(default=None)
    pause_before_ms: int | None = Field(default=None)
    pause_after_ms: int | None = Field(default=None)
    emotion: str | None = Field(default=None, max_length=30)  # happy, sad, serious, etc.

    # Generated audio
    audio_path: str | None = Field(default=None, max_length=1024)
    duration_seconds: float | None = Field(default=None)
    status: str = Field(default="pending", max_length=20)

    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


# --------------------------------------------------------------------------- #
# Project Versions (for both Audiobook and Podcast)
# --------------------------------------------------------------------------- #

class ProjectVersion(SQLModel, table=True):
    """Generic version history for audiobook/podcast projects."""
    __tablename__ = "project_version"
    __table_args__ = (
        Index("ix_project_version_project", "project_type", "project_id"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_type: str = Field(max_length=20, index=True)  # "audiobook" | "podcast"
    project_id: uuid.UUID = Field(index=True)
    version_number: int = Field(default=1)
    label: str | None = Field(default=None, max_length=200)  # User-friendly label
    change_summary: str | None = Field(default=None, max_length=1000)
    snapshot_json: str = Field(max_length=65535)  # Full project state JSON
    created_by_id: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(default_factory=_utcnow)


TTSVoice.model_rebuild()
PronunciationRule.model_rebuild()
AudiobookProject.model_rebuild()
AudiobookChapter.model_rebuild()
PodcastProject.model_rebuild()
PodcastSpeaker.model_rebuild()
PodcastSegment.model_rebuild()
ProjectVersion.model_rebuild()