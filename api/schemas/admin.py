"""Pydantic schemas for the FastAPI admin endpoints."""

from __future__ import annotations

from datetime import datetime
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


class AuditLogResponse(BaseModel):
    """Single audit log entry."""

    audit_log_id: int
    audit_log_timestamp: datetime
    audit_log_user_id: int | None
    audit_log_action: str
    audit_log_entity_type: str
    audit_log_entity_id: int | None
    audit_log_changes: dict | None
    user: UserResponse | None

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    """Paginated list of audit logs."""

    items: list[AuditLogResponse]
    total: int
    page: int
    per_page: int
    pages: int


class UserStats(BaseModel):
    """Aggregate user statistics."""

    total: int
    verified: int
    by_role: dict[str, int]


class DashboardStatsResponse(BaseModel):
    """Admin dashboard payload with user, resource, and activity data."""

    user_stats: UserStats
    resource_counts: dict[str, int]
    recent_activity: list[AuditLogResponse]
