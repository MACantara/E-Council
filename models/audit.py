"""
Audit log model for E-Council.

Tracks state-changing actions for accountability and review.
"""

import json
from datetime import datetime
from decimal import Decimal

from flask_login import current_user
from sqlalchemy import event
from sqlalchemy.orm import Session, object_mapper

from models.base import db


def _serialize_value(value: object) -> object:
    """Return a JSON-safe representation of a value."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (dict, list)):
        return json.loads(json.dumps(value, default=str))
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _get_primary_key_value(obj: object) -> object | None:
    """Return the primary key value for an object, if it has one."""
    try:
        return object_mapper(obj).primary_key_from_instance(obj)[0]
    except Exception:
        return None


def _build_changes(obj: object, action: str) -> dict:
    """Build a JSON-serializable dictionary of changes for an object."""
    changes: dict = {}
    mapper = object_mapper(obj)
    for attr in mapper.column_attrs:
        key = attr.key
        if key == "audit_log_id":
            continue
        try:
            value = getattr(obj, key)
        except Exception:
            continue
        if action == "update":
            hist = db.inspect(obj).attrs[key].history
            if not hist.has_changes():
                continue
        changes[key] = _serialize_value(value)
    return changes


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    audit_log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    audit_log_timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    audit_log_user_id = db.Column(db.Integer, db.ForeignKey("users.users_id"), nullable=True, index=True)
    audit_log_action = db.Column(db.String(50), nullable=False, index=True)
    audit_log_entity_type = db.Column(db.String(100), nullable=False, index=True)
    audit_log_entity_id = db.Column(db.Integer, nullable=True, index=True)
    audit_log_changes = db.Column(db.JSON, nullable=True)

    user = db.relationship("Users", backref=db.backref("audit_logs", lazy="dynamic"))

    def __repr__(self):
        return (
            f"<AuditLog {self.audit_log_id}: {self.audit_log_action} "
            f"{self.audit_log_entity_type}#{self.audit_log_entity_id}>"
        )


def _audit_listener(session: Session, flush_context: object = None) -> None:
    """Generate AuditLog records for create, update, and delete operations."""
    if session.info.get("_audit_logging"):
        return

    session.info["_audit_logging"] = True
    try:
        logs = []
        for obj in session.new:
            if isinstance(obj, AuditLog):
                continue
            logs.append(
                AuditLog(
                    audit_log_user_id=(
                        current_user.users_id if current_user and current_user.is_authenticated else None
                    ),
                    audit_log_action="create",
                    audit_log_entity_type=obj.__class__.__name__,
                    audit_log_entity_id=_get_primary_key_value(obj),
                    audit_log_changes=_build_changes(obj, "create"),
                )
            )

        for obj in session.dirty:
            if isinstance(obj, AuditLog):
                continue
            logs.append(
                AuditLog(
                    audit_log_user_id=(
                        current_user.users_id if current_user and current_user.is_authenticated else None
                    ),
                    audit_log_action="update",
                    audit_log_entity_type=obj.__class__.__name__,
                    audit_log_entity_id=_get_primary_key_value(obj),
                    audit_log_changes=_build_changes(obj, "update"),
                )
            )

        for obj in session.deleted:
            if isinstance(obj, AuditLog):
                continue
            logs.append(
                AuditLog(
                    audit_log_user_id=(
                        current_user.users_id if current_user and current_user.is_authenticated else None
                    ),
                    audit_log_action="delete",
                    audit_log_entity_type=obj.__class__.__name__,
                    audit_log_entity_id=_get_primary_key_value(obj),
                    audit_log_changes=_build_changes(obj, "delete"),
                )
            )

        if logs:
            session.add_all(logs)
    finally:
        session.info["_audit_logging"] = False


def _before_commit_listener(session: Session) -> None:
    """Flush any generated audit logs before the transaction commits."""
    if session.info.get("_audit_committing"):
        return

    session.info["_audit_committing"] = True
    try:
        if any(isinstance(obj, AuditLog) for obj in session.new):
            session.flush()
    finally:
        session.info["_audit_committing"] = False


# Listen on the SQLAlchemy Session class used by Flask-SQLAlchemy.
event.listen(db.Session, "after_flush", _audit_listener)
event.listen(db.Session, "before_commit", _before_commit_listener)
