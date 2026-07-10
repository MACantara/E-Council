"""Seed sample documentation records."""

from __future__ import annotations

from models import Documentation
from seeds import data
from seeds.core import get_or_create
from seeds.factories import DocumentationFactory


def seed(department_map: dict, user_map: dict, signatories: list, events: list) -> list:
    """Create sample documentation and return the list of instances."""
    department = department_map["College of Computer Studies"]
    officer = user_map["officer"]
    checked_by = signatories[0]
    noted_by = signatories[1]

    records = []

    for doc in data.SAMPLE_DOCUMENTATION:
        event = events[doc["event_index"]]

        instance, _ = get_or_create(
            Documentation,
            documentation_type=doc["type"],
            documentation_academic_year=data.SAMPLE_ACADEMIC_YEAR,
            documentation_semester=data.SAMPLE_SEMESTER,
            events=event,
            defaults={
                "documentation_status": doc["status"],
                "documentation_date_of_submission": event.events_end_date_and_time,
                "documentation_rating": doc["rating"],
                "documentation_comments_suggestions": doc["comments"],
                "department": department,
                "prepared_by_user": officer,
                "checked_by_signatory": checked_by,
                "noted_by_signatory": noted_by,
            },
            factory=DocumentationFactory,
        )
        records.append(instance)

    return records
