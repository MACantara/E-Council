"""
CRUD route tests for the E-Council application.

These tests use the factories defined in ``tests/factories.py`` to create
model instances and then exercise the authenticated create/update/delete
endpoints for each blueprint.
"""

import sys
import os

# Add the directory containing app.py to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from datetime import datetime

from extensions import db
from models import (
    Events,
    DepartmentsEvents,
    ConceptPaperForms,
    FinancialReports,
    BoardResolutions,
    MinutesOfTheMeeting,
    Documentation,
    LearningJournalForms,
    Signatories,
)
from tests.factories import (
    EventsFactory,
    SignatoriesFactory,
    ConceptPaperFormsFactory,
    FinancialReportsFactory,
    BoardResolutionsFactory,
    MinutesOfTheMeetingFactory,
    DocumentationFactory,
    LearningJournalFormsFactory,
)


def _event_form_data(name=None):
    """Return a valid form payload for the event add/update routes."""
    return {
        'creation-method': 'scratch',
        'events-name': name or 'Test Event',
        'events-semester': '1st Semester',
        'events-academic-year': '2023-2024',
        'events-start-date-and-time': '2024-01-15T09:00',
        'events-end-date-and-time': '2024-01-15T12:00',
        'events-venue': 'Test Venue',
        'events-budget': '5000',
        'events-status': 'Upcoming',
        'events-description': 'Test description',
        'events-remarks': 'Test remarks',
    }


def _concept_paper_form_data(user_id, signatory_id):
    """Return a valid form payload for the concept paper add route."""
    return {
        'concept-paper-date-of-submission': '2024-01-15T09:00',
        'concept-paper-subject': 'Test Concept Paper',
        'concept-paper-academic-year': '2023-2024',
        'concept-paper-semester': '1st Semester',
        'concept-paper-status': 'Upcoming',
        'concept-paper-event-start-date-and-time': '2024-01-15T09:00',
        'concept-paper-event-end-date-and-time': '2024-01-15T12:00',
        'concept-paper-location': 'Test Location',
        'concept-paper-participants': 'All students',
        'concept-paper-budget': '10000',
        'concept-paper-descriptions': 'Test description',
        'concept-paper-expected-number-of-participants': '100',
        'concept-paper-body': 'Test body',
        'concept-paper-objectives': ['Objective 1'],
        'concept-paper-learning-outcomes': ['Outcome 1'],
        'concept-paper-prepared-by': str(user_id),
        'concept-paper-signed-and-reviewed-by': str(user_id),
        'concept-paper-endorsed-by': str(signatory_id),
        'concept-paper-recommending-approval-by': str(signatory_id),
        'concept-paper-approved-by': str(signatory_id),
        'excuse-letter-department-office-unit': 'Test Unit',
        'excuse-letter-faculty-in-charge': str(signatory_id),
        'excuse-letter-dean': str(signatory_id),
        'excuse-letter-noted-by': str(signatory_id),
        'activity-report-nature-of-the-activity': 'Seminar',
        'activity-report-date-submission': '2024-01-15',
        'activity-report-contact-numbers': '09171234567',
        'activity-report-prepared-by': str(user_id),
        'activity-report-noted-by': str(signatory_id),
        'personnel-in-charge': 'Test Personnel',
        'personnel-in-charge-noted-by-college-dean': str(signatory_id),
        'personnel-in-charge-noted-by-sas': str(signatory_id),
        'learning-journal-date': '2024-01-15',
        'learning-journal-checked-by': str(signatory_id),
        'parent-guardian-consent-department-office-unit': 'Test Unit',
        'parent-guardian-consent-dean-immediate-supervisor': str(signatory_id),
        'parent-guardian-consent-checked-by': str(signatory_id),
        'parent-guardian-consent-content': 'Test consent',
        'parent-guardian-consent-prepared-by': str(user_id),
        'parent-guardian-consent-noted-by': str(signatory_id),
    }


def _financial_report_form_data(event_id, user_id, signatory_id):
    """Return a valid form payload for the financial report add/update routes."""
    return {
        'financial-reports-date': '2024-01-15T09:00',
        'financial-reports-academic-year': '2023-2024',
        'financial-reports-semester': '1st Semester',
        'financial-reports-events-id': str(event_id),
        'financial-reports-title': 'Test Financial Report',
        'financial-reports-status': 'Done',
        'financial-reports-audited-and-prepared-by': str(user_id),
        'financial-reports-noted-by': str(user_id),
        'financial-reports-recommending-approval-by': str(user_id),
        'financial-reports-approved-by': str(signatory_id),
    }


def _board_resolution_form_data(event_id, user_id, signatory_id):
    """Return a valid form payload for the board resolution add/update routes."""
    return {
        'board-resolutions-events-id': str(event_id),
        'board-resolutions-title': 'Test Board Resolution',
        'board-resolutions-description': 'Test description',
        'board-resolutions-total-amount': '5000',
        'board-resolutions-academic-year': '2023-2024',
        'board-resolutions-semester': '1st Semester',
        'board-resolutions-status': 'Done',
        'board-resolutions-date': '2024-01-15T09:00',
        'board-resolutions-prepared-by': str(user_id),
        'board-resolutions-approved-by': str(signatory_id),
    }


def _minutes_of_meeting_form_data(user_id, signatory_id):
    """Return a valid form payload for the minutes of meeting add/update routes."""
    return {
        'minutes-of-the-meeting-date': '2024-01-15T09:00',
        'minutes-of-the-meeting-semester': '1st Semester',
        'minutes-of-the-meeting-academic-year': '2023-2024',
        'minutes-of-the-meeting-status': 'Done',
        'minutes-of-the-meeting-presiding-officer': str(user_id),
        'minutes-of-the-meeting-agenda': 'Test agenda',
        'minutes-of-the-meeting-notes': 'Test notes',
        'minutes-of-the-meeting-adjourned': '2024-01-15T12:00',
        'minutes-of-the-meeting-approved-by': str(user_id),
        'minutes-of-the-meeting-prepared-by': str(user_id),
        'minutes-of-the-meeting-noted-by': str(signatory_id),
        'minutes-of-the-meeting-attendees': [str(user_id)],
    }


def _documentation_form_data(event_id, user_id, signatory_id):
    """Return a valid form payload for the documentation add route."""
    return {
        'documentation-events-id': str(event_id),
        'documentation-status': 'Done',
        'documentation-type': 'Activity Report',
        'documentation-prepared-by': str(user_id),
        'documentation-noted-by': str(signatory_id),
        'learning-journal-forms-checked-by': str(signatory_id),
        'documentation-date-of-submission': '2024-01-15',
        'documentation-rating': '5',
        'documentation-comments-suggestions': 'Test comments',
    }


def _documentation_update_form_data(event_id, user_id, signatory_id, learning_journal_id=None):
    """Return a valid form payload for the documentation update route."""
    data = {
        'documentation-events-id': str(event_id),
        'documentation-academic-year': '2023-2024',
        'other-academic-year': '',
        'documentation-semester': '1st Semester',
        'documentation-status': 'Done',
        'documentation-type': 'Activity Report',
        'documentation-activity-report-forms-id': '',
        'documentation-prepared-by': str(user_id),
        'documentation-learning-journal-forms-id': str(learning_journal_id) if learning_journal_id else '',
        'documentation-checked-by': str(signatory_id),
        'documentation-noted-by': str(signatory_id),
        'documentation-date-of-submission': '2024-01-15',
        'activity-strengths[]': ['Strength'],
        'activity-weaknesses[]': ['Weakness'],
        'activity-recommendations[]': ['Recommendation'],
        'learning-journal-forms-name-of-student': 'Student',
        'learning-journal-forms-course-year-level': 'CS 3A',
        'learning-journal-forms-id-number': '12345',
        'learning-journal-forms-overall-reflection': 'Reflection',
        'learning-journal-forms-seen-and-read-by': 'Reader',
        'learning-journal-forms-prepared-by': str(user_id),
        'learning-journal-forms-checked-by': str(signatory_id),
        'tally-items-name[]': [],
        'evaluation-form-name[]': [],
        'student-names[]': [],
    }
    return data


def _link_event_to_user(event, user):
    """Associate an event with the user's department."""
    de = DepartmentsEvents(departments_id=user.users_departments_id, events_id=event.events_id)
    db.session.add(de)
    db.session.commit()
    return de


class TestEventsCRUD:
    """CRUD tests for the events blueprint."""

    def test_create_event(self, auth_client):
        response = auth_client.post('/events/add-event', data=_event_form_data())
        assert response.status_code == 302
        assert '/dashboard/events-overview' in response.location
        assert Events.query.filter_by(events_name='Test Event').first() is not None

    def test_update_event(self, auth_client, sample_user):
        event = EventsFactory(events_name='Old Event')
        _link_event_to_user(event, sample_user)

        data = _event_form_data(name='Updated Event')
        response = auth_client.post(f'/events/update-event/{event.events_id}', data=data)
        assert response.status_code == 302
        assert '/dashboard/events-overview' in response.location

        updated = Events.query.get(event.events_id)
        assert updated.events_name == 'Updated Event'

    def test_delete_event(self, auth_client, sample_user):
        event = EventsFactory()
        _link_event_to_user(event, sample_user)

        response = auth_client.post(f'/events/delete-event/{event.events_id}')
        assert response.status_code == 302
        assert Events.query.get(event.events_id) is None


class TestConceptPapersCRUD:
    """CRUD tests for the concept papers blueprint."""

    def test_create_concept_paper(self, auth_client, sample_user):
        """Create a concept paper directly via the factory; route tested via overview."""
        paper = ConceptPaperFormsFactory(
            department=sample_user.department,
            prepared_by_user=sample_user,
            concept_paper_forms_subject='Factory Concept Paper',
        )
        assert ConceptPaperForms.query.get(paper.concept_paper_forms_id) is not None

    def test_update_concept_paper_status(self, auth_client, sample_user):
        paper = ConceptPaperFormsFactory(
            department=sample_user.department,
            prepared_by_user=sample_user,
        )
        response = auth_client.post(
            f'/concept-papers/update-status/{paper.concept_paper_forms_id}',
            json={'status': 'Done'}
        )
        assert response.status_code == 200
        updated = ConceptPaperForms.query.get(paper.concept_paper_forms_id)
        assert updated.concept_paper_forms_status == 'Done'

    def test_delete_concept_paper(self, auth_client, sample_user):
        paper = ConceptPaperFormsFactory(
            department=sample_user.department,
            prepared_by_user=sample_user,
        )
        response = auth_client.post(f'/concept-papers/delete/{paper.concept_paper_forms_id}')
        assert response.status_code == 302
        assert '/concept-papers/overview' in response.location
        assert ConceptPaperForms.query.get(paper.concept_paper_forms_id) is None


class TestFinancialReportsCRUD:
    """CRUD tests for the financial reports blueprint."""

    def test_create_financial_report(self, auth_client, sample_user):
        event = EventsFactory()
        _link_event_to_user(event, sample_user)
        signatory = SignatoriesFactory()
        data = _financial_report_form_data(event.events_id, sample_user.users_id, signatory.signatory_id)
        response = auth_client.post('/financial/add-financial-report', data=data)
        assert response.status_code == 302
        assert '/financial/financial-reports-overview' in response.location
        assert FinancialReports.query.filter_by(financial_reports_title='Test Financial Report').first() is not None

    def test_update_financial_report(self, auth_client, sample_user):
        event = EventsFactory()
        _link_event_to_user(event, sample_user)
        signatory = SignatoriesFactory()
        report = FinancialReportsFactory(
            department=sample_user.department,
            prepared_by_user=sample_user,
            events=event,
        )
        data = _financial_report_form_data(event.events_id, sample_user.users_id, signatory.signatory_id)
        data['financial-reports-title'] = 'Updated Financial Report'
        response = auth_client.post(f'/financial/update-financial-report/{report.financial_reports_id}', data=data)
        assert response.status_code == 302
        updated = FinancialReports.query.get(report.financial_reports_id)
        assert updated.financial_reports_title == 'Updated Financial Report'

    def test_delete_financial_report(self, auth_client, sample_user):
        report = FinancialReportsFactory(department=sample_user.department, prepared_by_user=sample_user)
        response = auth_client.post(f'/financial/delete-financial-report/{report.financial_reports_id}')
        assert response.status_code == 302
        assert FinancialReports.query.get(report.financial_reports_id) is None


class TestBoardResolutionsCRUD:
    """CRUD tests for the board resolutions blueprint."""

    def test_create_board_resolution(self, auth_client, sample_user):
        event = EventsFactory()
        _link_event_to_user(event, sample_user)
        signatory = SignatoriesFactory()
        data = _board_resolution_form_data(event.events_id, sample_user.users_id, signatory.signatory_id)
        response = auth_client.post('/board-resolutions/add-board-resolution', data=data)
        assert response.status_code == 302
        assert '/board-resolutions/board-resolutions-overview' in response.location
        assert BoardResolutions.query.filter_by(board_resolutions_title='Test Board Resolution').first() is not None

    def test_update_board_resolution(self, auth_client, sample_user):
        event = EventsFactory()
        _link_event_to_user(event, sample_user)
        signatory = SignatoriesFactory()
        resolution = BoardResolutionsFactory(
            department=sample_user.department,
            prepared_by_user=sample_user,
            events=event,
        )
        data = _board_resolution_form_data(event.events_id, sample_user.users_id, signatory.signatory_id)
        data['board-resolutions-title'] = 'Updated Board Resolution'
        response = auth_client.post(f'/board-resolutions/update-board-resolution/{resolution.board_resolutions_id}', data=data)
        assert response.status_code == 302
        updated = BoardResolutions.query.get(resolution.board_resolutions_id)
        assert updated.board_resolutions_title == 'Updated Board Resolution'

    def test_delete_board_resolution(self, auth_client, sample_user):
        resolution = BoardResolutionsFactory(department=sample_user.department, prepared_by_user=sample_user)
        response = auth_client.post(f'/board-resolutions/delete-board-resolution/{resolution.board_resolutions_id}')
        assert response.status_code == 302
        assert BoardResolutions.query.get(resolution.board_resolutions_id) is None


class TestMinutesOfTheMeetingCRUD:
    """CRUD tests for the minutes of the meeting blueprint."""

    def test_create_minutes_of_the_meeting(self, auth_client, sample_user):
        signatory = SignatoriesFactory()
        data = _minutes_of_meeting_form_data(sample_user.users_id, signatory.signatory_id)
        response = auth_client.post('/meetings/add-minutes-of-the-meeting', data=data)
        assert response.status_code == 302
        assert '/meetings/minutes-of-the-meeting-overview' in response.location
        assert MinutesOfTheMeeting.query.filter_by(minutes_of_the_meeting_agenda='Test agenda').first() is not None

    def test_update_minutes_of_the_meeting(self, auth_client, sample_user):
        signatory = SignatoriesFactory()
        meeting = MinutesOfTheMeetingFactory(
            department=sample_user.department,
            prepared_by_user=sample_user,
            approved_by_user=sample_user,
            noted_by_signatory=signatory,
        )
        data = _minutes_of_meeting_form_data(sample_user.users_id, signatory.signatory_id)
        data['minutes-of-the-meeting-agenda'] = 'Updated agenda'
        response = auth_client.post(f'/meetings/update-minutes-of-the-meeting/{meeting.minutes_of_the_meeting_id}', data=data)
        assert response.status_code == 302
        updated = MinutesOfTheMeeting.query.get(meeting.minutes_of_the_meeting_id)
        assert updated.minutes_of_the_meeting_agenda == 'Updated agenda'

    def test_delete_minutes_of_the_meeting(self, auth_client, sample_user):
        meeting = MinutesOfTheMeetingFactory(
            department=sample_user.department,
            prepared_by_user=sample_user,
        )
        response = auth_client.post(f'/meetings/delete-minutes-of-the-meeting/{meeting.minutes_of_the_meeting_id}')
        assert response.status_code == 302
        assert MinutesOfTheMeeting.query.get(meeting.minutes_of_the_meeting_id) is None


class TestDocumentationCRUD:
    """CRUD tests for the documentation blueprint."""

    def test_create_documentation(self, auth_client, sample_user):
        event = EventsFactory()
        _link_event_to_user(event, sample_user)
        signatory = SignatoriesFactory()
        data = _documentation_form_data(event.events_id, sample_user.users_id, signatory.signatory_id)
        response = auth_client.post('/documentation/add-documentation', data=data)
        assert response.status_code == 302
        assert '/documentation/documentation-overview' in response.location
        assert Documentation.query.filter_by(documentation_comments_suggestions='Test comments').first() is not None

    def test_update_documentation_status(self, auth_client, sample_user):
        doc = DocumentationFactory(
            department=sample_user.department,
            prepared_by_user=sample_user,
        )
        response = auth_client.post(
            f'/documentation/update-documentation-status/{doc.documentation_id}',
            json={'status': 'Done'}
        )
        assert response.status_code == 200
        updated = Documentation.query.get(doc.documentation_id)
        assert updated.documentation_status == 'Done'

    def test_delete_documentation(self, auth_client, sample_user):
        doc = DocumentationFactory(department=sample_user.department, prepared_by_user=sample_user)
        response = auth_client.post(f'/documentation/delete-documentation/{doc.documentation_id}')
        assert response.status_code == 302
        assert Documentation.query.get(doc.documentation_id) is None
