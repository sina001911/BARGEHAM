"""Index worker: orchestrate OCR + embedding for a document (future use)."""
from __future__ import annotations

import logging
import uuid

from app.celery import celery_app
from app.workers._db import run_async, worker_session

logger = logging.getLogger(__name__)


@celery_app.task(
    name="app.workers.index.index_document",
    bind=True,
    max_retries=3,
    default_retry_delay=10,
)
def index_document(self, document_id: str) -> dict:
    """Run OCR then embeddings for a document (orchestration task)."""
    return run_async(_index_document(uuid.UUID(document_id)))


async def _index_document(document_id: uuid.UUID) -> dict:
    from app.workers.ocr import _process_document

    logger.info("Indexing document %s", document_id)
    # OCR is the pipeline entrypoint; embeddings are queued from there.
    return await _process_document(document_id)