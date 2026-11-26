"""Tests for document service helpers and DB-backed document operations."""
from __future__ import annotations

import uuid

import pytest

from app.documents import service
from app.documents.models import DocumentStatus, DocumentType
from app.exceptions import ValidationFailedError


def test_document_type_from_mime():
    assert service.document_type_from("a.pdf", "application/pdf") == DocumentType.PDF


def test_document_type_from_extension_fallback():
    assert service.document_type_from("image.png", "application/octet-stream") == DocumentType.PNG


def test_document_type_unknown():
    assert service.document_type_from("x.zzz", "application/unknown") == DocumentType.OTHER


def test_ensure_allowed_pdf():
    service._ensure_allowed("application/pdf", "a.pdf")


def test_ensure_allowed_rejects_exe():
    with pytest.raises(ValidationFailedError):
        service._ensure_allowed("application/x-msdownload", "a.exe")


def test_check_size_ok():
    service._check_size(100)


def test_check_size_rejects_large():
    service._check_size(1)
    with pytest.raises(ValidationFailedError):
        service._check_size(100 * 1024 * 1024 + 1)


@pytest.mark.asyncio
async def test_create_and_get_document(session):
    doc = await service.create_document_from_upload(
        session,
        title="مشتریان",
        file_name="customers.pdf",
        mime_type="application/pdf",
        data=b"%PDF-1.4 fake",
        owner_id=uuid.uuid4(),
    )
    assert doc.status == DocumentStatus.PROCESSING
    got = await service.get_document_read(session, doc.id)
    assert got.title == "مشتریان"
    assert got.file_name == "customers.pdf"


@pytest.mark.asyncio
async def test_update_document(session):
    doc = await service.create_document_from_upload(
        session,
        title=None,
        file_name="a.txt",
        mime_type="text/plain",
        data=b"hello",
        owner_id=uuid.uuid4(),
    )
    updated = await service.update_document(
        session, doc.id, title="تصحیح شد", folder_id=None
    )
    assert updated.title == "تصحیح شد"


@pytest.mark.asyncio
async def test_soft_delete_and_restore(session):
    doc = await service.create_document_from_upload(
        session,
        title="حذف",
        file_name="d.txt",
        mime_type="text/plain",
        data=b"x",
        owner_id=uuid.uuid4(),
    )
    await service.soft_delete_document(session, doc.id)
    got = await service.get_document_read(session, doc.id)
    restored = await service.restore_document(session, doc.id)
    assert restored.is_deleted is False
