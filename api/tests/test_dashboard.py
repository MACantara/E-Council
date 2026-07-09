"""Tests for the FastAPI admin dashboard and audit endpoints."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from models import AuditLog, Users

from api.dependencies import create_access_token


def _admin_headers(admin_user):
    token = create_access_token(admin_user.users_id)
    return {"Authorization": f"Bearer {token}"}


def _reset_audit_logs(db):
    """Clear the audit log table so tests can use deterministic counts."""
    db.query(AuditLog).delete(synchronize_session=False)
    db.commit()


class TestDashboard:
    """Tests for admin dashboard and audit endpoints."""

    def test_dashboard_requires_admin(self, fastapi_client, authenticated_client):
        response = authenticated_client.get("/api/v1/admin/dashboard")
        assert response.status_code == 403

    def test_dashboard(self, fastapi_client, admin_user, fastapi_user, fastapi_db):
        _reset_audit_logs(fastapi_db)

        log = AuditLog(
            audit_log_user_id=admin_user.users_id,
            audit_log_action="create",
            audit_log_entity_type="Users",
            audit_log_entity_id=1,
            audit_log_changes={"key": "value"},
        )
        fastapi_db.add(log)
        fastapi_db.commit()

        response = fastapi_client.get(
            "/api/v1/admin/dashboard",
            headers=_admin_headers(admin_user),
        )
        assert response.status_code == 200
        data = response.json()
        assert "user_stats" in data
        assert "resource_counts" in data
        assert "recent_activity" in data
        assert data["user_stats"]["total"] >= 2
        assert data["recent_activity"][0]["audit_log_action"] == "create"

    def test_audit_logs_require_admin(self, fastapi_client, authenticated_client):
        response = authenticated_client.get("/api/v1/admin/audit-logs")
        assert response.status_code == 403

    def test_audit_logs(self, fastapi_client, admin_user, fastapi_db):
        _reset_audit_logs(fastapi_db)

        now = datetime.utcnow()
        for i in range(3):
            log = AuditLog(
                audit_log_user_id=admin_user.users_id,
                audit_log_action="create",
                audit_log_entity_type="Users",
                audit_log_entity_id=i,
                audit_log_changes={"i": i},
                audit_log_timestamp=now - timedelta(minutes=i),
            )
            fastapi_db.add(log)
        fastapi_db.commit()

        response = fastapi_client.get(
            "/api/v1/admin/audit-logs",
            headers=_admin_headers(admin_user),
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] == 3
        assert data["items"][0]["audit_log_action"] == "create"

    def test_audit_logs_filter_by_action(self, fastapi_client, admin_user, fastapi_db):
        _reset_audit_logs(fastapi_db)

        log1 = AuditLog(
            audit_log_user_id=admin_user.users_id,
            audit_log_action="create",
            audit_log_entity_type="Users",
        )
        log2 = AuditLog(
            audit_log_user_id=admin_user.users_id,
            audit_log_action="delete",
            audit_log_entity_type="Events",
        )
        fastapi_db.add_all([log1, log2])
        fastapi_db.commit()

        response = fastapi_client.get(
            "/api/v1/admin/audit-logs",
            params={"action": "create"},
            headers=_admin_headers(admin_user),
        )
        assert response.status_code == 200
        data = response.json()
        assert all(item["audit_log_action"] == "create" for item in data["items"])

    def test_audit_logs_filter_by_entity_type(self, fastapi_client, admin_user, fastapi_db):
        _reset_audit_logs(fastapi_db)

        log1 = AuditLog(
            audit_log_user_id=admin_user.users_id,
            audit_log_action="create",
            audit_log_entity_type="Users",
        )
        log2 = AuditLog(
            audit_log_user_id=admin_user.users_id,
            audit_log_action="create",
            audit_log_entity_type="Events",
        )
        fastapi_db.add_all([log1, log2])
        fastapi_db.commit()

        response = fastapi_client.get(
            "/api/v1/admin/audit-logs",
            params={"entity_type": "Events"},
            headers=_admin_headers(admin_user),
        )
        assert response.status_code == 200
        data = response.json()
        assert all(item["audit_log_entity_type"] == "Events" for item in data["items"])

    def test_audit_logs_search(self, fastapi_client, admin_user, fastapi_db):
        _reset_audit_logs(fastapi_db)

        log1 = AuditLog(
            audit_log_user_id=admin_user.users_id,
            audit_log_action="create",
            audit_log_entity_type="Users",
        )
        log2 = AuditLog(
            audit_log_user_id=admin_user.users_id,
            audit_log_action="delete",
            audit_log_entity_type="Events",
        )
        fastapi_db.add_all([log1, log2])
        fastapi_db.commit()

        response = fastapi_client.get(
            "/api/v1/admin/audit-logs",
            params={"search": "event"},
            headers=_admin_headers(admin_user),
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["audit_log_entity_type"] == "Events"

    def test_audit_log_detail(self, fastapi_client, admin_user, fastapi_db):
        _reset_audit_logs(fastapi_db)

        log = AuditLog(
            audit_log_user_id=admin_user.users_id,
            audit_log_action="create",
            audit_log_entity_type="Users",
        )
        fastapi_db.add(log)
        fastapi_db.commit()
        fastapi_db.refresh(log)

        response = fastapi_client.get(
            f"/api/v1/admin/audit-logs/{log.audit_log_id}",
            headers=_admin_headers(admin_user),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["audit_log_id"] == log.audit_log_id

    def test_audit_log_detail_not_found(self, fastapi_client, admin_user):
        response = fastapi_client.get(
            "/api/v1/admin/audit-logs/99999",
            headers=_admin_headers(admin_user),
        )
        assert response.status_code == 404

    def test_audit_logs_pagination(self, fastapi_client, admin_user, fastapi_db):
        _reset_audit_logs(fastapi_db)

        for i in range(5):
            fastapi_db.add(
                AuditLog(
                    audit_log_user_id=admin_user.users_id,
                    audit_log_action="create",
                    audit_log_entity_type="Users",
                    audit_log_entity_id=i,
                )
            )
        fastapi_db.commit()

        response = fastapi_client.get(
            "/api/v1/admin/audit-logs",
            params={"per_page": 2, "page": 2},
            headers=_admin_headers(admin_user),
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["page"] == 2
        assert data["per_page"] == 2

    def test_dashboard_recent_activity_sorted(self, fastapi_client, admin_user, fastapi_db):
        _reset_audit_logs(fastapi_db)

        now = datetime.utcnow()
        for i in range(3):
            fastapi_db.add(
                AuditLog(
                    audit_log_user_id=admin_user.users_id,
                    audit_log_action="create",
                    audit_log_entity_type="Users",
                    audit_log_entity_id=i,
                    audit_log_timestamp=now - timedelta(minutes=i),
                )
            )
        fastapi_db.commit()

        response = fastapi_client.get(
            "/api/v1/admin/dashboard",
            headers=_admin_headers(admin_user),
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["recent_activity"]) == 3
        assert data["recent_activity"][0]["audit_log_entity_id"] == 0
