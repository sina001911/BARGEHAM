"""Knowledge Graph HTTP endpoints — entities and relations."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.router import get_current_user
from app.database import get_session
from app.knowledge.graph_service import (
    create_entity,
    create_relation,
    delete_entity,
    extract_entities_from_text,
    get_related_entities,
    list_entities,
    list_relations,
)
from app.users.models import User
from app.users.schemas import Message

router = APIRouter(prefix="/knowledge/entities", tags=["knowledge-graph"])


@router.post("", response_model=dict, status_code=201)
async def create_entity_endpoint(
    body: dict,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    entity = await create_entity(
        session,
        kb_id=uuid.UUID(body["kb_id"]),
        name=body["name"],
        entity_type=body.get("entity_type", "person"),
        description=body.get("description"),
        source_entry_ids=body.get("source_entry_ids"),
    )
    return {
        "id": str(entity.id),
        "kb_id": str(entity.kb_id),
        "name": entity.name,
        "entity_type": entity.entity_type,
        "created_at": entity.created_at.isoformat(),
    }


@router.get("", response_model=list[dict])
async def list_entities_endpoint(
    kb_id: str = Query(...),
    entity_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    entities = await list_entities(
        session,
        kb_id=uuid.UUID(kb_id),
        entity_type=entity_type,
        limit=limit,
    )
    return [
        {
            "id": str(e.id),
            "name": e.name,
            "entity_type": e.entity_type,
            "description": e.description,
            "created_at": e.created_at.isoformat(),
        }
        for e in entities
    ]


@router.delete("/{entity_id}", response_model=Message)
async def delete_entity_endpoint(
    entity_id: str,
    kb_id: str = Query(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Message:
    deleted = await delete_entity(
        session, uuid.UUID(entity_id), uuid.UUID(kb_id)
    )
    if not deleted:
        return Message(message="Entity not found or not in this KB")
    return Message(message="Entity deleted")


# --------------------------------------------------------------------------- #
# Relations
# --------------------------------------------------------------------------- #

relations_router = APIRouter(prefix="/knowledge/relations", tags=["knowledge-graph"])


@relations_router.post("", response_model=dict, status_code=201)
async def create_relation_endpoint(
    body: dict,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    rel = await create_relation(
        session,
        kb_id=uuid.UUID(body["kb_id"]),
        subject_id=uuid.UUID(body["subject_id"]),
        predicate=body["predicate"],
        object_value=body["object_value"],
        object_type=body.get("object_type", "literal"),
        confidence=float(body.get("confidence", 0.5)),
        evidence_entry_ids=body.get("evidence_entry_ids"),
    )
    return {
        "id": str(rel.id),
        "kb_id": str(rel.kb_id),
        "subject_id": str(rel.subject_id),
        "predicate": rel.predicate,
        "object_value": rel.object_value,
        "confidence": rel.confidence,
    }


@relations_router.get("", response_model=list[dict])
async def list_relations_endpoint(
    kb_id: str = Query(...),
    subject_id: str | None = Query(default=None),
    predicate: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    relations = await list_relations(
        session,
        kb_id=uuid.UUID(kb_id),
        subject_id=uuid.UUID(subject_id) if subject_id else None,
        predicate=predicate,
        limit=limit,
    )
    return [
        {
            "id": str(r.id),
            "subject_id": str(r.subject_id),
            "predicate": r.predicate,
            "object_value": r.object_value,
            "object_type": r.object_type,
            "confidence": r.confidence,
        }
        for r in relations
    ]


# --------------------------------------------------------------------------- #
# Entity extraction from text
# --------------------------------------------------------------------------- #

extract_router = APIRouter(prefix="/knowledge/extract", tags=["knowledge-graph"])


@extract_router.post("", response_model=list[dict])
async def extract_entities_endpoint(
    body: dict,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    entities = await extract_entities_from_text(
        session,
        kb_id=uuid.UUID(body["kb_id"]),
        text=body["text"],
        source_entry_id=body.get("source_entry_id"),
    )
    return [
        {"id": str(e.id), "name": e.name, "entity_type": e.entity_type}
        for e in entities
    ]


# --------------------------------------------------------------------------- #
# Traversal
# --------------------------------------------------------------------------- #

traverse_router = APIRouter(prefix="/knowledge/traverse", tags=["knowledge-graph"])


@traverse_router.get("/neighbors/{entity_id}")
async def get_neighbors_endpoint(
    entity_id: str,
    kb_id: str = Query(...),
    depth: int = Query(default=1, ge=1, le=3),
    max_results: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    result = await get_related_entities(
        session,
        kb_id=uuid.UUID(kb_id),
        entity_id=uuid.UUID(entity_id),
        depth=depth,
        max_results=max_results,
    )
    return {
        "entity": {
            "id": str(result["entity"].id),
            "name": result["entity"].name,
            "entity_type": result["entity"].entity_type,
        }
        if result["entity"]
        else None,
        "relations": [
            {
                "id": str(r.id),
                "predicate": r.predicate,
                "object_value": r.object_value,
            }
            for r in result["relations"]
        ],
        "neighbors": [
            {
                "id": str(n.id),
                "name": n.name,
                "entity_type": n.entity_type,
            }
            for n in result["neighbors"]
        ],
    }
