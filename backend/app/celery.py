"""Celery application for background OCR/embedding/indexing tasks."""
from __future__ import annotations

import os

from celery import Celery

from app.config import settings

celery_app = Celery(
    "bargeham",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.workers.ocr",
        "app.workers.embed",
        "app.workers.index",
        "app.workers.transcribe",
        "app.workers.audiobook",
        "app.workers.podcast",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_routes={
        "app.workers.ocr.process_document": {"queue": "ocr"},
        "app.workers.embed.embed_chunks": {"queue": "embed"},
        "app.workers.index.index_document": {"queue": "index"},
        "app.workers.transcribe.transcribe_audio": {"queue": "transcribe"},
        "app.workers.audiobook.generate_audiobook": {"queue": "audiobook"},
        "app.workers.podcast.generate_podcast": {"queue": "podcast"},
    },
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    task_acks_late=True,
    task_default_retry_delay=5,
    task_max_retries=3,
)

if os.environ.get("CELERY_WORKER", "0") == "1":
    # Allow running as a standalone worker without importing FastAPI
    pass