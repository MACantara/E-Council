"""Seed sample events and link them to departments."""

from __future__ import annotations

from models import DepartmentsEvents, Events
from seeds import data
from seeds.core import get_or_create
from seeds.factories import DepartmentsEventsFactory, EventsFactory


def seed(department_map: dict, concept_papers: list) -> list:
    """Create sample events and return the list of instances."""
    department = department_map["College of Computer Studies"]
    events = []

    for event_info in data.SAMPLE_EVENTS:
        concept_paper = concept_papers[event_info["concept_paper_index"]]

        event, _ = get_or_create(
            Events,
            events_name=event_info["name"],
            events_academic_year=data.SAMPLE_ACADEMIC_YEAR,
            events_semester=data.SAMPLE_SEMESTER,
            defaults={
                "events_status": event_info["status"],
                "events_venue": event_info["venue"],
                "events_budget": event_info["budget"],
                "events_description": event_info["description"],
                "events_remarks": event_info["remarks"],
                "events_start_date_and_time": event_info["start"],
                "events_end_date_and_time": event_info["end"],
                "events_concept_paper_forms_id": concept_paper.concept_paper_forms_id,
            },
            factory=EventsFactory,
        )

        get_or_create(
            DepartmentsEvents,
            department=department,
            event=event,
            factory=DepartmentsEventsFactory,
        )

        events.append(event)

    return events
