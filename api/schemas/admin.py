"""Pydantic schemas for the FastAPI admin endpoints."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from api.schemas.auth import ROLE_CHOICES, UserResponse


class UserRoleUpdate(BaseModel):
    """Request body for updating a user's role."""

    users_role: Literal[ROLE_CHOICES]


class UserListResponse(BaseModel):
    """Paginated list of users."""

    items: list[UserResponse]
    total: int
    page: int
    per_page: int
    pages: int
