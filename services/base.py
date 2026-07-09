"""
Base service layer for E-Council.

Provides a generic ServiceResult pattern so services can return either a
successful payload or a user-friendly error message without raising HTTP
exceptions.
"""

from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from flask_login import current_user

from repositories import repo

T = TypeVar("T")


@dataclass
class ServiceResult(Generic[T]):
    """Result of a service operation.

    Attributes:
        success: True if the operation succeeded.
        data: Payload returned on success (may be None).
        error: Human-readable error message returned on failure.
    """

    success: bool
    data: T | None = None
    error: str | None = None

    def __bool__(self) -> bool:
        return self.success

    @classmethod
    def ok(cls, data: T | None = None) -> "ServiceResult[T]":
        """Create a successful result."""
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, message: str) -> "ServiceResult[Any]":
        """Create a failed result with an error message."""
        return cls(success=False, error=message)


def log_action(
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    changes: dict | None = None,
    user_id: int | None = None,
) -> None:
    """Create an AuditLog record for a state-changing action.

    Args:
        action: The action performed (e.g. create, update, delete, status_change, generate_pdf).
        entity_type: The model/class name of the affected entity.
        entity_id: The primary key of the affected entity, if available.
        changes: A dictionary of changed values or additional context.
        user_id: Optional user ID; defaults to the currently logged-in user.
    """
    from models import AuditLog

    if user_id is None and current_user and current_user.is_authenticated:
        user_id = current_user.users_id

    audit = AuditLog(
        audit_log_user_id=user_id,
        audit_log_action=action,
        audit_log_entity_type=entity_type,
        audit_log_entity_id=entity_id,
        audit_log_changes=changes,
    )
    repo.add(audit)
    repo.commit()
