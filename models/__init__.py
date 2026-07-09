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
from models.financial import FinancialReports
from models.meeting import MinutesOfTheMeeting, Signatories
from models.user import EmailVerification, LoginAttempts, PasswordReset, Users

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
    # Concept paper models
    "ConceptPaperForms",
    "ExcuseLetterForms",
    "ActivityReportForms",
    "PersonnelInChargeForms",
    "LearningJournalForms",
    "ParentGuardianConsentForms",
    # Documentation models
    "Documentation",
    # Financial models
    "FinancialReports",
    # Board resolution models
    "BoardResolutions",
    # Meeting models
    "MinutesOfTheMeeting",
    "Signatories",
]
