"""Document schemas."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlmodel import SQLModel


class TagRead(SQLModel):
    id: uuid.UUID
    name: str
    color: str | None = None


class TagCreate(SQLModel):
    name: str
    color: str | None = None


class FolderRead(SQLModel):
    id: uuid.UUID
    name: str
    parent_id: uuid.UUID | None = None
    created_at: datetime


class FolderCreate(SQLModel):
    name: str
    parent_id: uuid.UUID | None = None


class DocumentRead(SQLModel):
    id: uuid.UUID
    title: str
    file_name: str
    file_size: int
    mime_type: str
    document_type: str
    folder_id: uuid.UUID | None = None
    status: str
    version: int
    page_count: int | None = None
    language: str | None = None
    has_text_layer: bool
    ocr_confidence: float | None = None
    # --- Classification ---
    classification: str | None = None
    classification_confidence: float | None = None
    classification_version: int = 0
    # --- Duplicate Detection ---
    content_hash: str | None = None
    duplicate_of: uuid.UUID | None = None
    duplicate_similarity: float | None = None
    created_at: datetime
    updated_at: datetime


class DocumentReadWithTags(DocumentRead):
    tags: list[TagRead] = []


class DocumentCreate(SQLModel):
    title: str
    folder_id: uuid.UUID | None = None
    tags: list[uuid.UUID] = []


class DocumentUpdate(SQLModel):
    title: str | None = None
    folder_id: uuid.UUID | None = None
    is_deleted: bool | None = None


class DocumentVersionRead(SQLModel):
    id: uuid.UUID
    document_id: uuid.UUID
    version: int
    file_name: str
    file_size: int
    change_summary: str | None = None
    created_at: datetime


class TextChunkRead(SQLModel):
    id: uuid.UUID
    document_id: uuid.UUID
    chunk_index: int
    text: str
    page_number: int
    section: str | None = None
    direction: str = "ltr"


class UploadResponse(SQLModel):
    document_id: uuid.UUID
    message: str
    status: str


class FolderUpdate(SQLModel):
    name: str | None = None
    parent_id: uuid.UUID | None = None


class TagUpdate(SQLModel):
    name: str | None = None
    color: str | None = None


class DocumentListResponse(SQLModel):
    items: list[DocumentReadWithTags]
    total: int
    skip: int
    limit: int


# --------------------------------------------------------------------------- #
# Folder Watcher schemas
# --------------------------------------------------------------------------- #


class WatcherCreate(SQLModel):
    """Request body for creating a watched folder."""
    path: str
    name: str | None = None
    poll_interval_seconds: int | None = None


class WatcherRead(SQLModel):
    id: uuid.UUID
    folder_id: uuid.UUID
    directory_path: str
    display_name: str
    is_active: bool
    items_scanned: int = 0
    items_new: int = 0
    items_updated: int = 0
    last_scan_at: datetime | None = None
    created_at: datetime


class WatcherStats(SQLModel):
    path: str
    scanned: int = 0
    new: int = 0
    updated: int = 0
    triggered: int = 0
    error: str | None = None