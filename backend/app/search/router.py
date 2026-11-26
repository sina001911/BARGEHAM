"""Search endpoints: hybrid search over documents and chunks."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Body, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.comparison import compare
from app.ai.redaction import detect_pii, redact
from app.ai.summarization import summarize
from app.auth.router import get_current_user
from app.database import get_session
from app.search.service import hybrid_search
from app.users.models import User

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/chunks")
async def search_chunks(
    q: str = Query(..., min_length=1),
    document_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=30, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """Hybrid full-text + vector search across document chunks."""
    results = await hybrid_search(
        session,
        query=q,
        limit=limit,
        document_id=document_id,
    )
    return [
        {
            "chunk_id": chunk.id,
            "document_id": chunk.document_id,
            "page_number": chunk.page_number,
            "section": chunk.section,
            "direction": chunk.direction,
            "text": chunk.text,
            "score": round(score, 4),
        }
        for chunk, score in results
    ]


# --------------------------------------------------------------------------- #
# Document Intelligence: Summarization
# --------------------------------------------------------------------------- #


class SummarizeRequest(BaseModel):
    text: str
    max_length: int = 500
    prefer_local: bool = False


@router.post("/summarize")
async def summarize_endpoint(
    req: SummarizeRequest,
    current_user: User = Depends(get_current_user),
) -> dict:
    """Summarize a text using the best available AI provider."""
    summary = await summarize(
        req.text,
        max_length=req.max_length,
        prefer_local=req.prefer_local,
    )
    return {"summary": summary}


# --------------------------------------------------------------------------- #
# Document Intelligence: Comparison
# --------------------------------------------------------------------------- #


class CompareRequest(BaseModel):
    text_a: str
    text_b: str
    prefer_local: bool = False


@router.post("/compare")
async def compare_endpoint(
    req: CompareRequest,
    current_user: User = Depends(get_current_user),
) -> dict:
    """Compare two documents and return a structured diff."""
    return await compare(
        req.text_a,
        req.text_b,
        prefer_local=req.prefer_local,
    )


# --------------------------------------------------------------------------- #
# Document Intelligence: Redaction
# --------------------------------------------------------------------------- #


class RedactRequest(BaseModel):
    text: str


@router.post("/redact")
async def redact_endpoint(
    req: RedactRequest,
    current_user: User = Depends(get_current_user),
) -> dict:
    """Detect and redact PII from a text."""
    redacted_text, matches = redact(req.text)
    return {"redacted_text": redacted_text, "redactions": matches}


@router.post("/detect-pii")
async def detect_pii_endpoint(
    req: RedactRequest,
    current_user: User = Depends(get_current_user),
) -> dict:
    """Detect PII in a text without redacting."""
    return {"pii": detect_pii(req.text)}


# --------------------------------------------------------------------------- #
# Document Intelligence: Fact Verification (placeholder, evidence-based)
# --------------------------------------------------------------------------- #


class FactVerifyRequest(BaseModel):
    claim: str
    document_ids: list[uuid.UUID] = []


@router.post("/fact-verify")
async def fact_verify_endpoint(
    req: FactVerifyRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Verify a claim against indexed document excerpts.

    Returns one of: Supported / Contradicted / Partially Supported / Unknown /
    Insufficient Evidence.
    """
    from app.search.service import hybrid_search

    chunks = await hybrid_search(
        session,
        query=req.claim,
        limit=8,
    )

    if not chunks:
        return {
            "verdict": "Insufficient Evidence",
            "confidence": 0.0,
            "evidence": [],
        }

    # Simple evidence-based check: count chunks that contain claim keywords
    claim_words = set(req.claim.lower().split())
    supporting = 0
    contradicting = 0
    evidence = []

    for chunk, score in chunks:
        chunk_words = set(chunk.text.lower().split())
        overlap = len(claim_words & chunk_words)
        if overlap >= max(1, len(claim_words) // 2):
            supporting += 1
            evidence.append(
                {
                    "chunk_id": str(chunk.id),
                    "page_number": chunk.page_number,
                    "text": chunk.text[:200],
                    "score": round(score, 4),
                }
            )
        elif overlap > 0:
            contradicting += 1

    total = supporting + contradicting
    if total == 0:
        verdict = "Unknown"
        confidence = 0.0
    elif supporting >= total * 0.7:
        verdict = "Supported"
        confidence = supporting / total
    elif contradicting >= total * 0.7:
        verdict = "Contradicted"
        confidence = contradicting / total
    else:
        verdict = "Partially Supported"
        confidence = max(supporting, contradicting) / total if total else 0.0

    return {
        "verdict": verdict,
        "confidence": round(confidence, 2),
        "evidence": evidence[:5],
    }


# --------------------------------------------------------------------------- #
# Document Intelligence: Timeline Extraction (placeholder)
# --------------------------------------------------------------------------- #


class TimelineRequest(BaseModel):
    document_id: uuid.UUID


@router.post("/timeline")
async def timeline_endpoint(
    req: TimelineRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Extract timeline events from a document (placeholder)."""
    from app.documents.service import list_chunks

    chunks = await list_chunks(session, req.document_id, limit=1000)
    events = []
    for c in chunks:
        # Very basic: look for date-like patterns
        import re

        dates = re.findall(
            r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",
            c.text,
        )
        for d in dates[:3]:
            events.append(
                {
                    "date": d,
                    "chunk_id": str(c.id),
                    "page_number": c.page_number,
                    "context": c.text[:200],
                }
            )
    return {
        "document_id": str(req.document_id),
        "events": events[:50],
    }
