"""Document, folder, tag, and version models."""
import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import Column, Index
from sqlalchemy.dialects import postgresql
from sqlmodel import Field, SQLModel, Relationship

from app.config import settings

from pgvector.sqlalchemy import Vector as _Vector

_VECTOR_COL = lambda dim: Column(_Vector(dim), nullable=True)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DocumentType(str, enum.Enum):
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    TXT = "txt"
    PNG = "png"
    JPEG = "jpeg"
    TIFF = "tiff"
    WEBP = "webp"
    OTHER = "other"


class DocumentStatus(str, enum.Enum):
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    DUPLICATE = "duplicate"
    OCR_FAILED = "ocr_failed"
    ERROR = "error"


class DocumentCategory(str, enum.Enum):
    CONTRACT = "contract"
    INVOICE = "invoice"
    RECEIPT = "receipt"
    REPORT = "report"
    BOOK = "book"
    PERSONAL_DOCUMENT = "personal_document"
    TECHNICAL_DOCUMENT = "technical_document"
    CORRESPONDENCE = "correspondence"
    OTHER = "other"


class Folder(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255)
    parent_id: uuid.UUID | None = Field(default=None, foreign_key="folder.id")
    owner_id: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class Tag(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=100)
    color: str | None = Field(default=None, max_length=20)
    created_at: datetime = Field(default_factory=_utcnow)


class DocumentTagLink(SQLModel, table=True):
    document_id: uuid.UUID = Field(foreign_key="document.id", primary_key=True)
    tag_id: uuid.UUID = Field(foreign_key="tag.id", primary_key=True)


class Document(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(max_length=500)
    file_name: str = Field(max_length=500)
    file_size: int = Field(default=0)
    mime_type: str = Field(max_length=100)
    document_type: DocumentType = Field(default=DocumentType.OTHER)
    storage_path: str = Field(max_length=1024)
    folder_id: uuid.UUID | None = Field(default=None, foreign_key="folder.id")
    owner_id: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    status: DocumentStatus = Field(default=DocumentStatus.UPLOADING)
    is_deleted: bool = Field(default=False)
    deleted_at: datetime | None = Field(default=None)
    version: int = Field(default=1)
    page_count: int | None = Field(default=None)
    language: str | None = Field(default=None, max_length=10)
    has_text_layer: bool = Field(default=False)
    ocr_confidence: float | None = Field(default=None)
    # --- Classification ---
    classification: DocumentCategory | None = Field(default=None)
    classification_confidence: float | None = Field(default=None)
    classification_version: int = Field(default=0)
    # --- Duplicate Detection ---
    content_hash: str | None = Field(default=None, max_length=64)  # SHA-256 hex
    duplicate_of: uuid.UUID | None = Field(default=None, foreign_key="document.id")
    duplicate_similarity: float | None = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    tags: list[Tag] = Relationship(
        link_model=DocumentTagLink,
        sa_relationship_kwargs={"cascade": "save-update, merge"},
    )


class DocumentVersion(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    document_id: uuid.UUID = Field(foreign_key="document.id")
    version: int = Field(default=1)
    file_name: str = Field(max_length=500)
    storage_path: str = Field(max_length=1024)
    file_size: int = Field(default=0)
    change_summary: str | None = Field(default=None, max_length=1000)
    created_at: datetime = Field(default_factory=_utcnow)
    created_by_id: uuid.UUID | None = Field(default=None, foreign_key="user.id")


class TextChunk(SQLModel, table=True):
    """A chunk of extracted text with page-level mapping and its embedding."""
    __table_args__ = (
        Index(
            "ix_textchunk_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        Index("ix_textchunk_tsv", "tsv", postgresql_using="gin"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    document_id: uuid.UUID = Field(foreign_key="document.id", index=True)
    chunk_index: int = Field(default=0)
    text: str = Field(max_length=65535)
    page_number: int = Field(default=1)
    section: str | None = Field(default=None, max_length=255)
    direction: str = Field(default="ltr", max_length=3)  # rtl | ltr
    metadata_json: str | None = Field(default=None, max_length=4096)
    embedding: list[float] | None = Field(
        default=None,
        sa_column=_VECTOR_COL(settings.embedding_dim),
    )
    # Full-text search vector (language-agnostic 'simple' config).
    # Populated by the OCR worker and backfilled by migration 0002_fts_search.
    tsv: str | None = Field(
        default=None,
        sa_column=Column(postgresql.TSVECTOR(), nullable=True),
    )
    created_at: datetime = Field(default_factory=_utcnow)


# Resolve forward references
from app.users.models import User  # noqa: E402, F401

Document.model_rebuild()
Folder.model_rebuild()