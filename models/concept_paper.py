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


class PersonnelInChargeForms(db.Model):
    __tablename__ = 'personnel_in_charge_forms'

    personnel_in_charge_forms_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    personnel_in_charge_forms_name = db.Column(db.String(255), nullable=False)
    personnel_in_charge_forms_position = db.Column(db.String(255), nullable=False)
    personnel_in_charge_forms_department = db.Column(db.String(255), nullable=False)
    personnel_in_charge_forms_contact_number = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f'<PersonnelInChargeForms {self.personnel_in_charge_forms_id}>'


class LearningJournalForms(db.Model):
    __tablename__ = 'learning_journal_forms'

    learning_journal_forms_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    learning_journal_forms_name = db.Column(db.String(255), nullable=False)
    learning_journal_forms_date = db.Column(db.Date, nullable=False)
    learning_journal_forms_time = db.Column(db.Time, nullable=False)
    learning_journal_forms_location = db.Column(db.String(255), nullable=False)
    learning_journal_forms_activity = db.Column(db.String(255), nullable=False)
    learning_journal_forms_role = db.Column(db.String(255), nullable=False)
    learning_journal_forms_prepared_by = db.Column(db.Integer, db.ForeignKey('users.users_id'), nullable=True)

    prepared_by_user = db.relationship('Users', foreign_keys=[learning_journal_forms_prepared_by])

    def __repr__(self):
        return f'<LearningJournalForms {self.learning_journal_forms_id}>'


class Observations(db.Model):
    __tablename__ = 'observations'

    observations_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    observations_learning_journal_forms_id = db.Column(db.Integer, db.ForeignKey('learning_journal_forms.learning_journal_forms_id'), nullable=False)
    observations_content = db.Column(db.Text, nullable=False)

    learning_journal_form = db.relationship('LearningJournalForms', backref='observations')

    def __repr__(self):
        return f'<Observations {self.observations_id}>'


class Learnings(db.Model):
    __tablename__ = 'learnings'

    learnings_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    learnings_learning_journal_forms_id = db.Column(db.Integer, db.ForeignKey('learning_journal_forms.learning_journal_forms_id'), nullable=False)
    learnings_content = db.Column(db.Text, nullable=False)

    learning_journal_form = db.relationship('LearningJournalForms', backref='learnings')

    def __repr__(self):
        return f'<Learnings {self.learnings_id}>'


class ParentGuardianConsentForms(db.Model):
    __tablename__ = 'parent_guardian_consent_forms'

    parent_guardian_consent_forms_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    parent_guardian_consent_forms_concept_paper_forms_id = db.Column(db.Integer, db.ForeignKey('concept_paper_forms.concept_paper_forms_id'), nullable=True)
    parent_guardian_consent_forms_parent_guardian_name = db.Column(db.String(255), nullable=False)
    parent_guardian_consent_forms_parent_guardian_contact_number = db.Column(db.String(20), nullable=False)
    parent_guardian_consent_forms_parent_guardian_address = db.Column(db.String(255), nullable=False)
    parent_guardian_consent_forms_parent_guardian_relationship = db.Column(db.String(255), nullable=False)
    parent_guardian_consent_forms_student_name = db.Column(db.String(255), nullable=False)
    parent_guardian_consent_forms_student_year_and_section = db.Column(db.String(255), nullable=False)
    parent_guardian_consent_forms_student_contact_number = db.Column(db.String(20), nullable=False)
    parent_guardian_consent_forms_consent = db.Column(db.String(10), nullable=False)
    parent_guardian_consent_forms_date = db.Column(db.Date, nullable=False)
    parent_guardian_consent_forms_signature = db.Column(db.String(255), nullable=True)

    concept_paper_form = db.relationship('ConceptPaperForms', backref='parent_guardian_consent_forms')

    def __repr__(self):
        return f'<ParentGuardianConsentForms {self.parent_guardian_consent_forms_id}>'


# Association tables for ActivityReportForms
class ActivityReportFormsActivityStrengths(db.Model):
    __tablename__ = 'activity_report_forms_activity_strengths'

    activity_report_forms_id = db.Column(db.Integer, db.ForeignKey('activity_report_forms.activity_report_forms_id'), primary_key=True, nullable=False)
    activity_strengths_id = db.Column(db.Integer, db.ForeignKey('activity_strengths.activity_strengths_id'), primary_key=True, nullable=False)

    activity_report_form = db.relationship('ActivityReportForms', backref='activity_strengths_assoc')
    activity_strength = db.relationship('ActivityStrengths', backref='activity_report_forms_assoc')

    def __repr__(self):
        return f'<ActivityReportFormsActivityStrengths({self.activity_report_forms_id}, {self.activity_strengths_id})>'


class ActivityReportFormsActivityWeaknesses(db.Model):
    __tablename__ = 'activity_report_forms_activity_weaknesses'

    activity_report_forms_id = db.Column(db.Integer, db.ForeignKey('activity_report_forms.activity_report_forms_id'), primary_key=True, nullable=False)
    activity_weaknesses_id = db.Column(db.Integer, db.ForeignKey('activity_weaknesses.activity_weaknesses_id'), primary_key=True, nullable=False)

    activity_report_form = db.relationship('ActivityReportForms', backref='activity_weaknesses_assoc')
    activity_weakness = db.relationship('ActivityWeaknesses', backref='activity_report_forms_assoc')

    def __repr__(self):
        return f'<ActivityReportFormsActivityWeaknesses({self.activity_report_forms_id}, {self.activity_weaknesses_id})>'


class ActivityReportFormsActivityRecommendations(db.Model):
    __tablename__ = 'activity_report_forms_activity_recommendations'

    activity_report_forms_id = db.Column(db.Integer, db.ForeignKey('activity_report_forms.activity_report_forms_id'), primary_key=True, nullable=False)
    activity_recommendations_id = db.Column(db.Integer, db.ForeignKey('activity_recommendations.activity_recommendations_id'), primary_key=True, nullable=False)

    activity_report_form = db.relationship('ActivityReportForms', backref='activity_recommendations_assoc')
    activity_recommendation = db.relationship('ActivityRecommendations', backref='activity_report_forms_assoc')

    def __repr__(self):
        return f'<ActivityReportFormsActivityRecommendations({self.activity_report_forms_id}, {self.activity_recommendations_id})>'