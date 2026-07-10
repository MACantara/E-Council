"""Seed sample data for the E-Council application."""

from __future__ import annotations

from extensions import db

from seeds import (
    board_resolutions,
    concept_papers,
    departments,
    documentation,
    events,
    financial,
    meetings,
    signatories,
    users,
)


def run_all() -> dict:
    """Run every seed script and return a summary of seeded records.

    Creates tables if they do not already exist and runs each seed in
    dependency order so a new developer can run a single command and have a
    fully populated development environment.
    """
    db.create_all()

    department_map = departments.seed()
    user_map = users.seed(department_map)
    signatory_list = signatories.seed()
    concept_paper_list = concept_papers.seed(department_map, user_map)
    event_list = events.seed(department_map, concept_paper_list)
    meeting_list = meetings.seed(department_map, user_map, signatory_list)
    financial_report_list = financial.seed(
        department_map, user_map, signatory_list, event_list
    )
    board_resolution_list = board_resolutions.seed(
        department_map, user_map, signatory_list, event_list
    )
    documentation_list = documentation.seed(
        department_map, user_map, signatory_list, event_list
    )

    return {
        "departments": len(department_map),
        "users": len(user_map),
        "signatories": len(signatory_list),
        "concept_papers": len(concept_paper_list),
        "events": len(event_list),
        "meetings": len(meeting_list),
        "financial_reports": len(financial_report_list),
        "board_resolutions": len(board_resolution_list),
        "documentation": len(documentation_list),
    }
