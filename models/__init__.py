"""
Database models package for E-Council.
This package contains all database models organized by feature.
"""

from models.base import db

# Import all models for easy access
from models.department import Departments, StudentOrganizations
from models.user import Users, EmailVerification, PasswordReset, LoginAttempts
from models.event import Events, DepartmentsEvents, EventInvitations, TransactionHistory
from models.concept_paper import (
    ConceptPaperForms,
    ObjectivesOfTheActivity,
    LearningOutcomes,
    ExcuseLetterForms,
    ActivityReportForms,
    PersonnelInChargeForms,
    LearningJournalForms,
    Observations,
    Learnings,
    ParentGuardianConsentForms,
    ActivityReportFormsActivityStrengths,
    ActivityReportFormsActivityWeaknesses,
    ActivityReportFormsActivityRecommendations
)
from models.documentation import (
    Documentation,
    TallyItems,
    ResultsOfTheEvaluationImages,
    EvaluationForm,
    SummaryOfAttendanceImages,
    EvaluationListOfStudentNames,
    EventPhotoDocumentationImages,
    ActivityStrengths,
    ActivityWeaknesses,
    ActivityRecommendations
)
from models.financial import FinancialReports
from models.board_resolution import BoardResolutions, BoardResolutionsStudentSignatories
from models.meeting import (
    MinutesOfTheMeeting,
    Signatories,
    MinutesOfTheMeetingPhotoDocumentation,
    MinutesOfTheMeetingAttendees
)

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
    'TransactionHistory',
    
    # Concept paper models
    'ConceptPaperForms',
    'ObjectivesOfTheActivity',
    'LearningOutcomes',
    'ExcuseLetterForms',
    'ActivityReportForms',
    'PersonnelInChargeForms',
    'LearningJournalForms',
    'Observations',
    'Learnings',
    'ParentGuardianConsentForms',
    'ActivityReportFormsActivityStrengths',
    'ActivityReportFormsActivityWeaknesses',
    'ActivityReportFormsActivityRecommendations',
    
    # Documentation models
    'Documentation',
    'TallyItems',
    'ResultsOfTheEvaluationImages',
    'EvaluationForm',
    'SummaryOfAttendanceImages',
    'EvaluationListOfStudentNames',
    'EventPhotoDocumentationImages',
    'ActivityStrengths',
    'ActivityWeaknesses',
    'ActivityRecommendations',
    
    # Financial models
    'FinancialReports',
    
    # Board resolution models
    'BoardResolutions',
    'BoardResolutionsStudentSignatories',
    
    # Meeting models
    'MinutesOfTheMeeting',
    'Signatories',
    'MinutesOfTheMeetingPhotoDocumentation',
    'MinutesOfTheMeetingAttendees',
]