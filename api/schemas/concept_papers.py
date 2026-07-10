"""Pydantic request/response models for FastAPI concept paper endpoints."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

# Concept paper status values from the existing Flask templates.
CONCEPT_PAPER_STATUS_CHOICES = (
    "Upcoming",
    "Postponed",
    "Done",
    "Cancelled",
)

SEMESTER_CHOICES = (
    "1st Semester",
    "2nd Semester",
)


class ObjectiveBase(BaseModel):
    """Shared objective fields."""

    objective_text: str = Field(..., min_length=1)


class ObjectiveCreate(ObjectiveBase):
    """Objective creation payload."""

    pass


class ObjectiveResponse(ObjectiveBase):
    """Objective response."""

    objective_id: int

    model_config = {"from_attributes": True}


class LearningOutcomeBase(BaseModel):
    """Shared learning outcome fields."""

    learning_outcome_text: str = Field(..., min_length=1)


class LearningOutcomeCreate(LearningOutcomeBase):
    """Learning outcome creation payload."""

    pass


class LearningOutcomeResponse(LearningOutcomeBase):
    """Learning outcome response."""

    learning_outcome_id: int

    model_config = {"from_attributes": True}


class ActivityReportItemBase(BaseModel):
    """Shared activity report item fields."""

    item_type: Literal["strength", "weakness", "recommendation"]
    item_text: str = Field(..., min_length=1)


class ActivityReportItemCreate(ActivityReportItemBase):
    """Activity report item creation payload."""

    pass


class ActivityReportItemResponse(ActivityReportItemBase):
    """Activity report item response."""

    activity_report_item_id: int

    model_config = {"from_attributes": True}


class ActivityReportBase(BaseModel):
    """Shared activity report fields."""

    activity_report_forms_nature_of_the_activity: str | None = None
    activity_report_forms_contact_numbers: str | None = None
    activity_report_forms_prepared_by: int | None = None
    activity_report_forms_noted_by: int | None = None
    activity_report_date_submission: date | None = None
    activity_report_items: list[ActivityReportItemCreate] | None = None


class ActivityReportCreate(ActivityReportBase):
    """Activity report creation payload."""

    pass


class ActivityReportResponse(ActivityReportBase):
    """Activity report response."""

    activity_report_forms_id: int
    activity_report_items: list[ActivityReportItemResponse] = []

    model_config = {"from_attributes": True}


class PersonnelInChargeBase(BaseModel):
    """Shared personnel in charge fields."""

    personnel_in_charge_forms_name: str = Field(..., min_length=1)
    personnel_in_charge_forms_position: str = Field(..., min_length=1)
    personnel_in_charge_forms_department: str = Field(..., min_length=1)
    personnel_in_charge_forms_contact_number: str = Field(..., min_length=1)


class PersonnelInChargeCreate(PersonnelInChargeBase):
    """Personnel in charge creation payload."""

    pass


class PersonnelInChargeResponse(PersonnelInChargeBase):
    """Personnel in charge response."""

    personnel_in_charge_forms_id: int

    model_config = {"from_attributes": True}


class ExcuseLetterBase(BaseModel):
    """Shared excuse letter fields."""

    excuse_letter_forms_department_office_unit: str | None = None
    excuse_letter_forms_personnel_in_charge_forms_id: int | None = None
    excuse_letter_forms_dean: int | None = None
    excuse_letter_forms_noted_by: int | None = None


class ExcuseLetterCreate(ExcuseLetterBase):
    """Excuse letter creation payload."""

    pass


class ExcuseLetterResponse(ExcuseLetterBase):
    """Excuse letter response."""

    excuse_letter_forms_id: int

    model_config = {"from_attributes": True}


class LearningJournalBase(BaseModel):
    """Shared learning journal fields."""

    learning_journal_forms_name: str | None = None
    learning_journal_forms_date: date | None = None
    learning_journal_forms_time: str | None = None
    learning_journal_forms_location: str | None = None
    learning_journal_forms_activity: str | None = None
    learning_journal_forms_role: str | None = None
    learning_journal_forms_prepared_by: int | None = None
    observations: list[str] | None = None
    learnings: list[str] | None = None


class LearningJournalCreate(LearningJournalBase):
    """Learning journal creation payload."""

    pass


class LearningJournalResponse(LearningJournalBase):
    """Learning journal response."""

    learning_journal_forms_id: int

    model_config = {"from_attributes": True}


class ParentGuardianConsentBase(BaseModel):
    """Shared parent/guardian consent fields."""

    parent_guardian_consent_forms_parent_guardian_name: str | None = None
    parent_guardian_consent_forms_parent_guardian_contact_number: str | None = None
    parent_guardian_consent_forms_parent_guardian_address: str | None = None
    parent_guardian_consent_forms_parent_guardian_relationship: str | None = None
    parent_guardian_consent_forms_student_name: str | None = None
    parent_guardian_consent_forms_student_year_and_section: str | None = None
    parent_guardian_consent_forms_student_contact_number: str | None = None
    parent_guardian_consent_forms_consent: str | None = None
    parent_guardian_consent_forms_date: date | None = None
    parent_guardian_consent_forms_signature: str | None = None
    parent_guardian_consent_forms_personnel_in_charge_forms_id: int | None = None


class ParentGuardianConsentCreate(ParentGuardianConsentBase):
    """Parent/guardian consent creation payload."""

    pass


class ParentGuardianConsentResponse(ParentGuardianConsentBase):
    """Parent/guardian consent response."""

    parent_guardian_consent_forms_id: int

    model_config = {"from_attributes": True}


class ConceptPaperBase(BaseModel):
    """Shared concept paper fields."""

    concept_paper_forms_academic_year: str | None = Field(None, max_length=50)
    concept_paper_forms_semester: Literal[SEMESTER_CHOICES] | None = None
    concept_paper_forms_status: Literal[CONCEPT_PAPER_STATUS_CHOICES] | None = "Upcoming"
    concept_paper_forms_subject: str = Field(..., min_length=1, max_length=255)
    concept_paper_forms_date: datetime | None = None
    concept_paper_forms_body: str | None = None
    concept_paper_forms_event_start_date_and_time: datetime | None = None
    concept_paper_forms_event_end_date_and_time: datetime | None = None
    concept_paper_forms_location: str | None = Field(None, max_length=255)
    concept_paper_forms_participants: str | None = None
    concept_paper_forms_budget: str | None = None
    concept_paper_forms_descriptions: str | None = None
    concept_paper_forms_expected_number_of_participants: str | None = None
    concept_paper_forms_prepared_by: int | None = None
    concept_paper_forms_signed_and_reviewed_by: int | None = None
    concept_paper_forms_endorsed_by: int | None = None
    concept_paper_forms_recommending_approval_by: int | None = None
    concept_paper_forms_approved_by: int | None = None


class ConceptPaperCreate(ConceptPaperBase):
    """Concept paper creation payload."""

    objectives: list[ObjectiveCreate] | None = None
    learning_outcomes: list[LearningOutcomeCreate] | None = None
    activity_report: ActivityReportCreate | None = None
    personnel_in_charge: PersonnelInChargeCreate | None = None
    excuse_letter: ExcuseLetterCreate | None = None
    learning_journal: LearningJournalCreate | None = None
    parent_guardian_consent: ParentGuardianConsentCreate | None = None


class ConceptPaperUpdate(BaseModel):
    """Concept paper update payload."""

    concept_paper_forms_academic_year: str | None = Field(None, max_length=50)
    concept_paper_forms_semester: Literal[SEMESTER_CHOICES] | None = None
    concept_paper_forms_status: Literal[CONCEPT_PAPER_STATUS_CHOICES] | None = None
    concept_paper_forms_subject: str | None = Field(None, min_length=1, max_length=255)
    concept_paper_forms_date: datetime | None = None
    concept_paper_forms_body: str | None = None
    concept_paper_forms_event_start_date_and_time: datetime | None = None
    concept_paper_forms_event_end_date_and_time: datetime | None = None
    concept_paper_forms_location: str | None = Field(None, max_length=255)
    concept_paper_forms_participants: str | None = None
    concept_paper_forms_budget: str | None = None
    concept_paper_forms_descriptions: str | None = None
    concept_paper_forms_expected_number_of_participants: str | None = None
    concept_paper_forms_prepared_by: int | None = None
    concept_paper_forms_signed_and_reviewed_by: int | None = None
    concept_paper_forms_endorsed_by: int | None = None
    concept_paper_forms_recommending_approval_by: int | None = None
    concept_paper_forms_approved_by: int | None = None
    objectives: list[ObjectiveCreate] | None = None
    learning_outcomes: list[LearningOutcomeCreate] | None = None
    activity_report: ActivityReportCreate | None = None
    personnel_in_charge: PersonnelInChargeCreate | None = None
    excuse_letter: ExcuseLetterCreate | None = None
    learning_journal: LearningJournalCreate | None = None
    parent_guardian_consent: ParentGuardianConsentCreate | None = None


class ConceptPaperResponse(ConceptPaperBase):
    """Concept paper response."""

    concept_paper_forms_id: int
    concept_paper_forms_departments_id: int | None = None
    objectives: list[ObjectiveResponse] = []
    learning_outcomes: list[LearningOutcomeResponse] = []
    activity_report: ActivityReportResponse | None = None
    excuse_letter: ExcuseLetterResponse | None = None
    learning_journal: LearningJournalResponse | None = None
    parent_guardian_consent: ParentGuardianConsentResponse | None = None

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def _extract_related_forms(cls, data: Any) -> Any:
        """Extract the first related form from each list relationship."""
        if isinstance(data, dict):
            return data

        from models import ConceptPaperForms

        if isinstance(data, ConceptPaperForms):
            obj = data
            base = {k: getattr(obj, k) for k in obj.__dict__ if not k.startswith("_")}
            base["objectives"] = obj.objectives
            base["learning_outcomes"] = obj.learning_outcomes
            base["activity_report"] = obj.activity_report_forms[0] if obj.activity_report_forms else None
            base["excuse_letter"] = obj.excuse_letter_forms[0] if obj.excuse_letter_forms else None
            base["learning_journal"] = obj.learning_journal_forms[0] if obj.learning_journal_forms else None
            base["parent_guardian_consent"] = (
                obj.parent_guardian_consent_forms[0] if obj.parent_guardian_consent_forms else None
            )
            return base
        return data


class ConceptPaperStatusUpdate(BaseModel):
    """Status update payload."""

    status: Literal[CONCEPT_PAPER_STATUS_CHOICES]


class ConceptPaperListParams(BaseModel):
    """Query parameters for listing concept papers."""

    status: Literal[CONCEPT_PAPER_STATUS_CHOICES] | None = None
    search: str | None = None


class ConceptPaperAIRequestBody(BaseModel):
    """Payload for AI-generated concept paper body."""

    subject: str
    start_date: str
    end_date: str
    location: str


class ConceptPaperAITextRequest(BaseModel):
    """Payload for AI-generated text fields."""

    subject: str


class ConceptPaperAIResponse(BaseModel):
    """Response for AI-generated content."""

    content: str
