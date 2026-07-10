"""Seed sample board resolutions."""

from __future__ import annotations

from models import BoardResolutions
from seeds import data
from seeds.core import get_or_create
from seeds.factories import BoardResolutionsFactory


def seed(department_map: dict, user_map: dict, signatories: list, events: list) -> list:
    """Create sample board resolutions and return the list of instances."""
    department = department_map["College of Computer Studies"]
    officer = user_map["officer"]
    approved_by = signatories[0]

    resolutions = []

    for resolution in data.SAMPLE_BOARD_RESOLUTIONS:
        event = events[resolution["event_index"]]

        instance, _ = get_or_create(
            BoardResolutions,
            board_resolutions_title=resolution["title"],
            board_resolutions_academic_year=data.SAMPLE_ACADEMIC_YEAR,
            board_resolutions_semester=data.SAMPLE_SEMESTER,
            defaults={
                "board_resolutions_date": event.events_start_date_and_time,
                "board_resolutions_status": resolution["status"],
                "board_resolutions_total_amount": resolution["amount"],
                "board_resolutions_description": resolution["description"],
                "events": event,
                "department": department,
                "prepared_by_user": officer,
                "approved_by_signatory": approved_by,
                "student_signatory_ids": [officer.users_id],
            },
            factory=BoardResolutionsFactory,
        )
        resolutions.append(instance)

    return resolutions
