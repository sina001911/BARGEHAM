"""Cross-module integration HTTP endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from app.auth.router import get_current_user
from app.database import get_session
from app.integration import service
from app.users.models import User

router = APIRouter(prefix="/integration", tags=["integration"])


@router.get("/search")
async def unified_search_endpoint(
    q: str = Query(..., min_length=1),
    limit_per_module: int = Query(default=10, ge=1, le=50),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Search across documents, audio transcriptions, and knowledge entries."""
    return await service.unified_search(
        session,
        query=q,
        owner_id=current_user.id,
        limit_per_module=limit_per_module,
    )


@router.post("/audio-to-knowledge")
async def audio_to_knowledge_endpoint(
    body: dict,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Import audio transcript segments into a knowledge base."""
    return await service.audio_transcript_to_knowledge(
        session,
        audio_id=uuid.UUID(body["audio_id"]),
        kb_id=uuid.UUID(body["kb_id"]),
        owner_id=current_user.id,
    )


@router.post("/audio-to-academy")
async def audio_to_academy_endpoint(
    body: dict,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Create an Academy lesson from an audio file's transcript."""
    return await service.audio_to_academy_lesson(
        session,
        audio_id=uuid.UUID(body["audio_id"]),
        course_id=uuid.UUID(body["course_id"]),
        topic=body.get("topic"),
        owner_id=current_user.id,
    )


@router.get("/workspace")
async def workspace_stats_endpoint(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Return aggregate counts across all modules for the Workspace dashboard."""
    return await service.get_workspace_stats(session, owner_id=current_user.id)