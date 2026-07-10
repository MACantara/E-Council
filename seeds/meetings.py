"""Seed sample meeting minutes."""

from __future__ import annotations

from models import MinutesOfTheMeeting

from seeds import data
from seeds.core import get_or_create
from seeds.factories import MinutesOfTheMeetingFactory


def seed(department_map: dict, user_map: dict, signatories: list) -> list:
    """Create sample meeting minutes and return the list of instances."""
    department = department_map["College of Computer Studies"]
    officer = user_map["officer"]
    noted_by = signatories[0]

    meetings = []

    for meeting in data.SAMPLE_MEETINGS:
        instance, _ = get_or_create(
            MinutesOfTheMeeting,
            minutes_of_the_meeting_agenda=meeting["agenda"],
            minutes_of_the_meeting_academic_year=data.SAMPLE_ACADEMIC_YEAR,
            minutes_of_the_meeting_semester=data.SAMPLE_SEMESTER,
            defaults={
                "minutes_of_the_meeting_date": meeting["date"],
                "minutes_of_the_meeting_status": meeting["status"],
                "minutes_of_the_meeting_presiding_officer": meeting["presiding_officer"],
                "minutes_of_the_meeting_notes": meeting["notes"],
                "minutes_of_the_meeting_adjourned": meeting["adjourned"],
                "department": department,
                "prepared_by_user": officer,
                "approved_by_user": officer,
                "noted_by_signatory": noted_by,
            },
            factory=MinutesOfTheMeetingFactory,
        )
        meetings.append(instance)

    return meetings
