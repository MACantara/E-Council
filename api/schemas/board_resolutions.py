"""Pydantic request/response models for FastAPI board resolution endpoints."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


BOARD_RESOLUTION_STATUS_CHOICES = (
    "Upcoming",
    "Postponed",
    "Done",
    "Cancelled",
)

SEMESTER_CHOICES = (
    "1st Semester",
    "2nd Semester",
)


class BoardResolutionBase(BaseModel):
    """Shared board resolution fields."""

    board_resolutions_date: datetime
    board_resolutions_events_id: int | None = None
    board_resolutions_title: str = Field(..., min_length=1, max_length=255)
    board_resolutions_description: str | None = None
    board_resolutions_total_amount: str | None = None
    board_resolutions_academic_year: str | None = Field(None, max_length=50)
    board_resolutions_semester: Literal[SEMESTER_CHOICES] | None = None
    board_resolutions_status: Literal[BOARD_RESOLUTION_STATUS_CHOICES] = "Upcoming"
    board_resolutions_prepared_by: int | None = None
    board_resolutions_approved_by: int | None = None
    student_signatory_ids: list[int] = []


class BoardResolutionCreate(BaseModel):
    """Board resolution creation payload."""

    board_resolutions_date: datetime
    board_resolutions_events_id: int | None = None
    board_resolutions_title: str = Field(..., min_length=1, max_length=255)
    board_resolutions_description: str | None = None
    board_resolutions_total_amount: str | None = None
    board_resolutions_academic_year: str | None = Field(None, max_length=50)
    other_academic_year: str | None = None
    board_resolutions_semester: Literal[SEMESTER_CHOICES] | None = None
    board_resolutions_status: Literal[BOARD_RESOLUTION_STATUS_CHOICES] = "Upcoming"
    board_resolutions_prepared_by: int | None = None
    board_resolutions_approved_by: int | None = None
    student_signatory_ids: list[int] = []
    new_event_name: str | None = None


class BoardResolutionUpdate(BaseModel):
    """Board resolution update payload."""

    board_resolutions_date: datetime | None = None
    board_resolutions_events_id: int | None = None
    board_resolutions_title: str | None = Field(None, min_length=1, max_length=255)
    board_resolutions_description: str | None = None
    board_resolutions_total_amount: str | None = None
    board_resolutions_academic_year: str | None = Field(None, max_length=50)
    other_academic_year: str | None = None
    board_resolutions_semester: Literal[SEMESTER_CHOICES] | None = None
    board_resolutions_status: Literal[BOARD_RESOLUTION_STATUS_CHOICES] | None = None
    board_resolutions_prepared_by: int | None = None
    board_resolutions_approved_by: int | None = None
    student_signatory_ids: list[int] | None = None
    new_event_name: str | None = None


class BoardResolutionResponse(BaseModel):
    """Board resolution response."""

    board_resolutions_id: int
    board_resolutions_date: datetime
    board_resolutions_departments_id: int | None = None
    board_resolutions_events_id: int | None = None
    board_resolutions_title: str | None = None
    board_resolutions_description: str | None = None
    board_resolutions_total_amount: str | None = None
    board_resolutions_academic_year: str | None = None
    board_resolutions_semester: str | None = None
    board_resolutions_status: str | None = None
    board_resolutions_prepared_by: int | None = None
    board_resolutions_approved_by: int | None = None
    student_signatory_ids: list[Any] = []

    model_config = {"from_attributes": True}

    @field_validator("board_resolutions_total_amount", mode="before")
    @classmethod
    def _total_amount_to_string(cls, value: Any) -> str | None:
        """Convert Decimal totals from the ORM into a string representation."""
        if value is None:
            return None
        if isinstance(value, Decimal):
            return str(value)
        return value


class BoardResolutionStatusUpdate(BaseModel):
    """Board resolution status update payload."""

    status: Literal[BOARD_RESOLUTION_STATUS_CHOICES]


class BoardResolutionAIRequest(BaseModel):
    """Payload for AI-generated board resolution description."""

    event_name: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    date: str | None = None
    total_amount: str | None = None


class BoardResolutionAIResponse(BaseModel):
    """Response for AI-generated board resolution content."""

    content: str
