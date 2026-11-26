"""Knowledge Engine service: CRUD, hybrid retrieval, provenance, dedup, versioning."""
from __future__ import annotations

import asyncio
import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import embed_query, embed_texts
from app.ai.router import ModelRouter
from app.ai.providers import registry
from app.config import settings
from app.documents.models import Document
from app.duplicates.service import DuplicateDetector, compute_minhash, sha256_hash
from app.knowledge.models import (
    KnowledgeBase,
    KnowledgeEntry,
    KnowledgeDocumentLink,
)

logger = logging.getLogger(__name__)

router = ModelRouter(registry)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------- #
# Knowledge Base CRUD
# --------------------------------------------------------------------------- #

async def create_kb(
    session: AsyncSession,
    *,
    name: str,
    description: str | None = None,
    owner_id: uuid.UUID | None = None,
    is_public: bool = False,
) -> KnowledgeBase:
    kb = KnowledgeBase(
        name=name,
        description=description,
        owner_id=owner_id,
        is_public=is_public,
    )
    session.add(kb)
    await session.commit()
    await session.refresh(kb)
    return kb


async def list_kbs(
    session: AsyncSession,
    *,
    owner_id: uuid.UUID | None = None,
    include_public: bool = True,
) -> list[KnowledgeBase]:
    stmt = select(KnowledgeBase)
    conditions = []
    if owner_id is not None:
        conditions.append(KnowledgeBase.owner_id == owner_id)
    if include_public:
        conditions.append(KnowledgeBase.is_public == True)  # noqa: E712
    if conditions:
        stmt = stmt.where(or_(*conditions))
    stmt = stmt.order_by(KnowledgeBase.name)
    return list((await session.execute(stmt)).scalars().all())


async def get_kb(session: AsyncSession, kb_id: uuid.UUID) -> KnowledgeBase | None:
    return await session.get(KnowledgeBase, kb_id)


async def update_kb(
    session: AsyncSession,
    kb_id: uuid.UUID,
    *,
    name: str | None = None,
    description: str | None = None,
    is_public: bool | None = None,
) -> KnowledgeBase | None:
    kb = await get_kb(session, kb_id)
    if kb is None:
        return None
    if name is not None:
        kb.name = name
    if description is not None:
        kb.description = description
    if is_public is not None:
        kb.is_public = is_public
    kb.updated_at = _utcnow()
    kb.version += 1
    session.add(kb)
    await session.commit()
    await session.refresh(kb)
    return kb


async def delete_kb(session: AsyncSession, kb_id: uuid.UUID) -> bool:
    kb = await get_kb(session, kb_id)
    if kb is None:
        return False
    await session.delete(kb)
    await session.commit()
    return True


# --------------------------------------------------------------------------- #
# Knowledge Entry management
# --------------------------------------------------------------------------- #

async def add_entry(
    session: AsyncSession,
    *,
    kb_id: uuid.UUID,
    text: str,
    chunk_index: int = 0,
    page_number: int = 1,
    section: str | None = None,
    direction: str = "ltr",
    metadata_json: str | None = None,
    document_id: uuid.UUID | None = None,
    source_page: int | None = None,
    source_section: str | None = None,
) -> KnowledgeEntry:
    """Add a new entry to a knowledge base with embedding and tsv."""
    # Generate embedding (sync function, run in executor to avoid blocking loop)
    loop = asyncio.get_running_loop()
    vectors = await loop.run_in_executor(None, lambda: embed_texts([text]))
    embedding = vectors[0] if vectors else None

    entry = KnowledgeEntry(
        kb_id=kb_id,
        chunk_index=chunk_index,
        text=text,
        page_number=page_number,
        section=section,
        direction=direction,
        metadata_json=metadata_json,
        embedding=embedding,
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)

    # Link to source document for provenance
    if document_id is not None:
        link = KnowledgeDocumentLink(
            entry_id=entry.id,
            document_id=document_id,
            page_number=source_page,
            section=source_section,
        )
        session.add(link)
        await session.commit()

    return entry


async def list_entries(
    session: AsyncSession,
    kb_id: uuid.UUID,
    *,
    skip: int = 0,
    limit: int = 100,
) -> list[KnowledgeEntry]:
    stmt = (
        select(KnowledgeEntry)
        .where(KnowledgeEntry.kb_id == kb_id)
        .order_by(KnowledgeEntry.chunk_index)
        .offset(skip)
        .limit(limit)
    )
    return list((await session.execute(stmt)).scalars().all())


async def get_entry(session: AsyncSession, entry_id: uuid.UUID) -> KnowledgeEntry | None:
    return await session.get(KnowledgeEntry, entry_id)


async def delete_entry(session: AsyncSession, entry_id: uuid.UUID) -> bool:
    entry = await get_entry(session, entry_id)
    if entry is None:
        return False
    await session.delete(entry)
    await session.commit()
    return True


# --------------------------------------------------------------------------- #
# Hybrid Retrieval (FTS + Vector + RRF) within a KB
# --------------------------------------------------------------------------- #

async def hybrid_search_kb(
    session: AsyncSession,
    kb_id: uuid.UUID,
    *,
    query: str,
    limit: int = 30,
) -> list[tuple[KnowledgeEntry, float]]:
    """Hybrid search over knowledge base entries using FTS + vector + RRF."""
    from sqlalchemy import func as sa_func

    if not query.strip():
        return []

    fts_limit = max(limit * 2, 30)
    vec_limit = max(limit * 2, 30)

    # FTS
    ts_query = sa_func.plainto_tsquery("simple", query)
    fts_stmt = (
        select(KnowledgeEntry)
        .where(KnowledgeEntry.kb_id == kb_id)
        .where(KnowledgeEntry.tsv.op("@@")(ts_query))
        .order_by(sa_func.ts_rank(KnowledgeEntry.tsv, ts_query).desc())
        .limit(fts_limit)
    )
    fts_rows = (await session.execute(fts_stmt)).scalars().all()

    # Vector
    vector = await embed_query(query)
    vec_results: list[tuple[KnowledgeEntry, float]] = []
    if vector is not None:
        try:
            vec_stmt = (
                select(
                    KnowledgeEntry,
                    KnowledgeEntry.embedding.cosine_distance(vector).label("dist"),
                )
                .where(KnowledgeEntry.kb_id == kb_id)
                .where(KnowledgeEntry.embedding.is_not(None))
                .order_by("dist")
                .limit(vec_limit)
            )
            vec_rows = (await session.execute(vec_stmt)).all()
            vec_results = [(c, float(d)) for c, d in vec_rows]
        except Exception as exc:  # noqa: BLE001
            logger.warning("KB vector search failed: %s", exc)

    if not fts_rows and not vec_results:
        return []

    if not vec_results:
        return [(c, 0.0) for c in fts_rows[:limit]]
    if not fts_rows:
        return [(c, 1.0 - d) for c, d in vec_results[:limit]]

    # RRF
    ranks: dict[uuid.UUID, list[int]] = defaultdict(list)
    for rank, chunk in enumerate(fts_rows):
        ranks[chunk.id].append(rank)
    for rank, (chunk, _) in enumerate(vec_results):
        ranks[chunk.id].append(rank)

    def _rrf(rank_list: list[int], k: int = 60) -> float:
        return sum(1.0 / (k + r) for r in rank_list)

    fused = sorted(
        [(cid, _rrf(rl)) for cid, rl in ranks.items()],
        key=lambda x: x[1],
        reverse=True,
    )

    by_id: dict[uuid.UUID, KnowledgeEntry] = {c.id: c for c in fts_rows}
    by_id.update({c.id: c for c, _ in vec_results})

    results: list[tuple[KnowledgeEntry, float]] = []
    for chunk_id, score in fused[:limit]:
        results.append((by_id[chunk_id], score))
    return results


# --------------------------------------------------------------------------- #
# Provenance
# --------------------------------------------------------------------------- #

async def get_entry_provenance(
    session: AsyncSession, entry_id: uuid.UUID
) -> list[dict]:
    """Return source document links for an entry."""
    stmt = select(KnowledgeDocumentLink).where(
        KnowledgeDocumentLink.entry_id == entry_id
    )
    rows = (await session.execute(stmt)).scalars().all()
    out = []
    for r in rows:
        doc = await session.get(Document, r.document_id)
        out.append(
            {
                "entry_id": str(r.entry_id),
                "document_id": str(r.document_id),
                "document_name": doc.file_name if doc else None,
                "page_number": r.page_number,
                "section": r.section,
            }
        )
    return out


# --------------------------------------------------------------------------- #
# Deduplication
# --------------------------------------------------------------------------- #

async def deduplicate_kb(
    session: AsyncSession, kb_id: uuid.UUID
) -> dict:
    """Remove near-duplicate entries within a KB using MinHash."""
    entries = await list_entries(session, kb_id, limit=10000)
    if not entries:
        return {"removed": 0, "remaining": 0}

    detector = DuplicateDetector()
    to_remove: set[uuid.UUID] = set()

    for entry in entries:
        content_hash = sha256_hash(entry.text.encode("utf-8"))
        mh = compute_minhash(entry.text)

        # Exact duplicate
        existing = detector.check_exact(content_hash)
        if existing is not None and existing != str(entry.id):
            to_remove.add(entry.id)
            continue

        # Near duplicate
        near_id, sim = detector.check_near_duplicate(str(entry.id), mh)
        if near_id is not None and sim >= 0.9:
            to_remove.add(entry.id)
            continue

        detector.register(str(entry.id), content_hash, mh)

    for eid in to_remove:
        await delete_entry(session, eid)

    remaining = len(entries) - len(to_remove)
    return {"removed": len(to_remove), "remaining": remaining}


# --------------------------------------------------------------------------- #
# Backup / Export
# --------------------------------------------------------------------------- #

async def export_kb(
    session: AsyncSession, kb_id: uuid.UUID
) -> dict:
    """Export a knowledge base as a serializable dict."""
    kb = await get_kb(session, kb_id)
    if kb is None:
        return {}

    entries = await list_entries(session, kb_id)
    export_entries = []
    for e in entries:
        prov = await get_entry_provenance(session, e.id)
        export_entries.append(
            {
                "id": str(e.id),
                "chunk_index": e.chunk_index,
                "text": e.text,
                "page_number": e.page_number,
                "section": e.section,
                "direction": e.direction,
                "metadata_json": e.metadata_json,
                "provenance": prov,
            }
        )

    return {
        "kb": {
            "id": str(kb.id),
            "name": kb.name,
            "description": kb.description,
            "version": kb.version,
            "embedding_model": kb.embedding_model,
            "embedding_dim": kb.embedding_dim,
        },
        "entries": export_entries,
    }
