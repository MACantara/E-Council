"""Concrete storage backend implementations for E-Council."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from werkzeug.utils import secure_filename

from .errors import StorageError
from .protocol import StorageBackend


class NullStorage(StorageBackend):
    """No-op storage backend. Uploads are ignored and deletions always succeed."""

    def upload(
        self,
        file: Any,
        folder: str | None = None,
        resource_type: str = "image",
        **kwargs: Any,
    ) -> dict[str, str]:
        """Return a placeholder result without storing anything."""
        return {"url": "", "public_id": ""}

    def delete(self, public_id: str, **kwargs: Any) -> bool:
        """Always report success."""
        return True

    def get_url(self, public_id: str, **kwargs: Any) -> str | None:
        """Return an empty string."""
        return ""


class MemoryStorage(StorageBackend):
    """In-memory storage backend for unit tests and local development.

    Files are kept in a dictionary keyed by the generated public_id.
    """

    def __init__(self) -> None:
        """Initialize the in-memory file store."""
        self._files: dict[str, bytes] = {}

    def upload(
        self,
        file: Any,
        folder: str | None = None,
        resource_type: str = "image",
        **kwargs: Any,
    ) -> dict[str, str]:
        """Store the file in memory and return a memory:// URL."""
        try:
            content = file.read()
        except Exception as e:
            raise StorageError("Failed to read file for memory storage", e) from e

        public_id = f"{folder}/{uuid.uuid4().hex}" if folder else uuid.uuid4().hex
        self._files[public_id] = content
        return {"url": f"memory://{public_id}", "public_id": public_id}

    def delete(self, public_id: str, **kwargs: Any) -> bool:
        """Remove the file from memory."""
        return self._files.pop(public_id, None) is not None

    def get_url(self, public_id: str, **kwargs: Any) -> str | None:
        """Return the memory URL if the file exists."""
        return f"memory://{public_id}" if public_id in self._files else None


class LocalFilesystemStorage(StorageBackend):
    """Local filesystem storage backend.

    Files are saved under ``upload_dir`` and served from ``base_url``.
    """

    def __init__(self, upload_dir: str | Path = "uploads", base_url: str = "/static/uploads") -> None:
        """Initialize the local filesystem backend.

        Args:
            upload_dir: Root directory on disk where files are stored.
            base_url: Public URL prefix used in ``get_url``.
        """
        self.upload_dir = Path(upload_dir)
        self.base_url = base_url.rstrip("/")

    def upload(
        self,
        file: Any,
        folder: str | None = None,
        resource_type: str = "image",
        **kwargs: Any,
    ) -> dict[str, str]:
        """Save the file to disk and return a local URL."""
        try:
            filename = secure_filename(getattr(file, "filename", None) or str(uuid.uuid4().hex))
            if not filename:
                filename = uuid.uuid4().hex

            # Ensure a unique filename
            name = Path(filename).stem
            ext = Path(filename).suffix
            unique_name = f"{name}_{uuid.uuid4().hex}{ext}" if name else f"{uuid.uuid4().hex}{ext}"

            public_id = f"{folder}/{unique_name}" if folder else unique_name
            target_path = self.upload_dir / public_id
            target_path.parent.mkdir(parents=True, exist_ok=True)

            with target_path.open("wb") as f:
                f.write(file.read())
        except Exception as e:
            raise StorageError("Failed to save file to local filesystem", e) from e

        return {"url": f"{self.base_url}/{public_id}", "public_id": public_id}

    def delete(self, public_id: str, **kwargs: Any) -> bool:
        """Delete the file from disk."""
        try:
            path = self.upload_dir / public_id
            if path.exists():
                path.unlink()
                return True
            return False
        except Exception as e:
            raise StorageError("Failed to delete file from local filesystem", e) from e

    def get_url(self, public_id: str, **kwargs: Any) -> str | None:
        """Return the public URL for the stored file."""
        path = self.upload_dir / public_id
        return f"{self.base_url}/{public_id}" if path.exists() else None


class CloudinaryStorage(StorageBackend):
    """Cloudinary storage backend adapter."""

    def __init__(self) -> None:
        """Initialize Cloudinary configuration from environment variables."""
        import cloudinary

        from config.config import CloudinaryConfig

        if CloudinaryConfig.CLOUDINARY_CLOUD_NAME:
            cloudinary.config(
                cloud_name=CloudinaryConfig.CLOUDINARY_CLOUD_NAME,
                api_key=CloudinaryConfig.CLOUDINARY_API_KEY,
                api_secret=CloudinaryConfig.CLOUDINARY_API_SECRET,
                secure=CloudinaryConfig.CLOUDINARY_SECURE,
            )

    def upload(
        self,
        file: Any,
        folder: str | None = None,
        resource_type: str = "image",
        **kwargs: Any,
    ) -> dict[str, str]:
        """Upload a file to Cloudinary."""
        import cloudinary.exceptions
        import cloudinary.uploader

        upload_kwargs = {"resource_type": resource_type, **kwargs}
        if folder:
            upload_kwargs["folder"] = folder

        try:
            result = cloudinary.uploader.upload(file, **upload_kwargs)
        except cloudinary.exceptions.Error as e:
            raise StorageError(f"Cloudinary upload failed: {e}", e) from e

        return {
            "url": result.get("secure_url") or result.get("url", ""),
            "public_id": result.get("public_id", ""),
        }

    def delete(self, public_id: str, **kwargs: Any) -> bool:
        """Delete a file from Cloudinary."""
        import cloudinary.exceptions
        import cloudinary.uploader

        try:
            cloudinary.uploader.destroy(public_id, **kwargs)
            return True
        except cloudinary.exceptions.Error as e:
            raise StorageError(f"Cloudinary delete failed: {e}", e) from e

    def get_url(self, public_id: str, **kwargs: Any) -> str | None:
        """Return a Cloudinary URL for the public_id."""
        import cloudinary.utils

        try:
            url, _ = cloudinary.utils.cloudinary_url(public_id, secure=True, **kwargs)
            return url
        except Exception:
            return None
