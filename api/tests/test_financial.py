"""Tests for the FastAPI financial endpoints."""

from __future__ import annotations

import json

from models import Events, FinancialReports


def _default_payload(**overrides):
    """Return a valid financial report payload with optional overrides."""
    payload = {
        "financial_reports_date": "2025-09-20T10:00",
        "financial_reports_academic_year": "2025-2026",
        "financial_reports_semester": "1st Semester",
        "financial_reports_status": "Upcoming",
        "financial_reports_title": "FastAPI Test Financial Report",
        "financial_reports_audited_and_prepared_by": None,
        "financial_reports_noted_by": None,
        "financial_reports_recommending_approval_by": None,
        "financial_reports_approved_by": None,
    }
    payload.update(overrides)
    return payload


def _create_event(fastapi_db):
    """Create an event and return it."""
    event = Events(
        events_name="Financial Test Event",
        events_semester="1st Semester",
        events_academic_year="2025-2026",
        events_budget="10000",
    )
    fastapi_db.add(event)
    fastapi_db.commit()
    fastapi_db.refresh(event)
    return event


def _create_report(authenticated_client, event_id=None, **overrides):
    """Create a financial report through the API and return the response."""
    payload = _default_payload(**overrides)
    if event_id is not None:
        payload["financial_reports_events_id"] = event_id
    response = authenticated_client.post("/api/v1/financial", json=payload)
    assert response.status_code == 201
    return response.json()["data"]


def _transaction_payload(**overrides):
    """Return a valid transaction payload."""
    payload = {
        "transaction_name": "Supplies",
        "transaction_date": "2025-09-20T10:00",
        "unit_amount": 2,
        "unit_price": "500.00",
        "total": "1000.00",
        "category": "Supplies",
        "type": "Expense",
    }
    payload.update(overrides)
    return payload


class TestFinancial:
    """FastAPI financial endpoint tests."""

    def test_create_financial_report(self, authenticated_client):
        response = authenticated_client.post("/api/v1/financial", json=_default_payload())
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["financial_reports_title"] == "FastAPI Test Financial Report"
        assert data["financial_reports_status"] == "Upcoming"

    def test_create_financial_report_with_other_academic_year(self, authenticated_client):
        payload = _default_payload(
            financial_reports_academic_year="Other",
            other_academic_year="2026-2027",
        )
        response = authenticated_client.post("/api/v1/financial", json=payload)
        assert response.status_code == 201
        assert response.json()["data"]["financial_reports_academic_year"] == "2026-2027"

    def test_list_financial_reports(self, authenticated_client):
        _create_report(authenticated_client)
        response = authenticated_client.get("/api/v1/financial")
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data["items"]) == 1
        assert data["pagination"]["total"] == 1

    def test_list_financial_reports_filtered_by_status(self, authenticated_client):
        _create_report(authenticated_client)
        response = authenticated_client.get("/api/v1/financial?status=Done")
        assert response.status_code == 200
        assert len(response.json()["data"]["items"]) == 0

    def test_list_financial_reports_search(self, authenticated_client):
        _create_report(authenticated_client)
        response = authenticated_client.get("/api/v1/financial?search=FastAPI")
        assert response.status_code == 200
        assert len(response.json()["data"]["items"]) == 1

    def test_get_financial_report(self, authenticated_client):
        report = _create_report(authenticated_client)
        response = authenticated_client.get(f"/api/v1/financial/{report['financial_reports_id']}")
        assert response.status_code == 200
        assert response.json()["data"]["financial_reports_id"] == report["financial_reports_id"]

    def test_update_financial_report(self, authenticated_client):
        report = _create_report(authenticated_client)
        response = authenticated_client.put(
            f"/api/v1/financial/{report['financial_reports_id']}",
            json={"financial_reports_title": "Updated Title"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["financial_reports_title"] == "Updated Title"

    def test_update_status(self, authenticated_client):
        report = _create_report(authenticated_client)
        response = authenticated_client.put(
            f"/api/v1/financial/{report['financial_reports_id']}/status",
            json={"status": "Done"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["financial_reports_status"] == "Done"

    def test_delete_financial_report(self, authenticated_client, fastapi_db):
        report = _create_report(authenticated_client)
        response = authenticated_client.delete(f"/api/v1/financial/{report['financial_reports_id']}")
        assert response.status_code == 200
        assert fastapi_db.get(FinancialReports, report["financial_reports_id"]) is None

    def test_summary(self, authenticated_client, fastapi_db):
        event = _create_event(fastapi_db)
        report = _create_report(authenticated_client, event_id=event.events_id)

        response = authenticated_client.get(f"/api/v1/financial/{report['financial_reports_id']}/summary")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["budget"] == "10000"
        assert data["total_expenses"] == 0
        assert data["total_income"] == 0
        assert data["remaining"] == 10000

    def test_add_transaction(self, authenticated_client, fastapi_db):
        event = _create_event(fastapi_db)
        report = _create_report(authenticated_client, event_id=event.events_id)

        response = authenticated_client.post(
            f"/api/v1/financial/{report['financial_reports_id']}/transactions",
            data={"data": json.dumps(_transaction_payload())},
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["transaction_name"] == "Supplies"
        assert data["events_id"] == event.events_id

    def test_update_transaction(self, authenticated_client, fastapi_db):
        event = _create_event(fastapi_db)
        report = _create_report(authenticated_client, event_id=event.events_id)

        created = authenticated_client.post(
            f"/api/v1/financial/{report['financial_reports_id']}/transactions",
            data={"data": json.dumps(_transaction_payload())},
        )
        assert created.status_code == 201
        transaction_id = created.json()["data"]["transaction_id"]

        response = authenticated_client.put(
            f"/api/v1/financial/{report['financial_reports_id']}/transactions/{transaction_id}",
            data={"data": json.dumps({"transaction_name": "Updated Supplies"})},
        )
        assert response.status_code == 200
        assert response.json()["data"]["transaction_name"] == "Updated Supplies"

    def test_list_transactions(self, authenticated_client, fastapi_db):
        event = _create_event(fastapi_db)
        report = _create_report(authenticated_client, event_id=event.events_id)

        authenticated_client.post(
            f"/api/v1/financial/{report['financial_reports_id']}/transactions",
            data={"data": json.dumps(_transaction_payload())},
        )

        response = authenticated_client.get(f"/api/v1/financial/{report['financial_reports_id']}/transactions")
        assert response.status_code == 200
        assert len(response.json()["data"]) == 1

    def test_summary_with_transactions(self, authenticated_client, fastapi_db):
        event = _create_event(fastapi_db)
        report = _create_report(authenticated_client, event_id=event.events_id)

        authenticated_client.post(
            f"/api/v1/financial/{report['financial_reports_id']}/transactions",
            data={"data": json.dumps(_transaction_payload())},
        )

        response = authenticated_client.get(f"/api/v1/financial/{report['financial_reports_id']}/summary")
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["total_expenses"] == 1000
        assert data["remaining"] == 9000

    def test_download_pdf(self, authenticated_client, fastapi_db):
        event = _create_event(fastapi_db)
        report = _create_report(authenticated_client, event_id=event.events_id)

        response = authenticated_client.get(f"/api/v1/financial/{report['financial_reports_id']}/pdf")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    def test_department_scoping(self, authenticated_client, fastapi_db):
        """Non-admin users can only see reports from their own department."""
        from api.dependencies import create_access_token
        from models import Departments, Users

        _create_report(authenticated_client)

        other_department = Departments(departments_name="Other Financial Department")
        fastapi_db.add(other_department)
        fastapi_db.commit()

        other_user = Users(
            users_first_name="Other",
            users_last_name="Financial",
            users_username="otherfinancial",
            users_email="otherfinancial@example.com",
            users_departments_id=other_department.departments_id,
            users_role="Faculty",
            users_email_verified=1,
        )
        other_user.set_password("Password123!")
        fastapi_db.add(other_user)
        fastapi_db.commit()

        response = authenticated_client.client.get(
            "/api/v1/financial",
            headers={"Authorization": f"Bearer {create_access_token(other_user.users_id)}"},
        )
        assert response.status_code == 200
        assert len(response.json()["data"]["items"]) == 0

    def test_transaction_not_found(self, authenticated_client, fastapi_db):
        event = _create_event(fastapi_db)
        report = _create_report(authenticated_client, event_id=event.events_id)

        response = authenticated_client.put(
            f"/api/v1/financial/{report['financial_reports_id']}/transactions/999",
            data={"data": json.dumps({"transaction_name": "Missing"})},
        )
        assert response.status_code == 404
