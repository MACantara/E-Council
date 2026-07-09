"""Pydantic request/response models for FastAPI financial endpoints."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

FINANCIAL_STATUS_CHOICES = (
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


class FinancialReportBase(BaseModel):
    """Shared financial report fields."""

    financial_reports_date: datetime
    financial_reports_academic_year: str = Field(..., max_length=50)
    financial_reports_semester: Literal[SEMESTER_CHOICES]
    financial_reports_status: Literal[FINANCIAL_STATUS_CHOICES]
    financial_reports_events_id: int | None = None
    financial_reports_title: str = Field(..., min_length=1, max_length=255)
    financial_reports_audited_and_prepared_by: int | None = None
    financial_reports_noted_by: int | None = None
    financial_reports_recommending_approval_by: int | None = None
    financial_reports_approved_by: int | None = None


class FinancialReportCreate(BaseModel):
    """Financial report creation payload."""

    financial_reports_date: datetime
    financial_reports_academic_year: str = Field(..., max_length=50)
    other_academic_year: str | None = None
    financial_reports_semester: Literal[SEMESTER_CHOICES]
    financial_reports_status: Literal[FINANCIAL_STATUS_CHOICES] = "Upcoming"
    financial_reports_events_id: int | None = None
    financial_reports_title: str = Field(..., min_length=1, max_length=255)
    financial_reports_audited_and_prepared_by: int | None = None
    financial_reports_noted_by: int | None = None
    financial_reports_recommending_approval_by: int | None = None
    financial_reports_approved_by: int | None = None


class FinancialReportUpdate(BaseModel):
    """Financial report update payload."""

    financial_reports_date: datetime | None = None
    financial_reports_academic_year: str | None = Field(None, max_length=50)
    other_academic_year: str | None = None
    financial_reports_semester: Literal[SEMESTER_CHOICES] | None = None
    financial_reports_status: Literal[FINANCIAL_STATUS_CHOICES] | None = None
    financial_reports_events_id: int | None = None
    financial_reports_title: str | None = Field(None, min_length=1, max_length=255)
    financial_reports_audited_and_prepared_by: int | None = None
    financial_reports_noted_by: int | None = None
    financial_reports_recommending_approval_by: int | None = None
    financial_reports_approved_by: int | None = None


class FinancialReportResponse(FinancialReportBase):
    """Financial report response."""

    financial_reports_id: int
    financial_reports_departments_id: int | None = None

    model_config = {"from_attributes": True}


class FinancialReportStatusUpdate(BaseModel):
    """Financial report status update payload."""

    status: Literal[FINANCIAL_STATUS_CHOICES]


class FinancialSummaryResponse(BaseModel):
    """Budget vs actuals summary for a financial report."""

    budget: str | None = None
    total_income: float
    total_expenses: float
    remaining: float
    transaction_count: int


class TransactionCreate(BaseModel):
    """Transaction creation payload for a financial report's event."""

    transaction_name: str | None = None
    transaction_date: datetime | None = None
    unit_amount: int | None = 0
    unit_price: Decimal | None = Decimal("0.00")
    total: Decimal | None = None
    category: str | None = None
    other_category: str | None = None
    type: Literal[TRANSACTION_TYPE_CHOICES] = "Expense"


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


class TransactionResponse(BaseModel):
    """Transaction response."""

    transaction_id: int
    events_id: int
    transaction_name: str | None = None
    transaction_date: datetime | None = None
    unit_amount: int | None = None
    unit_price: Decimal | None = None
    total: Decimal | None = None
    category: str | None = None
    type: str | None = None
    receipt_url: str | None = None
    receipt_public_id: str | None = None

    model_config = {"from_attributes": True}
