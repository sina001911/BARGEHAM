"""Knowledge Engine API endpoints."""
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Body, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.router import get_current_user
from app.database import get_session
from app.knowledge import service
from app.knowledge.models import KnowledgeBase, KnowledgeEntry
from app.users.models import User

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


# --------------------------------------------------------------------------- #
# Schemas
# --------------------------------------------------------------------------- #

class KBCreate(BaseModel):
    name: str
    description: str | None = None
    is_public: bool = False


class KBRead(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None = None
    owner_id: uuid.UUID | None = None
    is_public: bool
    version: int
    embedding_model: str
    embedding_dim: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EntryCreate(BaseModel):
    text: str
    chunk_index: int = 0
    page_number: int = 1
    section: str | None = None
    direction: str = "ltr"
    metadata_json: str | None = None
    document_id: uuid.UUID | None = None
    source_page: int | None = None
    source_section: str | None = None


class EntryRead(BaseModel):
    id: uuid.UUID
    kb_id: uuid.UUID
    chunk_index: int
    text: str
    page_number: int
    section: str | None = None
    direction: str
    metadata_json: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SearchRequest(BaseModel):
    query: str
    limit: int = 30


class DedupResponse(BaseModel):
    removed: int
    remaining: int


# --------------------------------------------------------------------------- #
# Knowledge Base endpoints
# --------------------------------------------------------------------------- #

@router.post("/bases", response_model=KBRead, status_code=201)
async def create_kb_endpoint(
    req: KBCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Create a new knowledge base."""
    kb = await service.create_kb(
        session,
        name=req.name,
        description=req.description,
        owner_id=current_user.id,
        is_public=req.is_public,
    )
    return kb


@router.get("/bases", response_model=list[KBRead])
async def list_kbs_endpoint(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    owner_id: uuid.UUID | None = Query(default=None),
    include_public: bool = Query(default=True),
):
    """List knowledge bases. Defaults to current user's KBs plus public ones."""
    if owner_id is None:
        owner_id = current_user.id
    return await service.list_kbs(
        session, owner_id=owner_id, include_public=include_public
    )


@router.get("/bases/{kb_id}", response_model=KBRead)
async def get_kb_endpoint(
    kb_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get a knowledge base by ID."""
    kb = await service.get_kb(session, kb_id)
    if kb is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return kb


@router.patch("/bases/{kb_id}", response_model=KBRead)
async def update_kb_endpoint(
    kb_id: uuid.UUID,
    req: KBCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Update a knowledge base."""
    kb = await service.update_kb(
        session,
        kb_id,
        name=req.name,
        description=req.description,
        is_public=req.is_public,
    )
    if kb is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return kb


@router.delete("/bases/{kb_id}", status_code=204)
async def delete_kb_endpoint(
    kb_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Delete a knowledge base."""
    ok = await service.delete_kb(session, kb_id)
    if not ok:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Knowledge base not found")


# --------------------------------------------------------------------------- #
# Entry endpoints
# --------------------------------------------------------------------------- #

@router.post("/bases/{kb_id}/entries", response_model=EntryRead, status_code=201)
async def add_entry_endpoint(
    kb_id: uuid.UUID,
    req: EntryCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Add an entry to a knowledge base."""
    entry = await service.add_entry(
        session,
        kb_id=kb_id,
        text=req.text,
        chunk_index=req.chunk_index,
        page_number=req.page_number,
        section=req.section,
        direction=req.direction,
        metadata_json=req.metadata_json,
        document_id=req.document_id,
        source_page=req.source_page,
        source_section=req.source_section,
    )
    return entry


@router.get("/bases/{kb_id}/entries", response_model=list[EntryRead])
async def list_entries_endpoint(
    kb_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
):
    """List entries in a knowledge base."""
    return await service.list_entries(session, kb_id, skip=skip, limit=limit)


@router.get("/entries/{entry_id}", response_model=EntryRead)
async def get_entry_endpoint(
    entry_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get a knowledge entry by ID."""
    entry = await service.get_entry(session, entry_id)
    if entry is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.delete("/entries/{entry_id}", status_code=204)
async def delete_entry_endpoint(
    entry_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Delete a knowledge entry."""
    ok = await service.delete_entry(session, entry_id)
    if not ok:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Entry not found")


# --------------------------------------------------------------------------- #
# Search endpoint
# --------------------------------------------------------------------------- #

@router.post("/bases/{kb_id}/search")
async def search_kb_endpoint(
    kb_id: uuid.UUID,
    req: SearchRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Hybrid search (FTS + vector + RRF) within a knowledge base."""
    results = await service.hybrid_search_kb(
        session, kb_id, query=req.query, limit=req.limit
    )
    return [
        {
            "entry_id": str(entry.id),
            "kb_id": str(entry.kb_id),
            "text": entry.text,
            "page_number": entry.page_number,
            "section": entry.section,
            "direction": entry.direction,
            "score": round(score, 4),
        }
        for entry, score in results
    ]


# --------------------------------------------------------------------------- #
# Provenance endpoint
# --------------------------------------------------------------------------- #

@router.get("/entries/{entry_id}/provenance")
async def entry_provenance_endpoint(
    entry_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Get source document provenance for an entry."""
    return await service.get_entry_provenance(session, entry_id)


# --------------------------------------------------------------------------- #
# Deduplication endpoint
# --------------------------------------------------------------------------- #

@router.post("/bases/{kb_id}/deduplicate", response_model=DedupResponse)
async def dedup_kb_endpoint(
    kb_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Remove near-duplicate entries from a knowledge base."""
    return await service.deduplicate_kb(session, kb_id)


# --------------------------------------------------------------------------- #
# Export endpoint
# --------------------------------------------------------------------------- #

@router.get("/bases/{kb_id}/export")
async def export_kb_endpoint(
    kb_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Export a knowledge base as JSON."""
    return await service.export_kb(session, kb_id)
