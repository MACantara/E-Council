"""
PDF generation route tests for the E-Council application.

These tests verify that the implemented PDF endpoints return
``application/pdf`` content and non-empty payloads. The documentation
PDF endpoint is currently a placeholder and is expected to return 501.
"""

import sys
import os

# Add the directory containing app.py to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest

from tests.factories import (
    ConceptPaperFormsFactory,
    FinancialReportsFactory,
    MinutesOfTheMeetingFactory,
    BoardResolutionsFactory,
    DocumentationFactory,
    EventsFactory,
    SignatoriesFactory,
    StudentOrganizationsFactory,
)


def _link_event_to_user(event, user):
    """Associate an event with the user's department for access control."""
    from models import DepartmentsEvents
    from extensions import db
    db.session.add(DepartmentsEvents(departments_id=user.users_departments_id, events_id=event.events_id))
    db.session.commit()


def _ensure_user_has_organization(user):
    """Ensure the user has a student organization set for PDF generation."""
    from extensions import db
    if not user.student_organization:
        org = StudentOrganizationsFactory()
        user.users_student_organization = org.student_organizations_id
        user.users_student_organization_position = 'President'
        db.session.commit()


@pytest.mark.skip(reason="generate_concept_paper_pdf route requires model columns not yet defined")
def test_generate_concept_paper_pdf(auth_client, sample_user):
    signatory = SignatoriesFactory()
    paper = ConceptPaperFormsFactory(
        department=sample_user.department,
        prepared_by_user=sample_user,
        signed_and_reviewed_by_user=sample_user,
        concept_paper_forms_body='Test body content',
        approved_by_signatory=signatory,
        recommending_approval_by_signatory=signatory,
        endorsed_by_signatory=signatory,
    )
    response = auth_client.get(f'/concept-papers/generate-pdf/{paper.concept_paper_forms_id}')
    assert response.status_code == 200
    assert response.content_type == 'application/pdf'
    assert response.data


def test_generate_financial_report_pdf(auth_client, sample_user):
    _ensure_user_has_organization(sample_user)
    signatory = SignatoriesFactory()
    event = EventsFactory()
    _link_event_to_user(event, sample_user)
    report = FinancialReportsFactory(
        department=sample_user.department,
        prepared_by_user=sample_user,
        events=event,
        financial_reports_noted_by=sample_user.users_id,
        financial_reports_recommending_approval_by=sample_user.users_id,
        financial_reports_approved_by=signatory.signatory_id,
    )
    response = auth_client.get(f'/financial/generate-financial-report-pdf/{report.financial_reports_id}')
    assert response.status_code == 200
    assert response.content_type == 'application/pdf'
    assert response.data


def test_generate_mom_pdf(auth_client, sample_user):
    meeting = MinutesOfTheMeetingFactory(
        department=sample_user.department,
        prepared_by_user=sample_user,
        approved_by_user=sample_user,
    )
    response = auth_client.get(f'/meetings/generate-mom-pdf/{meeting.minutes_of_the_meeting_id}')
    assert response.status_code == 200
    assert response.content_type == 'application/pdf'
    assert response.data


def test_generate_board_resolution_pdf(auth_client, sample_user):
    signatory = SignatoriesFactory()
    resolution = BoardResolutionsFactory(
        department=sample_user.department,
        prepared_by_user=sample_user,
        approved_by_signatory=signatory,
    )
    response = auth_client.get(f'/board-resolutions/generate-board-resolution-pdf/{resolution.board_resolutions_id}')
    assert response.status_code == 200
    assert response.content_type == 'application/pdf'
    assert response.data


def test_generate_documentation_pdf_placeholder(auth_client, sample_user):
    doc = DocumentationFactory(department=sample_user.department, prepared_by_user=sample_user)
    response = auth_client.get(f'/documentation/generate-documentation-pdf/{doc.documentation_id}')
    assert response.status_code == 501
