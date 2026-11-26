"""Classification endpoints: classify documents and manage categories."""
from __future__ import annotations

import logging
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.router import get_current_user
from app.classification.service import classify_document
from app.config import settings
from app.database import get_session
from app.documents.models import Document
from app.documents.service import classify_document_content, detect_document_duplicates, reclassify_document
from app.exceptions import NotFoundError
from app.users.models import User
from app.users.schemas import Message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/classification", tags=["classification"])


@router.get("/categories")
async def list_categories(
    current_user: User = Depends(get_current_user),
) -> dict:
    """List available classification categories."""
    categories = [
        c.strip() for c in settings.classification_categories.split(",") if c.strip()
    ]
    return {"categories": categories}


@router.get("/config")
async def get_classification_config(
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get classification configuration."""
    return {
        "enabled": settings.classification_enabled,
        "threshold": settings.classification_confidence_threshold,
        "categories": [
            c.strip() for c in settings.classification_categories.split(",") if c.strip()
        ],
    }


@router.post("/documents/{document_id}/classify", response_model=dict)
async def classify_document_endpoint(
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Classify a document and store the result."""
    category, confidence = await classify_document_content(session, document_id, "")
    if category is None:
        raise NotFoundError("Classification not available or document has no text")
    return {
        "document_id": str(document_id),
        "category": category,
        "confidence": confidence,
    }


@router.post("/documents/{document_id}/duplicates", response_model=dict)
async def detect_duplicates_endpoint(
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Run duplicate detection on a document."""
    doc = await session.get(Document, document_id)
    if doc is None:
        raise NotFoundError("Document not found")

    # Get text from chunks
    from app.documents.service import list_chunks

    chunks = await list_chunks(session, document_id, limit=1000)
    text = "\n".join(c.text for c in chunks)

    # Get content for hash
    from app.documents.service import get_document_bytes

    content = await get_document_bytes(session, document_id)

    result = await detect_document_duplicates(session, document_id, content, text)
    return {
        "document_id": str(document_id),
        "is_exact_duplicate": result.is_exact_duplicate,
        "exact_match_id": result.exact_match_id,
        "is_near_duplicate": result.is_near_duplicate,
        "near_match_id": result.near_match_id,
        "near_similarity": result.near_similarity,
        "content_hash": result.content_hash,
    }


@router.post("/documents/{document_id}/reclassify", response_model=dict)
async def reclassify_document_endpoint(
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Re-run classification and duplicate detection on a document."""
    classification_result, duplicate_result = await reclassify_document(
        session, document_id
    )
    category, confidence = classification_result
    return {
        "document_id": str(document_id),
        "category": category,
        "confidence": confidence,
        "is_exact_duplicate": duplicate_result.is_exact_duplicate,
        "exact_match_id": duplicate_result.exact_match_id,
        "is_near_duplicate": duplicate_result.is_near_duplicate,
        "near_match_id": duplicate_result.near_match_id,
        "near_similarity": duplicate_result.near_similarity,
        "content_hash": duplicate_result.content_hash,
    }


@router.post("/classify-text", response_model=dict)
async def classify_text_endpoint(
    text: str,
    current_user: User = Depends(get_current_user),
) -> dict:
    """Classify a raw text string (for testing)."""
    try:
        category, confidence = classify_document(text)
        return {
            "category": category,
            "confidence": confidence,
        }
    except Exception as exc:
        logger.exception("Classification failed")
        return {
            "category": None,
            "confidence": None,
            "error": str(exc),
        }
