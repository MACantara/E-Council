"""FastAPI event endpoints."""

from __future__ import annotations

import contextlib
from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session, selectinload

from api.database import get_db
from api.dependencies import (
    get_current_user,
    get_email,
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
from api.schemas.events import (
    EventCreate,
    EventInviteAccept,
    EventInviteRequest,
    EventInviteResponse,
    EventInviteResponseData,
    EventResponse,
    EventStatusUpdate,
    EventUpdate,
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
)
from api.services.events import send_event_invite_email
from models import (
    ConceptPaperForms,
    DepartmentsEvents,
    EventInvitations,
    Events,
    Transaction,
    Users,
)

router = APIRouter(prefix="/events", tags=["events"])


def _event_access(db: Session, event: Events, user: Users) -> bool:
    """Return True if the user can access the event."""
    if is_admin(user):
        return True
    linked = (
        db.query(DepartmentsEvents)
        .filter_by(events_id=event.events_id, departments_id=user.users_departments_id)
        .first()
    )
    if linked is not None:
        return True
    if event.events_concept_paper_forms_id:
        concept_paper = db.get(ConceptPaperForms, event.events_concept_paper_forms_id)
        if concept_paper:
            if concept_paper.concept_paper_forms_departments_id == user.users_departments_id:
                return True
            if concept_paper.concept_paper_forms_prepared_by == user.users_id:
                return True
    return False


def _require_event_access(db: Session, event: Events, user: Users) -> None:
    """Raise 403 if the user cannot access the event."""
    if not _event_access(db, event, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this event",
        )


def _get_event(db: Session, event_id: int) -> Events:
    """Retrieve an event by ID or raise 404."""
    event = db.get(Events, event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    return event


def _get_event_or_404(db: Session, event_id: int) -> Events:
    """Retrieve an event with transactions eagerly loaded or raise 404."""
    event = db.query(Events).options(selectinload(Events.transactions)).filter_by(events_id=event_id).first()
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )
    return event


def _events_query(db: Session, user: Users) -> Any:
    """Return a base query scoped to the user's department."""
    query = db.query(Events).options(selectinload(Events.transactions))
    if not is_admin(user):
        query = query.join(DepartmentsEvents).filter(DepartmentsEvents.departments_id == user.users_departments_id)
    return query


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


def _event_name_exists(db: Session, name: str, exclude_id: int | None = None) -> bool:
    """Check whether an event name is already in use."""
    query = db.query(Events).filter(Events.events_name == name)
    if exclude_id is not None:
        query = query.filter(Events.events_id != exclude_id)
    return query.first() is not None


@router.get(
    "",
    response_model=ResponseEnvelope[PaginatedResponse[EventResponse]],
    status_code=status.HTTP_200_OK,
)
def list_events(
    status: str | None = Query(None),
    search: str | None = Query(None),
    pagination: Any = Depends(get_pagination_params),
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """List events with pagination, status filtering, and department scoping."""
    query = _events_query(db, current_user)

    if status:
        query = query.filter(Events.events_status == status)

    if search:
        query = query.filter(Events.events_name.ilike(f"%{search}%"))

    if pagination.sort:
        sort_field = getattr(Events, pagination.sort, Events.events_start_date_and_time)
        query = query.order_by(sort_field.desc() if pagination.order == "desc" else sort_field.asc())
    else:
        query = query.order_by(Events.events_start_date_and_time.desc())

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
    response_model=ResponseEnvelope[EventResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_event(
    data: EventCreate,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Create a new event from scratch or from an existing concept paper."""
    event = Events()

    if data.creation_method == "existing" and data.concept_paper_forms_id:
        concept_paper = db.get(ConceptPaperForms, data.concept_paper_forms_id)
        if concept_paper is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected concept paper not found",
            )
        event.events_concept_paper_forms_id = concept_paper.concept_paper_forms_id
        event.events_name = concept_paper.concept_paper_forms_subject
        event.events_semester = concept_paper.concept_paper_forms_semester
        event.events_academic_year = concept_paper.concept_paper_forms_academic_year
        event.events_start_date_and_time = concept_paper.concept_paper_forms_event_start_date_and_time
        event.events_end_date_and_time = concept_paper.concept_paper_forms_event_end_date_and_time
        event.events_venue = concept_paper.concept_paper_forms_location
        event.events_budget = concept_paper.concept_paper_forms_budget
        event.events_description = concept_paper.concept_paper_forms_descriptions
        event.events_status = data.events_status or "Upcoming"
        event.events_remarks = data.events_remarks
    else:
        if not data.events_name or not data.events_semester or not data.events_academic_year:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Event name, semester, and academic year are required",
            )
        start_dt = _parse_datetime(data.events_start_date_and_time)
        end_dt = _parse_datetime(data.events_end_date_and_time)
        if start_dt is None or end_dt is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Event start and end dates are required",
            )

        event.events_concept_paper_forms_id = data.concept_paper_forms_id
        event.events_name = data.events_name
        event.events_semester = data.events_semester
        academic_year = data.events_academic_year
        if academic_year == "Other" and data.other_academic_year:
            academic_year = data.other_academic_year
        event.events_academic_year = academic_year
        event.events_start_date_and_time = start_dt
        event.events_end_date_and_time = end_dt
        event.events_venue = data.events_venue
        event.events_budget = data.events_budget
        event.events_status = data.events_status or "Upcoming"
        event.events_description = data.events_description
        event.events_remarks = data.events_remarks

    if not event.events_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event name is required",
        )

    if _event_name_exists(db, event.events_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An event with this name already exists",
        )

    db.add(event)
    db.flush()

    db.add(
        DepartmentsEvents(
            departments_id=current_user.users_departments_id,
            events_id=event.events_id,
        )
    )
    db.commit()
    db.refresh(event)
    return ResponseEnvelope(data=event)


@router.get(
    "/{event_id}",
    response_model=ResponseEnvelope[EventResponse],
    status_code=status.HTTP_200_OK,
)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Get a single event by ID."""
    event = _get_event_or_404(db, event_id)
    _require_event_access(db, event, current_user)
    return ResponseEnvelope(data=event)


@router.put(
    "/{event_id}",
    response_model=ResponseEnvelope[EventResponse],
    status_code=status.HTTP_200_OK,
)
def update_event(
    event_id: int,
    data: EventUpdate,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Update an event."""
    event = _get_event_or_404(db, event_id)
    _require_event_access(db, event, current_user)

    if data.events_name is not None and data.events_name != event.events_name:
        if _event_name_exists(db, data.events_name, exclude_id=event.events_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An event with this name already exists",
            )
        event.events_name = data.events_name

    for field in (
        "events_concept_paper_forms_id",
        "events_semester",
        "events_academic_year",
        "events_venue",
        "events_budget",
        "events_status",
        "events_description",
        "events_remarks",
    ):
        value = getattr(data, field, None)
        if value is not None:
            setattr(event, field, value)

    if data.events_start_date_and_time is not None:
        event.events_start_date_and_time = _parse_datetime(data.events_start_date_and_time)
    if data.events_end_date_and_time is not None:
        event.events_end_date_and_time = _parse_datetime(data.events_end_date_and_time)

    db.commit()
    db.refresh(event)
    return ResponseEnvelope(data=event)


@router.delete(
    "/{event_id}",
    response_model=ResponseEnvelope[MessageResponse],
    status_code=status.HTTP_200_OK,
)
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Delete an event and its related records."""
    event = _get_event_or_404(db, event_id)
    _require_event_access(db, event, current_user)

    storage = get_storage()
    for transaction in event.transactions or []:
        if transaction.receipt_public_id:
            with contextlib.suppress(Exception):
                storage.delete(transaction.receipt_public_id)

    db.query(DepartmentsEvents).filter_by(events_id=event_id).delete()
    db.query(EventInvitations).filter_by(event_invitations_events_id=event_id).delete()
    db.delete(event)
    db.commit()
    return ResponseEnvelope(data=MessageResponse(message="Event deleted"))


@router.put(
    "/{event_id}/status",
    response_model=ResponseEnvelope[EventResponse],
    status_code=status.HTTP_200_OK,
)
def update_event_status(
    event_id: int,
    data: EventStatusUpdate,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Update the status of an event."""
    event = _get_event_or_404(db, event_id)
    _require_event_access(db, event, current_user)
    event.events_status = data.status
    db.commit()
    db.refresh(event)
    return ResponseEnvelope(data=event)


def _resolve_transaction_category(data: TransactionCreate | TransactionUpdate) -> str | None:
    """Resolve the transaction category, handling the 'Other' option."""
    category = data.category
    if category == "Other" and data.other_category:
        category = data.other_category
    return category


def _save_receipt(
    file: UploadFile | None,
    storage: Any,
    old_public_id: str | None = None,
):
    """Upload a receipt and optionally delete the previous one."""
    if file is None:
        return None, None
    if old_public_id:
        with contextlib.suppress(Exception):
            storage.delete(old_public_id)
    result = save_upload(file, storage, folder="transactions")
    return result.get("url"), result.get("public_id")


@router.post(
    "/{event_id}/transactions",
    response_model=ResponseEnvelope[TransactionResponse],
    status_code=status.HTTP_201_CREATED,
)
def add_transaction(
    event_id: int,
    data: str = Form(...),
    receipt: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
    storage: Any = Depends(get_storage),
):
    """Add a transaction to an event."""
    payload = TransactionCreate.model_validate_json(data)

    event = _get_event(db, event_id)
    _require_event_access(db, event, current_user)

    receipt_url, receipt_public_id = _save_receipt(receipt, storage)

    unit_amount = payload.unit_amount or 0
    unit_price = payload.unit_price or Decimal("0.00")
    total = payload.total
    if total is None:
        total = Decimal(unit_amount) * unit_price

    transaction = Transaction(
        events_id=event_id,
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
    "/{event_id}/transactions/{transaction_id}",
    response_model=ResponseEnvelope[TransactionResponse],
    status_code=status.HTTP_200_OK,
)
def update_transaction(
    event_id: int,
    transaction_id: int,
    data: str = Form(...),
    receipt: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
    storage: Any = Depends(get_storage),
):
    """Update a transaction for an event."""
    payload = TransactionUpdate.model_validate_json(data)

    event = _get_event(db, event_id)
    _require_event_access(db, event, current_user)

    transaction = db.query(Transaction).filter_by(transaction_id=transaction_id, events_id=event_id).first()
    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    for field in (
        "transaction_name",
        "type",
    ):
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


@router.post(
    "/{event_id}/invitations",
    response_model=ResponseEnvelope[EventInviteResponse],
    status_code=status.HTTP_201_CREATED,
)
def invite_user(
    event_id: int,
    data: EventInviteRequest,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
    backend: Any = Depends(get_email),
):
    """Invite a user to manage an event by email."""
    event = _get_event(db, event_id)
    _require_event_access(db, event, current_user)

    user = db.query(Users).filter_by(users_email=data.email).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email not found",
        )

    existing_entry = (
        db.query(DepartmentsEvents).filter_by(departments_id=user.users_departments_id, events_id=event_id).first()
    )
    if existing_entry is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user's department is already managing this event",
        )

    existing_invitation = (
        db.query(EventInvitations)
        .filter_by(event_invitations_events_id=event_id, event_invitations_email=data.email)
        .first()
    )
    if existing_invitation is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An invitation has already been sent to this email",
        )

    send_event_invite_email(db, backend, current_user, user, event)

    return ResponseEnvelope(data=EventInviteResponse(message=f"Invitation sent to {data.email}"))


@router.post(
    "/invitations/accept",
    response_model=ResponseEnvelope[EventInviteResponseData],
    status_code=status.HTTP_200_OK,
)
def accept_invite(
    data: EventInviteAccept,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Accept an event invitation by token."""
    from itsdangerous import BadSignature, SignatureExpired

    from api.emails import get_serializer

    s = get_serializer()
    try:
        email = s.loads(data.token, salt="invite-user", max_age=3600)
    except SignatureExpired as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The invitation link has expired",
        ) from err
    except BadSignature as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The invitation link is invalid",
        ) from err

    if email != current_user.users_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to accept this invitation",
        )

    invitation = db.query(EventInvitations).filter_by(event_invitations_token=data.token).first()
    if invitation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )

    existing = (
        db.query(DepartmentsEvents)
        .filter_by(
            departments_id=current_user.users_departments_id,
            events_id=invitation.event_invitations_events_id,
        )
        .first()
    )
    if existing is None:
        db.add(
            DepartmentsEvents(
                departments_id=current_user.users_departments_id,
                events_id=invitation.event_invitations_events_id,
            )
        )

    db.delete(invitation)
    db.commit()

    return ResponseEnvelope(
        data=EventInviteResponseData(
            message="Invitation accepted",
            event_id=invitation.event_invitations_events_id,
        )
    )


@router.post(
    "/invitations/reject",
    response_model=ResponseEnvelope[MessageResponse],
    status_code=status.HTTP_200_OK,
)
def reject_invite(
    data: EventInviteAccept,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Reject an event invitation by token."""
    from itsdangerous import BadSignature, SignatureExpired

    from api.emails import get_serializer

    s = get_serializer()
    try:
        email = s.loads(data.token, salt="invite-user", max_age=3600)
    except SignatureExpired as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The invitation link has expired",
        ) from err
    except BadSignature as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The invitation link is invalid",
        ) from err

    if email != current_user.users_email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to reject this invitation",
        )

    invitation = db.query(EventInvitations).filter_by(event_invitations_token=data.token).first()
    if invitation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )

    db.delete(invitation)
    db.commit()
    return ResponseEnvelope(data=MessageResponse(message="Invitation rejected"))
