"""FastAPI concept paper endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from api.database import get_db
from api.dependencies import get_current_user, get_pagination_params, is_admin
from api.schemas.common import (
    MessageResponse,
    PaginatedResponse,
    ResponseEnvelope,
    build_pagination_metadata,
)
from api.schemas.concept_papers import (
    ConceptPaperAIRequestBody,
    ConceptPaperAIResponse,
    ConceptPaperAITextRequest,
    ConceptPaperCreate,
    ConceptPaperResponse,
    ConceptPaperStatusUpdate,
    ConceptPaperUpdate,
)
from api.services.concept_papers import generate_concept_paper_pdf
from models import (
    ActivityReportForms,
    ActivityReportItem,
    ConceptPaperForms,
    ExcuseLetterForms,
    LearningJournalForms,
    LearningOutcome,
    Objective,
    ParentGuardianConsentForms,
    PersonnelInChargeForms,
    Users,
)

router = APIRouter(prefix="/concept-papers", tags=["concept-papers"])


def _require_concept_paper_access(paper: ConceptPaperForms, current_user: Users) -> None:
    """Raise 403 if the user cannot access the concept paper."""
    if is_admin(current_user):
        return
    if (
        paper.concept_paper_forms_departments_id is not None
        and paper.concept_paper_forms_departments_id == current_user.users_departments_id
    ):
        return
    if (
        paper.concept_paper_forms_prepared_by is not None
        and paper.concept_paper_forms_prepared_by == current_user.users_id
    ):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to access this concept paper",
    )


def _get_paper(db: Session, paper_id: int) -> ConceptPaperForms:
    """Retrieve a concept paper by ID or raise 404."""
    paper = db.get(ConceptPaperForms, paper_id)
    if paper is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Concept paper not found",
        )
    return paper


def _paper_query(db: Session) -> Any:
    """Return a query with all concept paper relationships eagerly loaded."""
    return db.query(ConceptPaperForms).options(
        selectinload(ConceptPaperForms.objectives),
        selectinload(ConceptPaperForms.learning_outcomes),
        selectinload(ConceptPaperForms.activity_report_forms).selectinload(ActivityReportForms.activity_report_items),
        selectinload(ConceptPaperForms.excuse_letter_forms),
        selectinload(ConceptPaperForms.learning_journal_forms),
        selectinload(ConceptPaperForms.parent_guardian_consent_forms),
    )


def _set_paper_attributes(paper: ConceptPaperForms, data: ConceptPaperCreate | ConceptPaperUpdate) -> None:
    """Apply scalar concept paper fields from the request data."""
    for field in ConceptPaperUpdate.model_fields:
        if field in {
            "objectives",
            "learning_outcomes",
            "activity_report",
            "personnel_in_charge",
            "excuse_letter",
            "learning_journal",
            "parent_guardian_consent",
        }:
            continue
        value = getattr(data, field, None)
        if value is not None:
            setattr(paper, field, value)


def _create_personnel_in_charge(db: Session, data: Any) -> PersonnelInChargeForms | None:
    """Create a personnel in charge record from the provided data."""
    if data is None:
        return None
    record = PersonnelInChargeForms(
        personnel_in_charge_forms_name=data.personnel_in_charge_forms_name,
        personnel_in_charge_forms_position=data.personnel_in_charge_forms_position,
        personnel_in_charge_forms_department=data.personnel_in_charge_forms_department,
        personnel_in_charge_forms_contact_number=data.personnel_in_charge_forms_contact_number,
    )
    db.add(record)
    db.flush()
    return record


def _create_or_update_activity_report(
    db: Session, paper: ConceptPaperForms, data: Any, personnel_id: int | None
) -> None:
    """Create or update the activity report form for a concept paper."""
    if data is None:
        return
    existing = (
        db.query(ActivityReportForms)
        .filter_by(activity_report_forms_concept_paper_forms_id=paper.concept_paper_forms_id)
        .first()
    )
    if existing:
        existing.activity_report_forms_nature_of_the_activity = data.activity_report_forms_nature_of_the_activity
        existing.activity_report_forms_contact_numbers = data.activity_report_forms_contact_numbers
        existing.activity_report_forms_prepared_by = data.activity_report_forms_prepared_by
        existing.activity_report_forms_noted_by = data.activity_report_forms_noted_by
        existing.activity_report_date_submission = data.activity_report_date_submission
        db.query(ActivityReportItem).filter_by(activity_report_forms_id=existing.activity_report_forms_id).delete()
        items = data.activity_report_items or []
    else:
        existing = ActivityReportForms(
            activity_report_forms_concept_paper_forms_id=paper.concept_paper_forms_id,
            activity_report_forms_nature_of_the_activity=data.activity_report_forms_nature_of_the_activity,
            activity_report_forms_contact_numbers=data.activity_report_forms_contact_numbers,
            activity_report_forms_prepared_by=data.activity_report_forms_prepared_by,
            activity_report_forms_noted_by=data.activity_report_forms_noted_by,
            activity_report_date_submission=data.activity_report_date_submission,
        )
        db.add(existing)
        db.flush()
        items = data.activity_report_items or []

    for item in items:
        db.add(
            ActivityReportItem(
                activity_report_forms_id=existing.activity_report_forms_id,
                item_type=item.item_type,
                item_text=item.item_text,
            )
        )

    if personnel_id is not None:
        existing.activity_report_forms_personnel_in_charge_forms_id = personnel_id


def _create_or_update_excuse_letter(db: Session, paper: ConceptPaperForms, data: Any, personnel_id: int | None) -> None:
    """Create or update the excuse letter form for a concept paper."""
    if data is None:
        return
    existing = (
        db.query(ExcuseLetterForms)
        .filter_by(excuse_letter_forms_concept_paper_forms_id=paper.concept_paper_forms_id)
        .first()
    )
    if existing:
        existing.excuse_letter_forms_department_office_unit = data.excuse_letter_forms_department_office_unit
        existing.excuse_letter_forms_dean = data.excuse_letter_forms_dean
        existing.excuse_letter_forms_noted_by = data.excuse_letter_forms_noted_by
    else:
        existing = ExcuseLetterForms(
            excuse_letter_forms_concept_paper_forms_id=paper.concept_paper_forms_id,
            excuse_letter_forms_department_office_unit=data.excuse_letter_forms_department_office_unit,
            excuse_letter_forms_dean=data.excuse_letter_forms_dean,
            excuse_letter_forms_noted_by=data.excuse_letter_forms_noted_by,
        )
        db.add(existing)

    if data.excuse_letter_forms_personnel_in_charge_forms_id is not None:
        existing.excuse_letter_forms_personnel_in_charge_forms_id = (
            data.excuse_letter_forms_personnel_in_charge_forms_id
        )
    elif personnel_id is not None:
        existing.excuse_letter_forms_personnel_in_charge_forms_id = personnel_id


def _create_or_update_learning_journal(db: Session, paper: ConceptPaperForms, data: Any) -> None:
    """Create or update the learning journal form for a concept paper."""
    if data is None:
        return
    existing = (
        db.query(LearningJournalForms)
        .filter_by(learning_journal_forms_concept_paper_forms_id=paper.concept_paper_forms_id)
        .first()
    )
    values = {
        "learning_journal_forms_name": data.learning_journal_forms_name,
        "learning_journal_forms_date": data.learning_journal_forms_date,
        "learning_journal_forms_time": data.learning_journal_forms_time,
        "learning_journal_forms_location": data.learning_journal_forms_location,
        "learning_journal_forms_activity": data.learning_journal_forms_activity,
        "learning_journal_forms_role": data.learning_journal_forms_role,
        "learning_journal_forms_prepared_by": data.learning_journal_forms_prepared_by,
        "observations": data.observations or [],
        "learnings": data.learnings or [],
    }
    if existing:
        for key, value in values.items():
            setattr(existing, key, value)
    else:
        new = LearningJournalForms(
            learning_journal_forms_concept_paper_forms_id=paper.concept_paper_forms_id,
            **values,
        )
        db.add(new)


def _create_or_update_parent_guardian_consent(
    db: Session, paper: ConceptPaperForms, data: Any, personnel_id: int | None
) -> None:
    """Create or update the parent/guardian consent form for a concept paper."""
    if data is None:
        return
    existing = (
        db.query(ParentGuardianConsentForms)
        .filter_by(parent_guardian_consent_forms_concept_paper_forms_id=paper.concept_paper_forms_id)
        .first()
    )
    values = {
        "parent_guardian_consent_forms_parent_guardian_name": data.parent_guardian_consent_forms_parent_guardian_name,
        "parent_guardian_consent_forms_parent_guardian_contact_number": data.parent_guardian_consent_forms_parent_guardian_contact_number,
        "parent_guardian_consent_forms_parent_guardian_address": data.parent_guardian_consent_forms_parent_guardian_address,
        "parent_guardian_consent_forms_parent_guardian_relationship": data.parent_guardian_consent_forms_parent_guardian_relationship,
        "parent_guardian_consent_forms_student_name": data.parent_guardian_consent_forms_student_name,
        "parent_guardian_consent_forms_student_year_and_section": data.parent_guardian_consent_forms_student_year_and_section,
        "parent_guardian_consent_forms_student_contact_number": data.parent_guardian_consent_forms_student_contact_number,
        "parent_guardian_consent_forms_consent": data.parent_guardian_consent_forms_consent,
        "parent_guardian_consent_forms_date": data.parent_guardian_consent_forms_date,
        "parent_guardian_consent_forms_signature": data.parent_guardian_consent_forms_signature,
    }
    if existing:
        for key, value in values.items():
            setattr(existing, key, value)
    else:
        new = ParentGuardianConsentForms(
            parent_guardian_consent_forms_concept_paper_forms_id=paper.concept_paper_forms_id,
            **values,
        )
        db.add(new)

    if data.parent_guardian_consent_forms_personnel_in_charge_forms_id is not None:
        existing.parent_guardian_consent_forms_personnel_in_charge_forms_id = (
            data.parent_guardian_consent_forms_personnel_in_charge_forms_id
        )
    elif personnel_id is not None:
        existing.parent_guardian_consent_forms_personnel_in_charge_forms_id = personnel_id


def _create_related_records(
    db: Session,
    paper: ConceptPaperForms,
    data: ConceptPaperCreate,
) -> None:
    """Create objectives, learning outcomes, and all nested forms for a new paper."""
    for objective in data.objectives or []:
        db.add(Objective(objective_text=objective.objective_text, concept_paper_form=paper))
    for outcome in data.learning_outcomes or []:
        db.add(
            LearningOutcome(
                learning_outcome_text=outcome.learning_outcome_text,
                concept_paper_form=paper,
            )
        )

    personnel_id = _create_personnel_in_charge(db, data.personnel_in_charge)
    if personnel_id is not None:
        personnel_id = personnel_id.personnel_in_charge_forms_id

    _create_or_update_activity_report(db, paper, data.activity_report, personnel_id)
    _create_or_update_excuse_letter(db, paper, data.excuse_letter, personnel_id)
    _create_or_update_learning_journal(db, paper, data.learning_journal)
    _create_or_update_parent_guardian_consent(db, paper, data.parent_guardian_consent, personnel_id)


def _update_related_records(
    db: Session,
    paper: ConceptPaperForms,
    data: ConceptPaperUpdate,
) -> None:
    """Update objectives, learning outcomes, and nested forms for an existing paper."""
    if data.objectives is not None:
        db.query(Objective).filter_by(concept_paper_forms_id=paper.concept_paper_forms_id).delete()
        for objective in data.objectives:
            db.add(Objective(objective_text=objective.objective_text, concept_paper_form=paper))

    if data.learning_outcomes is not None:
        db.query(LearningOutcome).filter_by(concept_paper_forms_id=paper.concept_paper_forms_id).delete()
        for outcome in data.learning_outcomes:
            db.add(
                LearningOutcome(
                    learning_outcome_text=outcome.learning_outcome_text,
                    concept_paper_form=paper,
                )
            )

    personnel_id = _create_personnel_in_charge(db, data.personnel_in_charge)
    if personnel_id is not None:
        personnel_id = personnel_id.personnel_in_charge_forms_id

    if data.activity_report is not None:
        _create_or_update_activity_report(db, paper, data.activity_report, personnel_id)
    if data.excuse_letter is not None:
        _create_or_update_excuse_letter(db, paper, data.excuse_letter, personnel_id)
    if data.learning_journal is not None:
        _create_or_update_learning_journal(db, paper, data.learning_journal)
    if data.parent_guardian_consent is not None:
        _create_or_update_parent_guardian_consent(db, paper, data.parent_guardian_consent, personnel_id)


@router.get(
    "",
    response_model=ResponseEnvelope[PaginatedResponse[ConceptPaperResponse]],
    status_code=status.HTTP_200_OK,
)
def list_concept_papers(
    status: str | None = Query(None),
    search: str | None = Query(None),
    pagination: Any = Depends(get_pagination_params),
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """List concept papers with pagination, status filtering, and department scoping."""
    query = _paper_query(db)

    if not is_admin(current_user):
        query = query.filter(
            or_(
                ConceptPaperForms.concept_paper_forms_departments_id == current_user.users_departments_id,
                ConceptPaperForms.concept_paper_forms_prepared_by == current_user.users_id,
            )
        )

    if status:
        query = query.filter(ConceptPaperForms.concept_paper_forms_status == status)

    if search:
        query = query.filter(ConceptPaperForms.concept_paper_forms_subject.ilike(f"%{search}%"))

    if pagination.sort:
        sort_field = getattr(ConceptPaperForms, pagination.sort, ConceptPaperForms.concept_paper_forms_date)
        query = query.order_by(sort_field.desc() if pagination.order == "desc" else sort_field.asc())
    else:
        query = query.order_by(ConceptPaperForms.concept_paper_forms_date.desc())

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
    response_model=ResponseEnvelope[ConceptPaperResponse],
    status_code=status.HTTP_201_CREATED,
)
def create_concept_paper(
    data: ConceptPaperCreate,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Create a new concept paper with optional nested forms."""
    paper = ConceptPaperForms(
        concept_paper_forms_departments_id=current_user.users_departments_id,
        concept_paper_forms_prepared_by=current_user.users_id,
    )
    _set_paper_attributes(paper, data)
    db.add(paper)
    db.flush()

    _create_related_records(db, paper, data)
    db.commit()
    db.refresh(paper)
    return ResponseEnvelope(data=paper)


@router.get(
    "/{paper_id}",
    response_model=ResponseEnvelope[ConceptPaperResponse],
    status_code=status.HTTP_200_OK,
)
def get_concept_paper(
    paper_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Get a single concept paper by ID."""
    paper = _paper_query(db).filter_by(concept_paper_forms_id=paper_id).first()
    if paper is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Concept paper not found",
        )
    _require_concept_paper_access(paper, current_user)
    return ResponseEnvelope(data=paper)


@router.put(
    "/{paper_id}",
    response_model=ResponseEnvelope[ConceptPaperResponse],
    status_code=status.HTTP_200_OK,
)
def update_concept_paper(
    paper_id: int,
    data: ConceptPaperUpdate,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Update a concept paper and its nested forms."""
    paper = _get_paper(db, paper_id)
    _require_concept_paper_access(paper, current_user)

    _set_paper_attributes(paper, data)
    _update_related_records(db, paper, data)
    db.commit()
    db.refresh(paper)
    return ResponseEnvelope(data=paper)


@router.delete(
    "/{paper_id}",
    response_model=ResponseEnvelope[MessageResponse],
    status_code=status.HTTP_200_OK,
)
def delete_concept_paper(
    paper_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Delete a concept paper and its related forms."""
    paper = _get_paper(db, paper_id)
    _require_concept_paper_access(paper, current_user)
    db.delete(paper)
    db.commit()
    return ResponseEnvelope(data=MessageResponse(message="Concept paper deleted"))


@router.put(
    "/{paper_id}/status",
    response_model=ResponseEnvelope[ConceptPaperResponse],
    status_code=status.HTTP_200_OK,
)
def update_concept_paper_status(
    paper_id: int,
    data: ConceptPaperStatusUpdate,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Update the status of a concept paper."""
    paper = _get_paper(db, paper_id)
    _require_concept_paper_access(paper, current_user)
    paper.concept_paper_forms_status = data.status
    db.commit()
    db.refresh(paper)
    return ResponseEnvelope(data=paper)


@router.post(
    "/generate-body",
    response_model=ResponseEnvelope[ConceptPaperAIResponse],
    status_code=status.HTTP_200_OK,
)
def generate_body(
    data: ConceptPaperAIRequestBody,
):
    """Generate a concept paper body using the AI service."""
    from services.ai.generation import generate_concept_paper_body

    result = generate_concept_paper_body(data.subject, data.start_date, data.end_date, data.location)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error or "AI generation failed",
        )
    return ResponseEnvelope(data=ConceptPaperAIResponse(content=result.data))


@router.post(
    "/generate-descriptions",
    response_model=ResponseEnvelope[ConceptPaperAIResponse],
    status_code=status.HTTP_200_OK,
)
def generate_descriptions(
    data: ConceptPaperAITextRequest,
):
    """Generate a concept paper description using the AI service."""
    from services.ai.generation import generate_concept_paper_descriptions

    result = generate_concept_paper_descriptions(data.subject)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error or "AI generation failed",
        )
    return ResponseEnvelope(data=ConceptPaperAIResponse(content=result.data))


@router.post(
    "/generate-objectives",
    response_model=ResponseEnvelope[ConceptPaperAIResponse],
    status_code=status.HTTP_200_OK,
)
def generate_objectives(
    data: ConceptPaperAITextRequest,
):
    """Generate concept paper objectives using the AI service."""
    from services.ai.generation import generate_concept_paper_objectives

    result = generate_concept_paper_objectives(data.subject)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error or "AI generation failed",
        )
    return ResponseEnvelope(data=ConceptPaperAIResponse(content=result.data))


@router.post(
    "/generate-learning-outcomes",
    response_model=ResponseEnvelope[ConceptPaperAIResponse],
    status_code=status.HTTP_200_OK,
)
def generate_learning_outcomes(
    data: ConceptPaperAITextRequest,
):
    """Generate concept paper learning outcomes using the AI service."""
    from services.ai.generation import generate_concept_paper_learning_outcomes

    result = generate_concept_paper_learning_outcomes(data.subject)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error or "AI generation failed",
        )
    return ResponseEnvelope(data=ConceptPaperAIResponse(content=result.data))


@router.post(
    "/generate-participants",
    response_model=ResponseEnvelope[ConceptPaperAIResponse],
    status_code=status.HTTP_200_OK,
)
def generate_participants(
    data: ConceptPaperAITextRequest,
):
    """Generate an expected participant count using the AI service."""
    from services.ai.generation import generate_concept_paper_participants

    result = generate_concept_paper_participants(data.subject)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error or "AI generation failed",
        )
    return ResponseEnvelope(data=ConceptPaperAIResponse(content=result.data))


@router.post(
    "/generate-consent",
    response_model=ResponseEnvelope[ConceptPaperAIResponse],
    status_code=status.HTTP_200_OK,
)
def generate_consent(
    data: ConceptPaperAIRequestBody,
):
    """Generate parent/guardian consent text using the AI service."""
    from services.ai.generation import generate_concept_paper_consent

    result = generate_concept_paper_consent(data.subject, data.start_date, data.end_date, data.location)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error or "AI generation failed",
        )
    return ResponseEnvelope(data=ConceptPaperAIResponse(content=result.data))


@router.get(
    "/{paper_id}/pdf",
    status_code=status.HTTP_200_OK,
)
def download_pdf(
    paper_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Generate and download a PDF for a concept paper."""
    paper = _get_paper(db, paper_id)
    _require_concept_paper_access(paper, current_user)
    pdf_buffer = generate_concept_paper_pdf(db, paper, current_user)
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=concept_paper_{paper_id}.pdf"},
    )
