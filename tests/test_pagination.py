"""
Pagination tests for E-Council overview routes.
"""

import os
import sys
from datetime import date, datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from extensions import db


def _login(client, user):
    return client.post(
        "/auth/login",
        data={"users-username-email": user.users_username, "users-password": "Password123!"},
        follow_redirects=True,
    )


def test_concept_papers_overview_pagination(client, sample_user, app_context):
    from models import ConceptPaperForms

    for i in range(1, 6):
        paper = ConceptPaperForms(
            concept_paper_forms_subject=f"Concept Paper {i}",
            concept_paper_forms_departments_id=sample_user.users_departments_id,
            concept_paper_forms_academic_year="2024-2025",
            concept_paper_forms_semester="1st Semester",
            concept_paper_forms_status="Upcoming",
            concept_paper_forms_date=date(2024, 1, i),
        )
        db.session.add(paper)
    db.session.commit()

    _login(client, sample_user)

    response = client.get("/concept-papers/overview?per_page=2")
    assert response.status_code == 200
    assert b"Concept Paper 5" in response.data
    assert b"Concept Paper 4" in response.data
    assert b"Concept Paper 3" not in response.data
    assert b"Next" in response.data

    response = client.get("/concept-papers/overview?per_page=2&page=2")
    assert response.status_code == 200
    assert b"Concept Paper 3" in response.data
    assert b"Concept Paper 2" in response.data
    assert b"Concept Paper 5" not in response.data
    assert b"Previous" in response.data

    response = client.get("/concept-papers/overview?per_page=2&page=999")
    assert response.status_code == 200


def test_events_overview_pagination(client, sample_user, app_context):
    from models import DepartmentsEvents, Events

    for i in range(1, 6):
        event = Events(
            events_name=f"Event {i}",
            events_semester="1st Semester",
            events_academic_year="2024-2025",
            events_start_date_and_time=datetime(2024, 1, i, 10, 0),
            events_end_date_and_time=datetime(2024, 1, i, 12, 0),
            events_status="Upcoming",
            events_budget="5000",
        )
        db.session.add(event)
        db.session.flush()
        db.session.add(DepartmentsEvents(departments_id=sample_user.users_departments_id, events_id=event.events_id))
    db.session.commit()

    _login(client, sample_user)

    response = client.get("/dashboard/events-overview?per_page=2")
    assert response.status_code == 200
    assert b"Event 5" in response.data
    assert b"Event 4" in response.data
    assert b"Event 3" not in response.data
    assert b"Next" in response.data

    response = client.get("/dashboard/events-overview?per_page=2&page=2")
    assert response.status_code == 200
    assert b"Event 3" in response.data
    assert b"Event 2" in response.data
    assert b"Event 5" not in response.data
    assert b"Previous" in response.data


def test_board_resolutions_overview_pagination(client, sample_user, app_context):
    from models import BoardResolutions

    for i in range(1, 6):
        resolution = BoardResolutions(
            board_resolutions_title=f"Resolution {i}",
            board_resolutions_departments_id=sample_user.users_departments_id,
            board_resolutions_academic_year="2024-2025",
            board_resolutions_semester="1st Semester",
            board_resolutions_status="Upcoming",
            board_resolutions_date=datetime(2024, 1, i, 10, 0),
        )
        db.session.add(resolution)
    db.session.commit()

    _login(client, sample_user)

    response = client.get("/board-resolutions/board-resolutions-overview?per_page=2")
    assert response.status_code == 200
    assert b"Resolution 5" in response.data
    assert b"Resolution 4" in response.data
    assert b"Resolution 3" not in response.data
    assert b"Next" in response.data

    response = client.get("/board-resolutions/board-resolutions-overview?per_page=2&page=2")
    assert response.status_code == 200
    assert b"Resolution 3" in response.data
    assert b"Resolution 2" in response.data
    assert b"Resolution 5" not in response.data
    assert b"Previous" in response.data


def test_financial_reports_overview_pagination(client, sample_user, app_context):
    from models import FinancialReports

    for i in range(1, 6):
        report = FinancialReports(
            financial_reports_title=f"Report {i}",
            financial_reports_departments_id=sample_user.users_departments_id,
            financial_reports_academic_year="2024-2025",
            financial_reports_semester="1st Semester",
            financial_reports_status="Done",
            financial_reports_date=datetime(2024, 1, i, 10, 0),
        )
        db.session.add(report)
    db.session.commit()

    _login(client, sample_user)

    response = client.get("/financial/financial-reports-overview?per_page=2")
    assert response.status_code == 200
    assert b"Report 5" in response.data
    assert b"Report 4" in response.data
    assert b"Report 3" not in response.data
    assert b"Next" in response.data

    response = client.get("/financial/financial-reports-overview?per_page=2&page=2")
    assert response.status_code == 200
    assert b"Report 3" in response.data
    assert b"Report 2" in response.data
    assert b"Report 5" not in response.data
    assert b"Previous" in response.data


def test_minutes_of_the_meeting_overview_pagination(client, sample_user, app_context):
    from models import MinutesOfTheMeeting

    for i in range(1, 6):
        meeting = MinutesOfTheMeeting(
            minutes_of_the_meeting_agenda=f"Agenda {i}",
            minutes_of_the_meeting_departments_id=sample_user.users_departments_id,
            minutes_of_the_meeting_academic_year="2024-2025",
            minutes_of_the_meeting_semester="1st Semester",
            minutes_of_the_meeting_status="Done",
            minutes_of_the_meeting_date=datetime(2024, 1, i, 10, 0),
            minutes_of_the_meeting_presiding_officer=str(sample_user.users_id),
            minutes_of_the_meeting_prepared_by=sample_user.users_id,
            minutes_of_the_meeting_notes="Notes",
        )
        db.session.add(meeting)
    db.session.commit()

    _login(client, sample_user)

    response = client.get("/meetings/minutes-of-the-meeting-overview?per_page=2")
    assert response.status_code == 200
    assert b"Agenda 5" in response.data
    assert b"Agenda 4" in response.data
    assert b"Agenda 3" not in response.data
    assert b"Next" in response.data

    response = client.get("/meetings/minutes-of-the-meeting-overview?per_page=2&page=2")
    assert response.status_code == 200
    assert b"Agenda 3" in response.data
    assert b"Agenda 2" in response.data
    assert b"Agenda 5" not in response.data
    assert b"Previous" in response.data


def test_documentation_overview_pagination(client, sample_user, app_context):
    from models import Documentation

    for i in range(1, 6):
        doc = Documentation(
            documentation_type=f"Type {i}",
            documentation_departments_id=sample_user.users_departments_id,
            documentation_academic_year="2024-2025",
            documentation_semester="1st Semester",
            documentation_status="Done",
            documentation_date_of_submission=datetime(2024, 1, i, 10, 0),
            documentation_prepared_by=sample_user.users_id,
        )
        db.session.add(doc)
    db.session.commit()

    _login(client, sample_user)

    response = client.get("/documentation/documentation-overview?per_page=2")
    assert response.status_code == 200
    assert b"Type 5" in response.data
    assert b"Type 4" in response.data
    assert b"Type 3" not in response.data
    assert b"Next" in response.data

    response = client.get("/documentation/documentation-overview?per_page=2&page=2")
    assert response.status_code == 200
    assert b"Type 3" in response.data
    assert b"Type 2" in response.data
    assert b"Type 5" not in response.data
    assert b"Previous" in response.data
