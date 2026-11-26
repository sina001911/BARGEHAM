"""MinIO / S3-compatible storage backend."""
from __future__ import annotations

import io
import uuid
from typing import Any

from minio import Minio
from minio.error import S3Error

from app.config import settings
from app.exceptions import AppException


class MinIOStorage:
    """S3-compatible object storage using MinIO."""

    def __init__(self) -> None:
        self.client = Minio(
            endpoint=settings.storage_endpoint.replace("http://", "").replace("https://", ""),
            access_key=settings.storage_access_key,
            secret_key=settings.storage_secret_key,
            secure=settings.storage_secure,
        )
        self.bucket = settings.storage_bucket
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except S3Error as exc:
            raise AppException(f"Storage error: {exc}") from exc

    def put_object(
        self,
        file_name: str,
        data: bytes | io.BytesIO,
        content_type: str = "application/octet-stream",
        length: int | None = None,
    ) -> str:
        """Upload an object and return its storage path."""
        try:
            if isinstance(data, bytes):
                data = io.BytesIO(data)
            self.client.put_object(
                self.bucket,
                file_name,
                data,
                length=length or -1,
                content_type=content_type,
            )
            return f"{self.bucket}/{file_name}"
        except S3Error as exc:
            raise AppException(f"Upload failed: {exc}") from exc

    def get_object(self, path: str) -> bytes:
        """Download an object's full content."""
        bucket, _, object_name = path.partition("/")
        try:
            response = self.client.get_object(bucket, object_name)
            return response.read()
        except S3Error as exc:
            raise AppException(f"Download failed: {exc}") from exc

    def get_stream(self, path: str) -> Any:
        """Get a stream for an object."""
        bucket, _, object_name = path.partition("/")
        return self.client.get_object(bucket, object_name)

    def delete_object(self, path: str) -> None:
        """Delete an object."""
        bucket, _, object_name = path.partition("/")
        try:
            self.client.remove_object(bucket, object_name)
        except S3Error as exc:
            raise AppException(f"Delete failed: {exc}") from exc

    def object_exists(self, path: str) -> bool:
        """Check if an object exists."""
        bucket, _, object_name = path.partition("/")
        try:
            self.client.stat_object(bucket, object_name)
            return True
        except S3Error:
            return False

    def generate_object_name(self, original_name: str, document_id: uuid.UUID | None = None) -> str:
        """Generate a unique storage path."""
        ext = ""
        if "." in original_name:
            ext = "." + original_name.rsplit(".", 1)[-1]
        unique_id = str(uuid.uuid4())
        prefix = f"{document_id}/" if document_id else ""
        return f"{prefix}{unique_id}{ext}"