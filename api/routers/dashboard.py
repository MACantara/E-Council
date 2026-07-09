"""FastAPI admin dashboard and audit endpoints for the E-Council API."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies import get_pagination_params, require_admin
from api.schemas.admin import (
    AuditLogListResponse,
    AuditLogResponse,
    DashboardStatsResponse,
)
from api.schemas.common import PaginationParams
from models import Users
from services.audit import (
    fetch_audit_log,
    get_audit_logs,
    get_dashboard_stats,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard", response_model=DashboardStatsResponse)
def admin_dashboard(
    db: Session = Depends(get_db),
    current_user: Users = Depends(require_admin),
):
    """Return admin dashboard statistics (admin only)."""
    return get_dashboard_stats(db)


@router.get("/audit-logs", response_model=AuditLogListResponse)
def list_audit_logs(
    params: PaginationParams = Depends(get_pagination_params),
    user_id: int | None = None,
    action: str | None = None,
    entity_type: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user: Users = Depends(require_admin),
):
    """List audit logs with pagination and optional filtering (admin only)."""
    return get_audit_logs(
        db,
        params,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        search=search,
    )


@router.get("/audit-logs/{audit_log_id}", response_model=AuditLogResponse)
def get_audit_log(
    audit_log_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(require_admin),
):
    """Return a single audit log entry (admin only)."""
    audit = fetch_audit_log(db, audit_log_id)
    if audit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found",
        )
    return audit
