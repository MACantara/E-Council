"""FastAPI meeting endpoints."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload
from starlette.responses import StreamingResponse

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
from api.schemas.meetings import (
    MeetingAgendaUpdate,
    MeetingAttendeeCreate,
    MeetingAttendeeResponse,
    MeetingAttendeeUpdate,
    MeetingCreate,
    MeetingMinutesUpdate,
    MeetingResponse,
    MeetingStatusUpdate,
    MeetingUpdate,
)
from models import MeetingAttendee, MinutesOfTheMeeting, Users

router = APIRouter(prefix="/meetings", tags=["meetings"])


def _meeting_access(meeting: MinutesOfTheMeeting, user: Users) -> bool:
    """Return True if the user can access the meeting."""
    if is_admin(user):
        return True
    return (
        meeting.minutes_of_the_meeting_departments_id is not None
        and meeting.minutes_of_the_meeting_departments_id == user.users_departments_id
    ) or (
        meeting.minutes_of_the_meeting_prepared_by is not None
        and meeting.minutes_of_the_meeting_prepared_by == user.users_id
    )


def _require_meeting_access(meeting: MinutesOfTheMeeting, user: Users) -> None:
    """Raise 403 if the user cannot access the meeting."""
    if not _meeting_access(meeting, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this meeting",
        )


def _get_meeting(db: Session, meeting_id: int) -> MinutesOfTheMeeting:
    """Get a meeting by ID or raise 404."""
    meeting = db.get(MinutesOfTheMeeting, meeting_id)
    if meeting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )
    return meeting


def _get_meeting_or_404(db: Session, meeting_id: int) -> MinutesOfTheMeeting:
    """Get a meeting with attendees eagerly loaded or raise 404."""
    meeting = (
        db.query(MinutesOfTheMeeting)
        .options(selectinload(MinutesOfTheMeeting.attendees).selectinload(MeetingAttendee.user))
        .filter_by(minutes_of_the_meeting_id=meeting_id)
        .first()
    )
    if meeting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )
    return meeting


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


@router.get(
    "",
    response_model=ResponseEnvelope[PaginatedResponse[MeetingResponse]],
    status_code=status.HTTP_200_OK,
)
def list_meetings(
    status: str | None = Query(None),
    search: str | None = Query(None),
    pagination: Any = Depends(get_pagination_params),
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """List meetings with pagination, status filtering, and department scoping."""
    query = db.query(MinutesOfTheMeeting)

    if not is_admin(current_user):
        query = query.filter(
            or_(
                MinutesOfTheMeeting.minutes_of_the_meeting_departments_id == current_user.users_departments_id,
                MinutesOfTheMeeting.minutes_of_the_meeting_prepared_by == current_user.users_id,
            )
        )

    if status:
        query = query.filter(MinutesOfTheMeeting.minutes_of_the_meeting_status == status)

    if search:
        query = query.filter(MinutesOfTheMeeting.minutes_of_the_meeting_agenda.ilike(f"%{search}%"))

    if pagination.sort:
        sort_field = getattr(MinutesOfTheMeeting, pagination.sort, MinutesOfTheMeeting.minutes_of_the_meeting_date)
        query = query.order_by(sort_field.desc() if pagination.order == "desc" else sort_field.asc())
    else:
        query = query.order_by(MinutesOfTheMeeting.minutes_of_the_meeting_date.desc())

    total = query.count()
    items = query.offset((pagination.page - 1) * pagination.per_page).limit(pagination.per_page).all()

    return ResponseEnvelope(
        data=PaginatedResponse(
            items=items,
            pagination=build_pagination_metadata(total=total, page=pagination.page, per_page=pagination.per_page),
        )
    )


def _process_photos(
    photos: list[UploadFile] | None,
    storage: Any,
    existing_photos: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """Upload new photos and optionally delete existing ones."""
    new_photos = []
    if photos:
        for photo in photos:
            if photo:
                result = save_upload(photo, storage, folder="meeting_photos")
                new_photos.append({"url": result.get("url"), "public_id": result.get("public_id")})
    if existing_photos:
        for photo in existing_photos:
            try:
                if photo.get("public_id"):
                    storage.delete(photo["public_id"])
            except Exception:
                pass
    return new_photos


@router.post(
    "",
    response_model=ResponseEnvelope[MeetingResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_meeting(
    data: str = Form(...),
    photos: list[UploadFile] | None = File(None),
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
    storage: Any = Depends(get_storage),
):
    """Create a new meeting."""
    payload = MeetingCreate.model_validate_json(data)

    academic_year = payload.minutes_of_the_meeting_academic_year
    if academic_year == "Other" and payload.other_academic_year:
        academic_year = payload.other_academic_year

    meeting = MinutesOfTheMeeting(
        minutes_of_the_meeting_date=_parse_datetime(payload.minutes_of_the_meeting_date),
        minutes_of_the_meeting_semester=payload.minutes_of_the_meeting_semester,
        minutes_of_the_meeting_academic_year=academic_year,
        minutes_of_the_meeting_status=payload.minutes_of_the_meeting_status,
        minutes_of_the_meeting_departments_id=current_user.users_departments_id,
        minutes_of_the_meeting_presiding_officer=str(payload.minutes_of_the_meeting_presiding_officer),
        minutes_of_the_meeting_agenda=payload.minutes_of_the_meeting_agenda,
        minutes_of_the_meeting_notes=payload.minutes_of_the_meeting_notes,
        minutes_of_the_meeting_adjourned=_parse_datetime(payload.minutes_of_the_meeting_adjourned),
        minutes_of_the_meeting_approved_by=payload.minutes_of_the_meeting_approved_by,
        minutes_of_the_meeting_prepared_by=current_user.users_id,
        minutes_of_the_meeting_noted_by=payload.minutes_of_the_meeting_noted_by,
    )

    if payload.attendees:
        meeting.attendees = [MeetingAttendee(users_id=int(user_id), attended=True) for user_id in payload.attendees]

    db.add(meeting)
    db.flush()

    if photos:
        meeting.photo_documentation = _process_photos(photos, storage, None)

    db.commit()
    db.refresh(meeting)
    return ResponseEnvelope(data=meeting)


@router.get(
    "/{meeting_id}",
    response_model=ResponseEnvelope[MeetingResponse],
    status_code=status.HTTP_200_OK,
)
def get_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Get a meeting by ID."""
    meeting = _get_meeting_or_404(db, meeting_id)
    _require_meeting_access(meeting, current_user)
    return ResponseEnvelope(data=meeting)


@router.put(
    "/{meeting_id}",
    response_model=ResponseEnvelope[MeetingResponse],
    status_code=status.HTTP_200_OK,
)
def update_meeting(
    meeting_id: int,
    data: str = Form(...),
    photos: list[UploadFile] | None = File(None),
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
    storage: Any = Depends(get_storage),
):
    """Update a meeting."""
    payload = MeetingUpdate.model_validate_json(data)
    meeting = _get_meeting_or_404(db, meeting_id)
    _require_meeting_access(meeting, current_user)

    if payload.minutes_of_the_meeting_date is not None:
        meeting.minutes_of_the_meeting_date = _parse_datetime(payload.minutes_of_the_meeting_date)
    if payload.minutes_of_the_meeting_semester is not None:
        meeting.minutes_of_the_meeting_semester = payload.minutes_of_the_meeting_semester
    if payload.minutes_of_the_meeting_academic_year is not None:
        academic_year = payload.minutes_of_the_meeting_academic_year
        if academic_year == "Other" and payload.other_academic_year:
            academic_year = payload.other_academic_year
        meeting.minutes_of_the_meeting_academic_year = academic_year
    if payload.minutes_of_the_meeting_status is not None:
        meeting.minutes_of_the_meeting_status = payload.minutes_of_the_meeting_status
    if payload.minutes_of_the_meeting_presiding_officer is not None:
        meeting.minutes_of_the_meeting_presiding_officer = str(payload.minutes_of_the_meeting_presiding_officer)
    if payload.minutes_of_the_meeting_agenda is not None:
        meeting.minutes_of_the_meeting_agenda = payload.minutes_of_the_meeting_agenda
    if payload.minutes_of_the_meeting_notes is not None:
        meeting.minutes_of_the_meeting_notes = payload.minutes_of_the_meeting_notes
    if payload.minutes_of_the_meeting_adjourned is not None:
        meeting.minutes_of_the_meeting_adjourned = _parse_datetime(payload.minutes_of_the_meeting_adjourned)
    if payload.minutes_of_the_meeting_approved_by is not None:
        meeting.minutes_of_the_meeting_approved_by = payload.minutes_of_the_meeting_approved_by
    if payload.minutes_of_the_meeting_noted_by is not None:
        meeting.minutes_of_the_meeting_noted_by = payload.minutes_of_the_meeting_noted_by

    if payload.attendees is not None:
        meeting.attendees = [MeetingAttendee(users_id=int(user_id), attended=True) for user_id in payload.attendees]

    if photos:
        meeting.photo_documentation = _process_photos(photos, storage, meeting.photo_documentation)

    db.commit()
    db.refresh(meeting)
    return ResponseEnvelope(data=meeting)


@router.delete(
    "/{meeting_id}",
    response_model=ResponseEnvelope[MessageResponse],
    status_code=status.HTTP_200_OK,
)
def delete_meeting(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Delete a meeting."""
    meeting = _get_meeting_or_404(db, meeting_id)
    _require_meeting_access(meeting, current_user)

    for photo in meeting.photo_documentation or []:
        try:
            storage = get_storage()
            if photo.get("public_id"):
                storage.delete(photo["public_id"])
        except Exception:
            pass

    db.delete(meeting)
    db.commit()
    return ResponseEnvelope(data=MessageResponse(message="Meeting deleted"))


@router.put(
    "/{meeting_id}/status",
    response_model=ResponseEnvelope[MeetingResponse],
    status_code=status.HTTP_200_OK,
)
def update_meeting_status(
    meeting_id: int,
    data: MeetingStatusUpdate,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Update a meeting's status."""
    meeting = _get_meeting_or_404(db, meeting_id)
    _require_meeting_access(meeting, current_user)
    meeting.minutes_of_the_meeting_status = data.status
    db.commit()
    db.refresh(meeting)
    return ResponseEnvelope(data=meeting)


@router.put(
    "/{meeting_id}/agenda",
    response_model=ResponseEnvelope[MeetingResponse],
    status_code=status.HTTP_200_OK,
)
def update_meeting_agenda(
    meeting_id: int,
    data: MeetingAgendaUpdate,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Update a meeting's agenda."""
    meeting = _get_meeting_or_404(db, meeting_id)
    _require_meeting_access(meeting, current_user)
    meeting.minutes_of_the_meeting_agenda = data.agenda
    db.commit()
    db.refresh(meeting)
    return ResponseEnvelope(data=meeting)


@router.put(
    "/{meeting_id}/minutes",
    response_model=ResponseEnvelope[MeetingResponse],
    status_code=status.HTTP_200_OK,
)
def update_meeting_minutes(
    meeting_id: int,
    data: MeetingMinutesUpdate,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Update a meeting's minutes/notes."""
    meeting = _get_meeting_or_404(db, meeting_id)
    _require_meeting_access(meeting, current_user)
    meeting.minutes_of_the_meeting_notes = data.minutes
    db.commit()
    db.refresh(meeting)
    return ResponseEnvelope(data=meeting)


@router.post(
    "/{meeting_id}/attendees",
    response_model=ResponseEnvelope[MeetingAttendeeResponse],
    status_code=status.HTTP_201_CREATED,
)
def add_meeting_attendee(
    meeting_id: int,
    data: MeetingAttendeeCreate,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Add an attendee to a meeting."""
    meeting = _get_meeting(db, meeting_id)
    _require_meeting_access(meeting, current_user)

    if db.get(Users, data.users_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    attendee = MeetingAttendee(
        minutes_of_the_meeting_id=meeting_id,
        users_id=data.users_id,
        attended=data.attended,
    )
    db.add(attendee)
    db.commit()
    db.refresh(attendee)
    return ResponseEnvelope(data=attendee)


@router.put(
    "/{meeting_id}/attendees/{attendee_id}/attendance",
    response_model=ResponseEnvelope[MeetingAttendeeResponse],
    status_code=status.HTTP_200_OK,
)
def mark_attendance(
    meeting_id: int,
    attendee_id: int,
    data: MeetingAttendeeUpdate,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Mark an attendee's attendance for a meeting."""
    meeting = _get_meeting(db, meeting_id)
    _require_meeting_access(meeting, current_user)

    attendee = (
        db.query(MeetingAttendee)
        .filter_by(meeting_attendee_id=attendee_id, minutes_of_the_meeting_id=meeting_id)
        .first()
    )
    if attendee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendee not found",
        )

    attendee.attended = data.attended
    db.commit()
    db.refresh(attendee)
    return ResponseEnvelope(data=attendee)


@router.delete(
    "/{meeting_id}/attendees/{attendee_id}",
    response_model=ResponseEnvelope[MessageResponse],
    status_code=status.HTTP_200_OK,
)
def remove_meeting_attendee(
    meeting_id: int,
    attendee_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Remove an attendee from a meeting."""
    meeting = _get_meeting(db, meeting_id)
    _require_meeting_access(meeting, current_user)

    attendee = (
        db.query(MeetingAttendee)
        .filter_by(meeting_attendee_id=attendee_id, minutes_of_the_meeting_id=meeting_id)
        .first()
    )
    if attendee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendee not found",
        )

    db.delete(attendee)
    db.commit()
    return ResponseEnvelope(data=MessageResponse(message="Attendee removed"))


@router.get(
    "/{meeting_id}/pdf",
    status_code=status.HTTP_200_OK,
)
def generate_meeting_pdf(
    meeting_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Generate a simple PDF for the meeting minutes."""
    meeting = _get_meeting_or_404(db, meeting_id)
    _require_meeting_access(meeting, current_user)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=18,
        alignment=1,
        spaceAfter=20,
    )
    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontSize=12,
        spaceAfter=10,
    )
    normal_style = ParagraphStyle(
        "Normal",
        parent=styles["Normal"],
        fontSize=11,
        leading=14,
        spaceAfter=10,
    )

    story = []
    story.append(Paragraph("Minutes of the Meeting", title_style))
    story.append(Spacer(1, 12))

    def _fmt(value):
        return value.strftime("%B %d, %Y %I:%M %p") if value else ""

    details = [
        f"Date: {_fmt(meeting.minutes_of_the_meeting_date)}",
        f"Semester: {meeting.minutes_of_the_meeting_semester}",
        f"Academic Year: {meeting.minutes_of_the_meeting_academic_year}",
        f"Status: {meeting.minutes_of_the_meeting_status}",
        f"Presiding Officer: {meeting.minutes_of_the_meeting_presiding_officer}",
    ]
    for detail in details:
        story.append(Paragraph(detail, normal_style))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Agenda", heading_style))
    for line in (meeting.minutes_of_the_meeting_agenda or "").split("\n"):
        if line.strip():
            story.append(Paragraph(line.strip(), normal_style))
    story.append(Spacer(1, 12))

    if meeting.minutes_of_the_meeting_notes:
        story.append(Paragraph("Minutes", heading_style))
        for line in meeting.minutes_of_the_meeting_notes.split("\n"):
            if line.strip():
                story.append(Paragraph(line.strip(), normal_style))

    if meeting.attendees:
        story.append(Paragraph("Attendees", heading_style))
        for attendee in meeting.attendees:
            name = f"{attendee.user.users_first_name} {attendee.user.users_last_name}" if attendee.user else "Unknown"
            attended = " (present)" if attendee.attended else " (absent)"
            story.append(Paragraph(f"• {name}{attended}", normal_style))

    doc.build(story)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=meeting-{meeting_id}.pdf"},
    )
