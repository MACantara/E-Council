"""Concept paper and supporting forms for E-Council."""

from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SelectField,
    TextAreaField,
    DateField,
    DateTimeField,
    FieldList,
)
from wtforms.validators import InputRequired, Optional

from forms.validators import coerce_int


class ConceptPaperForm(FlaskForm):
    """Form for creating and updating a concept paper and its related forms."""

    # Concept paper details
    concept_paper_date_of_submission = DateTimeField(
        'Date of Submission',
        name='concept-paper-date-of-submission',
        id='concept-paper-date-of-submission',
        validators=[InputRequired()],
        format='%Y-%m-%dT%H:%M',
    )
    concept_paper_subject = StringField(
        'Subject',
        name='concept-paper-subject',
        id='concept-paper-subject',
        validators=[InputRequired()],
    )
    concept_paper_academic_year = SelectField(
        'Academic Year',
        name='concept-paper-academic-year',
        id='concept-paper-academic-year',
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
    concept_paper_semester = SelectField(
        'Semester',
        name='concept-paper-semester',
        id='concept-paper-semester',
        validators=[InputRequired()],
        choices=[
            ('', 'Select a Semester'),
            ('1st Semester', '1st Semester'),
            ('2nd Semester', '2nd Semester'),
        ],
        default='',
    )
    concept_paper_status = SelectField(
        'Status',
        name='concept-paper-status',
        id='concept-paper-status',
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
    concept_paper_event_start_date_and_time = DateTimeField(
        'Event Start Date and Time',
        name='concept-paper-event-start-date-and-time',
        id='concept-paper-event-start-date-and-time',
        validators=[InputRequired()],
        format='%Y-%m-%dT%H:%M',
    )
    concept_paper_event_end_date_and_time = DateTimeField(
        'Event End Date and Time',
        name='concept-paper-event-end-date-and-time',
        id='concept-paper-event-end-date-and-time',
        validators=[InputRequired()],
        format='%Y-%m-%dT%H:%M',
    )
    concept_paper_location = StringField(
        'Location',
        name='concept-paper-location',
        id='concept-paper-location',
        validators=[Optional()],
    )
    concept_paper_participants = StringField(
        'Participants',
        name='concept-paper-participants',
        id='concept-paper-participants',
        validators=[Optional()],
    )
    concept_paper_budget = StringField(
        'Budget',
        name='concept-paper-budget',
        id='concept-paper-budget',
        validators=[Optional()],
    )
    concept_paper_descriptions = TextAreaField(
        'Descriptions',
        name='concept-paper-descriptions',
        id='concept-paper-descriptions',
        validators=[Optional()],
    )
    concept_paper_expected_number_of_participants = StringField(
        'Expected Number of Participants',
        name='concept-paper-expected-number-of-participants',
        id='concept-paper-expected-number-of-participants',
        validators=[Optional()],
    )
    concept_paper_body = TextAreaField(
        'Body',
        name='concept-paper-body',
        id='concept-paper-body',
        validators=[Optional()],
    )
    concept_paper_objectives = FieldList(
        StringField(
            'Objective',
            name='concept-paper-objectives',
            validators=[Optional()],
        ),
        name='concept-paper-objectives',
        min_entries=1,
    )
    concept_paper_learning_outcomes = FieldList(
        StringField(
            'Learning Outcome',
            name='concept-paper-learning-outcomes',
            validators=[Optional()],
        ),
        name='concept-paper-learning-outcomes',
        min_entries=1,
    )
    concept_paper_prepared_by = SelectField(
        'Prepared By',
        name='concept-paper-prepared-by',
        id='concept-paper-prepared-by',
        validators=[Optional()],
        choices=[],
        coerce=coerce_int,
        validate_choice=False,
    )
    concept_paper_signed_and_reviewed_by = SelectField(
        'Signed and Reviewed By',
        name='concept-paper-signed-and-reviewed-by',
        id='concept-paper-signed-and-reviewed-by',
        validators=[Optional()],
        choices=[],
        coerce=coerce_int,
        validate_choice=False,
    )
    concept_paper_endorsed_by = SelectField(
        'Endorsed By',
        name='concept-paper-endorsed-by',
        id='concept-paper-endorsed-by',
        validators=[Optional()],
        choices=[],
        coerce=coerce_int,
        validate_choice=False,
    )
    concept_paper_recommending_approval_by = SelectField(
        'Recommending Approval By',
        name='concept-paper-recommending-approval-by',
        id='concept-paper-recommending-approval-by',
        validators=[Optional()],
        choices=[],
        coerce=coerce_int,
        validate_choice=False,
    )
    concept_paper_approved_by = SelectField(
        'Approved By',
        name='concept-paper-approved-by',
        id='concept-paper-approved-by',
        validators=[Optional()],
        choices=[],
        coerce=coerce_int,
        validate_choice=False,
    )

    # Excuse letter form
    excuse_letter_department_office_unit = StringField(
        'Department / Office / Unit',
        name='excuse-letter-department-office-unit',
        id='excuse-letter-department-office-unit',
        validators=[Optional()],
    )
    excuse_letter_faculty_in_charge = SelectField(
        'Faculty In Charge',
        name='excuse-letter-faculty-in-charge',
        id='excuse-letter-faculty-in-charge',
        validators=[Optional()],
        choices=[],
        coerce=coerce_int,
        validate_choice=False,
    )
    excuse_letter_dean = SelectField(
        'Dean',
        name='excuse-letter-dean',
        id='excuse-letter-dean',
        validators=[Optional()],
        choices=[],
        coerce=coerce_int,
        validate_choice=False,
    )
    excuse_letter_noted_by = SelectField(
        'Noted By',
        name='excuse-letter-noted-by',
        id='excuse-letter-noted-by',
        validators=[Optional()],
        choices=[],
        coerce=coerce_int,
        validate_choice=False,
    )

    # Activity report form
    activity_report_nature_of_the_activity = StringField(
        'Nature of the Activity',
        name='activity-report-nature-of-the-activity',
        id='activity-report-nature-of-the-activity',
        validators=[Optional()],
    )
    activity_report_date_submission = DateField(
        'Date of Submission',
        name='activity-report-date-submission',
        id='activity-report-date-submission',
        validators=[Optional()],
        format='%Y-%m-%d',
    )
    activity_report_contact_numbers = StringField(
        'Contact Numbers',
        name='activity-report-contact-numbers',
        id='activity-report-contact-numbers',
        validators=[Optional()],
    )
    activity_report_prepared_by = SelectField(
        'Prepared By',
        name='activity-report-prepared-by',
        id='activity-report-prepared-by',
        validators=[Optional()],
        choices=[],
        coerce=coerce_int,
        validate_choice=False,
    )
    activity_report_noted_by = SelectField(
        'Noted By',
        name='activity-report-noted-by',
        id='activity-report-noted-by',
        validators=[Optional()],
        choices=[],
        coerce=coerce_int,
        validate_choice=False,
    )

    # Personnel in charge form
    personnel_in_charge = StringField(
        'Name of Personnel In Charge',
        name='personnel-in-charge',
        id='personnel-in-charge',
        validators=[Optional()],
    )
    personnel_in_charge_noted_by_college_dean = SelectField(
        'Noted By College Dean',
        name='personnel-in-charge-noted-by-college-dean',
        id='personnel-in-charge-noted-by-college-dean',
        validators=[Optional()],
        choices=[],
        coerce=coerce_int,
        validate_choice=False,
    )
    personnel_in_charge_noted_by_sas = SelectField(
        'Noted By SAS',
        name='personnel-in-charge-noted-by-sas',
        id='personnel-in-charge-noted-by-sas',
        validators=[Optional()],
        choices=[],
        coerce=coerce_int,
        validate_choice=False,
    )

    # Learning journal form
    learning_journal_date = DateField(
        'Date',
        name='learning-journal-date',
        id='learning-journal-date',
        validators=[Optional()],
        format='%Y-%m-%d',
    )
    learning_journal_checked_by = SelectField(
        'Checked By',
        name='learning-journal-checked-by',
        id='learning-journal-checked-by',
        validators=[Optional()],
        choices=[],
        coerce=coerce_int,
        validate_choice=False,
    )

    def __init__(self, academic_years=None, users=None, signatories=None, **kwargs):
        super().__init__(**kwargs)
        if academic_years is not None:
            self.concept_paper_academic_year.choices = (
                [('', 'Select an Academic Year')] +
                [(year, year) for year in academic_years] +
                [('Other', 'Other')]
            )
        if users is not None:
            user_choices = [(str(user.users_id), f'{user.users_first_name} {user.users_last_name}') for user in users]
            self.concept_paper_prepared_by.choices = [('', 'Select User')] + user_choices
            self.concept_paper_signed_and_reviewed_by.choices = [('', 'Select User')] + user_choices
            self.activity_report_prepared_by.choices = [('', 'Select User')] + user_choices
        if signatories is not None:
            signatory_choices = [(str(signatory.signatory_id), f'{signatory.signatory_first_name} {signatory.signatory_last_name} - {signatory.signatory_position}') for signatory in signatories]
            self.concept_paper_endorsed_by.choices = [('', 'Select Signatory')] + signatory_choices
            self.concept_paper_recommending_approval_by.choices = [('', 'Select Signatory')] + signatory_choices
            self.concept_paper_approved_by.choices = [('', 'Select Signatory')] + signatory_choices
            self.excuse_letter_faculty_in_charge.choices = [('', 'Select Signatory')] + signatory_choices
            self.excuse_letter_dean.choices = [('', 'Select Signatory')] + signatory_choices
            self.excuse_letter_noted_by.choices = [('', 'Select Signatory')] + signatory_choices
            self.activity_report_noted_by.choices = [('', 'Select Signatory')] + signatory_choices
            self.personnel_in_charge_noted_by_college_dean.choices = [('', 'Select Signatory')] + signatory_choices
            self.personnel_in_charge_noted_by_sas.choices = [('', 'Select Signatory')] + signatory_choices
            self.learning_journal_checked_by.choices = [('', 'Select Signatory')] + signatory_choices

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False
        if self.concept_paper_academic_year.data == 'Other':
            if not self.other_academic_year.data:
                self.other_academic_year.errors.append('Other academic year is required.')
                return False
            self.concept_paper_academic_year.data = self.other_academic_year.data
        return True
