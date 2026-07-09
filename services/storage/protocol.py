"""Storage backend protocol for E-Council."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class StorageBackend(ABC):
    """Abstract storage backend for uploads, deletions, and URL generation."""

    @abstractmethod
    def upload(
        self,
        file: Any,
        folder: str | None = None,
        resource_type: str = "image",
        **kwargs: Any,
    ) -> dict[str, str]:
        """Upload a file and return a dict with ``url`` and ``public_id``.

        Args:
            file: File-like object to upload.
            folder: Optional folder/path prefix.
            resource_type: Cloudinary-style resource type (e.g. ``image``, ``raw``, ``auto``).
            **kwargs: Additional backend-specific options.

        Returns:
            ``{"url": str, "public_id": str}``
        """

    @abstractmethod
    def delete(self, public_id: str, **kwargs: Any) -> bool:
        """Delete the file identified by ``public_id``.

        Args:
            public_id: Identifier returned by ``upload``.
            **kwargs: Additional backend-specific options.

        Returns:
            ``True`` if the deletion succeeded, otherwise ``False``.
        """

    @abstractmethod
    def get_url(self, public_id: str, **kwargs: Any) -> str | None:
        """Return a public URL for the file, or ``None`` if unavailable.

        Args:
            public_id: Identifier returned by ``upload``.
            **kwargs: Additional backend-specific options.
        """
