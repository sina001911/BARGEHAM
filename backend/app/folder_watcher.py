"""Folder Watcher — polls directories for new/modified files and auto-indexes them."""
from __future__ import annotations

import asyncio
import fnmatch
import logging
import os
import time
import uuid

from dataclasses import dataclass, field
from pathlib import Path

from app.celery import celery_app
from app.documents.models import Document, DocumentStatus
from app.storage import get_storage
from app.workers._db import run_async, worker_session
from app.workers.ocr import process_document as ocr_task

logger = logging.getLogger(__name__)

# Poll interval in seconds
POLL_INTERVAL = int(os.environ.get("BARGEHAM_WATCHER_POLL", "10"))
WATCH_PATTERNS = [
    "*.pdf", "*.docx", "*.xlsx", "*.txt",
    "*.png", "*.jpg", "*.jpeg", "*.tiff", "*.tif", "*.webp",
]
MIN_FILE_SIZE = 64


@dataclass
class WatchRecord:
    mtime_ns: int
    size: int


@dataclass
class FolderWatcherState:
    """In-memory state for one watched folder."""
    path: str
    records: dict[str, WatchRecord] = field(default_factory=dict)
    last_scan: float = 0.0
    items_scanned: int = 0
    items_new: int = 0
    items_updated: int = 0


def _matches_pattern(filename: str) -> bool:
    name = filename.lower()
    return any(fnmatch.fnmatch(name, p.lower()) for p in WATCH_PATTERNS)


def _file_mtime_ns(filepath: str) -> int | None:
    try:
        st = os.stat(filepath)
        if st.st_size < MIN_FILE_SIZE:
            return None
        return st.st_mtime_ns
    except OSError:
        return None


def _dir_walk(root: str) -> list[str]:
    out: list[str] = []
    for dirpath, _, filenames in os.walk(root):
        for fname in filenames:
            full = os.path.join(dirpath, fname)
            if _matches_pattern(fname):
                out.append(full)
    return sorted(out)


def _guess_mime(ext: str) -> str:
    mapping: dict[str, str] = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".doc": "application/msword",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xls": "application/vnd.ms-excel",
        ".txt": "text/plain",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
        ".webp": "image/webp",
    }
    return mapping.get(ext, "application/octet-stream")


class FolderWatcher:
    """Periodic scanner that detects new / modified files and triggers indexing."""

    def __init__(self) -> None:
        self._states: dict[str, FolderWatcherState] = {}
        self._stop_event: asyncio.Event | None = None
        self._task: asyncio.Task | None = None

    # ------------------------------------------------------------------ #
    # Management
    # ------------------------------------------------------------------ #

    def get_state(self, path: str) -> FolderWatcherState:
        realpath = os.path.realpath(path)
        if realpath not in self._states:
            self._states[realpath] = FolderWatcherState(path=realpath)
        return self._states[realpath]

    def remove_state(self, path: str) -> None:
        self._states.pop(os.path.realpath(path), None)

    # ------------------------------------------------------------------ #
    # Scanning
    # ------------------------------------------------------------------ #

    def scan_once(self, state: FolderWatcherState) -> dict:
        """Scan one directory; returns stats."""
        realpath = os.path.realpath(state.path)
        if not os.path.isdir(realpath):
            return {"path": state.path, "error": "directory_not_found"}

        found = _dir_walk(realpath)
        triggered: list[str] = []
        current_records: dict[str, WatchRecord] = {}

        for filepath in found:
            mtime = _file_mtime_ns(filepath)
            if mtime is None:
                continue
            record = WatchRecord(mtime_ns=mtime, size=os.path.getsize(filepath))
            old_record = state.records.get(filepath)
            if old_record is None:
                state.items_new += 1
                triggered.append(filepath)
            elif record.mtime_ns > old_record.mtime_ns:
                state.items_updated += 1
                triggered.append(filepath)
            current_records[filepath] = record

        state.records = current_records
        state.last_scan = time.time()
        state.items_scanned = len(found)
        return {
            "path": state.path,
            "scanned": len(found),
            "new": state.items_new,
            "updated": state.items_updated,
            "triggered": len(triggered),
        }

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    def start(self) -> None:
        if self._task and not self._task.done():
            return
        loop = asyncio.get_running_loop()
        self._stop_event = asyncio.Event()
        self._task = loop.create_task(self._poll_loop())
        logger.info("FolderWatcher started — polling every %ds", POLL_INTERVAL)

    def stop(self) -> None:
        if self._stop_event:
            self._stop_event.set()
        if self._task and not self._task.done():
            self._task.cancel()

    async def _poll_loop(self) -> None:
        assert self._stop_event is not None
        while not self._stop_event.is_set():
            try:
                for state in list(self._states.values()):
                    result = self.scan_once(state)
                    if result.get("error"):
                        continue
                    if result["triggered"] > 0:
                        for filepath in _dir_walk(state.path):
                            mtime = _file_mtime_ns(filepath)
                            if mtime is None:
                                continue
                            old = state.records.get(filepath)
                            if old is None or mtime > old.mtime_ns:
                                self._enqueue(filepath)
            except Exception as exc:
                logger.warning("Watcher poll error: %s", exc)
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(), timeout=POLL_INTERVAL
                )
            except asyncio.TimeoutError:
                pass

    @staticmethod
    def _enqueue(filepath: str) -> None:
        """Queue background job without blocking the poll loop."""
        try:
            run_async(_ingest_file(filepath))
        except RuntimeError:
            ingest_from_path.delay(filepath)  # type: ignore[attr-defined]


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def ingest_from_path(self, filepath: str) -> dict:
    """Celery entry-point: create document row + dispatch OCR worker."""
    return run_async(_ingest_file(filepath))


async def _ingest_file(filepath: str) -> dict:
    """Create a Document row and enqueue OCR pipeline."""
    fp = Path(filepath)
    mime_type = _guess_mime(fp.suffix.lower())
    doc_id = uuid.uuid4()
    storage_path = f"watcher/{doc_id}{fp.suffix}"

    with open(filepath, "rb") as f:
        data = f.read()

    try:
        stored_path = get_storage().put_object(storage_path, data)
    except Exception as exc:
        logger.warning("Storage upload failed for %s: %s", filepath, exc)
        return {"filepath": filepath, "status": "storage_failed"}

    async with worker_session() as session:
        doc = Document(
            id=doc_id,
            title=fp.stem,
            file_name=fp.name,
            storage_path=stored_path,
            mime_type=mime_type,
            status=DocumentStatus.UPLOADING,
        )
        session.add(doc)
        await session.commit()
        await session.refresh(doc)

    # Dispatch the full OCR → embed → classify → dedupe pipeline
    ocr_task.delay(str(doc.id))  # type: ignore[attr-defined]
    return {"filepath": filepath, "document_id": str(doc.id)}


# --------------------------------------------------------------------------- #
# Singleton
# --------------------------------------------------------------------------- #
_watcher: FolderWatcher | None = None


def get_watcher() -> FolderWatcher:
    global _watcher
    if _watcher is None:
        _watcher = FolderWatcher()
    return _watcher
