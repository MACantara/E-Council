"""Pydantic request/response models for FastAPI documentation endpoints."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

from api.schemas.concept_papers import ActivityReportItemCreate, ActivityReportItemResponse


class DocumentationStatus(str, Enum):
    """Documentation status values from the existing Flask forms."""

    upcoming = "Upcoming"
    postponed = "Postponed"
    done = "Done"
    cancelled = "Cancelled"


class DocumentationType(str, Enum):
    """Documentation type values from the existing Flask forms."""

    activity_report = "Activity Report"
    after_documentation = "After Documentation"


class SemesterChoices(str, Enum):
    """Semester values used across documentation forms."""

    first_semester = "1st Semester"
    second_semester = "2nd Semester"


class ImageItem(BaseModel):
    """A stored image reference."""

    url: str
    public_id: str | None = None


class TallyItemBase(BaseModel):
    """Shared tally item fields."""

    name: str = Field(..., min_length=1)
    extremely_satisfied: int = 0
    satisfied: int = 0
    neutral: int = 0
    dissatisfied: int = 0
    extremely_dissatisfied: int = 0


class TallyItemCreate(TallyItemBase):
    """Tally item creation payload."""

    pass


class TallyItemResponse(TallyItemBase):
    """Tally item response."""

    tally_item_id: int
    documentation_id: int | None = None

    model_config = {"from_attributes": True}


class EvaluationFormBase(BaseModel):
    """Shared evaluation form fields."""

    name: str = Field(..., min_length=1)
    rating: str | None = None


class EvaluationFormCreate(EvaluationFormBase):
    """Evaluation form creation payload."""

    pass


class EvaluationFormResponse(EvaluationFormBase):
    """Evaluation form response."""

    evaluation_form_id: int
    documentation_id: int | None = None

    model_config = {"from_attributes": True}


class DocumentationBase(BaseModel):
    """Shared documentation fields."""

    documentation_events_id: int | None = None
    documentation_academic_year: str | None = Field(None, max_length=50)
    documentation_semester: str | None = Field(None, max_length=50)
    documentation_status: str | None = "Upcoming"
    documentation_type: str | None = "Activity Report"
    documentation_activity_report_forms_id: int | None = None
    documentation_learning_journal_forms_id: int | None = None
    documentation_prepared_by: int | None = None
    documentation_checked_by: int | None = None
    documentation_noted_by: int | None = None
    documentation_date_of_submission: datetime | None = None
    documentation_rating: float | None = None
    documentation_comments_suggestions: str | None = None
    evaluation_images: list[ImageItem] = []
    attendance_images: list[ImageItem] = []
    event_photo_images: list[ImageItem] = []
    evaluation_student_names: list[str] = []
    activity_report_items: list[ActivityReportItemCreate] = []
    tally_items: list[TallyItemCreate] = []
    evaluation_forms: list[EvaluationFormCreate] = []
    learning_journal_observations: list[str] = []
    learning_journal_learnings: list[str] = []


class DocumentationCreate(DocumentationBase):
    """Documentation creation payload."""

    pass


class DocumentationUpdate(BaseModel):
    """Documentation update payload.

    Every field is optional so that partial updates can be performed without
    overwriting existing lists or scalar values.
    """

    documentation_events_id: int | None = None
    documentation_academic_year: str | None = Field(None, max_length=50)
    documentation_semester: str | None = Field(None, max_length=50)
    documentation_status: str | None = None
    documentation_type: str | None = None
    documentation_activity_report_forms_id: int | None = None
    documentation_learning_journal_forms_id: int | None = None
    documentation_prepared_by: int | None = None
    documentation_checked_by: int | None = None
    documentation_noted_by: int | None = None
    documentation_date_of_submission: datetime | None = None
    documentation_rating: float | None = None
    documentation_comments_suggestions: str | None = None
    evaluation_images: list[ImageItem] | None = None
    attendance_images: list[ImageItem] | None = None
    event_photo_images: list[ImageItem] | None = None
    evaluation_student_names: list[str] | None = None
    activity_report_items: list[ActivityReportItemCreate] | None = None
    tally_items: list[TallyItemCreate] | None = None
    evaluation_forms: list[EvaluationFormCreate] | None = None
    learning_journal_observations: list[str] | None = None
    learning_journal_learnings: list[str] | None = None


class DocumentationResponse(BaseModel):
    """Documentation response."""

    documentation_id: int
    documentation_events_id: int | None = None
    documentation_academic_year: str | None = None
    documentation_semester: str | None = None
    documentation_status: str | None = None
    documentation_type: str | None = None
    documentation_departments_id: int | None = None
    documentation_activity_report_forms_id: int | None = None
    documentation_learning_journal_forms_id: int | None = None
    documentation_prepared_by: int | None = None
    documentation_checked_by: int | None = None
    documentation_noted_by: int | None = None
    documentation_date_of_submission: datetime | None = None
    documentation_rating: float | None = None
    documentation_comments_suggestions: str | None = None
    evaluation_images: list[ImageItem] = []
    attendance_images: list[ImageItem] = []
    event_photo_images: list[ImageItem] = []
    evaluation_student_names: list[str] = []
    activity_report_items: list[ActivityReportItemResponse] = []
    tally_items: list[TallyItemResponse] = []
    evaluation_forms: list[EvaluationFormResponse] = []
    learning_journal_observations: list[str] = []
    learning_journal_learnings: list[str] = []

    model_config = {"from_attributes": True}


class DocumentationStatusUpdate(BaseModel):
    """Status update payload."""

    status: str


class DocumentationListParams(BaseModel):
    """Query parameters for listing documentation."""

    status: str | None = None
    type: str | None = None
    search: str | None = None


class FileType(str, Enum):
    """Supported documentation file upload types."""

    evaluation_image = "evaluation_image"
    attendance_image = "attendance_image"
    event_photo = "event_photo"


class FileUploadResponse(BaseModel):
    """Response after uploading a documentation file."""

    file: ImageItem


class DownloadUrlResponse(BaseModel):
    """Response containing a download URL for a stored file."""

    download_url: str | None
    is_direct: bool = True


class ActivityReportDetails(BaseModel):
    """Activity report details grouped by type."""

    strengths: list[dict[str, str]]
    weaknesses: list[dict[str, str]]
    recommendations: list[dict[str, str]]


class StudentListResponse(BaseModel):
    """Response for a parsed student list Excel file."""

    students: list[str]
