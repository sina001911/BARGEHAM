"""Knowledge Graph — entity extraction, relations, traversal."""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col

from app.ai.embeddings import embed_texts
from app.knowledge.models import (
    KnowledgeBase,
    KnowledgeEntity,
    KnowledgeRelation,
)

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Entity CRUD
# --------------------------------------------------------------------------- #


async def create_entity(
    session: AsyncSession,
    *,
    kb_id: uuid.UUID,
    name: str,
    entity_type: str = "person",
    description: str | None = None,
    source_entry_ids: list[str] | None = None,
) -> KnowledgeEntity:
    entry_ids_json = json.dumps(source_entry_ids or [])
    entity = KnowledgeEntity(
        kb_id=kb_id,
        name=name,
        entity_type=entity_type,
        description=description,
        source_entries=entry_ids_json,
    )
    session.add(entity)
    await session.commit()
    await session.refresh(entity)
    return entity


async def list_entities(
    session: AsyncSession,
    *,
    kb_id: uuid.UUID,
    entity_type: str | None = None,
    limit: int = 50,
) -> list[KnowledgeEntity]:
    conditions = [KnowledgeEntity.kb_id == kb_id]
    if entity_type:
        conditions.append(KnowledgeEntity.entity_type == entity_type)
    stmt = (
        select(KnowledgeEntity)
        .where(and_(*conditions))
        .order_by(col(KnowledgeEntity.name))
        .limit(limit)
    )
    return list((await session.execute(stmt)).scalars().all())


async def get_entity(
    session: AsyncSession, entity_id: uuid.UUID
) -> KnowledgeEntity | None:
    return await session.get(KnowledgeEntity, entity_id)


async def delete_entity(
    session: AsyncSession, entity_id: uuid.UUID, kb_id: uuid.UUID
) -> bool:
    stmt = select(KnowledgeEntity).where(
        KnowledgeEntity.id == entity_id,
        KnowledgeEntity.kb_id == kb_id,
    )
    entity = (await session.execute(stmt)).scalar_one_or_none()
    if entity is None:
        return False
    await session.delete(entity)
    await session.commit()
    return True


# --------------------------------------------------------------------------- #
# Relation CRUD
# --------------------------------------------------------------------------- #


async def create_relation(
    session: AsyncSession,
    *,
    kb_id: uuid.UUID,
    subject_id: uuid.UUID,
    predicate: str,
    object_value: str,
    object_type: str = "literal",
    confidence: float = 0.5,
    evidence_entry_ids: list[str] | None = None,
) -> KnowledgeRelation:
    evidence_json = json.dumps(evidence_entry_ids or [])
    rel = KnowledgeRelation(
        kb_id=kb_id,
        subject_id=subject_id,
        predicate=predicate,
        object_value=object_value,
        object_type=object_type,
        confidence=confidence,
        evidence_entry_ids=evidence_json,
    )
    session.add(rel)
    await session.commit()
    await session.refresh(rel)
    return rel


async def list_relations(
    session: AsyncSession,
    *,
    kb_id: uuid.UUID,
    subject_id: uuid.UUID | None = None,
    predicate: str | None = None,
    limit: int = 100,
) -> list[KnowledgeRelation]:
    conditions = [KnowledgeRelation.kb_id == kb_id]
    if subject_id:
        conditions.append(KnowledgeRelation.subject_id == subject_id)
    if predicate:
        conditions.append(KnowledgeRelation.predicate == predicate)
    stmt = (
        select(KnowledgeRelation)
        .where(and_(*conditions))
        .order_by(col(KnowledgeRelation.created_at).desc())
        .limit(limit)
    )
    return list((await session.execute(stmt)).scalars().all())


async def get_related_entities(
    session: AsyncSession,
    *,
    kb_id: uuid.UUID,
    entity_id: uuid.UUID,
    depth: int = 1,
    max_results: int = 50,
) -> dict:
    """Return an entity and its neighbors up to *depth* hops."""
    entity_stmt = select(KnowledgeEntity).where(
        and_(KnowledgeEntity.id == entity_id, KnowledgeEntity.kb_id == kb_id)
    )
    entity = (await session.execute(entity_stmt)).scalar_one_or_none()
    if entity is None:
        return {"entity": None, "relations": [], "neighbors": []}

    related_stmt = select(KnowledgeRelation).where(
        and_(
            KnowledgeRelation.kb_id == kb_id,
            KnowledgeRelation.subject_id == entity_id,
        )
    )
    relations = list((await session.execute(related_stmt)).scalars().all())

    neighbor_ids = {rel.subject_id for rel in relations}
    neighbors = []
    if neighbor_ids:
        nb_stmt = select(KnowledgeEntity).where(
            KnowledgeEntity.id.in_(neighbor_ids)
        )
        neighbors = list((await session.execute(nb_stmt)).scalars().all())

    return {
        "entity": entity,
        "relations": relations,
        "neighbors": neighbors[:max_results],
    }


# --------------------------------------------------------------------------- #
# Basic Named-Entity Extraction (heuristic, no external NER dependency)
# --------------------------------------------------------------------------- #

_COMMON_PREFIXES = {
    "person": ("Mr.", "Mrs.", "Ms.", "Dr.", "Prof.", "جناب", "سرکار", "دکتر"),
    "organization": ("Inc.", "Ltd.", "Co.", "Corp.", "GmbH", "SA", "بنگاه", "شرکت", "سازمان"),
    "location": (),  # determined by context
}


def _classify_entity_name(name: str) -> str:
    lower = name.lower().strip()
    if any(lower.startswith(p) for p in _COMMON_PREFIXES["person"]):
        return "person"
    if any(lower.endswith(s) for s in (" Corp", " Inc", " Ltd", " GmbH", " SA")):
        return "organization"
    if any(kw in lower for kw in ("company", "corporation", "org", "وزارت", "دانشگاه", "شرکت")):
        return "organization"
    return "concept"


async def extract_entities_from_text(
    session: AsyncSession,
    kb_id: uuid.UUID,
    text: str,
    source_entry_id: str | None = None,
) -> list[KnowledgeEntity]:
    """Simple keyword-based entity extractor; returns list of created entities."""
    words = text.split()
    seen: set[str] = set()
    entities: list[KnowledgeEntity] = []

    for word in words:
        cleaned = word.strip(".,;:!؟،؛")
        if len(cleaned) < 3:
            continue
        if cleaned.lower() in seen:
            continue
        seen.add(cleaned.lower())

        etype = _classify_entity_name(cleaned)
        existing = (
            await session.execute(
                select(KnowledgeEntity).where(
                    and_(
                        KnowledgeEntity.kb_id == kb_id,
                        KnowledgeEntity.name.ilike(cleaned),
                    )
                )
            )
        ).scalar_one_or_none()

        if existing:
            # Append source_entry to existing entity's source_entries
            try:
                sources = json.loads(existing.source_entries or "[]")
            except json.JSONDecodeError:
                sources = []
            if source_entry_id and source_entry_id not in sources:
                sources.append(source_entry_id)
                existing.source_entries = json.dumps(sources)
                session.add(existing)
            continue

        entity = await create_entity(
            session,
            kb_id=kb_id,
            name=cleaned,
            entity_type=etype,
            source_entry_ids=[source_entry_id] if source_entry_id else None,
        )
        entities.append(entity)

    if entities:
        await session.commit()

    return entities
