"""Local filesystem storage backend (development / single-node)."""
from __future__ import annotations

import io
import uuid
from pathlib import Path
from typing import Any

from app.exceptions import AppException


class LocalStorage:
    """Local filesystem storage backend."""

    def __init__(self) -> None:
        self.base_path = Path("storage")
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.bucket = "local"

    def _full_path(self, path: str) -> Path:
        # Storage is flat: only the final path segment (the object name) is used
        # on disk, so writes and reads must resolve to the same file regardless
        # of any bucket / document-id prefix carried in the logical path.
        return self.base_path / Path(path).name

    def put_object(
        self,
        file_name: str,
        data: bytes | io.BytesIO,
        content_type: str = "application/octet-stream",
        length: int | None = None,
    ) -> str:
        path = self._full_path(file_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, bytes):
            path.write_bytes(data)
        else:
            path.write_bytes(data.read())
        return f"{self.bucket}/{file_name}"

    def get_object(self, path: str) -> bytes:
        file_path = self._full_path(path)
        if not file_path.exists():
            raise AppException("Object not found", code="NOT_FOUND", status_code=404)
        return file_path.read_bytes()

    def get_stream(self, path: str) -> Any:
        file_path = self._full_path(path)
        if not file_path.exists():
            raise AppException("Object not found", code="NOT_FOUND", status_code=404)
        return open(file_path, "rb")

    def delete_object(self, path: str) -> None:
        file_path = self._full_path(path)
        if file_path.exists():
            file_path.unlink()

    def object_exists(self, path: str) -> bool:
        return self._full_path(path).exists()

    def generate_object_name(self, original_name: str, document_id: uuid.UUID | None = None) -> str:
        ext = ""
        if "." in original_name:
            ext = "." + original_name.rsplit(".", 1)[-1]
        unique_id = str(uuid.uuid4())
        prefix = f"{document_id}/" if document_id else ""
        return f"{prefix}{unique_id}{ext}"