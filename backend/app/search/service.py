"""Hybrid search: full-text + vector + metadata, merged with RRF."""
from __future__ import annotations

import logging
import uuid
from collections import defaultdict

from sqlalchemy import func
from sqlmodel import col, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import embed_query
from app.documents.models import TextChunk

logger = logging.getLogger(__name__)


async def _fts(session: AsyncSession, query: str, limit: int) -> list[TextChunk]:
    """PostgreSQL full-text search over chunk text using tsvector/plainto_tsquery."""
    ts_query = func.plainto_tsquery("simple", query)
    stmt = (
        select(TextChunk)
        .where(TextChunk.tsv.op("@@")(ts_query))
        .order_by(func.ts_rank(TextChunk.tsv, ts_query).desc(), col(TextChunk.chunk_index))
        .limit(limit)
    )
    return list((await session.execute(stmt)).scalars().all())


async def _vector(
    session: AsyncSession, query: str, limit: int
) -> list[tuple[TextChunk, float]]:
    """Cosine-similarity vector search via pgvector.

    Returns an empty list when pgvector is not available in the database so that
    hybrid search can gracefully fall back to full-text search only.
    """
    vector = await embed_query(query)
    if vector is None:
        return []
    try:
        stmt = (
            select(TextChunk, TextChunk.embedding.cosine_distance(vector).label("dist"))
            .where(TextChunk.embedding.is_not(None))
            .order_by("dist")
            .limit(limit)
        )
        rows = (await session.execute(stmt)).all()
    except Exception as exc:  # pgvector not installed or incompatible column type
        logger.warning(
            "Vector search unavailable (pgvector missing or column type mismatch): %s",
            exc,
        )
        return []
    out: list[tuple[TextChunk, float]] = []
    for chunk, dist in rows:
        out.append((chunk, float(dist)))
    return out


def _rrf(ranks: dict[uuid.UUID, list[int]], k: int = 60) -> list[tuple[uuid.UUID, float]]:
    """Reciprocal-rank fusion over per-query ranked lists."""
    scores: dict[uuid.UUID, float] = defaultdict(float)
    for chunk_id, rank_list in ranks.items():
        for rank in rank_list:
            scores[chunk_id] += 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)


async def hybrid_search(
    session: AsyncSession,
    *,
    query: str,
    limit: int = 30,
    document_id: uuid.UUID | None = None,
) -> list[tuple[TextChunk, float]]:
    """Merge FTS and vector results with RRF and return top chunks."""
    if not query.strip():
        return []

    fts_limit = max(limit * 2, 30)
    vec_limit = max(limit * 2, 30)

    fts_chunks = await _fts(session, query, fts_limit)
    vec_chunks = await _vector(session, query, vec_limit)

    if not fts_chunks and not vec_chunks:
        return []

    if not vec_chunks:
        return [(c, 0.0) for c in fts_chunks[:limit]]
    if not fts_chunks:
        return [(c, 1.0 - d) for c, d in vec_chunks[:limit]]

    ranks: dict[uuid.UUID, list[int]] = defaultdict(list)
    for rank, chunk in enumerate(fts_chunks):
        ranks[chunk.id].append(rank)
    for rank, (chunk, _) in enumerate(vec_chunks):
        ranks[chunk.id].append(rank)

    fused = _rrf(ranks)
    by_id: dict[uuid.UUID, TextChunk] = {c.id: c for c in fts_chunks}
    by_id.update({c.id: c for c, _ in vec_chunks})

    results: list[tuple[TextChunk, float]] = []
    for chunk_id, score in fused[:limit]:
        if document_id is not None and by_id[chunk_id].document_id != document_id:
            continue
        results.append((by_id[chunk_id], score))
    return results