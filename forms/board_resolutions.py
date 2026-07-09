"""Board resolution forms for E-Council."""

from flask_wtf import FlaskForm
from wtforms import DateTimeField, FloatField, SelectField, SelectMultipleField, StringField, TextAreaField
from wtforms.validators import InputRequired, Optional

from forms.validators import coerce_int


class BoardResolutionForm(FlaskForm):
    """Form for adding and updating board resolutions."""

    board_resolutions_date = DateTimeField(
        "Date",
        name="board-resolutions-date",
        id="board-resolutions-date",
        validators=[InputRequired()],
        format="%Y-%m-%dT%H:%M",
    )
    board_resolutions_events_id = SelectField(
        "Event Name",
        name="board-resolutions-events-id",
        id="board-resolutions-events-id",
        validators=[InputRequired()],
        choices=[],
        coerce=coerce_int,
        validate_choice=False,
    )
    other_event_name = StringField(
        "Other Event Name",
        name="other-event-name",
        id="other-event-name-input",
        validators=[Optional()],
    )
    board_resolutions_title = StringField(
        "Title",
        name="board-resolutions-title",
        id="board-resolutions-title",
        validators=[InputRequired()],
    )
    board_resolutions_academic_year = SelectField(
        "Academic Year",
        name="board-resolutions-academic-year",
        id="board-resolutions-academic-year",
        validators=[InputRequired()],
        choices=[],
        default="",
        validate_choice=False,
    )
    other_academic_year = StringField(
        "Other Academic Year",
        name="other-academic-year",
        id="other-academic-year-input",
        validators=[Optional()],
    )
    board_resolutions_semester = SelectField(
        "Semester",
        name="board-resolutions-semester",
        id="board-resolutions-semester",
        validators=[InputRequired()],
        choices=[
            ("", "Select a Semester"),
            ("1st Semester", "1st Semester"),
            ("2nd Semester", "2nd Semester"),
        ],
        default="",
    )
    board_resolutions_status = SelectField(
        "Status",
        name="board-resolutions-status",
        id="board-resolutions-status",
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
    board_resolutions_total_amount = FloatField(
        "Total Amount",
        name="board-resolutions-total-amount",
        id="board-resolutions-total-amount",
        validators=[InputRequired()],
    )
    board_resolutions_description = TextAreaField(
        "Description",
        name="board-resolutions-description",
        id="board-resolutions-description",
        validators=[InputRequired()],
    )
    board_resolutions_student_signatories = SelectMultipleField(
        "Student Signatories",
        name="board-resolutions-student-signatories",
        id="board-resolutions-student-signatories",
        validators=[Optional()],
        choices=[],
        coerce=coerce_int,
        validate_choice=False,
    )
    board_resolutions_prepared_by = SelectField(
        "Prepared By",
        name="board-resolutions-prepared-by",
        id="board-resolutions-prepared-by",
        validators=[InputRequired()],
        choices=[],
        coerce=coerce_int,
        validate_choice=False,
    )
    board_resolutions_approved_by = SelectField(
        "Approved By",
        name="board-resolutions-approved-by",
        id="board-resolutions-approved-by",
        validators=[InputRequired()],
        choices=[],
        coerce=coerce_int,
        validate_choice=False,
    )

    def __init__(self, events=None, academic_years=None, student_organizations=None, signatories=None, **kwargs):
        super().__init__(**kwargs)
        if events is not None:
            self.board_resolutions_events_id.choices = (
                [("", "Select Event"), ("None", "None")]
                + [(str(event.events_id), event.events_name) for event in events]
                + [("Other", "Other")]
            )
        if academic_years is not None:
            self.board_resolutions_academic_year.choices = (
                [("", "Select Academic Year")] + [(year, year) for year in academic_years] + [("Other", "Other")]
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
            all_users = [
                (
                    str(user.users_id),
                    f"{user.users_first_name} {user.users_last_name} - {user.users_student_organization_position}",
                )
                for org in student_organizations
                for user in org.users
            ]
            self.board_resolutions_prepared_by.choices = [("", "Select Preparer")] + user_choices
            self.board_resolutions_student_signatories.choices = all_users
        if signatories is not None:
            self.board_resolutions_approved_by.choices = [("", "Select Approver")] + [
                (
                    str(signatory.signatory_id),
                    f"{signatory.signatory_first_name} {signatory.signatory_last_name} - {signatory.signatory_position}",
                )
                for signatory in signatories
            ]

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False
        if self.board_resolutions_events_id.data == "Other":
            if not self.other_event_name.data:
                self.other_event_name.errors.append("Other event name is required.")
                return False
            # Store the custom name in a way the route can use; the event_id will be None
            self.board_resolutions_events_id.data = None
        elif self.board_resolutions_events_id.data == "None":
            self.board_resolutions_events_id.data = None
        if self.board_resolutions_academic_year.data == "Other":
            if not self.other_academic_year.data:
                self.other_academic_year.errors.append("Other academic year is required.")
                return False
            self.board_resolutions_academic_year.data = self.other_academic_year.data
        return True
