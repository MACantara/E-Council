"""FastAPI financial endpoints."""

from __future__ import annotations

import contextlib
from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from api.database import get_db
from api.dependencies import (
    get_current_user,
    get_pagination_params,
    get_storage,
    is_admin,
    save_upload,
)
from api.schemas.common import (
    MessageResponse,
    PaginatedResponse,
    ResponseEnvelope,
    build_pagination_metadata,
)
from api.schemas.financial import (
    FinancialReportCreate,
    FinancialReportResponse,
    FinancialReportStatusUpdate,
    FinancialReportUpdate,
    FinancialSummaryResponse,
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
)
from api.services.financial import generate_financial_report_pdf
from models import Events, FinancialReports, Transaction, Users

router = APIRouter(prefix="/financial", tags=["financial"])


def _report_access(report: FinancialReports, user: Users) -> bool:
    """Return True if the user can access the financial report."""
    if is_admin(user):
        return True
    return (
        report.financial_reports_departments_id is not None
        and report.financial_reports_departments_id == user.users_departments_id
    ) or (
        report.financial_reports_audited_and_prepared_by is not None
        and report.financial_reports_audited_and_prepared_by == user.users_id
    )


def _require_report_access(report: FinancialReports, user: Users) -> None:
    """Raise 403 if the user cannot access the financial report."""
    if not _report_access(report, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this financial report",
        )


def _get_report(db: Session, report_id: int) -> FinancialReports:
    """Get a financial report by ID or raise 404."""
    report = db.get(FinancialReports, report_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial report not found",
        )
    return report


def _get_report_or_404(db: Session, report_id: int) -> FinancialReports:
    """Get a financial report with event eagerly loaded or raise 404."""
    report = (
        db.query(FinancialReports)
        .options(selectinload(FinancialReports.events))
        .filter_by(financial_reports_id=report_id)
        .first()
    )
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial report not found",
        )
    return report


def _parse_datetime(value: str | datetime | None) -> datetime | None:
    """Parse a datetime value into a datetime object."""
    if value is None or isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            return datetime.strptime(value, "%Y-%m-%dT%H:%M")
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid datetime format. Use YYYY-MM-DDTHH:MM",
            ) from exc


def _resolve_academic_year(data: FinancialReportCreate | FinancialReportUpdate) -> str | None:
    """Return the final academic year, handling the 'Other' option."""
    year = data.financial_reports_academic_year
    if year == "Other" and getattr(data, "other_academic_year", None):
        return data.other_academic_year
    return year


def _get_event(db: Session, event_id: int | None) -> Events | None:
    """Get an event by ID or raise 404 if an ID is provided."""
    if event_id is None:
        return None
    event = db.get(Events, event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    return event


def _get_event_or_404(db: Session, event_id: int) -> Events:
    """Get an event with transactions eagerly loaded or raise 404."""
    event = db.query(Events).options(selectinload(Events.transactions)).filter_by(events_id=event_id).first()
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    return event


def _save_receipt(
    file: UploadFile | None,
    storage: Any,
    old_public_id: str | None = None,
) -> tuple[str | None, str | None]:
    """Upload a receipt and optionally delete the previous one."""
    if file is None:
        return None, None
    if old_public_id:
        with contextlib.suppress(Exception):
            storage.delete(old_public_id)
    result = save_upload(file, storage, folder="transactions")
    return result.get("url"), result.get("public_id")


def _resolve_transaction_category(data: TransactionCreate | TransactionUpdate) -> str | None:
    """Resolve the transaction category, handling the 'Other' option."""
    category = data.category
    if category == "Other" and getattr(data, "other_category", None):
        category = data.other_category
    return category


def _compute_summary(event: Events | None) -> FinancialSummaryResponse:
    """Compute budget vs actuals for an event."""
    budget = 0.0
    if event and event.events_budget:
        try:
            budget = float(event.events_budget)
        except (TypeError, ValueError):
            budget = 0.0

    transactions = event.transactions or [] if event else []
    total_income = sum(float(t.total or 0) for t in transactions if t.type == "Income")
    total_expenses = sum(float(t.total or 0) for t in transactions if t.type != "Income")
    remaining = budget - total_expenses + total_income

    return FinancialSummaryResponse(
        budget=str(event.events_budget) if event and event.events_budget else None,
        total_income=total_income,
        total_expenses=total_expenses,
        remaining=remaining,
        transaction_count=len(transactions),
    )


@router.get(
    "",
    response_model=ResponseEnvelope[PaginatedResponse[FinancialReportResponse]],
    status_code=status.HTTP_200_OK,
)
def list_financial_reports(
    status: str | None = Query(None),
    search: str | None = Query(None),
    pagination: Any = Depends(get_pagination_params),
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """List financial reports with pagination, status filtering, and department scoping."""
    query = db.query(FinancialReports)

    if not is_admin(current_user):
        query = query.filter(
            or_(
                FinancialReports.financial_reports_departments_id == current_user.users_departments_id,
                FinancialReports.financial_reports_audited_and_prepared_by == current_user.users_id,
            )
        )

    if status:
        query = query.filter(FinancialReports.financial_reports_status == status)

    if search:
        query = query.filter(FinancialReports.financial_reports_title.ilike(f"%{search}%"))

    if pagination.sort:
        sort_field = getattr(FinancialReports, pagination.sort, FinancialReports.financial_reports_date)
        query = query.order_by(sort_field.desc() if pagination.order == "desc" else sort_field.asc())
    else:
        query = query.order_by(FinancialReports.financial_reports_date.desc())

    total = query.count()
    items = query.offset((pagination.page - 1) * pagination.per_page).limit(pagination.per_page).all()

    return ResponseEnvelope(
        data=PaginatedResponse(
            items=items,
            pagination=build_pagination_metadata(total=total, page=pagination.page, per_page=pagination.per_page),
        )
    )


@router.post(
    "",
    response_model=ResponseEnvelope[FinancialReportResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_financial_report(
    data: FinancialReportCreate,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Create a new financial report."""
    event = _get_event(db, data.financial_reports_events_id)
    if event is not None and data.financial_reports_events_id is not None:
        pass

    report = FinancialReports(
        financial_reports_date=_parse_datetime(data.financial_reports_date),
        financial_reports_academic_year=_resolve_academic_year(data),
        financial_reports_semester=data.financial_reports_semester,
        financial_reports_status=data.financial_reports_status,
        financial_reports_events_id=data.financial_reports_events_id,
        financial_reports_departments_id=current_user.users_departments_id,
        financial_reports_title=data.financial_reports_title,
        financial_reports_audited_and_prepared_by=data.financial_reports_audited_and_prepared_by
        or current_user.users_id,
        financial_reports_noted_by=data.financial_reports_noted_by,
        financial_reports_recommending_approval_by=data.financial_reports_recommending_approval_by,
        financial_reports_approved_by=data.financial_reports_approved_by,
    )

    db.add(report)
    db.commit()
    db.refresh(report)
    return ResponseEnvelope(data=report)


@router.get(
    "/{report_id}",
    response_model=ResponseEnvelope[FinancialReportResponse],
    status_code=status.HTTP_200_OK,
)
def get_financial_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Get a financial report by ID."""
    report = _get_report_or_404(db, report_id)
    _require_report_access(report, current_user)
    return ResponseEnvelope(data=report)


@router.put(
    "/{report_id}",
    response_model=ResponseEnvelope[FinancialReportResponse],
    status_code=status.HTTP_200_OK,
)
def update_financial_report(
    report_id: int,
    data: FinancialReportUpdate,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Update a financial report."""
    report = _get_report_or_404(db, report_id)
    _require_report_access(report, current_user)

    if data.financial_reports_events_id is not None:
        _get_event(db, data.financial_reports_events_id)
        report.financial_reports_events_id = data.financial_reports_events_id
    if data.financial_reports_title is not None:
        report.financial_reports_title = data.financial_reports_title
    if data.financial_reports_academic_year is not None:
        report.financial_reports_academic_year = _resolve_academic_year(data)
    if data.financial_reports_semester is not None:
        report.financial_reports_semester = data.financial_reports_semester
    if data.financial_reports_status is not None:
        report.financial_reports_status = data.financial_reports_status
    if data.financial_reports_date is not None:
        report.financial_reports_date = _parse_datetime(data.financial_reports_date)
    if data.financial_reports_audited_and_prepared_by is not None:
        report.financial_reports_audited_and_prepared_by = data.financial_reports_audited_and_prepared_by
    if data.financial_reports_noted_by is not None:
        report.financial_reports_noted_by = data.financial_reports_noted_by
    if data.financial_reports_recommending_approval_by is not None:
        report.financial_reports_recommending_approval_by = data.financial_reports_recommending_approval_by
    if data.financial_reports_approved_by is not None:
        report.financial_reports_approved_by = data.financial_reports_approved_by

    db.commit()
    db.refresh(report)
    return ResponseEnvelope(data=report)


@router.delete(
    "/{report_id}",
    response_model=ResponseEnvelope[MessageResponse],
    status_code=status.HTTP_200_OK,
)
def delete_financial_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Delete a financial report."""
    report = _get_report_or_404(db, report_id)
    _require_report_access(report, current_user)

    db.delete(report)
    db.commit()
    return ResponseEnvelope(data=MessageResponse(message="Financial report deleted"))


@router.put(
    "/{report_id}/status",
    response_model=ResponseEnvelope[FinancialReportResponse],
    status_code=status.HTTP_200_OK,
)
def update_financial_report_status(
    report_id: int,
    data: FinancialReportStatusUpdate,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Update a financial report's status."""
    report = _get_report_or_404(db, report_id)
    _require_report_access(report, current_user)
    report.financial_reports_status = data.status
    db.commit()
    db.refresh(report)
    return ResponseEnvelope(data=report)


@router.get(
    "/{report_id}/summary",
    response_model=ResponseEnvelope[FinancialSummaryResponse],
    status_code=status.HTTP_200_OK,
)
def get_financial_summary(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Get budget vs actuals for a financial report."""
    report = _get_report_or_404(db, report_id)
    _require_report_access(report, current_user)

    event = None
    if report.financial_reports_events_id:
        event = _get_event_or_404(db, report.financial_reports_events_id)

    return ResponseEnvelope(data=_compute_summary(event))


@router.get(
    "/{report_id}/transactions",
    response_model=ResponseEnvelope[list[TransactionResponse]],
    status_code=status.HTTP_200_OK,
)
def list_financial_transactions(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """List transactions for the event linked to a financial report."""
    report = _get_report_or_404(db, report_id)
    _require_report_access(report, current_user)

    if report.financial_reports_events_id is None:
        return ResponseEnvelope(data=[])

    event = _get_event_or_404(db, report.financial_reports_events_id)
    return ResponseEnvelope(data=event.transactions or [])


@router.post(
    "/{report_id}/transactions",
    response_model=ResponseEnvelope[TransactionResponse],
    status_code=status.HTTP_201_CREATED,
)
def add_financial_transaction(
    report_id: int,
    data: str = Form(...),
    receipt: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
    storage: Any = Depends(get_storage),
):
    """Add a transaction to the event linked to a financial report."""
    payload = TransactionCreate.model_validate_json(data)
    report = _get_report_or_404(db, report_id)
    _require_report_access(report, current_user)

    if report.financial_reports_events_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Financial report is not linked to an event",
        )

    event = _get_event_or_404(db, report.financial_reports_events_id)

    receipt_url, receipt_public_id = _save_receipt(receipt, storage)

    unit_amount = payload.unit_amount or 0
    unit_price = payload.unit_price or Decimal("0.00")
    total = payload.total
    if total is None:
        total = Decimal(unit_amount) * unit_price

    transaction = Transaction(
        events_id=event.events_id,
        transaction_name=payload.transaction_name,
        transaction_date=_parse_datetime(payload.transaction_date),
        unit_amount=unit_amount,
        unit_price=unit_price,
        total=total,
        category=_resolve_transaction_category(payload),
        type=payload.type or "Expense",
        receipt_url=receipt_url,
        receipt_public_id=receipt_public_id,
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return ResponseEnvelope(data=transaction)


@router.put(
    "/{report_id}/transactions/{transaction_id}",
    response_model=ResponseEnvelope[TransactionResponse],
    status_code=status.HTTP_200_OK,
)
def update_financial_transaction(
    report_id: int,
    transaction_id: int,
    data: str = Form(...),
    receipt: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
    storage: Any = Depends(get_storage),
):
    """Update a transaction for the event linked to a financial report."""
    payload = TransactionUpdate.model_validate_json(data)
    report = _get_report_or_404(db, report_id)
    _require_report_access(report, current_user)

    if report.financial_reports_events_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Financial report is not linked to an event",
        )

    event = _get_event_or_404(db, report.financial_reports_events_id)

    transaction = db.query(Transaction).filter_by(transaction_id=transaction_id, events_id=event.events_id).first()
    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    for field in ("transaction_name", "type"):
        value = getattr(payload, field, None)
        if value is not None:
            setattr(transaction, field, value)

    if payload.transaction_date is not None:
        transaction.transaction_date = _parse_datetime(payload.transaction_date)

    if payload.unit_amount is not None:
        transaction.unit_amount = payload.unit_amount
    if payload.unit_price is not None:
        transaction.unit_price = payload.unit_price
    if payload.total is not None:
        transaction.total = payload.total
    else:
        transaction.total = Decimal(transaction.unit_amount or 0) * (transaction.unit_price or Decimal("0.00"))

    category = _resolve_transaction_category(payload)
    if category is not None:
        transaction.category = category

    if receipt is not None:
        receipt_url, receipt_public_id = _save_receipt(receipt, storage, transaction.receipt_public_id)
        transaction.receipt_url = receipt_url
        transaction.receipt_public_id = receipt_public_id

    db.commit()
    db.refresh(transaction)
    return ResponseEnvelope(data=transaction)


@router.get(
    "/{report_id}/pdf",
    status_code=status.HTTP_200_OK,
)
def download_financial_report_pdf(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Generate and download a PDF for a financial report."""
    report = _get_report_or_404(db, report_id)
    _require_report_access(report, current_user)
    pdf_buffer = generate_financial_report_pdf(db, report)
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=financial_report_{report_id}.pdf"},
    )
