"""Event and transaction forms for E-Council."""

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import DateTimeField, FloatField, SelectField, StringField, TextAreaField
from wtforms.validators import InputRequired, Optional

from forms.validators import coerce_int


class EventForm(FlaskForm):
    """Form for adding and updating events."""

    creation_method = SelectField(
        "Creation Method",
        name="creation-method",
        id="creation-method",
        validators=[InputRequired()],
        choices=[
            ("", "Select a Creation Method"),
            ("scratch", "Create from Scratch"),
            ("existing", "Use Existing Concept Paper"),
        ],
        default="",
    )
    concept_paper_forms_id = SelectField(
        "Concept Paper",
        name="concept-paper-forms-id",
        id="concept-paper-forms-id",
        validators=[Optional()],
        choices=[],
        coerce=coerce_int,
        validate_choice=False,
    )
    events_name = StringField(
        "Event Name",
        name="events-name",
        id="events-name",
        validators=[Optional()],
    )
    events_semester = SelectField(
        "Semester",
        name="events-semester",
        id="events-semester",
        validators=[Optional()],
        choices=[
            ("", "Select a Semester"),
            ("1st Semester", "1st Semester"),
            ("2nd Semester", "2nd Semester"),
        ],
        default="",
    )
    events_academic_year = SelectField(
        "Academic Year",
        name="events-academic-year",
        id="events-academic-year",
        validators=[Optional()],
        choices=[],
        default="",
        validate_choice=False,
    )
    other_academic_year = StringField(
        "Other Academic Year",
        name="other-academic-year",
        id="other-academic-year",
        validators=[Optional()],
    )
    events_start_date_and_time = DateTimeField(
        "Start Date and Time",
        name="events-start-date-and-time",
        id="events-start-date-and-time",
        validators=[Optional()],
        format="%Y-%m-%dT%H:%M",
    )
    events_end_date_and_time = DateTimeField(
        "End Date and Time",
        name="events-end-date-and-time",
        id="events-end-date-and-time",
        validators=[Optional()],
        format="%Y-%m-%dT%H:%M",
    )
    events_venue = StringField(
        "Venue",
        name="events-venue",
        id="events-venue",
        validators=[Optional()],
    )
    events_budget = FloatField(
        "Budget",
        name="events-budget",
        id="events-budget",
        validators=[Optional()],
    )
    events_status = SelectField(
        "Status",
        name="events-status",
        id="events-status",
        validators=[Optional()],
        choices=[
            ("", "Select a Status"),
            ("Upcoming", "Upcoming"),
            ("Postponed", "Postponed"),
            ("Done", "Done"),
            ("Cancelled", "Cancelled"),
        ],
        default="",
    )
    events_description = TextAreaField(
        "Description",
        name="events-description",
        id="events-description",
        validators=[Optional()],
    )
    events_remarks = StringField(
        "Remarks",
        name="events-remarks",
        id="events-remarks",
        validators=[Optional()],
    )

    def __init__(self, concept_papers=None, academic_years=None, **kwargs):
        super().__init__(**kwargs)
        if concept_papers is not None:
            self.concept_paper_forms_id.choices = [("", "Select a Concept Paper")] + [
                (str(cp.concept_paper_forms_id), cp.concept_paper_forms_subject) for cp in concept_papers
            ]
        if academic_years is not None:
            self.events_academic_year.choices = (
                [("", "Select an Academic Year")] + [(year, year) for year in academic_years] + [("Other", "Other")]
            )

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False
        if self.events_academic_year.data == "Other":
            if not self.other_academic_year.data:
                self.other_academic_year.errors.append("Other academic year is required.")
                return False
            self.events_academic_year.data = self.other_academic_year.data
        return True


class TransactionForm(FlaskForm):
    """Form for adding and updating event transactions."""

    transaction_name = StringField(
        "Transaction Name",
        name="transaction-name",
        id="transaction-name",
        validators=[InputRequired()],
    )
    transaction_date = DateTimeField(
        "Transaction Date",
        name="transaction-date",
        id="transaction-date",
        validators=[InputRequired()],
        format="%Y-%m-%dT%H:%M",
    )
    transaction_unit_amount = FloatField(
        "Unit Amount",
        name="transaction-unit-amount",
        id="transaction-unit-amount",
        validators=[InputRequired()],
    )
    transaction_unit_price = FloatField(
        "Unit Price",
        name="transaction-unit-price",
        id="transaction-unit-price",
        validators=[InputRequired()],
    )
    transaction_total = FloatField(
        "Total",
        name="transaction-total",
        id="transaction-total",
        validators=[InputRequired()],
    )
    transaction_category = SelectField(
        "Category",
        name="transaction-category",
        id="transaction-category",
        validators=[InputRequired()],
        choices=[],
        default="",
        validate_choice=False,
    )
    other_transaction_category = StringField(
        "Other Category",
        name="other-transaction-category",
        id="other-transaction-category",
        validators=[Optional()],
    )
    transaction_type = SelectField(
        "Type",
        name="transaction-type",
        id="transaction-type",
        validators=[InputRequired()],
        choices=[
            ("", "Select a Type"),
            ("Income", "Income"),
            ("Expense", "Expense"),
        ],
        default="",
    )
    transaction_receipt = FileField(
        "Receipt",
        name="transaction-receipt",
        id="transaction-receipt",
        validators=[FileAllowed(["jpg", "jpeg", "png", "pdf"], "Images and PDFs only.")],
    )

    def __init__(self, categories=None, **kwargs):
        super().__init__(**kwargs)
        if categories is not None:
            self.transaction_category.choices = (
                [("", "Select a Category")] + [(category, category) for category in categories] + [("Other", "Other")]
            )

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False
        if self.transaction_category.data == "Other":
            if not self.other_transaction_category.data:
                self.other_transaction_category.errors.append("Other category is required.")
                return False
            self.transaction_category.data = self.other_transaction_category.data
        return True
