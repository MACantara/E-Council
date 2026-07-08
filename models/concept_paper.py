"""
Concept paper and related models for E-Council.
"""

from datetime import datetime
from models.base import db
from models.department import Departments
from models.user import Users

# Note: Signatories model will need to be imported from meeting models
# This creates a circular dependency that needs to be resolved
# For now, we'll use string references to avoid import errors


class ConceptPaperForms(db.Model):
    __tablename__ = 'concept_paper_forms'

    concept_paper_forms_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    concept_paper_forms_semester = db.Column(db.String(50), nullable=True)
    concept_paper_forms_academic_year = db.Column(db.String(50), nullable=True)
    concept_paper_forms_status = db.Column(db.String(50), nullable=True)
    concept_paper_forms_departments_id = db.Column(db.Integer, db.ForeignKey('departments.departments_id'), nullable=True)
    concept_paper_forms_endorsed_by = db.Column(db.Integer, db.ForeignKey('signatories.signatory_id'), nullable=True)
    concept_paper_forms_recommending_approval_by = db.Column(db.Integer, db.ForeignKey('signatories.signatory_id'), nullable=True)
    concept_paper_forms_approved_by = db.Column(db.Integer, db.ForeignKey('signatories.signatory_id'), nullable=True)
    concept_paper_forms_subject = db.Column(db.String(255), nullable=True)
    concept_paper_forms_date = db.Column(db.Date, nullable=True)
    concept_paper_forms_body = db.Column(db.Text, nullable=True)
    concept_paper_forms_event_start_date_and_time = db.Column(db.DateTime, nullable=True)
    concept_paper_forms_event_end_date_and_time = db.Column(db.DateTime, nullable=True)
    concept_paper_forms_location = db.Column(db.String(255), nullable=True)
    concept_paper_forms_participants = db.Column(db.String(255), nullable=True)
    concept_paper_forms_budget = db.Column(db.String(255), nullable=True)
    concept_paper_forms_descriptions = db.Column(db.Text, nullable=True)
    concept_paper_forms_expected_number_of_participants = db.Column(db.Text, nullable=True)
    concept_paper_forms_prepared_by = db.Column(db.Integer, db.ForeignKey('users.users_id'), nullable=True)
    concept_paper_forms_signed_and_reviewed_by = db.Column(db.Integer, db.ForeignKey('users.users_id'), nullable=True)

    # Relationships - using string references to avoid circular imports
    endorsed_by_signatory = db.relationship('Signatories', foreign_keys=[concept_paper_forms_endorsed_by])
    recommending_approval_by_signatory = db.relationship('Signatories', foreign_keys=[concept_paper_forms_recommending_approval_by])
    approved_by_signatory = db.relationship('Signatories', foreign_keys=[concept_paper_forms_approved_by])
    prepared_by_user = db.relationship('Users', foreign_keys=[concept_paper_forms_prepared_by])
    signed_and_reviewed_by_user = db.relationship('Users', foreign_keys=[concept_paper_forms_signed_and_reviewed_by])
    department = db.relationship('Departments', foreign_keys=[concept_paper_forms_departments_id])
    objectives = db.relationship('ObjectivesOfTheActivity', 
                               backref='concept_paper',
                               lazy='dynamic',
                               cascade="all, delete-orphan",
                               primaryjoin="ConceptPaperForms.concept_paper_forms_id==ObjectivesOfTheActivity.objectives_of_the_activity_concept_paper_forms_id")

    learning_outcomes = db.relationship('LearningOutcomes', 
                                      backref='concept_paper',
                                      lazy='dynamic',
                                      cascade="all, delete-orphan",
                                      primaryjoin="ConceptPaperForms.concept_paper_forms_id==LearningOutcomes.learning_outcomes_concept_paper_forms_id")

    def __repr__(self):
        return f'<ConceptPaperForms {self.concept_paper_forms_id}: {self.concept_paper_forms_subject}>'


class ObjectivesOfTheActivity(db.Model):
    __tablename__ = 'objectives_of_the_activity'

    objectives_of_the_activity_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    objectives_of_the_activity_concept_paper_forms_id = db.Column(db.Integer, db.ForeignKey('concept_paper_forms.concept_paper_forms_id'), nullable=False)
    objectives_of_the_activity_content = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<ObjectivesOfTheActivity {self.objectives_of_the_activity_id}: {self.objectives_of_the_activity_content}>'


class LearningOutcomes(db.Model):
    __tablename__ = 'learning_outcomes'

    learning_outcomes_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    learning_outcomes_concept_paper_forms_id = db.Column(db.Integer, db.ForeignKey('concept_paper_forms.concept_paper_forms_id'), nullable=False)
    learning_outcomes_content = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<LearningOutcomes {self.learning_outcomes_id}: {self.learning_outcomes_content}>'


class ExcuseLetterForms(db.Model):
    __tablename__ = 'excuse_letter_forms'

    excuse_letter_forms_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    excuse_letter_forms_concept_paper_forms_id = db.Column(db.Integer, db.ForeignKey('concept_paper_forms.concept_paper_forms_id'), nullable=True)
    excuse_letter_forms_department_office_unit = db.Column(db.String(255), nullable=True)
    excuse_letter_forms_personnel_in_charge_forms_id = db.Column(db.Integer, db.ForeignKey('signatories.signatory_id'), nullable=True)
    excuse_letter_forms_dean = db.Column(db.Integer, db.ForeignKey('signatories.signatory_id'), nullable=True)
    excuse_letter_forms_noted_by = db.Column(db.Integer, db.ForeignKey('signatories.signatory_id'), nullable=True)

    concept_paper_form = db.relationship('ConceptPaperForms', backref='excuse_letter_forms')
    personnel_in_charge_signatory = db.relationship('Signatories', foreign_keys=[excuse_letter_forms_personnel_in_charge_forms_id])
    dean_signatory = db.relationship('Signatories', foreign_keys=[excuse_letter_forms_dean])
    noted_by_signatory = db.relationship('Signatories', foreign_keys=[excuse_letter_forms_noted_by])

    def __repr__(self):
        return f'<ExcuseLetterForms {self.excuse_letter_forms_id}>'


class ActivityReportForms(db.Model):
    __tablename__ = 'activity_report_forms'

    activity_report_forms_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    activity_report_forms_concept_paper_forms_id = db.Column(db.Integer, db.ForeignKey('concept_paper_forms.concept_paper_forms_id'), nullable=True)
    activity_report_forms_nature_of_the_activity = db.Column(db.String(255), nullable=True)
    activity_report_forms_personnel_in_charge_forms_id = db.Column(db.Integer, db.ForeignKey('personnel_in_charge_forms.personnel_in_charge_forms_id'), nullable=True)
    activity_report_forms_contact_numbers = db.Column(db.String(255), nullable=True)
    activity_report_forms_prepared_by = db.Column(db.Integer, db.ForeignKey('users.users_id'), nullable=True)
    activity_report_forms_noted_by = db.Column(db.Integer, db.ForeignKey('signatories.signatory_id'), nullable=True)
    activity_report_date_submission = db.Column(db.Date, nullable=True)

    concept_paper_form = db.relationship('ConceptPaperForms', backref='activity_report_forms')
    personnel_in_charge_form = db.relationship('PersonnelInChargeForms', backref='activity_report_forms')
    prepared_by_user = db.relationship('Users', foreign_keys=[activity_report_forms_prepared_by])
    noted_by_signatory = db.relationship('Signatories', foreign_keys=[activity_report_forms_noted_by])

    def __repr__(self):
        return f'<ActivityReportForms {self.activity_report_forms_id}>'