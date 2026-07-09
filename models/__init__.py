"""
Database models package for E-Council.
This package contains all database models organized by feature.
"""

from models.base import db
from models.board_resolution import BoardResolutions
from models.concept_paper import (
    ActivityReportForms,
    ConceptPaperForms,
    ExcuseLetterForms,
    LearningJournalForms,
    ParentGuardianConsentForms,
    PersonnelInChargeForms,
)

# Import all models for easy access
from models.department import Departments, StudentOrganizations
from models.documentation import Documentation
from models.event import DepartmentsEvents, EventInvitations, Events
from models.evaluation_form import EvaluationForm
from models.financial import FinancialReports
from models.learning_outcome import LearningOutcome
from models.meeting import MinutesOfTheMeeting, Signatories
from models.meeting_attendee import MeetingAttendee
from models.objective import Objective
from models.tally_item import TallyItem
from models.transaction import Transaction
from models.user import EmailVerification, LoginAttempts, PasswordReset, Users
from models.activity_report_item import ActivityReportItem

__all__ = [
    # Base
    "db",
    # Department models
    "Departments",
    "StudentOrganizations",
    # User models
    "Users",
    "EmailVerification",
    "PasswordReset",
    "LoginAttempts",
    # Event models
    "Events",
    "DepartmentsEvents",
    "EventInvitations",
    "Transaction",
    # Concept paper models
    "ConceptPaperForms",
    "ExcuseLetterForms",
    "ActivityReportForms",
    "PersonnelInChargeForms",
    "LearningJournalForms",
    "ParentGuardianConsentForms",
    "Objective",
    "LearningOutcome",
    "ActivityReportItem",
    # Documentation models
    "Documentation",
    "TallyItem",
    "EvaluationForm",
    # Financial models
    "FinancialReports",
    # Board resolution models
    "BoardResolutions",
    # Meeting models
    "MinutesOfTheMeeting",
    "Signatories",
    "MeetingAttendee",
]
