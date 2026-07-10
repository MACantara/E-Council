"""Pydantic request/response models for FastAPI event endpoints."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

EVENT_STATUS_CHOICES = (
    "Upcoming",
    "Postponed",
    "Done",
    "Cancelled",
)

SEMESTER_CHOICES = (
    "1st Semester",
    "2nd Semester",
)

TRANSACTION_TYPE_CHOICES = (
    "Expense",
    "Income",
)


class TransactionBase(BaseModel):
    """Shared transaction fields."""

    transaction_name: str | None = None
    transaction_date: datetime | None = None
    unit_amount: int | None = 0
    unit_price: Decimal | None = Decimal("0.00")
    total: Decimal | None = Decimal("0.00")
    category: str | None = None
    type: Literal[TRANSACTION_TYPE_CHOICES] | None = "Expense"
    receipt_url: str | None = None
    receipt_public_id: str | None = None


class TransactionCreate(BaseModel):
    """Transaction creation payload."""

    transaction_name: str | None = None
    transaction_date: datetime | None = None
    unit_amount: int | None = 0
    unit_price: Decimal | None = Decimal("0.00")
    total: Decimal | None = None
    category: str | None = None
    other_category: str | None = None
    type: Literal[TRANSACTION_TYPE_CHOICES] | None = "Expense"


class TransactionResponse(TransactionBase):
    """Transaction response."""

    transaction_id: int
    events_id: int

    model_config = {"from_attributes": True}


class TransactionUpdate(BaseModel):
    """Transaction update payload."""

    transaction_name: str | None = None
    transaction_date: datetime | None = None
    unit_amount: int | None = None
    unit_price: Decimal | None = None
    total: Decimal | None = None
    category: str | None = None
    other_category: str | None = None
    type: Literal[TRANSACTION_TYPE_CHOICES] | None = None


class EventBase(BaseModel):
    """Shared event fields."""

    events_concept_paper_forms_id: int | None = None
    events_name: str | None = Field(None, max_length=255)
    events_semester: Literal[SEMESTER_CHOICES] | None = None
    events_academic_year: str | None = Field(None, max_length=50)
    events_start_date_and_time: datetime | None = None
    events_end_date_and_time: datetime | None = None
    events_venue: str | None = Field(None, max_length=255)
    events_budget: str | None = Field(None, max_length=255)
    events_status: Literal[EVENT_STATUS_CHOICES] | None = "Upcoming"
    events_description: str | None = None
    events_remarks: str | None = None


class EventCreate(BaseModel):
    """Event creation payload."""

    creation_method: Literal["scratch", "existing"] = "scratch"
    concept_paper_forms_id: int | None = None
    events_name: str | None = Field(None, max_length=255)
    events_semester: Literal[SEMESTER_CHOICES] | None = None
    events_academic_year: str | None = Field(None, max_length=50)
    other_academic_year: str | None = None
    events_start_date_and_time: datetime | None = None
    events_end_date_and_time: datetime | None = None
    events_venue: str | None = Field(None, max_length=255)
    events_budget: str | None = Field(None, max_length=255)
    events_status: Literal[EVENT_STATUS_CHOICES] | None = "Upcoming"
    events_description: str | None = None
    events_remarks: str | None = None


class EventUpdate(BaseModel):
    """Event update payload."""

    events_concept_paper_forms_id: int | None = None
    events_name: str | None = Field(None, max_length=255)
    events_semester: Literal[SEMESTER_CHOICES] | None = None
    events_academic_year: str | None = Field(None, max_length=50)
    events_start_date_and_time: datetime | None = None
    events_end_date_and_time: datetime | None = None
    events_venue: str | None = Field(None, max_length=255)
    events_budget: str | None = Field(None, max_length=255)
    events_status: Literal[EVENT_STATUS_CHOICES] | None = None
    events_description: str | None = None
    events_remarks: str | None = None


class EventResponse(EventBase):
    """Event response."""

    events_id: int
    transactions: list[TransactionResponse] = []

    model_config = {"from_attributes": True}


class EventStatusUpdate(BaseModel):
    """Event status update payload."""

    status: Literal[EVENT_STATUS_CHOICES]


class EventInviteRequest(BaseModel):
    """Invitation request payload."""

    email: str = Field(..., min_length=1, max_length=255)


class EventInviteResponse(BaseModel):
    """Invitation response payload."""

    message: str


class EventInviteAccept(BaseModel):
    """Token payload for accepting an event invitation."""

    token: str


class EventInviteResponseData(BaseModel):
    """Invite acceptance response."""

    message: str
    event_id: int
