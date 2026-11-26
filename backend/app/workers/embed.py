"""Embedding worker: persist vector embeddings for text chunks."""
from __future__ import annotations

import logging

from sqlmodel import col, select

from app.celery import celery_app
from app.documents.models import TextChunk
from app.workers._db import run_async, worker_session

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.workers.embed.embed_chunks",
    bind=True,
    max_retries=3,
    default_retry_delay=10,
)
def embed_chunks(self, chunk_ids: list[str]) -> dict:
    """Generate and store embeddings for a list of chunk IDs."""
    return run_async(_embed_chunks(chunk_ids))


async def _embed_chunks(chunk_ids: list[str]) -> dict:
    from app.ai.embeddings import embed_texts

    async with worker_session() as session:
        chunks = list(
            (
                await session.execute(
                    select(TextChunk).where(
                        col(TextChunk.id).in_([__import__("uuid").UUID(cid) for cid in chunk_ids])
                    )
                )
            ).scalars().all()
        )
        if not chunks:
            return {"embedded": 0}

        vectors = embed_texts([c.text for c in chunks])
        for chunk, vector in zip(chunks, vectors, strict=True):
            chunk.embedding = vector
        session.add_all(chunks)
        await session.commit()
        logger.info("Embedded %d chunks", len(chunks))
        return {"embedded": len(chunks)}