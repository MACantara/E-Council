"""Audit log and dashboard statistics service for the FastAPI API."""

from __future__ import annotations

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from api.schemas.common import PaginationParams
from models import (
    AuditLog,
    BoardResolutions,
    ConceptPaperForms,
    Departments,
    Documentation,
    Events,
    FinancialReports,
    MinutesOfTheMeeting,
    StudentOrganizations,
    Users,
)

RESOURCE_MODELS = {
    "departments": Departments,
    "student_organizations": StudentOrganizations,
    "events": Events,
    "concept_papers": ConceptPaperForms,
    "financial_reports": FinancialReports,
    "documentation": Documentation,
    "board_resolutions": BoardResolutions,
    "meetings": MinutesOfTheMeeting,
}

SORT_COLUMNS = {
    "timestamp": AuditLog.audit_log_timestamp,
    "action": AuditLog.audit_log_action,
    "entity_type": AuditLog.audit_log_entity_type,
    "entity_id": AuditLog.audit_log_entity_id,
    "user_id": AuditLog.audit_log_user_id,
}


def log_action(
    session: Session,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    changes: dict | None = None,
    user_id: int | None = None,
) -> AuditLog:
    """Create an AuditLog record for a state-changing action."""
    audit = AuditLog(
        audit_log_user_id=user_id,
        audit_log_action=action,
        audit_log_entity_type=entity_type,
        audit_log_entity_id=entity_id,
        audit_log_changes=changes,
    )
    session.add(audit)
    session.commit()
    session.refresh(audit)
    return audit


def fetch_audit_log(session: Session, audit_log_id: int) -> AuditLog | None:
    """Return a single audit log by id, with the user relationship loaded."""
    return (
        session.query(AuditLog)
        .options(
            joinedload(AuditLog.user).joinedload(Users.department),
        )
        .filter_by(audit_log_id=audit_log_id)
        .first()
    )


def get_audit_logs(
    session: Session,
    params: PaginationParams,
    *,
    user_id: int | None = None,
    action: str | None = None,
    entity_type: str | None = None,
    search: str | None = None,
) -> dict:
    """Return paginated audit logs with optional filters."""
    query = (
        session.query(AuditLog)
        .options(
            joinedload(AuditLog.user).joinedload(Users.department),
        )
        .order_by(AuditLog.audit_log_timestamp.desc())
    )

    if user_id is not None:
        query = query.filter(AuditLog.audit_log_user_id == user_id)
    if action:
        query = query.filter(AuditLog.audit_log_action.ilike(action))
    if entity_type:
        query = query.filter(AuditLog.audit_log_entity_type.ilike(entity_type))
    if search:
        term = f"%{search}%"
        query = query.filter(
            or_(
                AuditLog.audit_log_action.ilike(term),
                AuditLog.audit_log_entity_type.ilike(term),
            )
        )

    if params.sort:
        column = SORT_COLUMNS.get(params.sort) or getattr(AuditLog, params.sort, None)
        if column is not None:
            query = query.order_by(column.desc() if params.order.value == "desc" else column.asc())

    total = query.count()
    items = query.offset((params.page - 1) * params.per_page).limit(params.per_page).all()
    pages = (total + params.per_page - 1) // params.per_page if params.per_page else 0

    return {
        "items": items,
        "total": total,
        "page": params.page,
        "per_page": params.per_page,
        "pages": pages,
    }


def get_recent_activity(session: Session, limit: int = 10) -> list[AuditLog]:
    """Return the most recent audit log entries."""
    return (
        session.query(AuditLog)
        .options(
            joinedload(AuditLog.user).joinedload(Users.department),
        )
        .order_by(AuditLog.audit_log_timestamp.desc())
        .limit(limit)
        .all()
    )


def get_user_stats(session: Session) -> dict:
    """Return aggregate user statistics."""
    total = session.query(func.count(Users.users_id)).scalar()
    verified = session.query(func.count(Users.users_id)).filter(Users.users_email_verified == 1).scalar()
    role_counts = session.query(Users.users_role, func.count(Users.users_id)).group_by(Users.users_role).all()
    return {
        "total": total or 0,
        "verified": verified or 0,
        "by_role": dict(role_counts),
    }


def get_resource_counts(session: Session) -> dict[str, int]:
    """Return counts for each resource type."""
    return {key: session.query(model).count() for key, model in RESOURCE_MODELS.items()}


def get_dashboard_stats(session: Session, activity_limit: int = 10) -> dict:
    """Return a dashboard payload with user stats, resource counts, and recent activity."""
    return {
        "user_stats": get_user_stats(session),
        "resource_counts": get_resource_counts(session),
        "recent_activity": get_recent_activity(session, limit=activity_limit),
    }
