"""Storage abstraction for object storage."""
from app.storage.minio import MinIOStorage
from app.storage.local import LocalStorage

__all__ = ["MinIOStorage", "LocalStorage", "get_storage"]


def get_storage():
    """Return the configured storage backend."""
    from app.config import settings

    if settings.storage_endpoint and "minio" in settings.storage_endpoint.lower():
        return MinIOStorage()
    return LocalStorage()