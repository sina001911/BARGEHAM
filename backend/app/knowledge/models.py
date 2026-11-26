"""Knowledge base models: independent KB, entries with provenance, document links."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector as _Vector
from sqlalchemy import Column, Index
from sqlalchemy.dialects import postgresql
from sqlmodel import Field, SQLModel, Relationship

from app.config import settings


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class KnowledgeBase(SQLModel, table=True):
    """An independent knowledge base, separate from Document Intelligence and Academy."""
    __tablename__ = "knowledgebase"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=255, index=True)
    description: str | None = Field(default=None, max_length=1000)
    owner_id: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    is_public: bool = Field(default=False)
    version: int = Field(default=1)
    embedding_model: str = Field(default=settings.embedding_model)
    embedding_dim: int = Field(default=settings.embedding_dim)

class KnowledgeEntry(SQLModel, table=True):
    """A single entry in a knowledge base: text chunk with embedding and provenance."""
    __tablename__ = "knowledgeentry"
    __table_args__ = (
        Index(
            "ix_knowledgeentry_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
        Index("ix_knowledgeentry_tsv", "tsv", postgresql_using="gin"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    kb_id: uuid.UUID = Field(foreign_key="knowledgebase.id", index=True)
    chunk_index: int = Field(default=0)
    text: str = Field(max_length=65535)
    page_number: int = Field(default=1)
    section: str | None = Field(default=None, max_length=255)
    direction: str = Field(default="ltr", max_length=3)  # rtl | ltr
    metadata_json: str | None = Field(default=None, max_length=4096)
    # Full-text search vector (language-agnostic 'simple' config).
    tsv: str | None = Field(
        default=None,
        sa_column=Column(postgresql.TSVECTOR(), nullable=True),
    )
    # pgvector embedding (1024 dims to match sentence-transformers model).
    embedding: list[float] | None = Field(
        default=None,
        sa_column=Column(_Vector(settings.embedding_dim), nullable=True),
    )
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class KnowledgeDocumentLink(SQLModel, table=True):
    """Links a knowledge entry to its source document for provenance."""
    __tablename__ = "knowledgedocumentlink"

    entry_id: uuid.UUID = Field(foreign_key="knowledgeentry.id", primary_key=True)
    document_id: uuid.UUID = Field(foreign_key="document.id", index=True)
    page_number: int | None = Field(default=None)
    section: str | None = Field(default=None, max_length=255)
    created_at: datetime = Field(default_factory=_utcnow)


# --------------------------------------------------------------------------- #
# Knowledge Graph — Entities & Relations
# --------------------------------------------------------------------------- #

class EntityTypeName(str, enum.Enum):
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    DATE = "date"
    CONCEPT = "concept"
    DOCUMENT = "document"
    EVENT = "event"
    OTHER = "other"


class KnowledgeEntity(SQLModel, table=True):
    """A named entity extracted from KB entries (person, org, location, etc.)."""
    __tablename__ = "knowledge_entity"
    __table_args__ = (
        Index(
            "ix_knowledge_entity_kb_type",
            "kb_id",
            "entity_type",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    kb_id: uuid.UUID = Field(foreign_key="knowledgebase.id", index=True)
    name: str = Field(max_length=500, index=True)
    entity_type: str = Field(default=EntityTypeName.PERSON.value, max_length=100)
    description: str | None = Field(default=None)
    source_entries: str = Field(default="[]", max_length=4096)  # JSON array of entry IDs
    embedding: list[float] | None = Field(
        default=None,
        sa_column=Column(_Vector(settings.embedding_dim), nullable=True),
    )
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class KnowledgeRelation(SQLModel, table=True):
    """A relation between two entities: subject --predicate--> object_value."""
    __tablename__ = "knowledge_relation"
    __table_args__ = (
        Index("ix_knowledge_relation_subject", "subject_id"),
        Index("ix_knowledge_relation_predicate", "predicate"),
        Index("ix_knowledge_relation_kb", "kb_id", "predicate"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    kb_id: uuid.UUID = Field(foreign_key="knowledgebase.id", index=True)
    subject_id: uuid.UUID = Field(foreign_key="knowledge_entity.id", index=True)
    predicate: str = Field(max_length=200, index=True)
    object_value: str = Field(max_length=500)
    object_type: str = Field(default="literal", max_length=100)  # entity | literal
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    evidence_entry_ids: str = Field(default="[]", max_length=4096)  # JSON array
    created_at: datetime = Field(default_factory=_utcnow)


KnowledgeBase.model_rebuild()
KnowledgeEntry.model_rebuild()
KnowledgeDocumentLink.model_rebuild()
KnowledgeEntity.model_rebuild()
