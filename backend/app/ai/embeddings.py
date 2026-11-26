"""Sentence-transformer embedding service (lazy-loaded singleton)."""
from __future__ import annotations

import asyncio
import logging
import threading

from app.config import settings

logger = logging.getLogger(__name__)

_model = None
_lock = threading.Lock()


def _get_model():
    """Load and cache the embedding model on first use."""
    global _model
    if _model is not None:
        return _model
    with _lock:
        if _model is not None:
            return _model
        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model %s", settings.embedding_model)
        try:
            _model = SentenceTransformer(settings.embedding_model)
        except Exception as exc:  # pragma: no cover - model download issues
            logger.warning(
                "Primary embedding model failed (%s); trying fallback %s",
                exc,
                settings.embedding_fallback_model,
            )
            _model = SentenceTransformer(settings.embedding_fallback_model)
        return _model


def model_dimension() -> int:
    """Return the configured embedding dimension."""
    return settings.embedding_dim


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts synchronously (used by Celery workers)."""
    if not texts:
        return []
    model = _get_model()
    vectors = model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
        batch_size=32,
        show_progress_bar=False,
    )
    return [v.tolist() for v in vectors]


async def embed_query(text: str) -> list[float] | None:
    """Embed a single query string without blocking the event loop."""
    if not settings.embedding_enabled or not text.strip():
        return None
    loop = asyncio.get_running_loop()
    try:
        return await loop.run_in_executor(None, lambda: embed_texts([text])[0])
    except Exception as exc:  # pragma: no cover
        logger.warning("Query embedding failed: %s", exc)
        return None


async def embed_batch(texts: list[str]) -> list[list[float]]:
    """Async wrapper around :func:`embed_texts` for API-side use."""
    if not texts:
        return []
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: embed_texts(texts))
