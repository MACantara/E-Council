"""Meeting forms for E-Council."""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, MultipleFileField
from wtforms import (
    StringField,
    SelectField,
    TextAreaField,
    DateTimeField,
    SelectMultipleField,
    HiddenField,
)
from wtforms.validators import InputRequired, Optional

from forms.validators import coerce_int


class MinutesOfTheMeetingForm(FlaskForm):
    """Form for adding and updating minutes of the meeting."""

    show_modal = HiddenField(
        name='show_modal',
        id='show_modal',
        default='false',
    )
    minutes_of_the_meeting_date = DateTimeField(
        'Date',
        name='minutes-of-the-meeting-date',
        id='minutes-of-the-meeting-date',
        validators=[InputRequired()],
        format='%Y-%m-%dT%H:%M',
    )
    minutes_of_the_meeting_semester = SelectField(
        'Semester',
        name='minutes-of-the-meeting-semester',
        id='minutes-of-the-meeting-semester',
        validators=[InputRequired()],
        choices=[
            ('', 'Select a Semester'),
            ('1st Semester', '1st Semester'),
            ('2nd Semester', '2nd Semester'),
        ],
        default='',
    )
    minutes_of_the_meeting_academic_year = SelectField(
        'Academic Year',
        name='minutes-of-the-meeting-academic-year',
        id='minutes-of-the-meeting-academic-year',
        validators=[InputRequired()],
        choices=[],
        default='',
        validate_choice=False,
    )
    other_academic_year = StringField(
        'Other Academic Year',
        name='other-academic-year',
        id='other-academic-year',
        validators=[Optional()],
    )
    minutes_of_the_meeting_status = SelectField(
        'Status',
        name='minutes-of-the-meeting-status',
        id='minutes-of-the-meeting-status',
        validators=[InputRequired()],
        choices=[
            ('', 'Select a Status'),
            ('Upcoming', 'Upcoming'),
            ('Postponed', 'Postponed'),
            ('Done', 'Done'),
            ('Cancelled', 'Cancelled'),
        ],
        default='',
    )
    minutes_of_the_meeting_presiding_officer = SelectField(
        'Presiding Officer',
        name='minutes-of-the-meeting-presiding-officer',
        id='minutes-of-the-meeting-presiding-officer',
        validators=[InputRequired()],
        choices=[],
        coerce=coerce_int,
        validate_choice=False,
    )
    minutes_of_the_meeting_attendees = SelectMultipleField(
        'Attendees',
        name='minutes-of-the-meeting-attendees',
        id='minutes-of-the-meeting-attendees',
        validators=[Optional()],
        choices=[],
        coerce=coerce_int,
        validate_choice=False,
    )
    minutes_of_the_meeting_agenda = TextAreaField(
        'Agenda',
        name='minutes-of-the-meeting-agenda',
        id='minutes-of-the-meeting-agenda',
        validators=[InputRequired()],
    )
    meeting_recording = FileField(
        'Meeting Recording',
        name='meeting-recording',
        id='meeting-recording',
        validators=[FileAllowed(['audio', 'video', 'mp3', 'mp4', 'webm', 'ogg', 'wav'], 'Audio or video files only.')],
    )
    minutes_of_the_meeting_adjourned = DateTimeField(
        'Adjourned',
        name='minutes-of-the-meeting-adjourned',
        id='minutes-of-the-meeting-adjourned',
        validators=[Optional()],
        format='%Y-%m-%dT%H:%M',
    )
    minutes_of_the_meeting_prepared_by = SelectField(
        'Prepared By',
        name='minutes-of-the-meeting-prepared-by',
        id='minutes-of-the-meeting-prepared-by',
        validators=[InputRequired()],
        choices=[],
        coerce=coerce_int,
        validate_choice=False,
    )
    minutes_of_the_meeting_prepared_by_display = StringField(
        'Prepared By Display',
        name='minutes-of-the-meeting-prepared-by-display',
        id='minutes-of-the-meeting-prepared-by-display',
        validators=[Optional()],
    )
    minutes_of_the_meeting_approved_by = SelectField(
        'Approved By',
        name='minutes-of-the-meeting-approved-by',
        id='minutes-of-the-meeting-approved-by',
        validators=[Optional()],
        choices=[],
        coerce=coerce_int,
        validate_choice=False,
    )
    minutes_of_the_meeting_noted_by = SelectField(
        'Noted By',
        name='minutes-of-the-meeting-noted-by',
        id='minutes-of-the-meeting-noted-by',
        validators=[InputRequired()],
        choices=[],
        coerce=coerce_int,
        validate_choice=False,
    )
    new_noted_by_title = StringField(
        'Title',
        name='new-noted-by-title',
        id='new-noted-by-title',
        validators=[Optional()],
    )
    new_noted_by_first_name = StringField(
        'First Name',
        name='new-noted-by-first-name',
        id='new-noted-by-first-name',
        validators=[Optional()],
    )
    new_noted_by_middle_name = StringField(
        'Middle Name',
        name='new-noted-by-middle-name',
        id='new-noted-by-middle-name',
        validators=[Optional()],
    )
    new_noted_by_last_name = StringField(
        'Last Name',
        name='new-noted-by-last-name',
        id='new-noted-by-last-name',
        validators=[Optional()],
    )
    new_noted_by_suffix = StringField(
        'Suffix',
        name='new-noted-by-suffix',
        id='new-noted-by-suffix',
        validators=[Optional()],
    )
    new_noted_by_position = StringField(
        'Position',
        name='new-noted-by-position',
        id='new-noted-by-position',
        validators=[Optional()],
    )
    new_noted_by_department = StringField(
        'Department',
        name='new-noted-by-department',
        id='new-noted-by-department',
        validators=[Optional()],
    )
    photo_documentation = MultipleFileField(
        'Photo Documentation',
        name='photo-documentation',
        id='photo-documentation',
        validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Images only.')],
    )

    def __init__(self, academic_years=None, student_organizations=None, signatories=None, users=None, **kwargs):
        super().__init__(**kwargs)
        if academic_years is not None:
            self.minutes_of_the_meeting_academic_year.choices = (
                [('', 'Select an Academic Year')] +
                [(year, year) for year in academic_years] +
                [('Other', 'Other A.Y.')]
            )
        if student_organizations is not None:
            org_user_choices = [
                (org.student_organizations_name, [
                    (str(user.users_id), f'{user.users_first_name} {user.users_last_name} - {user.users_student_organization_position}')
                    for user in org.users
                ])
                for org in student_organizations
            ]
            self.minutes_of_the_meeting_presiding_officer.choices = [('', 'Select a Presiding Officer')] + org_user_choices
            self.minutes_of_the_meeting_attendees.choices = [
                (str(user.users_id), f'{user.users_first_name} {user.users_last_name} - {user.users_student_organization_position}')
                for org in student_organizations
                for user in org.users
            ]
            self.minutes_of_the_meeting_prepared_by.choices = [('', 'Select a User')] + org_user_choices
            self.minutes_of_the_meeting_noted_by.choices = (
                [('', 'Select a Signatory'), ('add-new-noted-by', 'Add new signatory')] +
                [(str(signatory.signatory_id), f'{signatory.signatory_first_name} {signatory.signatory_last_name} - {signatory.signatory_position}')
                 for signatory in signatories]
            )
        if users is not None:
            self.minutes_of_the_meeting_approved_by.choices = (
                [('', 'Select a User')] +
                [(str(user.users_id), f'{user.users_first_name} {user.users_last_name} - {user.users_student_organization_position}')
                 for user in users if user.users_role == 'Student Council Officer']
            )

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False
        if self.minutes_of_the_meeting_academic_year.data == 'Other':
            if not self.other_academic_year.data:
                self.other_academic_year.errors.append('Other academic year is required.')
                return False
            self.minutes_of_the_meeting_academic_year.data = self.other_academic_year.data
        return True
