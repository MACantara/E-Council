"""FastAPI-friendly repository base that maps repository errors to API exceptions."""

from __future__ import annotations

from typing import Any

from api.exceptions import NotFoundError
from repositories.base import BaseRepository


class APIBaseRepository(BaseRepository):
    """Repository wrapper for FastAPI endpoints.

    Extends the shared ``BaseRepository`` and converts framework-specific
    errors (e.g. Werkzeug 404) into API exceptions that the global exception
    handlers can serialize.
    """

    def get_or_404(self, id: Any) -> Any:
        """Get a record by primary key or raise a 404 API error."""
        obj = self.get(id)
        if obj is None:
            model_name = self.model.__name__ if self.model else "Resource"
            raise NotFoundError(detail=f"{model_name} not found")
        return obj
