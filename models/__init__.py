"""
Database models package for E-Council.
This package contains all database models organized by feature.
"""

from models.base import db

# Import all models for easy access
from models.department import Departments, StudentOrganizations
from models.user import Users, EmailVerification, PasswordReset, LoginAttempts
from models.event import Events, DepartmentsEvents, EventInvitations
from models.concept_paper import (
    ConceptPaperForms,
    ExcuseLetterForms,
    ActivityReportForms,
    PersonnelInChargeForms,
    LearningJournalForms,
    ParentGuardianConsentForms
)
from models.documentation import Documentation
from models.financial import FinancialReports
from models.board_resolution import BoardResolutions
from models.meeting import MinutesOfTheMeeting, Signatories

__all__ = [
    # Base
    'db',

    # Department models
    'Departments',
    'StudentOrganizations',

    # User models
    'Users',
    'EmailVerification',
    'PasswordReset',
    'LoginAttempts',

    # Event models
    'Events',
    'DepartmentsEvents',
    'EventInvitations',

    # Concept paper models
    'ConceptPaperForms',
    'ExcuseLetterForms',
    'ActivityReportForms',
    'PersonnelInChargeForms',
    'LearningJournalForms',
    'ParentGuardianConsentForms',

    # Documentation models
    'Documentation',

    # Financial models
    'FinancialReports',

    # Board resolution models
    'BoardResolutions',

    # Meeting models
    'MinutesOfTheMeeting',
    'Signatories',
]
