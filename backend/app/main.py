"""BARGEHAM FastAPI application factory."""
from __future__ import annotations

import time
import uuid

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import Depends, FastAPI, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session

from app.ai.rag import ask, ask_stream
from app.auth.router import router as auth_router
from app.config import settings
from app.database import close_db, init_db, get_session
from app.documents.router import (
    folders_router,
    router as documents_router,
    tags_router,
    watchers_router,
)
from app.exceptions import register_exception_handlers
from app.logging import configure_logging
from app.middleware.auth import get_current_user
from app.middleware.cors import setup_cors
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security_headers import setup_security_headers
from app.academy.intelligence_router import router as academy_intelligence_router
from app.academy.learning_router import router as academy_learning_router
from app.academy.router import router as academy_router
from app.audio.router import playlists_router as audio_playlists_router
from app.audio.router import router as audio_router
from app.audio_creation.router import router as audio_creation_router
from app.classification.router import router as classification_router
from app.knowledge.graph_router import (
    extract_router as knowledge_extract_router,
    relations_router as knowledge_relations_router,
    router as knowledge_graph_router,
    traverse_router as knowledge_traverse_router,
)
from app.knowledge.router import router as knowledge_router
from app.search.router import router as search_router
from app.users.models import User
from app.users.router import router as users_router

configure_logging()

# Global flag: True when PostgreSQL is reachable, False otherwise.
# Endpoints that need DB check this before running.
db_available: bool = False


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup/shutdown lifecycle with graceful DB degradation."""
    global db_available
    try:
        await init_db()
        db_available = True
        print("[BARGEHAM] Database connected successfully.")
    except Exception as exc:  # noqa: BLE001
        db_available = False
        print(f"[BARGEHAM] WARNING: Database not available ({exc}). "
              f"Running in limited mode — DB endpoints will return 503.")
    # Start folder watcher after DB is ready
    from app.folder_watcher import get_watcher

    watcher = get_watcher()
    watcher.start()
    try:
        yield
    finally:
        watcher.stop()
    await close_db()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Intelligent Document Processing Platform with Knowledge Graph",
    lifespan=lifespan,
)

# Middleware (order matters: rate limit first, then CORS, then security headers)
app.add_middleware(RateLimitMiddleware)
setup_cors(app)
setup_security_headers(app)

# Exception handlers
register_exception_handlers(app)

# DB-availability guard: if DB is down, return 503 for all DB-dependent routes.
@app.middleware("db-availability")
async def _db_availability_middleware(request: Request, call_next):
    if not db_available and request.url.path not in (
        "/",
        "/health",
        "/metrics",
        "/docs",
        "/openapi.json",
    ):
        return JSONResponse(
            status_code=503,
            content={
                "error": True,
                "code": "DATABASE_UNAVAILABLE",
                "message": "Database is not available. Please start PostgreSQL and retry.",
            },
        )
    return await call_next(request)


# Routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(documents_router)
app.include_router(folders_router)
app.include_router(tags_router)
app.include_router(search_router)
app.include_router(classification_router)
app.include_router(knowledge_graph_router)
app.include_router(knowledge_relations_router)
app.include_router(knowledge_extract_router)
app.include_router(knowledge_traverse_router)
app.include_router(knowledge_router)
app.include_router(watchers_router)
app.include_router(academy_router)
app.include_router(academy_intelligence_router)
app.include_router(academy_learning_router)
app.include_router(audio_router)
app.include_router(audio_playlists_router)
app.include_router(audio_creation_router)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
)


@app.middleware("prometheus")
async def _prometheus_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    REQUEST_COUNT.labels(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
    ).inc()
    REQUEST_LATENCY.labels(method=request.method, path=request.url.path).observe(elapsed)
    return response


@app.get("/health", tags=["health"])
async def health() -> JSONResponse:
    """Liveness probe."""
    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "app": settings.app_name,
            "version": settings.app_version,
        },
    )


@app.get("/metrics", tags=["health"])
async def metrics() -> Response:
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/ask", tags=["ai"])
async def ask_endpoint(
    query: str,
    document_id: uuid.UUID | None = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Ask a question about documents and get an answer with citations."""
    answer = await ask(session, query=query, document_id=document_id)
    return {"answer": answer}


@app.post("/ask/stream", tags=["ai"])
async def ask_stream_endpoint(
    query: str,
    document_id: uuid.UUID | None = None,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Stream an answer token-by-token (Server-Sent Events)."""
    from fastapi.responses import StreamingResponse

    async def event_stream():
        async for token in ask_stream(
            session, query=query, document_id=document_id
        ):
            yield f"data: {token}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/", tags=["health"])
async def root() -> dict:
    """Root endpoint with service info."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }