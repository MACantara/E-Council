"""
Unit tests for the audit logging system.
"""

from models import AuditLog, Departments, db


def test_audit_log_created_on_create(app_context):
    """Creating a record should produce an audit log entry."""
    before = AuditLog.query.count()
    department = Departments(departments_name="Audit Create Test")
    db.session.add(department)
    db.session.commit()
    after = AuditLog.query.count()
    assert after == before + 1

    log = AuditLog.query.order_by(AuditLog.audit_log_id.desc()).first()
    assert log.audit_log_action == "create"
    assert log.audit_log_entity_type == "Departments"
    assert log.audit_log_entity_id == department.departments_id
    assert log.audit_log_changes["departments_name"] == "Audit Create Test"


def test_audit_log_created_on_update(app_context):
    """Updating a record should produce an audit log entry."""
    department = Departments(departments_name="Audit Update Test")
    db.session.add(department)
    db.session.commit()

    before = AuditLog.query.count()
    department.departments_name = "Updated Audit Name"
    db.session.commit()
    after = AuditLog.query.count()
    assert after == before + 1

    log = AuditLog.query.order_by(AuditLog.audit_log_id.desc()).first()
    assert log.audit_log_action == "update"
    assert log.audit_log_entity_type == "Departments"
    assert log.audit_log_changes["departments_name"] == "Updated Audit Name"


def test_audit_log_created_on_delete(app_context):
    """Deleting a record should produce an audit log entry."""
    department = Departments(departments_name="Audit Delete Test")
    db.session.add(department)
    db.session.commit()
    entity_id = department.departments_id

    before = AuditLog.query.count()
    db.session.delete(department)
    db.session.commit()
    after = AuditLog.query.count()
    assert after == before + 1

    log = AuditLog.query.order_by(AuditLog.audit_log_id.desc()).first()
    assert log.audit_log_action == "delete"
    assert log.audit_log_entity_type == "Departments"
    assert log.audit_log_entity_id == entity_id


def test_admin_audit_log_access_for_admin(client, admin_user):
    """Admins should be able to view the audit log page."""
    response = client.post(
        "/auth/login",
        data={"users-username-email": admin_user.users_username, "users-password": "Password123!"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    response = client.get("/admin/audit-log")
    assert response.status_code == 200
    assert b"Audit Log" in response.data


def test_admin_audit_log_denied_for_non_admin(client, sample_user):
    """Non-admin users should be denied access to the audit log page."""
    response = client.post(
        "/auth/login",
        data={"users-username-email": sample_user.users_username, "users-password": "Password123!"},
        follow_redirects=True,
    )
    assert response.status_code == 200

    response = client.get("/admin/audit-log")
    assert response.status_code == 403


def test_admin_audit_log_requires_login(client):
    """Anonymous users should be redirected to login when accessing the audit log."""
    response = client.get("/admin/audit-log", follow_redirects=False)
    assert response.status_code == 302
