"""Financial report forms for E-Council."""

from flask_wtf import FlaskForm
from wtforms import DateTimeField, SelectField, StringField
from wtforms.validators import InputRequired, Optional

from forms.validators import coerce_int


class FinancialReportForm(FlaskForm):
    """Form for adding and updating financial reports."""

    financial_reports_date = DateTimeField(
        "Date",
        name="financial-reports-date",
        id="financial-reports-date",
        validators=[InputRequired()],
        format="%Y-%m-%dT%H:%M",
    )
    financial_reports_academic_year = SelectField(
        "Academic Year",
        name="financial-reports-academic-year",
        id="financial-reports-academic-year",
        validators=[InputRequired()],
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
    financial_reports_semester = SelectField(
        "Semester",
        name="financial-reports-semester",
        id="financial-reports-semester",
        validators=[InputRequired()],
        choices=[
            ("", "Select a Semester"),
            ("1st Semester", "1st Semester"),
            ("2nd Semester", "2nd Semester"),
        ],
        default="",
    )
    financial_reports_events_id = SelectField(
        "Event",
        name="financial-reports-events-id",
        id="financial-reports-events-id",
        validators=[InputRequired()],
        choices=[],
        default="",
        coerce=coerce_int,
        validate_choice=False,
    )
    financial_reports_title = StringField(
        "Title",
        name="financial-reports-title",
        id="financial-reports-title",
        validators=[InputRequired()],
    )
    financial_reports_status = SelectField(
        "Status",
        name="financial-reports-status",
        id="financial-reports-status",
        validators=[InputRequired()],
        choices=[
            ("", "Select a Status"),
            ("Upcoming", "Upcoming"),
            ("Postponed", "Postponed"),
            ("Done", "Done"),
            ("Cancelled", "Cancelled"),
        ],
        default="",
    )
    financial_reports_audited_and_prepared_by = SelectField(
        "Audited and Prepared By",
        name="financial-reports-audited-and-prepared-by",
        id="financial-reports-audited-and-prepared-by",
        validators=[Optional()],
        choices=[],
        coerce=coerce_int,
        validate_choice=False,
    )
    financial_reports_noted_by = SelectField(
        "Noted By",
        name="financial-reports-noted-by",
        id="financial-reports-noted-by",
        validators=[Optional()],
        choices=[],
        coerce=coerce_int,
        validate_choice=False,
    )
    financial_reports_recommending_approval_by = SelectField(
        "Recommending Approval By",
        name="financial-reports-recommending-approval-by",
        id="financial-reports-recommending-approval-by",
        validators=[Optional()],
        choices=[],
        coerce=coerce_int,
        validate_choice=False,
    )
    financial_reports_approved_by = SelectField(
        "Approved By",
        name="financial-reports-approved-by",
        id="financial-reports-approved-by",
        validators=[Optional()],
        choices=[],
        coerce=coerce_int,
        validate_choice=False,
    )

    def __init__(self, events=None, academic_years=None, student_organizations=None, signatories=None, **kwargs):
        super().__init__(**kwargs)
        if academic_years is not None:
            self.financial_reports_academic_year.choices = (
                [("", "Select an Academic Year")] + [(year, year) for year in academic_years] + [("Other", "Other")]
            )
        if events is not None:
            self.financial_reports_events_id.choices = (
                [("", "Select an Event")]
                + [
                    (str(event.events_id), event.events_name)
                    for event in events
                    if not getattr(event, "financial_reports", [])
                ]
                + [("None", "None")]
            )
        if student_organizations is not None:
            user_choices = [
                (
                    org.student_organizations_name,
                    [
                        (
                            str(user.users_id),
                            f"{user.users_first_name} {user.users_last_name} - {user.users_student_organization_position}",
                        )
                        for user in org.users
                    ],
                )
                for org in student_organizations
            ]
            placeholder = [("", "Select a User")]
            self.financial_reports_audited_and_prepared_by.choices = placeholder + user_choices
            self.financial_reports_noted_by.choices = placeholder + user_choices
            self.financial_reports_recommending_approval_by.choices = placeholder + user_choices
        if signatories is not None:
            self.financial_reports_approved_by.choices = [("", "Select a Signatory")] + [
                (
                    str(signatory.signatory_id),
                    f"{signatory.signatory_first_name} {signatory.signatory_last_name} - {signatory.signatory_position}",
                )
                for signatory in signatories
            ]

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False
        if self.financial_reports_academic_year.data == "Other":
            if not self.other_academic_year.data:
                self.other_academic_year.errors.append("Other academic year is required.")
                return False
            self.financial_reports_academic_year.data = self.other_academic_year.data
        return True
