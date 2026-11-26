"""Document, folder, tag, and version business logic."""
from __future__ import annotations

import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

from sqlalchemy import delete, func
from sqlmodel import col, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.classification.service import classify_document
from app.config import settings
from app.duplicates.service import DuplicateResult, get_detector, sha256_hash
from app.documents.models import (
    Document,
    DocumentCategory,
    DocumentStatus,
    DocumentTagLink,
    DocumentType,
    DocumentVersion,
    Folder,
    Tag,
    TextChunk,
)
from app.documents.schemas import (
    DocumentReadWithTags,
    FolderRead,
    TagRead,
)
from app.exceptions import ConflictError, NotFoundError, ValidationFailedError
from app.storage import get_storage


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


_MIME_TO_TYPE: dict[str, DocumentType] = {
    "application/pdf": DocumentType.PDF,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DocumentType.DOCX,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": DocumentType.XLSX,
    "text/plain": DocumentType.TXT,
    "image/png": DocumentType.PNG,
    "image/jpeg": DocumentType.JPEG,
    "image/tiff": DocumentType.TIFF,
    "image/webp": DocumentType.WEBP,
}

_EXT_TO_TYPE: dict[str, DocumentType] = {
    "pdf": DocumentType.PDF,
    "docx": DocumentType.DOCX,
    "xlsx": DocumentType.XLSX,
    "txt": DocumentType.TXT,
    "png": DocumentType.PNG,
    "jpg": DocumentType.JPEG,
    "jpeg": DocumentType.JPEG,
    "tif": DocumentType.TIFF,
    "tiff": DocumentType.TIFF,
    "webp": DocumentType.WEBP,
}


def document_type_from(file_name: str, mime_type: str) -> DocumentType:
    """Resolve a document type from MIME type or file extension."""
    if mime_type in _MIME_TO_TYPE:
        return _MIME_TO_TYPE[mime_type]
    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
    return _EXT_TO_TYPE.get(ext, DocumentType.OTHER)


def _ensure_allowed(mime_type: str, file_name: str) -> None:
    allowed = {m.strip() for m in settings.allowed_mime_types.split(",") if m.strip()}
    if mime_type in allowed:
        return
    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
    if document_type_from(file_name, mime_type) is DocumentType.OTHER:
        raise ValidationFailedError(f"Unsupported file type: {mime_type or ext or 'unknown'}")


def _check_size(size: int) -> None:
    if size > settings.max_upload_size_mb * 1024 * 1024:
        raise ValidationFailedError(
            f"File exceeds maximum size of {settings.max_upload_size_mb} MB"
        )


# --------------------------------------------------------------------------- #
# Serialization helpers
# --------------------------------------------------------------------------- #
def _to_read(doc: Document, tags: list[Tag]) -> DocumentReadWithTags:
    return DocumentReadWithTags(
        id=doc.id,
        title=doc.title,
        file_name=doc.file_name,
        file_size=doc.file_size,
        mime_type=doc.mime_type,
        document_type=doc.document_type.value,
        folder_id=doc.folder_id,
        status=doc.status.value,
        version=doc.version,
        page_count=doc.page_count,
        language=doc.language,
        has_text_layer=doc.has_text_layer,
        ocr_confidence=doc.ocr_confidence,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        tags=[TagRead(id=t.id, name=t.name, color=t.color) for t in tags],
    )


async def _tags_for_docs(
    session: AsyncSession, doc_ids: list[uuid.UUID]
) -> dict[uuid.UUID, list[Tag]]:
    if not doc_ids:
        return {}
    stmt = (
        select(DocumentTagLink.document_id, Tag)
        .join(Tag, Tag.id == DocumentTagLink.tag_id)
        .where(col(DocumentTagLink.document_id).in_(doc_ids))
    )
    rows = (await session.execute(stmt)).all()
    out: dict[uuid.UUID, list[Tag]] = defaultdict(list)
    for doc_id, tag in rows:
        out[doc_id].append(tag)
    return out


async def _resolve_tags(session: AsyncSession, tag_ids: list[uuid.UUID]) -> list[Tag]:
    if not tag_ids:
        return []
    stmt = select(Tag).where(col(Tag.id).in_(tag_ids))
    return list((await session.execute(stmt)).scalars().all())


# --------------------------------------------------------------------------- #
# Folders
# --------------------------------------------------------------------------- #
async def create_folder(
    session: AsyncSession,
    name: str,
    parent_id: uuid.UUID | None = None,
    owner_id: uuid.UUID | None = None,
) -> FolderRead:
    if parent_id is not None:
        parent = await session.get(Folder, parent_id)
        if parent is None:
            raise NotFoundError("Parent folder not found")
    folder = Folder(name=name, parent_id=parent_id, owner_id=owner_id)
    session.add(folder)
    await session.commit()
    await session.refresh(folder)
    return FolderRead.model_validate(folder)


async def list_folders(
    session: AsyncSession, parent_id: uuid.UUID | None = None
) -> list[FolderRead]:
    stmt = select(Folder)
    if parent_id is not None:
        stmt = stmt.where(Folder.parent_id == parent_id)
    stmt = stmt.order_by(Folder.name)
    folders = (await session.execute(stmt)).scalars().all()
    return [FolderRead.model_validate(f) for f in folders]


async def update_folder(
    session: AsyncSession,
    folder_id: uuid.UUID,
    *,
    name: str | None = None,
    parent_id: uuid.UUID | None = None,
) -> FolderRead:
    folder = await session.get(Folder, folder_id)
    if folder is None:
        raise NotFoundError("Folder not found")
    if name is not None:
        folder.name = name
    if parent_id is not None:
        folder.parent_id = parent_id
    folder.updated_at = _utcnow()
    session.add(folder)
    await session.commit()
    await session.refresh(folder)
    return FolderRead.model_validate(folder)


async def delete_folder(session: AsyncSession, folder_id: uuid.UUID) -> None:
    folder = await session.get(Folder, folder_id)
    if folder is None:
        raise NotFoundError("Folder not found")
    # Detach children and documents rather than cascading deletes.
    await session.execute(delete(Folder).where(Folder.parent_id == folder_id))
    docs = (await session.execute(select(Document).where(Document.folder_id == folder_id))).scalars().all()
    for doc in docs:
        doc.folder_id = None
    await session.delete(folder)
    await session.commit()


# --------------------------------------------------------------------------- #
# Tags
# --------------------------------------------------------------------------- #
async def create_tag(session: AsyncSession, name: str, color: str | None = None) -> TagRead:
    existing = (await session.execute(select(Tag).where(Tag.name == name))).scalar_one_or_none()
    if existing is not None:
        raise ConflictError("Tag already exists")
    tag = Tag(name=name, color=color)
    session.add(tag)
    await session.commit()
    await session.refresh(tag)
    return TagRead.model_validate(tag)


async def list_tags(session: AsyncSession) -> list[TagRead]:
    tags = (await session.execute(select(Tag).order_by(Tag.name))).scalars().all()
    return [TagRead.model_validate(t) for t in tags]


async def update_tag(
    session: AsyncSession,
    tag_id: uuid.UUID,
    *,
    name: str | None = None,
    color: str | None = None,
) -> TagRead:
    tag = await session.get(Tag, tag_id)
    if tag is None:
        raise NotFoundError("Tag not found")
    if name is not None:
        tag.name = name
    if color is not None:
        tag.color = color
    session.add(tag)
    await session.commit()
    await session.refresh(tag)
    return TagRead.model_validate(tag)


async def delete_tag(session: AsyncSession, tag_id: uuid.UUID) -> None:
    tag = await session.get(Tag, tag_id)
    if tag is None:
        raise NotFoundError("Tag not found")
    await session.execute(delete(DocumentTagLink).where(DocumentTagLink.tag_id == tag_id))
    await session.delete(tag)
    await session.commit()


# --------------------------------------------------------------------------- #
# Documents
# --------------------------------------------------------------------------- #
async def create_document_from_upload(
    session: AsyncSession,
    *,
    title: str | None,
    file_name: str,
    mime_type: str,
    data: bytes,
    folder_id: uuid.UUID | None = None,
    tag_ids: list[uuid.UUID] | None = None,
    owner_id: uuid.UUID | None = None,
) -> Document:
    _ensure_allowed(mime_type, file_name)
    _check_size(len(data))

    if folder_id is not None:
        if await session.get(Folder, folder_id) is None:
            raise NotFoundError("Folder not found")

    doc_id = uuid.uuid4()
    storage = get_storage()
    object_name = storage.generate_object_name(file_name, doc_id)
    storage_path = storage.put_object(
        object_name, data, content_type=mime_type, length=len(data)
    )

    doc = Document(
        id=doc_id,
        title=title or file_name,
        file_name=file_name,
        file_size=len(data),
        mime_type=mime_type,
        document_type=document_type_from(file_name, mime_type),
        storage_path=storage_path,
        folder_id=folder_id,
        owner_id=owner_id,
        status=DocumentStatus.PROCESSING,
    )
    session.add(doc)

    for tag in await _resolve_tags(session, tag_ids or []):
        session.add(DocumentTagLink(document_id=doc_id, tag_id=tag.id))

    session.add(
        DocumentVersion(
            document_id=doc_id,
            version=1,
            file_name=file_name,
            storage_path=storage_path,
            file_size=len(data),
            change_summary="Initial upload",
            created_by_id=owner_id,
        )
    )

    await session.commit()
    await session.refresh(doc)

    _dispatch_ocr(doc.id)
    return doc


def _dispatch_ocr(document_id: uuid.UUID) -> None:
    """Best-effort enqueue of OCR processing without blocking the request.

    Runs :func:`app.workers.ocr._process_document` as a background task in the
    running event loop. No Celery/Redis broker is required, so upload returns
    immediately even in single-node dev.
    """
    try:
        import asyncio

        from app.workers.ocr import _process_document

        asyncio.create_task(_process_document(document_id))
    except Exception:  # pragma: no cover - no running loop in dev
        logger.warning("OCR dispatch failed for %s", document_id)


async def list_documents(
    session: AsyncSession,
    *,
    folder_id: uuid.UUID | None = None,
    q: str | None = None,
    skip: int = 0,
    limit: int = 50,
    include_deleted: bool = False,
    owner_id: uuid.UUID | None = None,
) -> tuple[list[DocumentReadWithTags], int]:
    conditions = []
    if not include_deleted:
        conditions.append(Document.is_deleted == False)  # noqa: E712
    if folder_id is not None:
        conditions.append(Document.folder_id == folder_id)
    if owner_id is not None:
        conditions.append(Document.owner_id == owner_id)
    if q:
        conditions.append(col(Document.title).ilike(f"%{q}%"))

    count_stmt = select(func.count()).select_from(Document)
    stmt = select(Document)
    for cond in conditions:
        count_stmt = count_stmt.where(cond)
        stmt = stmt.where(cond)

    total = (await session.execute(count_stmt)).scalar_one()
    stmt = stmt.order_by(col(Document.created_at).desc()).offset(skip).limit(limit)
    docs = list((await session.execute(stmt)).scalars().all())
    tags_map = await _tags_for_docs(session, [d.id for d in docs])
    return [_to_read(d, tags_map.get(d.id, [])) for d in docs], total


async def get_document(
    session: AsyncSession, document_id: uuid.UUID, include_deleted: bool = True
) -> Document:
    doc = await session.get(Document, document_id)
    if doc is None or (doc.is_deleted and not include_deleted):
        raise NotFoundError("Document not found")
    return doc


async def get_document_read(session: AsyncSession, document_id: uuid.UUID) -> DocumentReadWithTags:
    doc = await get_document(session, document_id)
    tags = (await _tags_for_docs(session, [doc.id])).get(doc.id, [])
    return _to_read(doc, tags)


async def update_document(
    session: AsyncSession,
    document_id: uuid.UUID,
    *,
    title: str | None = None,
    folder_id: uuid.UUID | None = None,
) -> DocumentReadWithTags:
    doc = await get_document(session, document_id)
    if title is not None:
        doc.title = title
    if folder_id is not None:
        if await session.get(Folder, folder_id) is None:
            raise NotFoundError("Folder not found")
        doc.folder_id = folder_id
    doc.updated_at = _utcnow()
    session.add(doc)
    await session.commit()
    await session.refresh(doc)
    return await get_document_read(session, document_id)


async def set_document_tags(
    session: AsyncSession, document_id: uuid.UUID, tag_ids: list[uuid.UUID]
) -> DocumentReadWithTags:
    await get_document(session, document_id)
    await session.execute(
        delete(DocumentTagLink).where(DocumentTagLink.document_id == document_id)
    )
    for tag in await _resolve_tags(session, tag_ids):
        session.add(DocumentTagLink(document_id=document_id, tag_id=tag.id))
    await session.commit()
    return await get_document_read(session, document_id)


async def soft_delete_document(session: AsyncSession, document_id: uuid.UUID) -> None:
    doc = await get_document(session, document_id)
    doc.is_deleted = True
    doc.deleted_at = _utcnow()
    session.add(doc)
    await session.commit()


async def restore_document(session: AsyncSession, document_id: uuid.UUID) -> DocumentReadWithTags:
    doc = await get_document(session, document_id)
    doc.is_deleted = False
    doc.deleted_at = None
    session.add(doc)
    await session.commit()
    return await get_document_read(session, document_id)


async def hard_delete_document(session: AsyncSession, document_id: uuid.UUID) -> None:
    doc = await get_document(session, document_id)
    try:
        get_storage().delete_object(doc.storage_path)
    except Exception:  # pragma: no cover
        pass
    await session.execute(delete(TextChunk).where(TextChunk.document_id == document_id))
    await session.execute(
        delete(DocumentVersion).where(DocumentVersion.document_id == document_id)
    )
    await session.execute(
        delete(DocumentTagLink).where(DocumentTagLink.document_id == document_id)
    )
    await session.delete(doc)
    await session.commit()


async def list_chunks(
    session: AsyncSession,
    document_id: uuid.UUID,
    skip: int = 0,
    limit: int = 500,
) -> list[TextChunk]:
    await get_document(session, document_id)
    stmt = (
        select(TextChunk)
        .where(TextChunk.document_id == document_id)
        .order_by(col(TextChunk.page_number), col(TextChunk.chunk_index))
        .offset(skip)
        .limit(limit)
    )
    return list((await session.execute(stmt)).scalars().all())


async def list_versions(session: AsyncSession, document_id: uuid.UUID) -> list[DocumentVersion]:
    await get_document(session, document_id)
    stmt = (
        select(DocumentVersion)
        .where(DocumentVersion.document_id == document_id)
        .order_by(col(DocumentVersion.version).desc())
    )
    return list((await session.execute(stmt)).scalars().all())


async def add_document_version(
    session: AsyncSession,
    document_id: uuid.UUID,
    *,
    file_name: str,
    mime_type: str,
    data: bytes,
    change_summary: str | None = None,
    user_id: uuid.UUID | None = None,
) -> DocumentVersion:
    _ensure_allowed(mime_type, file_name)
    _check_size(len(data))
    doc = await get_document(session, document_id)

    storage = get_storage()
    object_name = storage.generate_object_name(file_name, doc.id)
    storage_path = storage.put_object(
        object_name, data, content_type=mime_type, length=len(data)
    )

    next_version = doc.version + 1
    version = DocumentVersion(
        document_id=doc.id,
        version=next_version,
        file_name=file_name,
        storage_path=storage_path,
        file_size=len(data),
        change_summary=change_summary,
        created_by_id=user_id,
    )
    doc.version = next_version
    doc.file_name = file_name
    doc.file_size = len(data)
    doc.mime_type = mime_type
    doc.document_type = document_type_from(file_name, mime_type)
    doc.storage_path = storage_path
    doc.status = DocumentStatus.PROCESSING
    doc.updated_at = _utcnow()
    session.add(version)
    session.add(doc)
    await session.commit()
    await session.refresh(version)

    _dispatch_ocr(doc.id)
    return version


async def get_document_bytes(session: AsyncSession, document_id: uuid.UUID) -> bytes:
    doc = await get_document(session, document_id)
    return get_storage().get_object(doc.storage_path)


# --------------------------------------------------------------------------- #
# Classification
# --------------------------------------------------------------------------- #
async def classify_document_content(
    session: AsyncSession, document_id: uuid.UUID, text: str
) -> tuple[str | None, float | None]:
    """Classify a document's text and store the result on the Document row."""
    doc = await get_document(session, document_id)
    category, confidence = classify_document(text)

    if category is not None:
        doc.classification = category
        doc.classification_confidence = confidence
        doc.classification_version = (doc.classification_version or 0) + 1
        session.add(doc)
        await session.commit()
        logger.info(
            "Classification: %s → %s (conf=%.3f)", document_id, category, confidence or 0
        )

    return category, confidence


# --------------------------------------------------------------------------- #
# Duplicate Detection
# --------------------------------------------------------------------------- #
async def detect_document_duplicates(
    session: AsyncSession,
    document_id: uuid.UUID,
    content: bytes,
    text: str,
) -> DuplicateResult:
    """Run duplicate detection and store results on the Document row."""
    detector = get_detector()
    result = detector.detect(str(document_id), content, text)

    doc = await get_document(session, document_id)
    doc.content_hash = result.content_hash

    if result.is_exact_duplicate and result.exact_match_id:
        doc.duplicate_of = uuid.UUID(result.exact_match_id)
        doc.duplicate_similarity = 1.0
        doc.status = DocumentStatus.DUPLICATE  # type: ignore[assignment]
    elif result.is_near_duplicate and result.near_match_id is not None:
        doc.duplicate_of = uuid.UUID(result.near_match_id)
        doc.duplicate_similarity = result.near_similarity
    else:
        doc.duplicate_of = None
        doc.duplicate_similarity = None

    session.add(doc)
    await session.commit()

    logger.info(
        "Duplicate detection: %s → exact=%s near=%s sim=%.3f",
        document_id,
        result.is_exact_duplicate,
        result.is_near_duplicate,
        result.near_similarity,
    )

    return result


# --------------------------------------------------------------------------- #
# Re-classify (re-run classification + duplicate detection)
# --------------------------------------------------------------------------- #
async def reclassify_document(
    session: AsyncSession, document_id: uuid.UUID
) -> tuple[tuple[str | None, float | None], DuplicateResult]:
    """Re-run classification and duplicate detection on an existing document."""
    doc = await get_document(session, document_id)

    # Get the document's text from chunks
    chunks = await list_chunks(session, document_id, limit=1000)
    text = "\n".join(c.text for c in chunks)

    # Get original content for hash
    content = await get_document_bytes(session, document_id)

    classification_result = await classify_document_content(session, document_id, text)
    duplicate_result = await detect_document_duplicates(
        session, document_id, content, text
    )

    return classification_result, duplicate_result
