"""Document, folder, and tag HTTP endpoints."""
from __future__ import annotations

import uuid
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.router import get_current_admin, get_current_user
from app.database import get_session
from app.documents import service
from app.documents.schemas import (
    DocumentListResponse,
    DocumentReadWithTags,
    DocumentUpdate,
    DocumentVersionRead,
    FolderCreate,
    FolderRead,
    FolderUpdate,
    TagCreate,
    TagRead,
    TagUpdate,
    TextChunkRead,
    UploadResponse,
)
from app.exceptions import ValidationFailedError
from app.users.models import User
from app.users.schemas import Message

router = APIRouter(prefix="/documents", tags=["documents"])
folders_router = APIRouter(prefix="/folders", tags=["folders"])
tags_router = APIRouter(prefix="/tags", tags=["tags"])


def _parse_uuid_list(raw: str | None) -> list[uuid.UUID]:
    if not raw:
        return []
    out: list[uuid.UUID] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            out.append(uuid.UUID(part))
        except ValueError as exc:
            raise ValidationFailedError(f"Invalid id: {part}") from exc
    return out


# ------------------------------- Documents -------------------------------- #
@router.post("", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    folder_id: uuid.UUID | None = Form(default=None),
    tags: str | None = Form(default=None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UploadResponse:
    """Upload a document, store it, and enqueue OCR/indexing."""
    data = await file.read()
    if not data:
        raise ValidationFailedError("Uploaded file is empty")
    mime_type = file.content_type or "application/octet-stream"
    doc = await service.create_document_from_upload(
        session,
        title=title,
        file_name=file.filename or "upload",
        mime_type=mime_type,
        data=data,
        folder_id=folder_id,
        tag_ids=_parse_uuid_list(tags),
        owner_id=current_user.id,
    )
    return UploadResponse(
        document_id=doc.id,
        message="Document uploaded and queued for processing",
        status=doc.status.value,
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    folder_id: uuid.UUID | None = Query(default=None),
    q: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    include_deleted: bool = Query(default=False),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> DocumentListResponse:
    """List documents with optional folder/title filters."""
    items, total = await service.list_documents(
        session,
        folder_id=folder_id,
        q=q,
        skip=skip,
        limit=limit,
        include_deleted=include_deleted,
    )
    return DocumentListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/{document_id}", response_model=DocumentReadWithTags)
async def get_document(
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> DocumentReadWithTags:
    """Get a document's metadata and tags."""
    return await service.get_document_read(session, document_id)


@router.patch("/{document_id}", response_model=DocumentReadWithTags)
async def update_document(
    document_id: uuid.UUID,
    body: DocumentUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> DocumentReadWithTags:
    """Update a document's title or folder."""
    return await service.update_document(
        session, document_id, title=body.title, folder_id=body.folder_id
    )


@router.delete("/{document_id}", response_model=Message)
async def delete_document(
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Message:
    """Soft-delete a document (moves it to trash)."""
    await service.soft_delete_document(session, document_id)
    return Message(message="Document moved to trash")


@router.post("/{document_id}/restore", response_model=DocumentReadWithTags)
async def restore_document(
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> DocumentReadWithTags:
    """Restore a soft-deleted document."""
    return await service.restore_document(session, document_id)


@router.delete("/{document_id}/hard", response_model=Message)
async def hard_delete_document(
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin),
) -> Message:
    """Permanently delete a document and its derived data."""
    await service.hard_delete_document(session, document_id)
    return Message(message="Document permanently deleted")


@router.get("/{document_id}/chunks", response_model=list[TextChunkRead])
async def list_chunks(
    document_id: uuid.UUID,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=500, ge=1, le=2000),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[TextChunkRead]:
    """List extracted text chunks for a document."""
    chunks = await service.list_chunks(session, document_id, skip=skip, limit=limit)
    return [
        TextChunkRead(
            id=c.id,
            document_id=c.document_id,
            chunk_index=c.chunk_index,
            text=c.text,
            page_number=c.page_number,
            section=c.section,
            direction=c.direction,
        )
        for c in chunks
    ]


@router.get("/{document_id}/versions", response_model=list[DocumentVersionRead])
async def list_versions(
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[DocumentVersionRead]:
    """List a document's version history."""
    versions = await service.list_versions(session, document_id)
    return [DocumentVersionRead.model_validate(v) for v in versions]


@router.post(
    "/{document_id}/versions",
    response_model=DocumentVersionRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_version(
    document_id: uuid.UUID,
    file: UploadFile = File(...),
    change_summary: str | None = Form(default=None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> DocumentVersionRead:
    """Upload a new version of a document."""
    data = await file.read()
    if not data:
        raise ValidationFailedError("Uploaded file is empty")
    version = await service.add_document_version(
        session,
        document_id,
        file_name=file.filename or "upload",
        mime_type=file.content_type or "application/octet-stream",
        data=data,
        change_summary=change_summary,
        user_id=current_user.id,
    )
    return DocumentVersionRead.model_validate(version)


@router.get("/{document_id}/download")
async def download_document(
    document_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Download the original file."""
    doc = await service.get_document(session, document_id)
    data = await service.get_document_bytes(session, document_id)
    filename = quote(doc.file_name)
    return Response(
        content=data,
        media_type=doc.mime_type,
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{filename}",
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "default-src 'none'; sandbox",
        },
    )


@router.put("/{document_id}/tags", response_model=DocumentReadWithTags)
async def set_tags(
    document_id: uuid.UUID,
    tag_ids: list[uuid.UUID],
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> DocumentReadWithTags:
    """Replace the full set of tags on a document."""
    return await service.set_document_tags(session, document_id, tag_ids)


# -------------------------------- Folders --------------------------------- #
@folders_router.get("", response_model=list[FolderRead])
async def list_folders(
    parent_id: uuid.UUID | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[FolderRead]:
    """List folders."""
    return await service.list_folders(session, parent_id=parent_id)


@folders_router.post("", response_model=FolderRead, status_code=status.HTTP_201_CREATED)
async def create_folder(
    body: FolderCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> FolderRead:
    """Create a folder."""
    return await service.create_folder(
        session, body.name, parent_id=body.parent_id, owner_id=current_user.id
    )


@folders_router.patch("/{folder_id}", response_model=FolderRead)
async def update_folder(
    folder_id: uuid.UUID,
    body: FolderUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> FolderRead:
    """Rename or move a folder."""
    return await service.update_folder(
        session, folder_id, name=body.name, parent_id=body.parent_id
    )


@folders_router.delete("/{folder_id}", response_model=Message)
async def delete_folder(
    folder_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Message:
    """Delete a folder (documents are detached, not deleted)."""
    await service.delete_folder(session, folder_id)
    return Message(message="Folder deleted")


# --------------------------------- Tags ----------------------------------- #
@tags_router.get("", response_model=list[TagRead])
async def list_tags(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[TagRead]:
    """List tags."""
    return await service.list_tags(session)


@tags_router.post("", response_model=TagRead, status_code=status.HTTP_201_CREATED)
async def create_tag(
    body: TagCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TagRead:
    """Create a tag."""
    return await service.create_tag(session, body.name, body.color)


@tags_router.patch("/{tag_id}", response_model=TagRead)
async def update_tag(
    tag_id: uuid.UUID,
    body: TagUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TagRead:
    """Update a tag."""
    return await service.update_tag(session, tag_id, name=body.name, color=body.color)


@tags_router.delete("/{tag_id}", response_model=Message)
async def delete_tag(
    tag_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Message:
    """Delete a tag."""
    await service.delete_tag(session, tag_id)
    return Message(message="Tag deleted")
