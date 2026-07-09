"""Unit tests for the financial service."""

import json

import pytest
from werkzeug.exceptions import HTTPException

from extensions import db
from models import FinancialReports
from services import financial
from tests.factories import (
    EventsFactory,
    FinancialReportsFactory,
    SignatoriesFactory,
    StudentOrganizationsFactory,
)


class TestDeleteFinancialReport:
    def test_get_renders_delete_template(self, app_context, auth_service_context, sample_user):
        report = FinancialReportsFactory(
            department=sample_user.department,
            prepared_by_user=sample_user,
        )
        with auth_service_context():
            response = financial.delete_financial_report(report.financial_reports_id)
        assert isinstance(response, str)

    def test_post_deletes_financial_report(self, app_context, auth_service_context, sample_user):
        report = FinancialReportsFactory(
            department=sample_user.department,
            prepared_by_user=sample_user,
        )
        with auth_service_context(method="POST"):
            response = financial.delete_financial_report(report.financial_reports_id)
        assert response.status_code == 302
        assert FinancialReports.query.get(report.financial_reports_id) is None

    def test_delete_forbidden_for_other_user(self, app_context, auth_service_context, sample_user, other_user):
        report = FinancialReportsFactory(
            department=sample_user.department,
            prepared_by_user=sample_user,
        )
        with pytest.raises(HTTPException), auth_service_context(user=other_user):
            financial.delete_financial_report(report.financial_reports_id)


class TestUpdateFinancialReportStatus:
    def test_update_status(self, app_context, auth_service_context, sample_user):
        report = FinancialReportsFactory(
            department=sample_user.department,
            prepared_by_user=sample_user,
        )
        with auth_service_context(
            method="POST",
            data=json.dumps({"status": "Done"}),
            content_type="application/json",
        ):
            response = financial.update_financial_report_status(report.financial_reports_id)
        assert response.status_code == 200
        assert response.get_json()["success"] is True
        updated = FinancialReports.query.get(report.financial_reports_id)
        assert updated.financial_reports_status == "Done"

    def test_update_status_forbidden_for_other_user(self, app_context, auth_service_context, sample_user, other_user):
        report = FinancialReportsFactory(
            department=sample_user.department,
            prepared_by_user=sample_user,
        )
        with (
            pytest.raises(HTTPException),
            auth_service_context(
                method="POST",
                data=json.dumps({"status": "Done"}),
                content_type="application/json",
                user=other_user,
            ),
        ):
            financial.update_financial_report_status(report.financial_reports_id)


class TestAddFinancialReport:
    def test_get_renders_add_template(self, app_context, auth_service_context, sample_user):
        with auth_service_context():
            response = financial.add_financial_report()
        assert isinstance(response, str)


class TestGenerateFinancialReportPdf:
    def test_generates_pdf(self, app_context, auth_service_context, sample_user, link_event_to_user):
        org = StudentOrganizationsFactory()
        sample_user.users_student_organization = org.student_organizations_id
        sample_user.users_student_organization_position = "President"
        db.session.commit()

        signatory = SignatoriesFactory()
        event = EventsFactory()
        link_event_to_user(event, sample_user)

        report = FinancialReportsFactory(
            department=sample_user.department,
            prepared_by_user=sample_user,
            events=event,
            financial_reports_audited_and_prepared_by=sample_user.users_id,
            financial_reports_noted_by=sample_user.users_id,
            financial_reports_recommending_approval_by=sample_user.users_id,
            financial_reports_approved_by=signatory.signatory_id,
        )

        with auth_service_context():
            response = financial.generate_financial_report_pdf(report.financial_reports_id)
        assert response.status_code == 200
        assert response.mimetype == "application/pdf"
        assert "Content-Length" in response.headers
