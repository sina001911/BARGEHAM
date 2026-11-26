"""RAG service: retrieve chunks, build a prompt, stream an answer."""
from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm import chat, chat_stream, is_configured
from app.search.service import hybrid_search

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are BARGEHAM, an AI document assistant. Answer questions strictly from the "
    "provided document excerpts. If the excerpts do not contain enough information, say "
    "so and list what is missing. Always cite the source chunk using the format "
    "[page N]. Use the same language as the question. Be concise and factual."
)


def _build_prompt(query: str, chunks: list[tuple]) -> str:
    context_parts: list[str] = []
    for chunk, _score in chunks:
        context_parts.append(
            f"[page {chunk.page_number}] {chunk.text.strip()}"
        )
    context = "\n\n---\n\n".join(context_parts) if context_parts else "(no relevant excerpts)"

    return (
        f"Question: {query}\n\n"
        f"Relevant excerpts:\n{context}\n\n"
        "Answer the question using only the excerpts above, citing [page N]."
    )


async def ask(
    session: AsyncSession,
    *,
    query: str,
    document_id: uuid.UUID | None = None,
    limit: int = 8,
) -> str:
    """Return a single (non-streaming) answer with citations."""
    chunks = await hybrid_search(
        session,
        query=query,
        limit=limit,
        document_id=document_id,
    )
    if not chunks:
        return "I couldn't find any relevant excerpts to answer your question."

    prompt = _build_prompt(query, chunks)
    answer = await chat(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
    )
    return _attach_citations(answer, chunks)


async def ask_stream(
    session: AsyncSession,
    *,
    query: str,
    document_id: uuid.UUID | None = None,
    limit: int = 8,
) -> AsyncIterator[str]:
    """Stream an answer token-by-token, emitting a sources header first."""
    chunks = await hybrid_search(
        session,
        query=query,
        limit=limit,
        document_id=document_id,
    )
    if not chunks:
        yield "I couldn't find any relevant excerpts to answer your question.\n"
        return

    pages = sorted({c.page_number for c, _ in chunks})
    yield f"Sources: pages {', '.join(str(p) for p in pages)}\n\n"

    prompt = _build_prompt(query, chunks)
    async for token in chat_stream(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
    ):
        yield token


def _attach_citations(answer: str, chunks: list[tuple]) -> str:
    """Append a sources footer to a non-streaming answer."""
    pages = sorted({c.page_number for c, _ in chunks})
    if not pages:
        return answer
    footer = f"\n\nSources: pages {', '.join(str(p) for p in pages)}"
    return answer + footer