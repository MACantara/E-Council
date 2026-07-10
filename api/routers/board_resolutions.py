"""FastAPI board resolution endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies import get_current_user, get_pagination_params, is_admin
from api.schemas.board_resolutions import (
    BoardResolutionAIRequest,
    BoardResolutionAIResponse,
    BoardResolutionCreate,
    BoardResolutionResponse,
    BoardResolutionStatusUpdate,
    BoardResolutionUpdate,
)
from api.schemas.common import (
    MessageResponse,
    PaginatedResponse,
    ResponseEnvelope,
    build_pagination_metadata,
)
from api.services.board_resolutions import generate_board_resolution_pdf
from models import BoardResolutions, DepartmentsEvents, Events, Users
from services.ai import generate_content

router = APIRouter(prefix="/board-resolutions", tags=["board-resolutions"])


def _resolution_access(resolution: BoardResolutions, user: Users) -> bool:
    """Return True if the user can access the board resolution."""
    if is_admin(user):
        return True
    return (
        resolution.board_resolutions_departments_id is not None
        and resolution.board_resolutions_departments_id == user.users_departments_id
    ) or (
        resolution.board_resolutions_prepared_by is not None
        and resolution.board_resolutions_prepared_by == user.users_id
    )


def _require_resolution_access(resolution: BoardResolutions, user: Users) -> None:
    """Raise 403 if the user cannot access the board resolution."""
    if not _resolution_access(resolution, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this board resolution",
        )


def _get_resolution(db: Session, resolution_id: int) -> BoardResolutions:
    """Get a board resolution by ID or raise 404."""
    resolution = db.get(BoardResolutions, resolution_id)
    if resolution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Board resolution not found",
        )
    return resolution


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


def _resolve_event(
    db: Session,
    payload: BoardResolutionCreate | BoardResolutionUpdate,
    current_user: Users,
) -> int | None:
    """Resolve the events_id for the payload, creating a new event if needed."""
    events_id = payload.board_resolutions_events_id
    if events_id is None:
        return None

    if events_id == 0:
        return None

    if events_id == -1 and getattr(payload, "new_event_name", None):
        new_event = Events(
            events_name=payload.new_event_name,
            events_academic_year=payload.board_resolutions_academic_year or "",
            events_semester=payload.board_resolutions_semester or "",
            events_description=payload.board_resolutions_description or "",
        )
        db.add(new_event)
        db.flush()
        events_id = new_event.events_id

        departments_events = DepartmentsEvents(
            departments_id=current_user.users_departments_id,
            events_id=events_id,
        )
        db.add(departments_events)
        db.flush()

    return events_id


def _resolve_academic_year(payload: BoardResolutionCreate | BoardResolutionUpdate) -> str | None:
    """Return the final academic year, handling the 'Other' option."""
    year = payload.board_resolutions_academic_year
    if year == "Other" and getattr(payload, "other_academic_year", None):
        return payload.other_academic_year
    return year


@router.get(
    "",
    response_model=ResponseEnvelope[PaginatedResponse[BoardResolutionResponse]],
    status_code=status.HTTP_200_OK,
)
def list_board_resolutions(
    status: str | None = Query(None),
    search: str | None = Query(None),
    pagination: Any = Depends(get_pagination_params),
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """List board resolutions with pagination, status filtering, and department scoping."""
    query = db.query(BoardResolutions)

    if not is_admin(current_user):
        query = query.filter(
            or_(
                BoardResolutions.board_resolutions_departments_id == current_user.users_departments_id,
                BoardResolutions.board_resolutions_prepared_by == current_user.users_id,
            )
        )

    if status:
        query = query.filter(BoardResolutions.board_resolutions_status == status)

    if search:
        query = query.filter(BoardResolutions.board_resolutions_title.ilike(f"%{search}%"))

    if pagination.sort:
        sort_field = getattr(BoardResolutions, pagination.sort, BoardResolutions.board_resolutions_date)
        query = query.order_by(sort_field.desc() if pagination.order == "desc" else sort_field.asc())
    else:
        query = query.order_by(BoardResolutions.board_resolutions_date.desc())

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
    response_model=ResponseEnvelope[BoardResolutionResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_board_resolution(
    data: BoardResolutionCreate,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Create a new board resolution."""
    events_id = _resolve_event(db, data, current_user)
    academic_year = _resolve_academic_year(data)

    resolution = BoardResolutions(
        board_resolutions_departments_id=current_user.users_departments_id,
        board_resolutions_events_id=events_id,
        board_resolutions_title=data.board_resolutions_title,
        board_resolutions_description=data.board_resolutions_description,
        board_resolutions_total_amount=data.board_resolutions_total_amount,
        board_resolutions_academic_year=academic_year,
        board_resolutions_semester=data.board_resolutions_semester,
        board_resolutions_status=data.board_resolutions_status,
        board_resolutions_date=_parse_datetime(data.board_resolutions_date),
        board_resolutions_prepared_by=data.board_resolutions_prepared_by or current_user.users_id,
        board_resolutions_approved_by=data.board_resolutions_approved_by,
        student_signatory_ids=data.student_signatory_ids or [],
    )

    db.add(resolution)
    db.commit()
    db.refresh(resolution)
    return ResponseEnvelope(data=resolution)


@router.get(
    "/{resolution_id}",
    response_model=ResponseEnvelope[BoardResolutionResponse],
    status_code=status.HTTP_200_OK,
)
def get_board_resolution(
    resolution_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Get a board resolution by ID."""
    resolution = _get_resolution(db, resolution_id)
    _require_resolution_access(resolution, current_user)
    return ResponseEnvelope(data=resolution)


@router.put(
    "/{resolution_id}",
    response_model=ResponseEnvelope[BoardResolutionResponse],
    status_code=status.HTTP_200_OK,
)
def update_board_resolution(
    resolution_id: int,
    data: BoardResolutionUpdate,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Update a board resolution."""
    resolution = _get_resolution(db, resolution_id)
    _require_resolution_access(resolution, current_user)

    if data.board_resolutions_events_id is not None:
        resolution.board_resolutions_events_id = _resolve_event(db, data, current_user)
    if data.board_resolutions_title is not None:
        resolution.board_resolutions_title = data.board_resolutions_title
    if data.board_resolutions_description is not None:
        resolution.board_resolutions_description = data.board_resolutions_description
    if data.board_resolutions_total_amount is not None:
        resolution.board_resolutions_total_amount = data.board_resolutions_total_amount
    if data.board_resolutions_academic_year is not None:
        resolution.board_resolutions_academic_year = _resolve_academic_year(data)
    if data.board_resolutions_semester is not None:
        resolution.board_resolutions_semester = data.board_resolutions_semester
    if data.board_resolutions_status is not None:
        resolution.board_resolutions_status = data.board_resolutions_status
    if data.board_resolutions_date is not None:
        resolution.board_resolutions_date = _parse_datetime(data.board_resolutions_date)
    if data.board_resolutions_prepared_by is not None:
        resolution.board_resolutions_prepared_by = data.board_resolutions_prepared_by
    if data.board_resolutions_approved_by is not None:
        resolution.board_resolutions_approved_by = data.board_resolutions_approved_by
    if data.student_signatory_ids is not None:
        resolution.student_signatory_ids = data.student_signatory_ids

    db.commit()
    db.refresh(resolution)
    return ResponseEnvelope(data=resolution)


@router.delete(
    "/{resolution_id}",
    response_model=ResponseEnvelope[MessageResponse],
    status_code=status.HTTP_200_OK,
)
def delete_board_resolution(
    resolution_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Delete a board resolution."""
    resolution = _get_resolution(db, resolution_id)
    _require_resolution_access(resolution, current_user)

    if resolution.board_resolutions_events_id:
        db.query(DepartmentsEvents).filter_by(events_id=resolution.board_resolutions_events_id).delete()

    db.delete(resolution)
    db.commit()
    return ResponseEnvelope(data=MessageResponse(message="Board resolution deleted"))


@router.put(
    "/{resolution_id}/status",
    response_model=ResponseEnvelope[BoardResolutionResponse],
    status_code=status.HTTP_200_OK,
)
def update_board_resolution_status(
    resolution_id: int,
    data: BoardResolutionStatusUpdate,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Update a board resolution's status."""
    resolution = _get_resolution(db, resolution_id)
    _require_resolution_access(resolution, current_user)
    resolution.board_resolutions_status = data.status
    db.commit()
    db.refresh(resolution)
    return ResponseEnvelope(data=resolution)


@router.post(
    "/generate-description",
    response_model=ResponseEnvelope[BoardResolutionAIResponse],
    status_code=status.HTTP_200_OK,
)
def generate_description(
    data: BoardResolutionAIRequest,
):
    """Generate a board resolution description using the AI service."""
    try:
        if data.date:
            date_obj = datetime.strptime(data.date, "%Y-%m-%dT%H:%M")
            formatted_date = (
                f"Signed this {date_obj.day}th of {date_obj.strftime('%B')} "
                f"in the name of the Lord Jesus Christ {date_obj.year}"
            )
        else:
            formatted_date = "Signed this 13th of May in the name of the Lord Jesus Christ 2024"
    except ValueError:
        formatted_date = "Signed this 13th of May in the name of the Lord Jesus Christ 2024"

    formatted_amount = f"₱{float(data.total_amount):,.2f}" if data.total_amount else "the specified amount"

    prompt = f"""Generate a formal description for a proposed board resolution with the following details:
            Event: {data.event_name}
            Title: {data.title}
            Total Amount: {formatted_amount}

            Requirements:
            1. Use clear, formal language in present tense
            2. Focus only on describing the purpose, scope, and proposed decisions
            3. Keep it concise and straightforward
            4. Do not include any signatories
            5. Do not use any text formatting
            6. Do not include the board resolution title
            7. Do not include any resolution numbers
            8. Do not use 'WHEREAS' statements
            9. Begin with 'The College of Computer Studies Student Council proposes to'
            10. Use language that indicates the resolution is pending approval (e.g., 'seeks to allocate', 'proposes to implement')
            11. Explicitly mention the total amount in the main paragraph using the phrase 'with a proposed budget of {formatted_amount}'
            12. Include a financial breakdown section with the following format:
                Proposed Financial Breakdown:
                [List all relevant expense categories based on the event type and purpose]
                Proposed Total Amount: {formatted_amount}
            13. The description should be 1 paragraph only, followed by the financial breakdown
            14. End with exactly this date: '{formatted_date}'

            Note: Create a comprehensive list of expense categories appropriate for this specific event"""

    result = generate_content(prompt)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error or "AI generation failed",
        )
    return ResponseEnvelope(data=BoardResolutionAIResponse(content=result.data))


@router.get(
    "/{resolution_id}/pdf",
    status_code=status.HTTP_200_OK,
)
def download_board_resolution_pdf(
    resolution_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Generate and download a PDF for a board resolution."""
    resolution = _get_resolution(db, resolution_id)
    _require_resolution_access(resolution, current_user)
    pdf_buffer = generate_board_resolution_pdf(db, resolution, current_user)
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=board_resolution_{resolution_id}.pdf"},
    )
