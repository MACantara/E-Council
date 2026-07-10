"""FastAPI documentation endpoints."""

from __future__ import annotations

import contextlib
from datetime import datetime
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
from api.schemas.documentation import (
    ActivityReportDetails,
    DocumentationCreate,
    DocumentationResponse,
    DocumentationStatusUpdate,
    DocumentationUpdate,
    DownloadUrlResponse,
    FileType,
    FileUploadResponse,
    ImageItem,
    StudentListResponse,
)
from api.services.documentation import generate_documentation_pdf
from models import (
    ActivityReportForms,
    ActivityReportItem,
    Documentation,
    EvaluationForm,
    Events,
    LearningJournalForms,
    Signatories,
    TallyItem,
    Users,
)

router = APIRouter(prefix="/documentation", tags=["documentation"])


# Maps the file type to the documentation image attribute and the storage folder.
_FILE_TYPE_MAP = {
    FileType.evaluation_image: ("evaluation_images", "results_of_the_evaluation_images"),
    FileType.attendance_image: ("attendance_images", "summary_of_attendance_images"),
    FileType.event_photo: ("event_photo_images", "event_photo_documentation_images"),
}

# Lists that should be treated as child objects rather than scalar values.
_CHILD_LIST_FIELDS = {
    "activity_report_items",
    "tally_items",
    "evaluation_forms",
    "evaluation_images",
    "attendance_images",
    "event_photo_images",
    "evaluation_student_names",
    "learning_journal_observations",
    "learning_journal_learnings",
}


def _doc_access(doc: Documentation, user: Users) -> bool:
    """Return True if the user can access the documentation record."""
    if is_admin(user):
        return True
    return (
        doc.documentation_departments_id is not None and doc.documentation_departments_id == user.users_departments_id
    ) or (doc.documentation_prepared_by is not None and doc.documentation_prepared_by == user.users_id)


def _require_doc_access(doc: Documentation, user: Users) -> None:
    """Raise 403 if the user cannot access the documentation record."""
    if not _doc_access(doc, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this documentation",
        )


def _get_doc_or_404(db: Session, doc_id: int) -> Documentation:
    """Retrieve a documentation record by ID or raise 404."""
    doc = (
        db.query(Documentation)
        .options(
            selectinload(Documentation.tally_items),
            selectinload(Documentation.evaluation_forms),
            selectinload(Documentation.activity_report_items),
            selectinload(Documentation.events),
        )
        .filter_by(documentation_id=doc_id)
        .first()
    )
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documentation not found",
        )
    return doc


def _get_doc(db: Session, doc_id: int) -> Documentation:
    """Retrieve a documentation record by ID or raise 404 without eager loading."""
    doc = db.get(Documentation, doc_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documentation not found",
        )
    return doc


def _parse_date(value: Any) -> Any:
    """Coerce a date string into a datetime object if needed."""
    if value is None or isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            try:
                return datetime.strptime(value, "%Y-%m-%d")
            except ValueError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date format. Use ISO datetime or YYYY-MM-DD",
                ) from exc
    return value


def _process_image_uploads(
    files: list[UploadFile] | None,
    storage: Any,
    folder: str,
) -> list[dict[str, Any]]:
    """Upload a list of image files and return dict references."""
    items = []
    if not files:
        return items
    for file in files:
        if file is None or not file.filename:
            continue
        result = save_upload(file, storage, folder=folder, resource_type="auto")
        items.append({"url": result.get("url", ""), "public_id": result.get("public_id", "")})
    return items


def _apply_scalar_fields(
    doc: Documentation,
    payload: DocumentationCreate | DocumentationUpdate,
) -> None:
    """Apply scalar fields from a create or update payload."""
    for field in payload.model_fields:
        if field in _CHILD_LIST_FIELDS:
            continue
        value = getattr(payload, field, None)
        if value is not None:
            if field == "documentation_date_of_submission":
                value = _parse_date(value)
            setattr(doc, field, value)


def _set_child_lists(doc: Documentation, payload: DocumentationCreate) -> None:
    """Create child objects for activity report items, tally items, and forms."""
    for item in payload.activity_report_items:
        doc.activity_report_items.append(ActivityReportItem(item_type=item.item_type, item_text=item.item_text))
    for tally in payload.tally_items:
        doc.tally_items.append(
            TallyItem(
                name=tally.name,
                extremely_satisfied=tally.extremely_satisfied,
                satisfied=tally.satisfied,
                neutral=tally.neutral,
                dissatisfied=tally.dissatisfied,
                extremely_dissatisfied=tally.extremely_dissatisfied,
            )
        )
    for form in payload.evaluation_forms:
        doc.evaluation_forms.append(EvaluationForm(name=form.name, rating=form.rating))
    doc.evaluation_student_names = list(payload.evaluation_student_names)


def _derive_event_fields(doc: Documentation, payload: DocumentationCreate, db: Session) -> None:
    """Derive academic year and semester from the linked event if not provided."""
    if payload.documentation_events_id:
        event = db.get(Events, payload.documentation_events_id)
        if event:
            if not doc.documentation_academic_year and event.events_academic_year:
                doc.documentation_academic_year = event.events_academic_year
            if not doc.documentation_semester and event.events_semester:
                doc.documentation_semester = event.events_semester


def _update_child_lists(doc: Documentation, payload: DocumentationUpdate, db: Session) -> None:
    """Replace child lists when explicitly provided in an update payload."""
    if payload.activity_report_items is not None:
        doc.activity_report_items = [
            ActivityReportItem(item_type=item.item_type, item_text=item.item_text)
            for item in payload.activity_report_items
        ]
    if payload.tally_items is not None:
        doc.tally_items = [
            TallyItem(
                name=tally.name,
                extremely_satisfied=tally.extremely_satisfied,
                satisfied=tally.satisfied,
                neutral=tally.neutral,
                dissatisfied=tally.dissatisfied,
                extremely_dissatisfied=tally.extremely_dissatisfied,
            )
            for tally in payload.tally_items
        ]
    if payload.evaluation_forms is not None:
        doc.evaluation_forms = [EvaluationForm(name=form.name, rating=form.rating) for form in payload.evaluation_forms]
    if payload.evaluation_student_names is not None:
        doc.evaluation_student_names = list(payload.evaluation_student_names)

    # Update linked learning journal observations/learnings if provided.
    learning_journal_id = payload.documentation_learning_journal_forms_id or doc.documentation_learning_journal_forms_id
    if learning_journal_id:
        learning_journal = db.get(LearningJournalForms, learning_journal_id)
        if learning_journal:
            if payload.learning_journal_observations is not None:
                learning_journal.observations = list(payload.learning_journal_observations)
            if payload.learning_journal_learnings is not None:
                learning_journal.learnings = list(payload.learning_journal_learnings)


def _update_image_lists(
    doc: Documentation,
    payload: DocumentationUpdate,
    evaluation_images: list[UploadFile] | None,
    attendance_images: list[UploadFile] | None,
    event_photo_images: list[UploadFile] | None,
    storage: Any,
) -> None:
    """Replace image lists from payload and append newly uploaded images."""
    image_inputs = [
        ("evaluation_images", evaluation_images, "results_of_the_evaluation_images"),
        ("attendance_images", attendance_images, "summary_of_attendance_images"),
        ("event_photo_images", event_photo_images, "event_photo_documentation_images"),
    ]
    for attr, files, folder in image_inputs:
        payload_list = getattr(payload, attr)
        if payload_list is not None:
            setattr(doc, attr, [item.model_dump() for item in payload_list])
        if files:
            existing = getattr(doc, attr) or []
            existing.extend(_process_image_uploads(files, storage, folder))
            setattr(doc, attr, existing)


def _update_from_json(
    doc: Documentation,
    data: str,
    evaluation_images: list[UploadFile] | None,
    attendance_images: list[UploadFile] | None,
    event_photo_images: list[UploadFile] | None,
    storage: Any,
    db: Session,
) -> None:
    """Apply an update from a JSON string and any uploaded image files."""
    payload = DocumentationUpdate.model_validate_json(data)
    _apply_scalar_fields(doc, payload)
    _update_child_lists(doc, payload, db)
    _update_image_lists(
        doc,
        payload,
        evaluation_images,
        attendance_images,
        event_photo_images,
        storage,
    )


def _delete_document_images(doc: Documentation, storage: Any) -> None:
    """Best-effort deletion of all stored images associated with a document."""
    for attr in ("evaluation_images", "attendance_images", "event_photo_images"):
        for image in getattr(doc, attr) or []:
            public_id = image.get("public_id") if isinstance(image, dict) else image.public_id
            if public_id:
                with contextlib.suppress(Exception):
                    storage.delete(public_id, resource_type="image")


def _find_image(doc: Documentation, public_id: str) -> dict[str, Any] | None:
    """Return the image dict with the given public_id if it belongs to the document."""
    for attr in ("evaluation_images", "attendance_images", "event_photo_images"):
        for image in getattr(doc, attr) or []:
            if isinstance(image, dict):
                if image.get("public_id") == public_id:
                    return image
            elif image.public_id == public_id:
                return {"url": image.url, "public_id": image.public_id}
    return None


@router.get(
    "",
    response_model=ResponseEnvelope[PaginatedResponse[DocumentationResponse]],
    status_code=status.HTTP_200_OK,
)
def list_documentation(
    status: str | None = Query(None),
    type: str | None = Query(None),
    search: str | None = Query(None),
    pagination: Any = Depends(get_pagination_params),
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """List documentation records with pagination, filtering, and department scoping."""
    query = db.query(Documentation).options(
        selectinload(Documentation.tally_items),
        selectinload(Documentation.evaluation_forms),
        selectinload(Documentation.activity_report_items),
        selectinload(Documentation.events),
    )

    if not is_admin(current_user):
        query = query.filter(
            or_(
                Documentation.documentation_departments_id == current_user.users_departments_id,
                Documentation.documentation_prepared_by == current_user.users_id,
            )
        )

    if status:
        query = query.filter(Documentation.documentation_status == status)
    if type:
        query = query.filter(Documentation.documentation_type == type)
    if search:
        query = query.filter(
            or_(
                Documentation.documentation_type.ilike(f"%{search}%"),
                Documentation.documentation_comments_suggestions.ilike(f"%{search}%"),
            )
        )

    if pagination.sort:
        sort_field = getattr(Documentation, pagination.sort, Documentation.documentation_date_of_submission)
        query = query.order_by(sort_field.desc() if pagination.order == "desc" else sort_field.asc())
    else:
        query = query.order_by(
            Documentation.documentation_academic_year.desc(),
            Documentation.documentation_semester.desc(),
            Documentation.documentation_date_of_submission.desc(),
        )

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
    response_model=ResponseEnvelope[DocumentationResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_documentation(
    data: str = Form(...),
    evaluation_images: list[UploadFile] | None = File(None),
    attendance_images: list[UploadFile] | None = File(None),
    event_photo_images: list[UploadFile] | None = File(None),
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
    storage: Any = Depends(get_storage),
):
    """Create a new documentation record with optional image uploads."""
    payload = DocumentationCreate.model_validate_json(data)

    doc = Documentation(
        documentation_departments_id=current_user.users_departments_id,
        documentation_prepared_by=current_user.users_id,
    )
    _apply_scalar_fields(doc, payload)
    _derive_event_fields(doc, payload, db)

    # Upload and attach image files.
    doc.evaluation_images = _process_image_uploads(evaluation_images, storage, "results_of_the_evaluation_images")
    doc.attendance_images = _process_image_uploads(attendance_images, storage, "summary_of_attendance_images")
    doc.event_photo_images = _process_image_uploads(event_photo_images, storage, "event_photo_documentation_images")

    # If the JSON payload also contained image references, merge them.
    if payload.evaluation_images:
        doc.evaluation_images.extend(item.model_dump() for item in payload.evaluation_images)
    if payload.attendance_images:
        doc.attendance_images.extend(item.model_dump() for item in payload.attendance_images)
    if payload.event_photo_images:
        doc.event_photo_images.extend(item.model_dump() for item in payload.event_photo_images)

    _set_child_lists(doc, payload)

    db.add(doc)
    db.flush()

    # Update linked learning journal observations/learnings if requested.
    if payload.documentation_learning_journal_forms_id:
        learning_journal = db.get(LearningJournalForms, payload.documentation_learning_journal_forms_id)
        if learning_journal:
            if payload.learning_journal_observations:
                learning_journal.observations = list(payload.learning_journal_observations)
            if payload.learning_journal_learnings:
                learning_journal.learnings = list(payload.learning_journal_learnings)

    db.commit()
    db.refresh(doc)
    return ResponseEnvelope(data=doc)


@router.get(
    "/{doc_id}",
    response_model=ResponseEnvelope[DocumentationResponse],
    status_code=status.HTTP_200_OK,
)
def get_documentation(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Get a single documentation record by ID."""
    doc = _get_doc_or_404(db, doc_id)
    _require_doc_access(doc, current_user)
    return ResponseEnvelope(data=doc)


@router.put(
    "/{doc_id}",
    response_model=ResponseEnvelope[DocumentationResponse],
    status_code=status.HTTP_200_OK,
)
def update_documentation(
    doc_id: int,
    data: str = Form(...),
    evaluation_images: list[UploadFile] | None = File(None),
    attendance_images: list[UploadFile] | None = File(None),
    event_photo_images: list[UploadFile] | None = File(None),
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
    storage: Any = Depends(get_storage),
):
    """Update a documentation record and its associated image lists."""
    doc = _get_doc_or_404(db, doc_id)
    _require_doc_access(doc, current_user)
    _update_from_json(doc, data, evaluation_images, attendance_images, event_photo_images, storage, db)
    db.commit()
    db.refresh(doc)
    return ResponseEnvelope(data=doc)


@router.put(
    "/{doc_id}/status",
    response_model=ResponseEnvelope[DocumentationResponse],
    status_code=status.HTTP_200_OK,
)
def update_documentation_status(
    doc_id: int,
    payload: DocumentationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Update a documentation record's status."""
    doc = _get_doc(db, doc_id)
    _require_doc_access(doc, current_user)
    doc.documentation_status = payload.status
    db.commit()
    db.refresh(doc)
    return ResponseEnvelope(data=doc)


@router.delete(
    "/{doc_id}",
    response_model=ResponseEnvelope[MessageResponse],
    status_code=status.HTTP_200_OK,
)
def delete_documentation(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
    storage: Any = Depends(get_storage),
):
    """Delete a documentation record and its associated images."""
    doc = _get_doc_or_404(db, doc_id)
    _require_doc_access(doc, current_user)
    _delete_document_images(doc, storage)
    db.delete(doc)
    db.commit()
    return ResponseEnvelope(data=MessageResponse(message="Documentation deleted"))


@router.get(
    "/{doc_id}/pdf",
    status_code=status.HTTP_200_OK,
)
def download_documentation_pdf(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Generate and download a PDF for a documentation record."""
    doc = _get_doc_or_404(db, doc_id)
    _require_doc_access(doc, current_user)
    pdf_buffer = generate_documentation_pdf(db, doc, current_user)
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=documentation-{doc_id}.pdf"},
    )


@router.post(
    "/{doc_id}/files",
    response_model=ResponseEnvelope[FileUploadResponse],
    status_code=status.HTTP_201_CREATED,
)
def upload_documentation_file(
    doc_id: int,
    file_type: FileType,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
    storage: Any = Depends(get_storage),
):
    """Upload a single file and attach it to a documentation record."""
    doc = _get_doc_or_404(db, doc_id)
    _require_doc_access(doc, current_user)

    attr, folder = _FILE_TYPE_MAP[file_type]
    result = save_upload(file, storage, folder=folder, resource_type="auto")
    image_dict = {"url": result.get("url", ""), "public_id": result.get("public_id", "")}
    image = ImageItem.model_validate(image_dict)

    existing = getattr(doc, attr) or []
    existing.append(image_dict)
    setattr(doc, attr, existing)

    db.commit()
    db.refresh(doc)
    return ResponseEnvelope(data=FileUploadResponse(file=image))


@router.get(
    "/{doc_id}/files/{public_id:path}",
    response_model=ResponseEnvelope[DownloadUrlResponse],
    status_code=status.HTTP_200_OK,
)
def download_documentation_file(
    doc_id: int,
    public_id: str,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
    storage: Any = Depends(get_storage),
):
    """Return a download URL for a stored documentation file."""
    doc = _get_doc_or_404(db, doc_id)
    _require_doc_access(doc, current_user)

    image = _find_image(doc, public_id)
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found for this documentation record",
        )

    url = storage.get_url(public_id)
    if not url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File URL not available",
        )

    is_direct = url.startswith("http") or url.startswith("/")
    return ResponseEnvelope(data=DownloadUrlResponse(download_url=url, is_direct=is_direct))


@router.get(
    "/related-forms/{event_id}",
    response_model=ResponseEnvelope[dict],
    status_code=status.HTTP_200_OK,
)
def get_related_forms(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Return activity report forms, learning journal forms, and signatories for an event."""
    event = db.get(Events, event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    concept_paper_id = event.events_concept_paper_forms_id
    activity_reports = (
        (
            db.query(ActivityReportForms)
            .filter(ActivityReportForms.activity_report_forms_concept_paper_forms_id == concept_paper_id)
            .all()
        )
        if concept_paper_id
        else []
    )

    learning_journals = (
        (
            db.query(LearningJournalForms)
            .filter(LearningJournalForms.learning_journal_forms_concept_paper_forms_id == concept_paper_id)
            .all()
        )
        if concept_paper_id
        else []
    )

    checked_by_ids = {
        journal.learning_journal_forms_checked_by
        for journal in learning_journals
        if journal.learning_journal_forms_checked_by
    }
    signatories = (
        (db.query(Signatories).filter(Signatories.signatory_id.in_(checked_by_ids)).all()) if checked_by_ids else []
    )

    return ResponseEnvelope(
        data={
            "activity_reports": [
                {
                    "activity_report_forms_id": report.activity_report_forms_id,
                    "events_name": report.concept_paper_form.concept_paper_forms_subject
                    if report.concept_paper_form
                    else None,
                }
                for report in activity_reports
            ],
            "learning_journals": [
                {
                    "learning_journal_forms_id": journal.learning_journal_forms_id,
                    "events_name": journal.concept_paper_form.concept_paper_forms_subject
                    if journal.concept_paper_form
                    else None,
                    "learning_journal_forms_checked_by": journal.learning_journal_forms_checked_by,
                }
                for journal in learning_journals
            ],
            "signatories": [
                {
                    "signatory_id": signatory.signatory_id,
                    "signatory_first_name": signatory.signatory_first_name,
                    "signatory_last_name": signatory.signatory_last_name,
                    "signatory_position": signatory.signatory_position,
                    "signatory_department": signatory.signatory_department,
                }
                for signatory in signatories
            ],
        }
    )


@router.get(
    "/activity-report/{activity_report_id}/details",
    response_model=ResponseEnvelope[ActivityReportDetails],
    status_code=status.HTTP_200_OK,
)
def get_activity_report_details(
    activity_report_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Return the strengths, weaknesses, and recommendations for an activity report."""
    activity_report = db.get(ActivityReportForms, activity_report_id)
    if activity_report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity report not found",
        )

    items = db.query(ActivityReportItem).filter_by(activity_report_forms_id=activity_report_id).all()

    strengths = [{"activity_strengths_content": item.item_text} for item in items if item.item_type == "strength"]
    weaknesses = [{"activity_weaknesses_content": item.item_text} for item in items if item.item_type == "weakness"]
    recommendations = [
        {"activity_recommendations_content": item.item_text} for item in items if item.item_type == "recommendation"
    ]

    return ResponseEnvelope(
        data=ActivityReportDetails(
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
        )
    )


@router.post(
    "/process-student-excel",
    response_model=ResponseEnvelope[StudentListResponse],
    status_code=status.HTTP_200_OK,
)
def process_student_excel(
    file: UploadFile = File(...),
    current_user: Users = Depends(get_current_user),
):
    """Parse a student list Excel file and return the names found."""
    if not file.filename or not file.filename.endswith(".xlsx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please upload an Excel (.xlsx) file",
        )

    try:
        import pandas as pd
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="pandas is not available for Excel processing",
        ) from exc

    try:
        df = pd.read_excel(file.file)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read Excel file: {exc}",
        ) from exc

    name_column = None
    for col in df.columns:
        if "full name" in str(col).lower():
            name_column = col
            break

    if name_column is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='No column containing "full name" found',
        )

    student_names = df[name_column].dropna().astype(str).tolist()
    return ResponseEnvelope(data=StudentListResponse(students=student_names))
