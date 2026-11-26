"""Academy Foundation models: courses, folder links, learner memory, progress."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector as _Vector
from sqlalchemy import Column, Index, ForeignKey
from sqlalchemy.dialects import postgresql
from sqlmodel import Field, SQLModel

from app.config import settings


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CourseType(str, enum.Enum):
    PERSONAL = "personal"
    ACADEMIC = "academic"
    PROFESSIONAL = "professional"
    LANGUAGE = "language"
    OTHER = "other"


class Course(SQLModel, table=True):
    """A course in BARGEHAM Academy - isolated learning context."""
    __tablename__ = "course"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255, index=True)
    description: str | None = Field(default=None, max_length=2000)
    course_type: CourseType = Field(default=CourseType.PERSONAL)
    owner_id: uuid.UUID = Field(index=True)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    is_active: bool = Field(default=True)
    embedding_model: str = Field(default=settings.embedding_model)
    embedding_dim: int = Field(default=settings.embedding_dim)


class CourseFolderLink(SQLModel, table=True):
    """Links a real system folder to a course for incremental indexing."""
    __tablename__ = "coursefolderlink"
    __table_args__ = (
        Index("ix_coursefolderlink_folder_id", "folder_id"),
        Index("ix_coursefolderlink_course_id", "course_id"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    course_id: uuid.UUID = Field(foreign_key="course.id", index=True)
    folder_id: uuid.UUID = Field(foreign_key="folder.id", index=True)
    folder_path: str = Field(max_length=2000)  # Real filesystem path
    watch_enabled: bool = Field(default=True)  # Folder watcher toggle
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    last_indexed: datetime | None = Field(default=None)


class LearnerMemory(SQLModel, table=True):
    """Persistent learner memory - survives restart, course-isolated."""
    __tablename__ = "learnermemory"
    __table_args__ = (
        Index("ix_learnermemory_course_id", "course_id"),
        Index("ix_learnermemory_user_id", "user_id"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    course_id: uuid.UUID = Field(foreign_key="course.id", index=True)
    user_id: uuid.UUID = Field(index=True)
    topic: str = Field(max_length=255, index=True)  # Subject/topic being learned
    mastery_level: float = Field(default=0.0, ge=0.0, le=1.0)  # Estimated mastery 0-1
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)  # Uncertainty of assessment
    test_results: str | None = Field(default=None, max_length=4096)  # JSON of test scores
    mistakes: str | None = Field(default=None, max_length=4096)  # JSON of recurring mistakes
    weaknesses: str | None = Field(default=None, max_length=1000)  # Knowledge gaps
    goals: str | None = Field(default=None, max_length=1000)  # Learning goals
    preferences: str | None = Field(default=None, max_length=1000)  # Learning preferences
    review_schedule: str | None = Field(default=None, max_length=2000)  # Spaced repetition schedule
    progress_summary: str | None = Field(default=None, max_length=2000)  # Progress narrative
    updated_at: datetime = Field(default_factory=_utcnow)
    created_at: datetime = Field(default_factory=_utcnow)


class CourseProgress(SQLModel, table=True):
    """Per-course progress tracking."""
    __tablename__ = "courseprogress"
    __table_args__ = (
        Index("ix_courseprogress_course_id", "course_id"),
        Index("ix_courseprogress_user_id", "user_id"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    course_id: uuid.UUID = Field(foreign_key="course.id", index=True)
    user_id: uuid.UUID = Field(index=True)
    documents_indexed: int = Field(default=0)
    chunks_indexed: int = Field(default=0)
    lessons_completed: int = Field(default=0)
    quizzes_taken: int = Field(default=0)
    average_score: float = Field(default=0.0, ge=0.0, le=1.0)
    last_activity: datetime | None = Field(default=None)
    updated_at: datetime = Field(default_factory=_utcnow)
    created_at: datetime = Field(default_factory=_utcnow)
