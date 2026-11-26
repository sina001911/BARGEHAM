"""Pytest configuration and shared fixtures for BARGEHAM tests."""
from __future__ import annotations

import asyncio
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.documents.models import Document, DocumentStatus

TEST_DB = "postgresql+asyncpg://bargeham:bargeham@localhost/bargeham_test"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_engine():
    eng = create_async_engine(TEST_DB, poolclass=NullPool, future=True)
    yield eng
    await eng.dispose()


@pytest.fixture
async def session(test_engine):
    maker = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with maker() as s:
        yield s


@pytest.fixture
async def doc(session: AsyncSession):
    d = Document(
        id=uuid.uuid4(),
        title="تست اسناد",
        file_name="test.pdf",
        file_size=123,
        mime_type="application/pdf",
        document_type="pdf",
        storage_path="bargeham-documents/abc.pdf",
        status=DocumentStatus.READY,
    )
    session.add(d)
    await session.commit()
    await session.refresh(d)
    return d
