"""Integration tests for the seed scripts."""

import pytest

from models import (
    BoardResolutions,
    ConceptPaperForms,
    Departments,
    Documentation,
    Events,
    FinancialReports,
    MinutesOfTheMeeting,
    Signatories,
    StudentOrganizations,
    Users,
)


pytestmark = pytest.mark.usefixtures("app_context")


def test_seed_run_creates_expected_records():
    """Running the seeds should populate all major feature tables."""
    from seeds import run_all

    run_all()

    assert Departments.query.count() >= 5
    assert StudentOrganizations.query.count() >= 2
    assert Users.query.count() >= 4
    assert Signatories.query.count() >= 3
    assert ConceptPaperForms.query.count() >= 2
    assert Events.query.count() >= 2
    assert MinutesOfTheMeeting.query.count() >= 1
    assert FinancialReports.query.count() >= 1
    assert BoardResolutions.query.count() >= 1
    assert Documentation.query.count() >= 1


def test_seed_run_is_idempotent():
    """Running the seeds twice should not duplicate sample records."""
    from seeds import run_all

    run_all()
    first_counts = {
        "departments": Departments.query.count(),
        "users": Users.query.count(),
        "signatories": Signatories.query.count(),
        "events": Events.query.count(),
        "concept_papers": ConceptPaperForms.query.count(),
        "meetings": MinutesOfTheMeeting.query.count(),
        "financial_reports": FinancialReports.query.count(),
        "board_resolutions": BoardResolutions.query.count(),
        "documentation": Documentation.query.count(),
    }

    run_all()
    second_counts = {
        "departments": Departments.query.count(),
        "users": Users.query.count(),
        "signatories": Signatories.query.count(),
        "events": Events.query.count(),
        "concept_papers": ConceptPaperForms.query.count(),
        "meetings": MinutesOfTheMeeting.query.count(),
        "financial_reports": FinancialReports.query.count(),
        "board_resolutions": BoardResolutions.query.count(),
        "documentation": Documentation.query.count(),
    }

    assert first_counts == second_counts
