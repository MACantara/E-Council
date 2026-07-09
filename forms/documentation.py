"""Documentation and evaluation forms for E-Council."""

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, MultipleFileField
from wtforms import (
    DateField,
    FieldList,
    Form,
    FormField,
    HiddenField,
    SelectField,
    StringField,
    TextAreaField,
)
from wtforms.validators import InputRequired, Optional

from forms.validators import coerce_int


class TallyItemForm(Form):
    """Sub-form for a single documentation tally item."""

    name = StringField(
        "Tally Item Name",
        name="tally-items-name",
        validators=[InputRequired()],
    )
    extremely_satisfied = StringField(
        "Extremely Satisfied",
        name="tally-items-extremely-satisfied-rating-total",
        validators=[InputRequired()],
        default="0",
    )
    satisfied = StringField(
        "Satisfied",
        name="tally-items-satisfied-rating-total",
        validators=[InputRequired()],
        default="0",
    )
    neutral = StringField(
        "Neutral",
        name="tally-items-neutral-rating-total",
        validators=[InputRequired()],
        default="0",
    )
    dissatisfied = StringField(
        "Dissatisfied",
        name="tally-items-dissatisfied-rating-total",
        validators=[InputRequired()],
        default="0",
    )
    extremely_dissatisfied = StringField(
        "Extremely Dissatisfied",
        name="tally-items-extremely-dissatisfied-rating-total",
        validators=[InputRequired()],
        default="0",
    )


class EvaluationTallyItemForm(Form):
    """Sub-form for a single evaluation tally item."""

    name = StringField(
        "Item",
        name="evaluation-tally-item-name",
        validators=[InputRequired()],
    )
    extremely_satisfied = StringField(
        "Extremely Satisfied",
        name="evaluation-tally-items-extremely-satisfied",
        validators=[InputRequired()],
        default="0",
    )
    satisfied = StringField(
        "Satisfied",
        name="evaluation-tally-items-satisfied",
        validators=[InputRequired()],
        default="0",
    )
    neutral = StringField(
        "Neutral",
        name="evaluation-tally-items-neutral",
        validators=[InputRequired()],
        default="0",
    )
    dissatisfied = StringField(
        "Dissatisfied",
        name="evaluation-tally-items-dissatisfied",
        validators=[InputRequired()],
        default="0",
    )
    extremely_dissatisfied = StringField(
        "Extremely Dissatisfied",
        name="evaluation-tally-items-extremely-dissatisfied",
        validators=[InputRequired()],
        default="0",
    )


class DocumentationForm(FlaskForm):
    """Form for adding and updating documentation entries."""

    documentation_type = SelectField(
        "Type",
        name="documentation-type",
        id="documentation-type",
        validators=[InputRequired()],
        choices=[
            ("", "Select Type"),
            ("Activity Report", "Activity Report"),
            ("After Documentation", "After Documentation"),
        ],
        default="",
    )
    documentation_events_id = SelectField(
        "Event",
        name="documentation-events-id",
        id="documentation-events-id",
        validators=[InputRequired()],
        choices=[],
        coerce=coerce_int,
        validate_choice=False,
    )
    documentation_status = SelectField(
        "Status",
        name="documentation-status",
        id="documentation-status",
        validators=[InputRequired()],
        choices=[
            ("", "Select Status"),
            ("Upcoming", "Upcoming"),
            ("Postponed", "Postponed"),
            ("Done", "Done"),
            ("Cancelled", "Cancelled"),
        ],
        default="",
    )
    documentation_activity_report_forms_id = SelectField(
        "Activity Report Form",
        name="documentation-activity-report-forms-id",
        id="documentation-activity-report-forms-id",
        validators=[Optional()],
        choices=[],
        coerce=coerce_int,
        validate_choice=False,
    )
    documentation_learning_journal_forms_id = SelectField(
        "Learning Journal Form",
        name="documentation-learning-journal-forms-id",
        id="documentation-learning-journal-forms-id",
        validators=[Optional()],
        choices=[],
        coerce=coerce_int,
        validate_choice=False,
    )
    documentation_prepared_by = SelectField(
        "Prepared By",
        name="documentation-prepared-by",
        id="documentation-prepared-by",
        validators=[InputRequired()],
        choices=[],
        coerce=coerce_int,
        validate_choice=False,
    )
    documentation_noted_by = SelectField(
        "Noted By",
        name="documentation-noted-by",
        id="documentation-noted-by",
        validators=[InputRequired()],
        choices=[],
        coerce=coerce_int,
        validate_choice=False,
    )
    documentation_checked_by = SelectField(
        "Checked By",
        name="documentation-checked-by",
        id="documentation-checked-by",
        validators=[Optional()],
        choices=[],
        coerce=coerce_int,
        validate_choice=False,
    )
    documentation_date_of_submission = DateField(
        "Date of Submission",
        name="documentation-date-of-submission",
        id="documentation-date-of-submission",
        validators=[InputRequired()],
        format="%Y-%m-%d",
    )
    documentation_rating = HiddenField(
        name="documentation-rating",
        id="documentation-rating",
        default="0",
    )
    documentation_comments_suggestions = TextAreaField(
        "Comments/Suggestions",
        name="documentation-comments-suggestions",
        id="documentation-comments-suggestions",
        validators=[Optional()],
    )

    # Activity report form fields
    activity_strengths = FieldList(
        StringField(
            "Activity Strength",
            name="activity-strengths",
            validators=[Optional()],
        ),
        name="activity-strengths",
        min_entries=1,
    )
    activity_weaknesses = FieldList(
        StringField(
            "Activity Weakness",
            name="activity-weaknesses",
            validators=[Optional()],
        ),
        name="activity-weaknesses",
        min_entries=1,
    )
    activity_recommendations = FieldList(
        StringField(
            "Activity Recommendation",
            name="activity-recommendations",
            validators=[Optional()],
        ),
        name="activity-recommendations",
        min_entries=1,
    )

    # Learning journal form fields
    learning_journal_forms_name = StringField(
        "Name of Student",
        name="learning-journal-forms-name-of-student",
        id="learning-journal-forms-name-of-student",
        validators=[InputRequired()],
    )
    learning_journal_forms_course_year_level = StringField(
        "Course & Year Level",
        name="learning-journal-forms-course-year-level",
        id="learning-journal-forms-course-year-level",
        validators=[InputRequired()],
    )
    learning_journal_forms_id_number = StringField(
        "ID Number",
        name="learning-journal-forms-id-number",
        id="learning-journal-forms-id-number",
        validators=[InputRequired()],
    )
    learnings = FieldList(
        StringField(
            "Learning",
            name="learnings",
            validators=[Optional()],
        ),
        name="learnings",
        min_entries=1,
    )
    observations = FieldList(
        StringField(
            "Observation",
            name="observations",
            validators=[Optional()],
        ),
        name="observations",
        min_entries=1,
    )
    learning_journal_forms_overall_reflection = TextAreaField(
        "Overall Reflection",
        name="learning-journal-forms-overall-reflection",
        id="learning-journal-forms-overall-reflection",
        validators=[InputRequired()],
    )
    learning_journal_forms_prepared_by = SelectField(
        "Prepared By",
        name="learning-journal-forms-prepared-by",
        id="learning-journal-forms-prepared-by",
        validators=[InputRequired()],
        choices=[],
        coerce=coerce_int,
        validate_choice=False,
    )
    learning_journal_forms_seen_and_read_by = StringField(
        "Seen and Read By",
        name="learning-journal-forms-seen-and-read-by",
        id="learning-journal-forms-seen-and-read-by",
        validators=[Optional()],
    )
    learning_journal_forms_checked_by = SelectField(
        "Checked By",
        name="learning-journal-forms-checked-by",
        id="learning-journal-forms-checked-by",
        validators=[InputRequired()],
        choices=[],
        coerce=coerce_int,
        validate_choice=False,
    )

    # Tally and evaluation fields
    tally_items = FieldList(
        FormField(TallyItemForm),
        name="tally-items",
        min_entries=1,
    )
    evaluation_tally_items = FieldList(
        FormField(EvaluationTallyItemForm),
        name="evaluation-tally-items",
        min_entries=0,
    )

    # File uploads
    evaluation_images = MultipleFileField(
        "Evaluation Images",
        name="evaluation-images",
        id="evaluation-images",
        validators=[FileAllowed(["jpg", "jpeg", "png"], "Images only.")],
    )
    attendance_images = MultipleFileField(
        "Attendance Images",
        name="attendance-images",
        id="attendance-images",
        validators=[FileAllowed(["jpg", "jpeg", "png"], "Images only.")],
    )
    photo_documentation_images = MultipleFileField(
        "Photo Documentation",
        name="photo-documentation-images",
        id="photo-documentation-images",
        validators=[FileAllowed(["jpg", "jpeg", "png"], "Images only.")],
    )
    student_list_excel = FileField(
        "Student List Excel",
        name="student-list-excel",
        id="student-list-excel",
        validators=[FileAllowed(["xlsx"], "Excel files only.")],
    )

    def __init__(
        self, events=None, users=None, signatories=None, activity_reports=None, learning_journals=None, **kwargs
    ):
        super().__init__(**kwargs)
        if events is not None:
            self.documentation_events_id.choices = [("", "Select Event")] + [
                (str(event.events_id), event.events_name) for event in events
            ]
        if users is not None:
            user_choices = [(str(user.users_id), f"{user.users_first_name} {user.users_last_name}") for user in users]
            self.documentation_prepared_by.choices = [("", "Select Preparer")] + user_choices
            self.learning_journal_forms_prepared_by.choices = [("", "Select User")] + user_choices
        if signatories is not None:
            signatory_choices = [
                (
                    str(signatory.signatory_id),
                    f"{signatory.signatory_first_name} {signatory.signatory_last_name} - {signatory.signatory_position}",
                )
                for signatory in signatories
            ]
            self.documentation_noted_by.choices = [("", "Select Noter")] + signatory_choices
            self.documentation_checked_by.choices = [("", "Select Checker")] + signatory_choices
            self.learning_journal_forms_checked_by.choices = [("", "Select Signatory")] + signatory_choices
        if activity_reports is not None:
            self.documentation_activity_report_forms_id.choices = [("", "Select Activity Report Form")] + [
                (str(ar.activity_report_forms_id), ar.activity_report_forms_nature_of_the_activity)
                for ar in activity_reports
            ]
        if learning_journals is not None:
            self.documentation_learning_journal_forms_id.choices = [("", "Select Learning Journal Form")] + [
                (str(lj.learning_journal_forms_id), lj.learning_journal_forms_name) for lj in learning_journals
            ]
