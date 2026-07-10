"""Pydantic request/response models for FastAPI meeting endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from api.schemas.auth import UserResponse

MEETING_STATUS_CHOICES = (
    "Upcoming",
    "Postponed",
    "Done",
    "Cancelled",
)

SEMESTER_CHOICES = (
    "1st Semester",
    "2nd Semester",
)


class PhotoDocumentation(BaseModel):
    """A single photo documentation entry."""

    url: str
    public_id: str | None = None


class MeetingAttendeeBase(BaseModel):
    """Shared meeting attendee fields."""

    users_id: int
    attended: bool | None = None


class MeetingAttendeeCreate(BaseModel):
    """Payload for adding a meeting attendee."""

    users_id: int
    attended: bool = True


class MeetingAttendeeUpdate(BaseModel):
    """Payload for updating a meeting attendee's attendance."""

    attended: bool


class MeetingAttendeeResponse(MeetingAttendeeBase):
    """Meeting attendee response."""

    meeting_attendee_id: int
    minutes_of_the_meeting_id: int
    user: UserResponse | None = None

    model_config = {"from_attributes": True}


class MeetingBase(BaseModel):
    """Shared meeting fields."""

    minutes_of_the_meeting_date: datetime
    minutes_of_the_meeting_semester: str
    minutes_of_the_meeting_academic_year: str
    minutes_of_the_meeting_status: str
    minutes_of_the_meeting_presiding_officer: str
    minutes_of_the_meeting_agenda: str
    minutes_of_the_meeting_notes: str | None = None
    minutes_of_the_meeting_adjourned: datetime | None = None
    minutes_of_the_meeting_approved_by: int | None = None
    minutes_of_the_meeting_prepared_by: int | None = None
    minutes_of_the_meeting_noted_by: int | None = None
    photo_documentation: list[PhotoDocumentation] = []


class MeetingCreate(BaseModel):
    """Meeting creation payload."""

    minutes_of_the_meeting_date: datetime
    minutes_of_the_meeting_semester: str
    minutes_of_the_meeting_academic_year: str
    other_academic_year: str | None = None
    minutes_of_the_meeting_status: str = "Upcoming"
    minutes_of_the_meeting_presiding_officer: str
    minutes_of_the_meeting_agenda: str
    minutes_of_the_meeting_notes: str | None = None
    minutes_of_the_meeting_adjourned: datetime | None = None
    minutes_of_the_meeting_approved_by: int | None = None
    minutes_of_the_meeting_noted_by: int | None = None
    attendees: list[int] = []


class MeetingUpdate(BaseModel):
    """Meeting update payload."""

    minutes_of_the_meeting_date: datetime | None = None
    minutes_of_the_meeting_semester: str | None = None
    minutes_of_the_meeting_academic_year: str | None = None
    other_academic_year: str | None = None
    minutes_of_the_meeting_status: str | None = None
    minutes_of_the_meeting_presiding_officer: str | None = None
    minutes_of_the_meeting_agenda: str | None = None
    minutes_of_the_meeting_notes: str | None = None
    minutes_of_the_meeting_adjourned: datetime | None = None
    minutes_of_the_meeting_approved_by: int | None = None
    minutes_of_the_meeting_noted_by: int | None = None
    attendees: list[int] | None = None


class MeetingResponse(MeetingBase):
    """Meeting response."""

    minutes_of_the_meeting_id: int
    minutes_of_the_meeting_departments_id: int | None = None
    attendees: list[MeetingAttendeeResponse] = []

    model_config = {"from_attributes": True}


class MeetingStatusUpdate(BaseModel):
    """Meeting status update payload."""

    status: str


class MeetingAgendaUpdate(BaseModel):
    """Agenda update payload."""

    agenda: str


class MeetingMinutesUpdate(BaseModel):
    """Minutes/notes update payload."""

    minutes: str
