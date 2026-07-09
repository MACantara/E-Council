"""
Authorization tests for the E-Council resource-level access control.
"""

import os
import sys

# Add the directory containing app.py to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime

from extensions import db
from utils.auth import belongs_to_user_or_department, is_admin


def test_is_admin_returns_true_for_admin(admin_user):
    assert is_admin(admin_user) is True


def test_is_admin_returns_false_for_non_admin(sample_user):
    assert is_admin(sample_user) is False


def test_belongs_to_user_or_department_admin_bypass(app_context, sample_user, other_user):
    from models import ConceptPaperForms

    paper = ConceptPaperForms(
        concept_paper_forms_subject="Admin Test",
        concept_paper_forms_departments_id=other_user.users_departments_id,
        concept_paper_forms_prepared_by=other_user.users_id,
    )
    db.session.add(paper)
    db.session.commit()

    assert belongs_to_user_or_department(paper, sample_user) is False

    admin = other_user
    admin.users_role = "Admin"
    db.session.commit()
    assert belongs_to_user_or_department(paper, admin) is True


def test_belongs_to_user_or_department_by_department(app_context, sample_user):
    from models import ConceptPaperForms

    paper = ConceptPaperForms(
        concept_paper_forms_subject="Department Test",
        concept_paper_forms_departments_id=sample_user.users_departments_id,
    )
    db.session.add(paper)
    db.session.commit()

    assert belongs_to_user_or_department(paper, sample_user) is True


def test_belongs_to_user_or_department_by_prepared_by(app_context, sample_user):
    from models import ConceptPaperForms

    paper = ConceptPaperForms(
        concept_paper_forms_subject="Prepared By Test", concept_paper_forms_prepared_by=sample_user.users_id
    )
    db.session.add(paper)
    db.session.commit()

    assert belongs_to_user_or_department(paper, sample_user) is True


def test_belongs_to_user_or_department_other_department_denied(app_context, sample_user, other_user):
    from models import ConceptPaperForms

    paper = ConceptPaperForms(
        concept_paper_forms_subject="Other Department Test",
        concept_paper_forms_departments_id=other_user.users_departments_id,
        concept_paper_forms_prepared_by=other_user.users_id,
    )
    db.session.add(paper)
    db.session.commit()

    assert belongs_to_user_or_department(paper, sample_user) is False


def test_belongs_to_user_or_department_events_via_departments_events(app_context, sample_user):
    from models import DepartmentsEvents, Events

    event = Events(events_name="Department Event", events_semester="1st Semester", events_academic_year="2024-2025")
    db.session.add(event)
    db.session.commit()

    de = DepartmentsEvents(departments_id=sample_user.users_departments_id, events_id=event.events_id)
    db.session.add(de)
    db.session.commit()

    assert belongs_to_user_or_department(event, sample_user) is True


def test_belongs_to_user_or_department_events_without_link_denied(app_context, sample_user):
    from models import Events

    event = Events(events_name="Unlinked Event", events_semester="1st Semester", events_academic_year="2024-2025")
    db.session.add(event)
    db.session.commit()

    assert belongs_to_user_or_department(event, sample_user) is False


def test_belongs_to_user_or_department_financial_report_via_event(app_context, sample_user):
    from models import DepartmentsEvents, Events, FinancialReports

    event = Events(events_name="Financial Event", events_semester="1st Semester", events_academic_year="2024-2025")
    db.session.add(event)
    db.session.commit()

    de = DepartmentsEvents(departments_id=sample_user.users_departments_id, events_id=event.events_id)
    db.session.add(de)
    db.session.commit()

    report = FinancialReports(
        financial_reports_date=datetime.now(),
        financial_reports_academic_year="2024-2025",
        financial_reports_semester="1st Semester",
        financial_reports_status="Draft",
        financial_reports_title="Financial Report",
        financial_reports_events_id=event.events_id,
    )
    db.session.add(report)
    db.session.commit()

    assert belongs_to_user_or_department(report, sample_user) is True


def test_event_update_access_denied_for_other_department(client, sample_user, other_user):
    from datetime import datetime

    from models import DepartmentsEvents, Events

    with client.application.app_context():
        event = Events(
            events_name="Protected Event",
            events_semester="1st Semester",
            events_academic_year="2024-2025",
            events_start_date_and_time=datetime.now(),
            events_end_date_and_time=datetime.now(),
            events_venue="Venue",
            events_budget="1000",
            events_description="Description",
        )
        db.session.add(event)
        db.session.commit()
        de = DepartmentsEvents(departments_id=sample_user.users_departments_id, events_id=event.events_id)
        db.session.add(de)
        db.session.commit()

        # Login as other user
        client.post(
            "/auth/login",
            data={"users-username-email": other_user.users_username, "users-password": "Password123!"},
            follow_redirects=True,
        )

        response = client.get(f"/events/update-event/{event.events_id}")
        assert response.status_code == 403


def test_event_update_access_allowed_for_department_member(client, sample_user):
    from datetime import datetime

    from models import DepartmentsEvents, Events

    with client.application.app_context():
        event = Events(
            events_name="Allowed Event",
            events_semester="1st Semester",
            events_academic_year="2024-2025",
            events_start_date_and_time=datetime.now(),
            events_end_date_and_time=datetime.now(),
            events_venue="Venue",
            events_budget="1000",
            events_description="Description",
        )
        db.session.add(event)
        db.session.commit()
        de = DepartmentsEvents(departments_id=sample_user.users_departments_id, events_id=event.events_id)
        db.session.add(de)
        db.session.commit()

        client.post(
            "/auth/login",
            data={"users-username-email": sample_user.users_username, "users-password": "Password123!"},
            follow_redirects=True,
        )

        response = client.get(f"/events/update-event/{event.events_id}")
        assert response.status_code == 200


def test_financial_report_update_access_allowed_for_creator(client, sample_user):
    from models import FinancialReports

    with client.application.app_context():
        report = FinancialReports(
            financial_reports_date=datetime.now(),
            financial_reports_academic_year="2024-2025",
            financial_reports_semester="1st Semester",
            financial_reports_status="Draft",
            financial_reports_title="Allowed Report",
            financial_reports_departments_id=sample_user.users_departments_id,
        )
        db.session.add(report)
        db.session.commit()

        client.post(
            "/auth/login",
            data={"users-username-email": sample_user.users_username, "users-password": "Password123!"},
            follow_redirects=True,
        )

        response = client.get(f"/financial/update-financial-report/{report.financial_reports_id}")
        assert response.status_code == 200


def test_concept_papers_overview_filters_by_department(client, sample_user, other_user):
    from models import ConceptPaperForms

    with client.application.app_context():
        own_paper = ConceptPaperForms(
            concept_paper_forms_subject="Own Paper",
            concept_paper_forms_departments_id=sample_user.users_departments_id,
            concept_paper_forms_academic_year="2024-2025",
            concept_paper_forms_semester="1st Semester",
        )
        other_paper = ConceptPaperForms(
            concept_paper_forms_subject="Other Paper",
            concept_paper_forms_departments_id=other_user.users_departments_id,
            concept_paper_forms_academic_year="2024-2025",
            concept_paper_forms_semester="1st Semester",
        )
        db.session.add_all([own_paper, other_paper])
        db.session.commit()

        client.post(
            "/auth/login",
            data={"users-username-email": sample_user.users_username, "users-password": "Password123!"},
            follow_redirects=True,
        )

        response = client.get("/concept-papers/overview")
        assert response.status_code == 200
        assert b"Own Paper" in response.data
        assert b"Other Paper" not in response.data


def test_admin_can_access_any_concept_paper(client, sample_user, admin_user):
    from models import ConceptPaperForms

    with client.application.app_context():
        paper = ConceptPaperForms(
            concept_paper_forms_subject="Admin Accessible Paper",
            concept_paper_forms_departments_id=sample_user.users_departments_id,
        )
        db.session.add(paper)
        db.session.commit()

        client.post(
            "/auth/login",
            data={"users-username-email": admin_user.users_username, "users-password": "Password123!"},
            follow_redirects=True,
        )

        response = client.get(f"/concept-papers/delete/{paper.concept_paper_forms_id}")
        assert response.status_code == 200
