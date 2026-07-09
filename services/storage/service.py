"""Factory for resolving the active storage backend."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flask import current_app, has_app_context

from config.config import StorageConfig

from .backends import CloudinaryStorage, LocalFilesystemStorage, MemoryStorage, NullStorage
from .errors import StorageError
from .protocol import StorageBackend

if TYPE_CHECKING:
    from flask import Flask


# Maps provider names to backend classes.  ``get_storage`` returns an instance of
# the configured provider, so the rest of the application does not import
# Cloudinary (or any other vendor SDK) directly.
_BACKENDS: dict[str, type[StorageBackend]] = {
    "cloudinary": CloudinaryStorage,
    "local": LocalFilesystemStorage,
    "memory": MemoryStorage,
    "null": NullStorage,
}


def get_storage(app: Flask | None = None) -> StorageBackend:
    """Return a storage backend configured for the current application.

    The provider is read from the Flask app config (``STORAGE_PROVIDER``) when
    an application context is available; otherwise it falls back to the
    ``StorageConfig`` class, which reads from environment variables.

    Args:
        app: Optional Flask app to read configuration from.

    Returns:
        An instance of the configured ``StorageBackend``.

    Raises:
        StorageError: If the configured provider is unknown.
    """
    if app is not None:
        provider = app.config.get("STORAGE_PROVIDER", StorageConfig.STORAGE_PROVIDER)
        upload_dir = app.config.get("STORAGE_LOCAL_PATH", StorageConfig.STORAGE_LOCAL_PATH)
        base_url = app.config.get("STORAGE_LOCAL_BASE_URL", StorageConfig.STORAGE_LOCAL_BASE_URL)
    elif has_app_context():
        provider = current_app.config.get("STORAGE_PROVIDER", StorageConfig.STORAGE_PROVIDER)
        upload_dir = current_app.config.get("STORAGE_LOCAL_PATH", StorageConfig.STORAGE_LOCAL_PATH)
        base_url = current_app.config.get("STORAGE_LOCAL_BASE_URL", StorageConfig.STORAGE_LOCAL_BASE_URL)
    else:
        provider = StorageConfig.STORAGE_PROVIDER
        upload_dir = StorageConfig.STORAGE_LOCAL_PATH
        base_url = StorageConfig.STORAGE_LOCAL_BASE_URL

    backend_cls = _BACKENDS.get(provider)
    if backend_cls is None:
        raise StorageError(f"Unknown storage provider: {provider!r}")

    if backend_cls is LocalFilesystemStorage:
        return backend_cls(upload_dir=upload_dir, base_url=base_url)

    return backend_cls()
