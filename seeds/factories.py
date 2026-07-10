"""Re-export factory-boy factories so seeds and tests share the same builders."""

from __future__ import annotations

from tests.factories import (
    ActivityReportFormsFactory,
    BaseFactory,
    BoardResolutionsFactory,
    ConceptPaperFormsFactory,
    DepartmentsEventsFactory,
    DepartmentsFactory,
    DocumentationFactory,
    EventsFactory,
    FinancialReportsFactory,
    LearningJournalFormsFactory,
    MinutesOfTheMeetingFactory,
    PersonnelInChargeFormsFactory,
    SignatoriesFactory,
    StudentOrganizationsFactory,
    UsersFactory,
)

__all__ = [
    "ActivityReportFormsFactory",
    "BaseFactory",
    "BoardResolutionsFactory",
    "ConceptPaperFormsFactory",
    "DepartmentsEventsFactory",
    "DepartmentsFactory",
    "DocumentationFactory",
    "EventsFactory",
    "FinancialReportsFactory",
    "LearningJournalFormsFactory",
    "MinutesOfTheMeetingFactory",
    "PersonnelInChargeFormsFactory",
    "SignatoriesFactory",
    "StudentOrganizationsFactory",
    "UsersFactory",
]
