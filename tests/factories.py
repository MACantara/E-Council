"""
Model factories for the E-Council test suite.

Uses factory_boy to create test data quickly. Factories are designed to be
used within a Flask application/test request context.
"""

import os
import sys

# Add the directory containing app.py to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime

import factory
from factory.alchemy import SQLAlchemyModelFactory
from factory.fuzzy import FuzzyChoice

from extensions import db
from models import (
    ActivityReportForms,
    BoardResolutions,
    ConceptPaperForms,
    Departments,
    DepartmentsEvents,
    Documentation,
    Events,
    FinancialReports,
    LearningJournalForms,
    MinutesOfTheMeeting,
    PersonnelInChargeForms,
    Signatories,
    StudentOrganizations,
    Users,
)


class BaseFactory(SQLAlchemyModelFactory):
    """Base factory with shared SQLAlchemy session configuration."""

    class Meta:
        abstract = True
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = "commit"


class DepartmentsFactory(BaseFactory):
    """Factory for creating test departments."""

    class Meta:
        model = Departments

    departments_name = factory.Sequence(lambda n: f"Department {n}")


class StudentOrganizationsFactory(BaseFactory):
    """Factory for creating test student organizations."""

    class Meta:
        model = StudentOrganizations

    student_organizations_name = factory.Sequence(lambda n: f"Organization {n}")
    student_organizations_financial_bank_book_amount = 10000.00


class SignatoriesFactory(BaseFactory):
    """Factory for creating test signatories."""

    class Meta:
        model = Signatories

    signatory_title = "Mr."
    signatory_first_name = factory.Faker("first_name")
    signatory_middle_name = factory.Faker("first_name")
    signatory_last_name = factory.Faker("last_name")
    signatory_suffix = ""
    signatory_position = "Dean"
    signatory_department = factory.Faker("company")


class UsersFactory(BaseFactory):
    """Factory for creating test users."""

    class Meta:
        model = Users

    users_first_name = factory.Faker("first_name")
    users_last_name = factory.Faker("last_name")
    users_username = factory.Sequence(lambda n: f"testuser{n}")
    users_email = factory.Sequence(lambda n: f"test{n}@example.com")
    users_role = FuzzyChoice(["Student Council Officer", "Faculty", "Staff"])
    users_email_verified = 1
    users_password = "Password123!"
    department = factory.SubFactory(DepartmentsFactory)

    @factory.post_generation
    def set_password(self, create, extracted, **kwargs):
        """Hash the user's password after creation."""
        self.set_password("Password123!")
        if create:
            db.session.commit()


class EventsFactory(BaseFactory):
    """Factory for creating test events."""

    class Meta:
        model = Events

    events_name = factory.Sequence(lambda n: f"Event {n}")
    events_semester = FuzzyChoice(["1st Semester", "2nd Semester"])
    events_academic_year = "2023-2024"
    events_start_date_and_time = factory.LazyFunction(datetime.utcnow)
    events_end_date_and_time = factory.LazyFunction(datetime.utcnow)
    events_venue = factory.Faker("city")
    events_budget = "5000"
    events_status = FuzzyChoice(["Upcoming", "Done", "Cancelled"])
    events_description = factory.Faker("sentence")
    events_remarks = "Test remarks"


class DepartmentsEventsFactory(BaseFactory):
    """Factory for the many-to-many department/event relationship."""

    class Meta:
        model = DepartmentsEvents

    department = factory.SubFactory(DepartmentsFactory)
    event = factory.SubFactory(EventsFactory)


class ConceptPaperFormsFactory(BaseFactory):
    """Factory for creating test concept papers."""

    class Meta:
        model = ConceptPaperForms

    concept_paper_forms_subject = factory.Sequence(lambda n: f"Concept Paper {n}")
    concept_paper_forms_semester = FuzzyChoice(["1st Semester", "2nd Semester"])
    concept_paper_forms_academic_year = "2023-2024"
    concept_paper_forms_status = FuzzyChoice(["Upcoming", "Done"])
    concept_paper_forms_date = factory.LazyFunction(datetime.utcnow)
    concept_paper_forms_event_start_date_and_time = factory.LazyFunction(datetime.utcnow)
    concept_paper_forms_event_end_date_and_time = factory.LazyFunction(datetime.utcnow)
    concept_paper_forms_location = factory.Faker("city")
    concept_paper_forms_participants = "All students"
    concept_paper_forms_budget = "10000"
    concept_paper_forms_descriptions = factory.Faker("sentence")
    concept_paper_forms_expected_number_of_participants = "100"
    department = factory.SubFactory(DepartmentsFactory)
    prepared_by_user = factory.SubFactory(UsersFactory)


class PersonnelInChargeFormsFactory(BaseFactory):
    """Factory for creating test personnel in charge records."""

    class Meta:
        model = PersonnelInChargeForms

    personnel_in_charge_forms_name = factory.Faker("name")
    personnel_in_charge_forms_position = "Adviser"
    personnel_in_charge_forms_department = factory.Faker("company")
    personnel_in_charge_forms_contact_number = "09171234567"


class ActivityReportFormsFactory(BaseFactory):
    """Factory for creating test activity report forms."""

    class Meta:
        model = ActivityReportForms

    activity_report_forms_nature_of_the_activity = "Seminar"
    activity_report_forms_contact_numbers = "09171234567"
    activity_report_date_submission = factory.LazyFunction(lambda: datetime.utcnow().date())
    concept_paper_form = factory.SubFactory(ConceptPaperFormsFactory)
    personnel_in_charge_form = factory.SubFactory(PersonnelInChargeFormsFactory)
    prepared_by_user = factory.SubFactory(UsersFactory)


class LearningJournalFormsFactory(BaseFactory):
    """Factory for creating test learning journal forms."""

    class Meta:
        model = LearningJournalForms

    learning_journal_forms_name = factory.Faker("name")
    learning_journal_forms_date = factory.LazyFunction(lambda: datetime.utcnow().date())
    learning_journal_forms_time = factory.LazyFunction(lambda: datetime.utcnow().time())
    learning_journal_forms_location = factory.Faker("city")
    learning_journal_forms_activity = "Workshop"
    learning_journal_forms_role = "Participant"
    prepared_by_user = factory.SubFactory(UsersFactory)


class DocumentationFactory(BaseFactory):
    """Factory for creating test documentation entries."""

    class Meta:
        model = Documentation

    documentation_type = "Activity Report"
    documentation_status = "Done"
    documentation_academic_year = "2023-2024"
    documentation_semester = FuzzyChoice(["1st Semester", "2nd Semester"])
    documentation_date_of_submission = factory.LazyFunction(datetime.utcnow)
    documentation_rating = 5.0
    documentation_comments_suggestions = factory.Faker("sentence")
    events = factory.SubFactory(EventsFactory)
    department = factory.SubFactory(DepartmentsFactory)
    prepared_by_user = factory.SubFactory(UsersFactory)
    checked_by_signatory = factory.SubFactory(SignatoriesFactory)
    noted_by_signatory = factory.SubFactory(SignatoriesFactory)


class FinancialReportsFactory(BaseFactory):
    """Factory for creating test financial reports."""

    class Meta:
        model = FinancialReports

    financial_reports_date = factory.LazyFunction(datetime.utcnow)
    financial_reports_academic_year = "2023-2024"
    financial_reports_semester = FuzzyChoice(["1st Semester", "2nd Semester"])
    financial_reports_status = "Done"
    financial_reports_title = factory.Sequence(lambda n: f"Financial Report {n}")
    events = factory.SubFactory(EventsFactory)
    department = factory.SubFactory(DepartmentsFactory)
    prepared_by_user = factory.SubFactory(UsersFactory)


class BoardResolutionsFactory(BaseFactory):
    """Factory for creating test board resolutions."""

    class Meta:
        model = BoardResolutions

    board_resolutions_title = factory.Sequence(lambda n: f"Board Resolution {n}")
    board_resolutions_date = factory.LazyFunction(datetime.utcnow)
    board_resolutions_academic_year = "2023-2024"
    board_resolutions_semester = FuzzyChoice(["1st Semester", "2nd Semester"])
    board_resolutions_status = "Done"
    board_resolutions_total_amount = 5000.00
    board_resolutions_description = factory.Faker("sentence")
    events = factory.SubFactory(EventsFactory)
    department = factory.SubFactory(DepartmentsFactory)
    prepared_by_user = factory.SubFactory(UsersFactory)
    approved_by_signatory = factory.SubFactory(SignatoriesFactory)


class MinutesOfTheMeetingFactory(BaseFactory):
    """Factory for creating test minutes of the meeting."""

    class Meta:
        model = MinutesOfTheMeeting

    minutes_of_the_meeting_date = factory.LazyFunction(datetime.utcnow)
    minutes_of_the_meeting_semester = FuzzyChoice(["1st Semester", "2nd Semester"])
    minutes_of_the_meeting_academic_year = "2023-2024"
    minutes_of_the_meeting_status = "Done"
    minutes_of_the_meeting_agenda = factory.Faker("sentence")
    minutes_of_the_meeting_notes = factory.Faker("sentence")
    minutes_of_the_meeting_adjourned = factory.LazyFunction(datetime.utcnow)
    department = factory.SubFactory(DepartmentsFactory)
    prepared_by_user = factory.SubFactory(UsersFactory)
    minutes_of_the_meeting_presiding_officer = factory.SelfAttribute("prepared_by_user.users_id")
    approved_by_user = factory.SubFactory(UsersFactory)
    noted_by_signatory = factory.SubFactory(SignatoriesFactory)

    @factory.post_generation
    def set_attendees(self, create, extracted, **kwargs):
        """Set the attendees JSON list to include the prepared_by user."""
        if create:
            self.attendees = [self.prepared_by_user.users_id]
            db.session.commit()
