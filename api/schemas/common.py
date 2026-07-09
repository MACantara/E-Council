"""Shared Pydantic schemas for the FastAPI API."""

from __future__ import annotations

from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class OrderEnum(str, Enum):
    """Sort order direction."""

    asc = "asc"
    desc = "desc"


class MessageResponse(BaseModel):
    """A simple message response."""

    message: str


class ErrorResponse(BaseModel):
    """A structured error response."""

    detail: str
    errors: list[str] | None = None


class PaginationParams(BaseModel):
    """Reusable pagination, sorting, and search parameters."""

    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)
    sort: str | None = None
    order: OrderEnum = OrderEnum.asc
    search: str | None = None


class PaginationMetadata(BaseModel):
    """Pagination metadata returned with list responses."""

    total: int
    page: int
    per_page: int
    pages: int


class ResponseEnvelope(BaseModel, Generic[T]):
    """Generic response wrapper used by every router."""

    success: bool = True
    data: T | None = None
    message: str | None = None
    errors: list[str] | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response with metadata."""

    items: list[T]
    pagination: PaginationMetadata


def build_pagination_metadata(*, total: int, page: int, per_page: int) -> PaginationMetadata:
    """Build pagination metadata from total count and page parameters."""
    pages = (total + per_page - 1) // per_page if per_page > 0 else 0
    return PaginationMetadata(total=total, page=page, per_page=per_page, pages=pages)
