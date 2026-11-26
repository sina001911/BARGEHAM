"""Per-task async DB sessions for Celery workers.

Each task creates its own engine/loop so connections are never reused across
event loops (which asyncio.run would otherwise invalidate).
"""
from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Coroutine
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings


@asynccontextmanager
async def worker_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(settings.database_url, poolclass=NullPool, future=True)
    maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with maker() as session:
            yield session
    finally:
        await engine.dispose()


def run_async(coro: Coroutine[Any, Any, Any]) -> Any:
    """Run a coroutine in a fresh event loop (for synchronous Celery tasks)."""
    return asyncio.run(coro)
