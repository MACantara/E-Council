import os
import re
from flask import Flask, render_template, request, flash, redirect, url_for, session, jsonify
from jinja2 import Environment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_migrate import Migrate
from flask_mail import Mail, Message
from flask_wtf import CSRFProtect
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from markupsafe import Markup
from datetime import datetime, timedelta
from sqlalchemy import Enum
from decimal import Decimal, InvalidOperation

import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url

# Load environment variables from .env file
load_dotenv()

# Flask Configuration
app = Flask(__name__, template_folder="templates")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")

# Flask Mail Configuration
app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT"))
app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS") == 'True'
app.config["MAIL_USE_SSL"] = os.getenv("MAIL_USE_SSL") == 'True'
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")

s = URLSafeTimedSerializer(app.config["SECRET_KEY"])

db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Cloudinary Configuration       
cloudinary.config( 
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"), 
    api_key = os.getenv("CLOUDINARY_API_KEY"), 
    api_secret = os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

csrf = CSRFProtect(app)

# Ensure the upload folder exists
UPLOAD_FOLDER = 'uploads/receipts'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Users, int(user_id))

@login_manager.unauthorized_handler
def unauthorized():
    flash("You need to be logged in to access this page.", "error")
    return redirect(url_for("login"))

# Database models
class Users(db.Model, UserMixin):
    __tablename__ = "users"

    users_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    users_profile_picture = db.Column(db.String(255), nullable=True)
    users_profile_picture_cloudinary_public_id = db.Column(db.String(255), nullable=True)
    users_first_name = db.Column(db.String(50), nullable=False)
    users_last_name = db.Column(db.String(50), nullable=False)
    users_username = db.Column(db.String(50), unique=True, nullable=False)
    users_email = db.Column(db.String(100), unique=True, nullable=False)
    
    # Changed users_department to reference the Departments model
    users_departments_id = db.Column(db.Integer, db.ForeignKey('departments.departments_id'), nullable=False)
    
    users_role = db.Column(db.Enum(
        'Student Council Officer',
        'Faculty',
        'Staff',
        'Admin',
        name='role_enum'
    ), nullable=False)

    users_student_organization = db.Column(db.Integer, db.ForeignKey('student_organizations.student_organizations_id'), nullable=True)

    users_student_organization_position = db.Column(db.Enum(
        'President',
        'Vice President',
        'Secretary',
        'Treasurer',
        'Auditor',
        'Business Manager',
        'Public Relations Officer',
        '1st Year IT Representative',
        '1st Year CS Representative',
        '2nd Year IT Representative',
        '2nd Year CS Representative',
        '3rd Year IT Representative',
        '3rd Year CS Representative',
        '4th Year IT Representative',
        '4th Year CS Representative',
        name='position_enum'
    ), nullable=True)

    users_home_address = db.Column(db.String(255), nullable=True)
    users_contact_number = db.Column(db.String(20), nullable=True)
    users_signature = db.Column(db.String(255), nullable=True)
    users_signature_cloudinary_public_id = db.Column(db.String(255), nullable=True)
    users_password = db.Column(db.String(255), nullable=False)
    users_email_verified = db.Column(db.Integer, nullable=False)

    # Relationship to Departments
    department = db.relationship('Departments', backref='users')
    
    student_organization = db.relationship("StudentOrganizations", backref="users")

    def set_password(self, password):
        self.users_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.users_password, password)

    def get_id(self):
        return str(self.users_id)

    def __repr__(self):
        return f"Users({self.users_id}, {self.users_profile_picture}, {self.users_first_name}, {self.users_last_name}, {self.users_username}, {self.users_email}, {self.users_departments_id}, {self.users_role}, {self.users_student_organization}, {self.users_student_organization_position}, {self.users_password}, {self.users_email_verified}, {self.users_home_address}, {self.users_contact_number}, {self.users_signature})"

class Departments(db.Model):
    __tablename__ = "departments"

    departments_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    departments_name = db.Column(db.String(255), nullable=False, unique=True)

    def __repr__(self):
        return f"Departments({self.departments_id}, {self.departments_name})"

class EmailVerification(db.Model):
    __tablename__ = "email_verification"

    email_verification_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    email_verification_users_id = db.Column(db.Integer, db.ForeignKey('users.users_id'), nullable=False)
    email_verification_token = db.Column(db.String(255), nullable=False)
    email_verification_new_email = db.Column(db.String(100), nullable=False)
    email_verification_created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

    user = db.relationship('Users', backref=db.backref('email_verifications', lazy=True))

class PasswordReset(db.Model):
    __tablename__ = "password_reset"

    password_reset_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    password_reset_users_id = db.Column(db.Integer, db.ForeignKey('users.users_id'), nullable=False)
    password_reset_selector = db.Column(db.String(255), nullable=False)
    password_reset_token = db.Column(db.String(255), nullable=False)
    password_reset_expires = db.Column(db.DateTime, nullable=False)

    user = db.relationship('Users', backref=db.backref('password_resets', lazy=True))

class LoginAttempts(db.Model):
    __tablename__ = "login_attempts"

    login_attempt_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    login_attempt_ip_address = db.Column(db.String(45), nullable=False)
    login_attempt_count = db.Column(db.Integer, nullable=False, default=0)
    login_attempt_last_attempt_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class Events(db.Model):
    __tablename__ = "events"

    events_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    events_concept_paper_forms_id = db.Column(db.Integer, db.ForeignKey('concept_paper_forms.concept_paper_forms_id'), nullable=True)
    events_name = db.Column(db.String(255), nullable=True)
    events_semester = db.Column(db.String(50), nullable=False)
    events_academic_year = db.Column(db.String(50), nullable=False)
    events_start_date_and_time = db.Column(db.DateTime, nullable=True)
    events_end_date_and_time = db.Column(db.DateTime, nullable=True)
    events_venue = db.Column(db.String(255), nullable=True)
    events_budget = db.Column(db.String(255), nullable=True)
    events_status = db.Column(db.String(50), nullable=True)
    events_description = db.Column(db.Text, nullable=True)
    events_remarks = db.Column(db.String(255), nullable=True)

    # Relationship to the BoardResolutions model
    board_resolutions = db.relationship('BoardResolutions', back_populates='events')

    def __repr__(self):
        return f"Events({self.events_id}, {self.events_name}, {self.events_semester}, {self.events_academic_year}, {self.events_start_date_and_time}, {self.events_end_date_and_time}, {self.events_venue}, {self.events_budget}, {self.events_status}, {self.events_description}, {self.events_remarks}, {self.events_concept_paper_forms_id})"

class DepartmentsEvents(db.Model):
    __tablename__ = "departments_events"

    # Composite primary key: departments_id and events_id
    departments_id = db.Column(db.Integer, db.ForeignKey('departments.departments_id'), primary_key=True, nullable=False)
    events_id = db.Column(db.Integer, db.ForeignKey('events.events_id'), primary_key=True, nullable=False)

    # Relationship to Departments and Events models
    department = db.relationship('Departments', backref='departments_events')
    event = db.relationship('Events', backref='departments_events')

    def __repr__(self):
        return f"DepartmentsEvents({self.departments_id}, {self.events_id})"

class EventInvitations(db.Model):
    __tablename__ = "event_invitations"

    event_invitations_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    event_invitations_events_id = db.Column(db.Integer, db.ForeignKey('events.events_id'), nullable=False)
    event_invitations_email = db.Column(db.String(255), nullable=False)
    event_invitations_token = db.Column(db.String(64), nullable=False)
    event_invitations_created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)

    # Relationship to Events model
    event = db.relationship('Events', backref='event_invitations')

    def __repr__(self):
        return f"EventInvitations({self.event_invitations_id}, {self.event_invitations_events_id}, {self.event_invitations_email}, {self.event_invitations_token}, {self.event_invitations_created_at})"

class TransactionHistory(db.Model):
    __tablename__ = 'transaction_history'

    transaction_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    events_id = db.Column(db.Integer, db.ForeignKey('events.events_id'), index=True, nullable=True)
    transaction_name = db.Column(db.String(255), nullable=True)
    transaction_date = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    transaction_unit_amount = db.Column(db.Numeric(10, 2), nullable=True)
    transaction_unit_price = db.Column(db.Numeric(10, 2), nullable=True)
    transaction_total = db.column_property(transaction_unit_amount * transaction_unit_price)
    transaction_category = db.Column(db.String(255), nullable=True)
    transaction_type = db.Column(db.Enum('Expense', 'Income', name='transaction_type_enum'), nullable=True)
    transaction_receipt_cloudinary_url = db.Column(db.String(255), nullable=True)
    transaction_receipt_cloudinary_public_id = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<TransactionHistory {self.transaction_name}>'

class BoardResolutions(db.Model):
    __tablename__ = 'board_resolutions'

    board_resolutions_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    board_resolutions_date = db.Column(db.DateTime, default=datetime.utcnow)
    board_resolutions_events_id = db.Column(db.Integer, db.ForeignKey('events.events_id'), nullable=True)
    board_resolutions_title = db.Column(db.String(255), nullable=True)
    board_resolutions_academic_year = db.Column(db.String(50), nullable=True)
    board_resolutions_semester = db.Column(db.String(50), nullable=True)
    board_resolutions_status = db.Column(db.String(50), nullable=True)
    board_resolutions_total_amount = db.Column(db.Numeric(20, 2), nullable=True)
    board_resolutions_description = db.Column(db.Text, nullable=True)
    board_resolutions_prepared_by = db.Column(db.Integer, db.ForeignKey('users.users_id'), nullable=True)
    board_resolutions_approved_by = db.Column(db.Integer, db.ForeignKey('signatories.signatory_id'), nullable=True)

    # Relationship to the Events model (if you have one)
    events = db.relationship('Events', back_populates='board_resolutions')
    prepared_by_user = db.relationship('Users', foreign_keys=[board_resolutions_prepared_by])
    approved_by_signatory = db.relationship('Signatories', foreign_keys=[board_resolutions_approved_by])

    def __repr__(self):
        return f'<BoardResolution {self.board_resolutions_id}: {self.board_resolutions_description}>'

class BoardResolutionsStudentSignatories(db.Model):
    __tablename__ = 'board_resolutions_student_signatories'

    board_resolutions_id = db.Column(db.Integer, db.ForeignKey('board_resolutions.board_resolutions_id'), primary_key=True, nullable=False)
    board_resolutions_users_id = db.Column(db.Integer, db.ForeignKey('users.users_id'), primary_key=True, nullable=False)

    board_resolution = db.relationship('BoardResolutions', backref='student_signatories')
    user = db.relationship('Users', backref='board_resolutions_signatories')

    def __repr__(self):
        return f'<BoardResolutionsStudentSignatories(board_resolutions_id={self.board_resolutions_id}, board_resolutions_users_id={self.board_resolutions_users_id})>'

class MinutesOfTheMeeting(db.Model):
    __tablename__ = 'minutes_of_the_meeting'

    minutes_of_the_meeting_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    minutes_of_the_meeting_date = db.Column(db.DateTime, nullable=False)
    minutes_of_the_meeting_semester = db.Column(db.String(50), nullable=False)
    minutes_of_the_meeting_academic_year = db.Column(db.String(50), nullable=False)
    minutes_of_the_meeting_status = db.Column(db.String(50), nullable=False)
    minutes_of_the_meeting_presiding_officer = db.Column(db.String(100), nullable=False)
    minutes_of_the_meeting_agenda = db.Column(db.Text, nullable=False)
    minutes_of_the_meeting_notes = db.Column(db.Text, nullable=True)
    minutes_of_the_meeting_adjourned = db.Column(db.DateTime, nullable=True)
    minutes_of_the_meeting_approved_by = db.Column(db.Integer, db.ForeignKey('users.users_id'), nullable=True)
    minutes_of_the_meeting_prepared_by = db.Column(db.Integer, db.ForeignKey('users.users_id'), nullable=True)
    minutes_of_the_meeting_noted_by = db.Column(db.Integer, db.ForeignKey('signatories.signatory_id'), nullable=True)

    def __repr__(self):
        return f'<MinutesOfTheMeeting {self.minutes_of_the_meeting_id}: {self.minutes_of_the_meeting_agenda}>'

class Signatories(db.Model):
    __tablename__ = 'signatories'

    signatory_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    signatory_title = db.Column(db.String(50), nullable=False)
    signatory_first_name = db.Column(db.String(50), nullable=False)
    signatory_middle_name = db.Column(db.String(50), nullable=True)
    signatory_last_name = db.Column(db.String(50), nullable=False)
    signatory_suffix = db.Column(db.String(10), nullable=True)
    signatory_position = db.Column(db.String(100), nullable=False)
    signatory_department = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Signatories {self.signatory_id}: {self.signatory_first_name} {self.signatory_last_name}>'

class MinutesOfTheMeetingPhotoDocumentation(db.Model):
    __tablename__ = 'minutes_of_the_meeting_photo_documentation'

    minutes_of_the_meeting_photo_documentation_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    minutes_of_the_meeting_id = db.Column(db.Integer, db.ForeignKey('minutes_of_the_meeting.minutes_of_the_meeting_id'), nullable=False)
    minutes_of_the_meeting_photo_documentation_cloudinary_url = db.Column(db.String(255), nullable=False)
    minutes_of_the_meeting_photo_documentation_cloudinary_public_id = db.Column(db.String(255), nullable=False)

    minutes_of_the_meeting = db.relationship('MinutesOfTheMeeting', foreign_keys=[minutes_of_the_meeting_id])

    def __repr__(self):
        return f'<MinutesOfTheMeetingPhotoDocumentation {self.minutes_of_the_meeting_photo_documentation_id}: {self.minutes_of_the_meeting_photo_documentation_url}>'

class MinutesOfTheMeetingAttendees(db.Model):
    __tablename__ = 'minutes_of_the_meeting_attendees'

    minutes_of_the_meeting_id = db.Column(db.Integer, db.ForeignKey('minutes_of_the_meeting.minutes_of_the_meeting_id'), primary_key=True, nullable=False)
    users_id = db.Column(db.Integer, db.ForeignKey('users.users_id'), primary_key=True, nullable=False)

    minutes_of_the_meeting = db.relationship('MinutesOfTheMeeting', backref='attendees')
    user = db.relationship('Users', backref='minutes_of_the_meeting_attendees')

    def __repr__(self):
        return f'<MinutesOfTheMeetingAttendees(minutes_of_the_meeting_id={self.minutes_of_the_meeting_id}, users_id={self.users_id})>'

class StudentOrganizations(db.Model):
    __tablename__ = 'student_organizations'
    
    student_organizations_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_organizations_name = db.Column(db.String(255), nullable=False)
    student_organizations_financial_bank_book_amount = db.Column(db.Numeric(20, 2), nullable=True)

    def __repr__(self):
        return f"<StudentOrganizations(id={self.student_organizations_id}, name={self.student_organizations_name})>"

class FinancialReports(db.Model):
    __tablename__ = 'financial_reports'

    financial_reports_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    financial_reports_date = db.Column(db.DateTime, nullable=False)
    financial_reports_academic_year = db.Column(db.String(50), nullable=False)
    financial_reports_semester = db.Column(db.String(50), nullable=False)
    financial_reports_events_id = db.Column(db.Integer, db.ForeignKey('events.events_id'), nullable=True)
    financial_reports_title = db.Column(db.String(255), nullable=False)
    financial_reports_status = db.Column(db.String(50), nullable=False)
    financial_reports_audited_and_prepared_by = db.Column(db.Integer, db.ForeignKey('users.users_id'), nullable=True)
    financial_reports_noted_by = db.Column(db.Integer, db.ForeignKey('users.users_id'), nullable=True)
    financial_reports_recommending_approval_by = db.Column(db.Integer, db.ForeignKey('users.users_id'), nullable=True)
    financial_reports_approved_by = db.Column(db.Integer, db.ForeignKey('signatories.signatory_id'), nullable=True)

    event = db.relationship('Events', backref='financial_reports')
    audited_and_prepared_by_user = db.relationship('Users', foreign_keys=[financial_reports_audited_and_prepared_by])
    noted_by_user = db.relationship('Users', foreign_keys=[financial_reports_noted_by])
    recommending_approval_by_user = db.relationship('Users', foreign_keys=[financial_reports_recommending_approval_by])
    approved_by_signatory = db.relationship('Signatories', foreign_keys=[financial_reports_approved_by])

    def __repr__(self):
        return f'<FinancialReports {self.financial_reports_id}>'

class ConceptPaperForms(db.Model):
    __tablename__ = 'concept_paper_forms'

    concept_paper_forms_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    concept_paper_forms_semester = db.Column(db.String(50), nullable=True)
    concept_paper_forms_academic_year = db.Column(db.String(50), nullable=True)
    concept_paper_forms_status = db.Column(db.String(50), nullable=True)
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

    endorsed_by_signatory = db.relationship('Signatories', foreign_keys=[concept_paper_forms_endorsed_by])
    recommending_approval_by_signatory = db.relationship('Signatories', foreign_keys=[concept_paper_forms_recommending_approval_by])
    approved_by_signatory = db.relationship('Signatories', foreign_keys=[concept_paper_forms_approved_by])
    prepared_by_user = db.relationship('Users', foreign_keys=[concept_paper_forms_prepared_by])
    signed_and_reviewed_by_user = db.relationship('Users', foreign_keys=[concept_paper_forms_signed_and_reviewed_by])

    def __repr__(self):
        return f'<ConceptPaperForms {self.concept_paper_forms_id}: {self.concept_paper_forms_subject}>'

class ObjectivesOfTheActivity(db.Model):
    __tablename__ = 'objectives_of_the_activity'

    objectives_of_the_activity_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    objectives_of_the_activity_content = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<ObjectivesOfTheActivity {self.objectives_of_the_activity_id}: {self.objectives_of_the_activity_content}>'

class ConceptPaperFormObjectivesOfTheActivity(db.Model):
    __tablename__ = 'concept_paper_form_objectives_of_the_activity'

    concept_paper_forms_id = db.Column(db.Integer, db.ForeignKey('concept_paper_forms.concept_paper_forms_id'), primary_key=True, nullable=False)
    objectives_of_the_activity_id = db.Column(db.Integer, db.ForeignKey('objectives_of_the_activity.objectives_of_the_activity_id'), primary_key=True, nullable=False)

    concept_paper_form = db.relationship('ConceptPaperForms', backref='objectives_of_the_activity')
    objective_of_the_activity = db.relationship('ObjectivesOfTheActivity', backref='concept_paper_forms')

    def __repr__(self):
        return f'<ConceptPaperFormObjectivesOfTheActivity(concept_paper_forms_id={self.concept_paper_forms_id}, objectives_of_the_activity_id={self.objectives_of_the_activity_id})>'

class LearningOutcomes(db.Model):
    __tablename__ = 'learning_outcomes'

    learning_outcomes_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    learning_outcomes_content = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<LearningOutcomes {self.learning_outcomes_id}: {self.learning_outcomes_content}>'

class ConceptPaperFormLearningOutcomes(db.Model):
    __tablename__ = 'concept_paper_form_learning_outcomes'

    concept_paper_forms_id = db.Column(db.Integer, db.ForeignKey('concept_paper_forms.concept_paper_forms_id'), primary_key=True, nullable=False)
    learning_outcomes_id = db.Column(db.Integer, db.ForeignKey('learning_outcomes.learning_outcomes_id'), primary_key=True, nullable=False)

    concept_paper_form = db.relationship('ConceptPaperForms', backref='learning_outcomes')
    learning_outcome = db.relationship('LearningOutcomes', backref='concept_paper_forms')

    def __repr__(self):
        return f'<ConceptPaperFormLearningOutcomes(concept_paper_forms_id={self.concept_paper_forms_id}, learning_outcomes_id={self.learning_outcomes_id})>'

class ExcuseLetterForms(db.Model):
    __tablename__ = 'excuse_letter_forms'

    excuse_letter_forms_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    excuse_letter_forms_concept_paper_forms_id = db.Column(db.Integer, db.ForeignKey('concept_paper_forms.concept_paper_forms_id'), nullable=True)
    excuse_letter_forms_department_office_unit = db.Column(db.String(255), nullable=True)
    excuse_letter_forms_faculty_in_charge = db.Column(db.Integer, db.ForeignKey('signatories.signatory_id'), nullable=True)
    excuse_letter_forms_dean = db.Column(db.Integer, db.ForeignKey('signatories.signatory_id'), nullable=True)
    excuse_letter_forms_noted_by = db.Column(db.Integer, db.ForeignKey('signatories.signatory_id'), nullable=True)

    concept_paper_form = db.relationship('ConceptPaperForms', backref='excuse_letter_forms')
    faculty_in_charge_signatory = db.relationship('Signatories', foreign_keys=[excuse_letter_forms_faculty_in_charge])
    dean_signatory = db.relationship('Signatories', foreign_keys=[excuse_letter_forms_dean])
    noted_by_signatory = db.relationship('Signatories', foreign_keys=[excuse_letter_forms_noted_by])

    def __repr__(self):
        return f'<ExcuseLetterForms {self.excuse_letter_forms_id}>'

class ActivityReportForms(db.Model):
    __tablename__ = 'activity_report_forms'

    activity_report_forms_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    activity_report_forms_concept_paper_forms_id = db.Column(db.Integer, db.ForeignKey('concept_paper_forms.concept_paper_forms_id'), nullable=True)
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

class ActivityStrengths(db.Model):
    __tablename__ = 'activity_strengths'

    activity_strengths_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    activity_strengths_content = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<ActivityStrengths {self.activity_strengths_id}: {self.activity_strengths_content}>'

class ActivityWeaknesses(db.Model):
    __tablename__ = 'activity_weaknesses'

    activity_weaknesses_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    activity_weaknesses_content = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<ActivityWeaknesses {self.activity_weaknesses_id}: {self.activity_weaknesses_content}>'

class ActivityRecommendations(db.Model):
    __tablename__ = 'activity_recommendations'

    activity_recommendations_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    activity_recommendations_content = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<ActivityRecommendations {self.activity_recommendations_id}: {self.activity_recommendations_content}>'

class ActivityReportFormsActivityStrengths(db.Model):
    __tablename__ = 'activity_report_forms_activity_strengths'

    activity_report_forms_id = db.Column(db.Integer, db.ForeignKey('activity_report_forms.activity_report_forms_id'), primary_key=True, nullable=False)
    activity_strengths_id = db.Column(db.Integer, db.ForeignKey('activity_strengths.activity_strengths_id'), primary_key=True, nullable=False)

    activity_report_form = db.relationship('ActivityReportForms', backref='activity_strengths')
    activity_strength = db.relationship('ActivityStrengths', backref='activity_report_forms')

    def __repr__(self):
        return f'<ActivityReportFormsActivityStrengths(activity_report_forms_id={self.activity_report_forms_id}, activity_strengths_id={self.activity_strengths_id})>'

class ActivityReportFormsActivityWeaknesses(db.Model):
    __tablename__ = 'activity_report_forms_activity_weaknesses'

    activity_report_forms_id = db.Column(db.Integer, db.ForeignKey('activity_report_forms.activity_report_forms_id'), primary_key=True, nullable=False)
    activity_weaknesses_id = db.Column(db.Integer, db.ForeignKey('activity_weaknesses.activity_weaknesses_id'), primary_key=True, nullable=False)

    activity_report_form = db.relationship('ActivityReportForms', backref='activity_weaknesses')
    activity_weakness = db.relationship('ActivityWeaknesses', backref='activity_report_forms')

    def __repr__(self):
        return f'<ActivityReportFormsActivityWeaknesses(activity_report_forms_id={self.activity_report_forms_id}, activity_weaknesses_id={self.activity_weaknesses_id})>'

class ActivityReportFormsActivityRecommendations(db.Model):
    __tablename__ = 'activity_report_forms_activity_recommendations'

    activity_report_forms_id = db.Column(db.Integer, db.ForeignKey('activity_report_forms.activity_report_forms_id'), primary_key=True, nullable=False)
    activity_recommendations_id = db.Column(db.Integer, db.ForeignKey('activity_recommendations.activity_recommendations_id'), primary_key=True, nullable=False)

    activity_report_form = db.relationship('ActivityReportForms', backref='activity_recommendations')
    activity_recommendation = db.relationship('ActivityRecommendations', backref='activity_report_forms')

    def __repr__(self):
        return f'<ActivityReportFormsActivityRecommendations(activity_report_forms_id={self.activity_report_forms_id}, activity_recommendations_id={self.activity_recommendations_id})>'

class PersonnelInChargeForms(db.Model):
    __tablename__ = 'personnel_in_charge_forms'

    personnel_in_charge_forms_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    personnel_in_charge_forms_concept_paper_forms_id = db.Column(db.Integer, db.ForeignKey('concept_paper_forms.concept_paper_forms_id'), nullable=True)
    personnel_in_charge_forms_name_of_personnel_in_charge = db.Column(db.Integer, db.ForeignKey('signatories.signatory_id'), nullable=True)
    personnel_in_charge_forms_noted_by_college_dean = db.Column(db.Integer, db.ForeignKey('signatories.signatory_id'), nullable=True)
    personnel_in_charge_forms_noted_by_sas = db.Column(db.Integer, db.ForeignKey('signatories.signatory_id'), nullable=True)

    concept_paper_form = db.relationship('ConceptPaperForms', backref='personnel_in_charge_forms')
    personnel_in_charge_signatory = db.relationship('Signatories', foreign_keys=[personnel_in_charge_forms_name_of_personnel_in_charge])
    noted_by_dean_signatory = db.relationship('Signatories', foreign_keys=[personnel_in_charge_forms_noted_by_college_dean])
    noted_by_sas_signatory = db.relationship('Signatories', foreign_keys=[personnel_in_charge_forms_noted_by_sas])

    def __repr__(self):
        return f'<PersonnelInChargeForms {self.personnel_in_charge_forms_id}>'

class LearningJournalForms(db.Model):
    __tablename__ = 'learning_journal_forms'

    learning_journal_forms_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    learning_journal_forms_name_of_student = db.Column(db.String(255), nullable=True)
    learning_journal_forms_course_year_level = db.Column(db.String(255), nullable=True)
    learning_journal_forms_id_number = db.Column(db.String(50), nullable=True)
    learning_journal_forms_date = db.Column(db.Date, nullable=True)
    learning_journal_forms_overall_reflection = db.Column(db.Text, nullable=True)
    learning_journal_forms_prepared_by = db.Column(db.Integer, db.ForeignKey('users.users_id'), nullable=True)
    learning_journal_forms_seen_and_read_by = db.Column(db.Integer, db.ForeignKey('users.users_id'), nullable=True)
    learning_journal_forms_checked_by = db.Column(db.Integer, db.ForeignKey('signatories.signatory_id'), nullable=True)
    learning_journal_forms_concept_paper_forms_id = db.Column(db.Integer, db.ForeignKey('concept_paper_forms.concept_paper_forms_id'), nullable=True)  # New column

    concept_paper_form = db.relationship('ConceptPaperForms', backref='learning_journal_forms')
    prepared_by_user = db.relationship('Users', foreign_keys=[learning_journal_forms_prepared_by])
    seen_and_read_by_user = db.relationship('Users', foreign_keys=[learning_journal_forms_seen_and_read_by])
    checked_by_signatory = db.relationship('Signatories', foreign_keys=[learning_journal_forms_checked_by])

    def __repr__(self):
        return f'<LearningJournalForms {self.learning_journal_forms_id}>'

class Observations(db.Model):
    __tablename__ = 'observations'

    observations_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    observations_content = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Observations {self.observations_id}: {self.observations_content}>'

class LearningJournalFormsObservations(db.Model):
    __tablename__ = 'learning_journal_forms_observations'

    learning_journal_forms_id = db.Column(db.Integer, db.ForeignKey('learning_journal_forms.learning_journal_forms_id'), primary_key=True, nullable=False)
    observations_id = db.Column(db.Integer, db.ForeignKey('observations.observations_id'), primary_key=True, nullable=False)

    learning_journal_form = db.relationship('LearningJournalForms', backref='observations')
    observation = db.relationship('Observations', backref='learning_journal_forms')

    def __repr__(self):
        return f'<LearningJournalFormsObservations(learning_journal_forms_id={self.learning_journal_forms_id}, observations_id={self.observations_id})>'

class Learnings(db.Model):
    __tablename__ = 'learnings'

    learnings_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    learnings_content = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Learnings {self.learnings_id}: {self.learnings_content}>'

class LearningJournalFormsLearnings(db.Model):
    __tablename__ = 'learning_journal_forms_learnings'

    learning_journal_forms_id = db.Column(db.Integer, db.ForeignKey('learning_journal_forms.learning_journal_forms_id'), primary_key=True, nullable=False)
    learnings_id = db.Column(db.Integer, db.ForeignKey('learnings.learnings_id'), primary_key=True, nullable=False)

    learning_journal_form = db.relationship('LearningJournalForms', backref='learnings')
    learning = db.relationship('Learnings', backref='learning_journal_forms')

    def __repr__(self):
        return f'<LearningJournalFormsLearnings(learning_journal_forms_id={self.learning_journal_forms_id}, learnings_id={self.learnings_id})>'

class ParentGuardianConsentForms(db.Model):
    __tablename__ = 'parent_guardian_consent_forms'

    parent_guardian_consent_forms_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    parent_guardian_consent_forms_concept_paper_forms_id = db.Column(db.Integer, db.ForeignKey('concept_paper_forms.concept_paper_forms_id'), nullable=True)
    parent_guardian_consent_forms_personnel_in_charge_forms_id = db.Column(db.Integer, db.ForeignKey('personnel_in_charge_forms.personnel_in_charge_forms_id'), nullable=True)
    parent_guardian_consent_forms_name_of_student = db.Column(db.String(255), nullable=True)
    parent_guardian_consent_forms_course_year_level = db.Column(db.String(255), nullable=True)
    parent_guardian_consent_forms_id_number = db.Column(db.String(50), nullable=True)
    parent_guardian_consent_forms_department_office_unit = db.Column(db.String(255), nullable=True)
    parent_guardian_consent_forms_dean_immediate_supervisor = db.Column(db.Integer, db.ForeignKey('signatories.signatory_id'), nullable=True)
    parent_guardian_consent_forms_checked_by = db.Column(db.Integer, db.ForeignKey('signatories.signatory_id'), nullable=True)
    parent_guardian_consent_forms_content = db.Column(db.Text, nullable=True)
    parent_guardian_consent_forms_prepared_by = db.Column(db.Integer, db.ForeignKey('users.users_id'), nullable=True)
    parent_guardian_consent_forms_noted_by = db.Column(db.Integer, db.ForeignKey('signatories.signatory_id'), nullable=True)

    concept_paper_form = db.relationship('ConceptPaperForms', backref='parent_guardian_consent_forms')
    personnel_in_charge_form = db.relationship('PersonnelInChargeForms', backref='parent_guardian_consent_forms')
    dean_immediate_supervisor_signatory = db.relationship('Signatories', foreign_keys=[parent_guardian_consent_forms_dean_immediate_supervisor])
    checked_by_signatory = db.relationship('Signatories', foreign_keys=[parent_guardian_consent_forms_checked_by])
    prepared_by_user = db.relationship('Users', foreign_keys=[parent_guardian_consent_forms_prepared_by])
    noted_by_signatory = db.relationship('Signatories', foreign_keys=[parent_guardian_consent_forms_noted_by])

    def __repr__(self):
        return f'<ParentGuardianConsentForms {self.parent_guardian_consent_forms_id}>'

class Documentation(db.Model):
    __tablename__ = 'documentation'

    documentation_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    documentation_events_id = db.Column(db.Integer, db.ForeignKey('events.events_id'), nullable=True)
    documentation_academic_year = db.Column(db.String(50), nullable=True)
    documentation_semester = db.Column(db.String(50), nullable=True)
    documentation_status = db.Column(db.String(50), nullable=True)
    documentation_type = db.Column(db.String(50), nullable=True)
    documentation_activity_report_forms_id = db.Column(db.Integer, db.ForeignKey('activity_report_forms.activity_report_forms_id'), nullable=True)
    documentation_prepared_by = db.Column(db.Integer, db.ForeignKey('users.users_id'), nullable=True)
    documentation_learning_journal_forms_id = db.Column(db.Integer, db.ForeignKey('learning_journal_forms.learning_journal_forms_id'), nullable=True)
    documentation_checked_by = db.Column(db.Integer, db.ForeignKey('signatories.signatory_id'), nullable=True)
    documentation_noted_by = db.Column(db.Integer, db.ForeignKey('signatories.signatory_id'), nullable=True)
    documentation_date_of_submission = db.Column(db.Date, nullable=True)
    documentation_rating = db.Column(db.Integer, nullable=True)
    documentation_comments_suggestions = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Documentation {self.documentation_id}>'

class TallyItems(db.Model):
    __tablename__ = 'tally_items'

    tally_items_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tally_items_name = db.Column(db.String(255), nullable=True)
    tally_items_extremely_satisfied_rating = db.Column(db.Integer, nullable=True)
    tally_items_satisfied_rating = db.Column(db.Integer, nullable=True)
    tally_items_neutral_rating = db.Column(db.Integer, nullable=True)
    tally_items_dissatisfied_rating = db.Column(db.Integer, nullable=True)
    tally_items_extremely_dissatisfied_rating = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return f'<TallyItems {self.tally_items_id}>'

class DocumentationTallyItems(db.Model):
    __tablename__ = 'documentation_tally_items'

    documentation_id = db.Column(db.Integer, db.ForeignKey('documentation.documentation_id'), primary_key=True, nullable=False)
    tally_items_id = db.Column(db.Integer, db.ForeignKey('tally_items.tally_items_id'), primary_key=True, nullable=False)

    documentation = db.relationship('Documentation', backref='tally_items')
    tally_item = db.relationship('TallyItems', backref='documentation')

    def __repr__(self):
        return f'<DocumentationTallyItems(documentation_id={self.documentation_id}, tally_items_id={self.tally_items_id})>'

class ResultsOfTheEvaluationImages(db.Model):
    __tablename__ = 'results_of_the_evaluation_images'

    results_of_the_evaluation_images_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    results_of_the_evaluation_images_cloudinary_url = db.Column(db.String(255), nullable=True)
    results_of_the_evaluation_images_cloudinary_public_id = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<ResultsOfTheEvaluationImages {self.results_of_the_evaluation_images_id}>'

class DocumentationResultsOfTheEvaluationImages(db.Model):
    __tablename__ = 'documentation_results_of_the_evaluation_images'

    documentation_id = db.Column(db.Integer, db.ForeignKey('documentation.documentation_id'), primary_key=True, nullable=False)
    results_of_the_evaluation_images_id = db.Column(db.Integer, db.ForeignKey('results_of_the_evaluation_images.results_of_the_evaluation_images_id'), primary_key=True, nullable=False)

    documentation = db.relationship('Documentation', backref='results_of_the_evaluation_images')
    results_of_the_evaluation_image = db.relationship('ResultsOfTheEvaluationImages', backref='documentation')

    def __repr__(self):
        return f'<DocumentationResultsOfTheEvaluationImages(documentation_id={self.documentation_id}, results_of_the_evaluation_images_id={self.results_of_the_evaluation_images_id})>'

class SummaryOfAttendanceImages(db.Model):
    __tablename__ = 'summary_of_attendance_images'

    summary_of_attendance_images_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    summary_of_attendance_images_cloudinary_url = db.Column(db.String(255), nullable=True)
    summary_of_attendance_images_cloudinary_public_id = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<SummaryOfAttendanceImages {self.summary_of_attendance_images_id}>'

class DocumentationSummaryOfAttendanceImages(db.Model):
    __tablename__ = 'documentation_summary_of_attendance_images'

    documentation_id = db.Column(db.Integer, db.ForeignKey('documentation.documentation_id'), primary_key=True, nullable=False)
    summary_of_attendance_images_id = db.Column(db.Integer, db.ForeignKey('summary_of_attendance_images.summary_of_attendance_images_id'), primary_key=True, nullable=False)

    documentation = db.relationship('Documentation', backref='summary_of_attendance_images')
    summary_of_attendance_image = db.relationship('SummaryOfAttendanceImages', backref='documentation')

    def __repr__(self):
        return f'<DocumentationSummaryOfAttendanceImages(documentation_id={self.documentation_id}, summary_of_attendance_images_id={self.summary_of_attendance_images_id})>'

class EvaluationListOfStudentNames(db.Model):
    __tablename__ = 'evaluation_list_of_student_names'

    evaluation_list_of_student_names_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    evaluation_list_of_student_names_student = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<EvaluationListOfStudentNames {self.evaluation_list_of_student_names_id}>'

class DocumentationEvaluationStudentList(db.Model):
    __tablename__ = 'documentation_evaluation_student_list'

    documentation_id = db.Column(db.Integer, db.ForeignKey('documentation.documentation_id'), primary_key=True, nullable=False)
    evaluation_list_of_student_names_id = db.Column(db.Integer, db.ForeignKey('evaluation_list_of_student_names.evaluation_list_of_student_names_id'), primary_key=True, nullable=False)

    documentation = db.relationship('Documentation', backref='evaluation_student_list')
    evaluation_list_of_student_name = db.relationship('EvaluationListOfStudentNames', backref='documentation')

    def __repr__(self):
        return f'<DocumentationEvaluationStudentList(documentation_id={self.documentation_id}, evaluation_list_of_student_names_id={self.evaluation_list_of_student_names_id})>'

class EventPhotoDocumentationImages(db.Model):
    __tablename__ = 'event_photo_documentation_images'

    event_photo_documentation_images_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_photo_documentation_images_cloudinary_url = db.Column(db.String(255), nullable=True)
    event_photo_documentation_images_cloudinary_public_id = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<EventPhotoDocumentationImages {self.event_photo_documentation_images_id}>'

class DocumentationEventPhotoDocumentationImages(db.Model):
    __tablename__ = 'documentation_event_photo_documentation_images'

    documentation_id = db.Column(db.Integer, db.ForeignKey('documentation.documentation_id'), primary_key=True, nullable=False)
    event_photo_documentation_images_id = db.Column(db.Integer, db.ForeignKey('event_photo_documentation_images.event_photo_documentation_images_id'), primary_key=True, nullable=False)

    documentation = db.relationship('Documentation', backref='event_photo_documentation_images')
    event_photo_documentation_image = db.relationship('EventPhotoDocumentationImages', backref='documentation')

    def __repr__(self):
        return f'<DocumentationEventPhotoDocumentationImages(documentation_id={self.documentation_id}, event_photo_documentation_images_id={self.event_photo_documentation_images_id})>'

# Custom Jinja2 Filters
def truncate_text(text, length=100):
    if len(text) > length:
        return text[:length] + '...'
    return text

app.jinja_env.filters['truncate'] = truncate_text

def has_events(events, semester, academic_year):
    return any(event.events_semester == semester and event.events_academic_year == academic_year for event in events)

app.jinja_env.filters['has_events'] = has_events

# Custom Jinja2 filter to check if there are resolutions for a given semester and academic year
@app.template_filter('has_resolutions')
def has_resolutions(resolutions, semester, academic_year):
    return any(resolution.board_resolutions_semester == semester and resolution.board_resolutions_academic_year == academic_year for resolution in resolutions)

app.jinja_env.filters['has_resolutions'] = has_resolutions

# Custom Jinja2 filter to check if there are meetings for a given semester and academic year
@app.template_filter('has_meetings')
def has_meetings(meetings, semester, academic_year):
    return any(meeting.minutes_of_the_meeting_semester == semester and meeting.minutes_of_the_meeting_academic_year == academic_year for meeting in meetings)

app.jinja_env.filters['has_meetings'] = has_meetings

# Custom Jinja2 filter to check if there are financial reports for a given semester and academic year
@app.template_filter('has_financial_reports')
def has_financial_reports(reports, semester, academic_year):
    return any(report.financial_reports_semester == semester and report.financial_reports_academic_year == academic_year for report in reports)

app.jinja_env.filters['has_financial_reports'] = has_financial_reports

# Custom Jinja2 filter to check if there are concept papers for a given semester and academic year
@app.template_filter('has_papers')
def has_papers(papers, semester, academic_year):
    return any(paper.concept_paper_forms_semester == semester and paper.concept_paper_forms_academic_year == academic_year for paper in papers)

app.jinja_env.filters['has_papers'] = has_papers

# Define the has_documentations filter
@app.template_filter('has_documentations')
def has_documentations(documentations, semester, academic_year):
    return any(doc.documentation_semester == semester and doc.documentation_academic_year == academic_year for doc in documentations)

# Python functions
def send_verification_email(users_email):
    user = Users.query.filter_by(users_email=users_email).first_or_404()
    token = s.dumps(users_email, salt='email-confirm')
    link = url_for('confirm_email', token=token, _external=True)
    msg = Message('New Account Email Verification', recipients=[users_email])
    
    # HTML email body
    msg.html = f"""
    <html>
    <body style="font-family: 'Arial', 'Helvetica', sans-serif; background-color: #f5f5f5; color: #1e1e1e; padding: 20px;">
        <h1 style="color: #00578a;">Welcome to E-Council!</h1>
        <p>You have successfully created an account. Please click the button below to verify your email:</p>
        <a href="{link}" style="background-color: #00578a; color: #ffffff; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 8px;">Verify Email</a>
        <p style="font-size: 0.8em; color: gray;">Or copy and paste this link into your browser: <br><a href="{link}" style="color: #00578a;">{link}</a></p>
        <p>If you didn't create this account, you can safely ignore this email.</p>
        <p>Sincerely,<br>E-Council Team</p>
    </body>
    </html>
    """
    
    # Plain text email body as a fallback
    msg.body = f"""
    Welcome to our website!

    You have successfully created an account. Please click the link below to verify your email:
    {link}

    Or copy and paste this link into your browser:
    {link}

    If you didn't create this account, you can safely ignore this email.

    Sincerely,
    E-Council Team
    """
    
    # Check for existing email verification records
    existing_verification = EmailVerification.query.filter_by(
        email_verification_users_id=user.users_id,
        email_verification_new_email=users_email
    ).first()

    if existing_verification:
        flash("A verification email has already been sent to this email address. Please check your email.", "error")
        return

    mail.send(msg)

    # Track email verification in the database
    email_verification = EmailVerification(
        email_verification_users_id=user.users_id,
        email_verification_token=token,
        email_verification_new_email=users_email
    )
    db.session.add(email_verification)
    db.session.commit()
    
def send_reset_password_email(users_email):
    user = Users.query.filter_by(users_email=users_email).first_or_404()
    selector = os.urandom(16).hex()
    token = os.urandom(32).hex()
    expires = datetime.utcnow() + timedelta(hours=1)
    
    # Create the password reset link
    link = url_for('reset_password', selector=selector, token=token, _external=True)
    msg = Message('Password Reset Request', recipients=[users_email])
    
    # HTML email body
    msg.html = f"""
    <html>
    <body style="font-family: 'Arial', 'Helvetica', sans-serif; background-color: #f5f5f5; color: #1e1e1e; padding: 20px;">
        <h1 style="color: #00578a;">Password Reset Request</h1>
        <p>To reset your password, click the button below:</p>
        <a href="{link}" style="background-color: #00578a; color: #ffffff; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 8px;">Reset Password</a>
        <p style="font-size: 0.8em; color: gray;">Or copy and paste this link into your browser: <br><a href="{link}" style="color: #00578a;">{link}</a></p>
        <p>If you didn't request a password reset, you can safely ignore this email.</p>
        <p>Sincerely,<br>E-Council Team</p>
    </body>
    </html>
    """
    
    # Plain text email body as a fallback
    msg.body = f"""
    Password Reset Request

    To reset your password, click the link below:
    {link}

    Or copy and paste this link into your browser:
    {link}

    If you didn't request a password reset, you can safely ignore this email.

    Sincerely,
    E-Council Team
    """
    
    # Check for existing password reset records
    existing_reset = PasswordReset.query.filter_by(
        password_reset_users_id=user.users_id
    ).first()

    if existing_reset:
        flash("A password reset email has already been sent to this email address. Please check your email.", "error")
        return
    
    mail.send(msg)

    # Track password reset in the database
    password_reset = PasswordReset(
        password_reset_users_id=user.users_id,
        password_reset_selector=selector,
        password_reset_token=token,
        password_reset_expires=expires
    )
    db.session.add(password_reset)
    db.session.commit()

def send_password_change_notification_email(users_email):
    msg = Message('Password Change Notification', recipients=[users_email])
    
    # HTML email body
    msg.html = f"""
    <html>
    <body style="font-family: 'Arial', 'Helvetica', sans-serif; background-color: #f5f5f5; color: #1e1e1e; padding: 20px;">
        <h1 style="color: #00578a;">Password Change Notification</h1>
        <p>Your password has been successfully changed. If you did not make this change, please contact support immediately.</p>
        <p>Sincerely,<br>E-Council Team</p>
    </body>
    </html>
    """
    
    # Plain text email body as a fallback
    msg.body = f"""
    Password Change Notification

    Your password has been successfully changed. If you did not make this change, please contact support immediately.

    Sincerely,
    E-Council Team
    """
    
    mail.send(msg)

def send_email_change_notification(users_old_email, users_new_email):
    msg = Message('Email Change Notification', recipients=[users_old_email])
    
    # HTML email body
    msg.html = f"""
    <html>
    <body style="font-family: 'Arial', 'Helvetica', sans-serif; background-color: #f5f5f5; color: #1e1e1e; padding: 20px;">
        <h1 style="color: #00578a;">Email Change Notification</h1>
        <p>Your email has been successfully changed from {users_old_email} to {users_new_email}. If you did not make this change, please contact support immediately.</p>
        <p>Sincerely,<br>E-Council Team</p>
    </body>
    </html>
    """
    
    # Plain text email body as a fallback
    msg.body = f"""
    Email Change Notification

    Your email has been successfully changed from {users_old_email} to {users_new_email}. If you did not make this change, please contact support immediately.

    Sincerely,
    E-Council Team
    """
    
    mail.send(msg)

def send_email_change_confirmation(users_old_email, users_new_email):
    msg = Message('Email Change Confirmation', recipients=[users_new_email])
    
    # HTML email body
    msg.html = f"""
    <html>
    <body style="font-family: 'Arial', 'Helvetica', sans-serif; background-color: #f5f5f5; color: #1e1e1e; padding: 20px;">
        <h1 style="color: #00578a;">Email Change Confirmation</h1>
        <p>Your email has been successfully changed from {users_old_email} to {users_new_email}. If you did not make this change, please contact support immediately.</p>
        <p>Sincerely,<br>E-Council Team</p>
    </body>
    </html>
    """
    
    # Plain text email body as a fallback
    msg.body = f"""
    Email Change Confirmation

    Your email has been successfully changed to {users_new_email}. If you did not make this change, please contact support immediately.

    Sincerely,
    E-Council Team
    """
    
    mail.send(msg)

def send_new_email_verification(users_new_email):
    user = current_user
    token = s.dumps(users_new_email, salt='email-change')
    link = url_for('confirm_new_email', token=token, _external=True)
    msg = Message('Email Change Verification', recipients=[users_new_email])
    
    # HTML email body
    msg.html = f"""
    <html>
    <body style="font-family: 'Arial', 'Helvetica', sans-serif; background-color: #f5f5f5; color: #1e1e1e; padding: 20px;">
        <h1 style="color: #00578a;">Email Change Verification</h1>
        <p>To verify your new email address, click the button below:</p>
        <a href="{link}" style="background-color: #00578a; color: #ffffff; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 8px;">Verify Email</a>
        <p style="font-size: 0.8em; color: gray;">Or copy and paste this link into your browser: <br><a href="{link}" style="color: #00578a;">{link}</a></p>
        <p>If you didn't request this change, you can safely ignore this email.</p>
        <p>Sincerely,<br>E-Council Team</p>
    </body>
    </html>
    """
    
    # Plain text email body as a fallback
    msg.body = f"""
    Email Change Verification

    To verify your new email address, click the link below:
    {link}

    Or copy and paste this link into your browser:
    {link}

    If you didn't request this change, you can safely ignore this email.

    Sincerely,
    E-Council Team
    """
    
    mail.send(msg)

    # Track email verification in the database
    email_verification = EmailVerification(
        email_verification_users_id=user.users_id,
        email_verification_token=token,
        email_verification_new_email=users_new_email
    )
    db.session.add(email_verification)
    db.session.commit()

def send_account_deletion_notification_email(users_email):
    msg = Message('Account Deletion Notification', recipients=[users_email])
    
    # HTML email body
    msg.html = f"""
    <html>
    <body style="font-family: 'Arial', 'Helvetica', sans-serif; background-color: #f5f5f5; color: #1e1e1e; padding: 20px;">
        <h1 style="color: #00578a;">Account Deletion Notification</h1>
        <p>Your account has been successfully deleted. If you did not request this deletion, please contact support immediately.</p>
        <p>Sincerely,<br>E-Council Team</p>
    </body>
    </html>
    """
    
    # Plain text email body as a fallback
    msg.body = f"""
    Account Deletion Notification

    Your account has been successfully deleted. If you did not request this deletion, please contact support immediately.

    Sincerely,
    E-Council Team
    """
    
    mail.send(msg)

def send_invite_email(users_email, event_name, event_id):
    # Get the current user's details
    inviter = Users.query.get(current_user.users_id)
    inviter_first_name = inviter.users_first_name
    inviter_last_name = inviter.users_last_name
    inviter_department = Departments.query.get(inviter.users_departments_id).departments_name

    token = s.dumps(users_email, salt='invite-user')
    accept_link = url_for('accept_invite', token=token, _external=True)
    reject_link = url_for('reject_invite', token=token, _external=True)
    msg = Message('Invitation to Manage Event', recipients=[users_email])
    
    # HTML email body
    msg.html = f"""
    <html>
    <body style="font-family: 'Arial', 'Helvetica', sans-serif; background-color: #f5f5f5; color: #1e1e1e; padding: 20px;">
        <h1 style="color: #00578a;">Invitation to Manage Event</h1>
        <p>You have been invited by {inviter_first_name} {inviter_last_name} from the {inviter_department} department to help manage the event "{event_name}". Please click the button below to accept the invitation:</p>
        <a href="{accept_link}" style="background-color: #00578a; color: #ffffff; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 8px;">Accept Invitation</a>
        <p>If you do not wish to manage this event, you can reject the invitation by clicking the link below:</p>
        <a href="{reject_link}" style="background-color: #d9534f; color: #ffffff; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 8px;">Reject Invitation</a>
        <p style="font-size: 0.8em; color: gray;">Or copy and paste these links into your browser: <br>Accept: <a href="{accept_link}" style="color: #00578a;">{accept_link}</a><br>Reject: <a href="{reject_link}" style="color: #d9534f;">{reject_link}</a></p>
        <p>If you didn't expect this invitation, you can safely ignore this email.</p>
        <p>Sincerely,<br>E-Council Team</p>
    </body>
    </html>
    """
    
    # Plain text email body as a fallback
    msg.body = f"""
    You have been invited by {inviter_first_name} {inviter_last_name} from the {inviter_department} department to help manage the event "{event_name}". Please click the link below to accept the invitation:
    {accept_link}

    If you do not wish to manage this event, you can reject the invitation by clicking the link below:
    {reject_link}

    Or copy and paste these links into your browser:
    Accept: {accept_link}
    Reject: {reject_link}

    If you didn't expect this invitation, you can safely ignore this email.

    Sincerely,
    E-Council Team
    """
    
    mail.send(msg)

    # Store the invitation details in the event_invitations table
    event_invitation = EventInvitations(
        event_invitations_events_id=event_id,
        event_invitations_email=users_email,
        event_invitations_token=token
    )
    db.session.add(event_invitation)
    db.session.commit()

def get_distinct_academic_years():
    return db.session.query(Events.events_academic_year).distinct().order_by(Events.events_academic_year.desc()).all()

def get_concept_papers():
    return ConceptPaperForms.query.all()

def safe_decimal_conversion(value):
    try:
        return Decimal(value)
    except (ValueError, TypeError, InvalidOperation):
        return str(value)

# Routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        student_organizations = StudentOrganizations.query.all()
        return render_template("signup.html", student_organizations=student_organizations)
    elif request.method == "POST":
        users_first_name = request.form.get("users-first-name")
        users_last_name = request.form.get("users-last-name")
        users_username = request.form.get("users-username")
        users_email = request.form.get("users-email")
        users_department = request.form.get("users-department")
        users_role = request.form.get("users-role")
        users_password = request.form.get("users-password")
        users_repeat_password = request.form.get("users-repeat-password")
        users_email_verified = 0
        
        users_student_organization = request.form.get("users-student-organization") if request.form.get("users-student-organization") else None
        users_student_organization_position = request.form.get("users-student-organization-position") if request.form.get("users-student-organization-position") else None

        # Validation
        if not users_first_name or not users_last_name or not users_username or not users_email or not users_department or not users_role or not users_password:
            flash("All fields are required.", "error")
            return render_template("signup.html")

        if users_role == "Student Council Officer":
            if not users_student_organization or not users_student_organization_position:
                flash("Student Organization and Position are required for Student Council Officers.", "error")
                return render_template("signup.html")

        # Check if username already exists
        if Users.query.filter_by(users_username=users_username).first():
            flash("Username already exists.", "error")
            return render_template("signup.html")

        # Check if passwords match
        if users_password != users_repeat_password:
            flash("Passwords do not match.", "error")
            return render_template("signup.html")

        # Check password requirements
        if len(users_password) < 8:
            flash("Password must be at least 8 characters.", "error")
            return render_template("signup.html")
        if not any(char.isupper() for char in users_password):
            flash("Password must contain at least one uppercase letter.", "error")
            return render_template("signup.html")
        if not any(char.islower() for char in users_password):
            flash("Password must contain at least one lowercase letter.", "error")
            return render_template("signup.html")
        if not any(char.isdigit() for char in users_password):
            flash("Password must contain at least one number.", "error")
            return render_template("signup.html")
        if not any(char in "!@#$%^&*(),.?\":{}|<>" for char in users_password):
            flash("Password must contain at least one special character.", "error")
            return render_template("signup.html")

        # Ensure the role, student organization, and position are valid Enum values
        if users_role not in Users.users_role.type.enums:
            flash("Invalid role.", "error")
            return render_template("signup.html")
        if users_student_organization and not db.session.get(StudentOrganizations, users_student_organization):
            flash("Invalid student organization.", "error")
            return render_template("signup.html")
        if users_student_organization_position and users_student_organization_position not in Users.users_student_organization_position.type.enums:
            flash("Invalid student organization position.", "error")
            return render_template("signup.html")

        # Get the departments_id through the departments_name
        department = Departments.query.filter_by(departments_name=users_department).first()
        if not department:
            flash("Department not found.", "error")
            return render_template("signup.html")
        users_departments_id = department.departments_id

        # Clear student organization fields if the role is Faculty or Staff
        if users_role in ["Faculty", "Staff"]:
            users_student_organization = None
            users_student_organization_position = None

        user = Users(
            users_first_name=users_first_name,
            users_last_name=users_last_name,
            users_username=users_username,
            users_email=users_email,
            users_departments_id=users_departments_id,
            users_role=users_role,
            users_student_organization=users_student_organization,
            users_student_organization_position=users_student_organization_position,
            users_email_verified=users_email_verified,
        )

        user.set_password(users_password)

        db.session.add(user)
        db.session.commit()
        
        send_verification_email(users_email)

        flash("Account created! Please check your email to verify your account.", "success")

        return redirect(url_for("login"))

@app.route("/confirm_email/<token>")
def confirm_email(token):
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
    except SignatureExpired:
        flash("The email confirmation link has expired.", "error")
        return redirect(url_for("signup"))
    except BadSignature:
        flash("The email confirmation link is invalid.", "error")
        return redirect(url_for("signup"))

    user = Users.query.filter_by(users_email=email).first_or_404()

    # Check for the existence of the email verification record
    email_verification = EmailVerification.query.filter_by(email_verification_users_id=user.users_id).first()
    if not email_verification:
        flash("The email confirmation link is invalid.", "error")
        return redirect(url_for("login"))

    if user.users_email_verified:
        flash("Account already verified. Please log in.", "error")
    else:
        user.users_email_verified = 1
        db.session.commit()
        flash("Your account has been verified. Please log in.", "success")

        # Delete the email verification record
        db.session.delete(email_verification)
        db.session.commit()

    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    elif request.method == "POST":
        users_username_email = request.form.get("users-username-email")
        users_password = request.form.get("users-password")
        ip_address = request.remote_addr

        # Check login attempts
        login_attempt = LoginAttempts.query.filter_by(login_attempt_ip_address=ip_address).first()
        if login_attempt and login_attempt.login_attempt_count > 4:
            if datetime.utcnow() - login_attempt.login_attempt_last_attempt_time < timedelta(minutes=15):
                # Increment login attempts even if the limit is exceeded
                login_attempt.login_attempt_count += 1
                db.session.commit()
                flash("Too many login attempts. Please try again later.", "error")
                return redirect(url_for("login"))
            else:
                # Reset login attempts after 15 minutes
                login_attempt.login_attempt_count = 0
                db.session.commit()

        # Check if the identifier is an email or username
        user = Users.query.filter(
            (Users.users_username == users_username_email) | (Users.users_email == users_username_email)
        ).first()

        if user:
            if user.users_email_verified == 0:
                # Generate verification link with 'next' parameter
                verification_link = url_for('send_verification_email_route', users_email=user.users_email, next='login', _external=True)
                
                flash(Markup(f"Please verify your email before logging in. <a href='{verification_link}'>Click here to resend the verification email.</a>"), "error")
                return redirect(url_for("login"))

            if user.check_password(users_password):
                login_user(user)
                # Reset login attempts on successful login
                if login_attempt:
                    login_attempt.login_attempt_count = 0
                else:
                    login_attempt = LoginAttempts(
                        login_attempt_ip_address=ip_address,
                        login_attempt_count=0
                    )
                    db.session.add(login_attempt)
                db.session.commit()
                return redirect(url_for("council_overview"))

        # Increment login attempts on failure
        if login_attempt:
            login_attempt.login_attempt_count += 1
        else:
            login_attempt = LoginAttempts(
                login_attempt_ip_address=ip_address,
                login_attempt_count=1
            )
            db.session.add(login_attempt)
        db.session.commit()

        # Flash message for remaining attempts if login_attempt_count is at least 2
        attempts_left = 5 - login_attempt.login_attempt_count
        if attempts_left == 0:
            flash("Too many login attempts. Please try again later.", "error")
        elif login_attempt.login_attempt_count >= 2:
            flash(f"Invalid username/email or password. You have {attempts_left} login attempts left.", "error")
        else:
            flash("Invalid username/email or password.", "error")

        return redirect(url_for("login"))
    
@app.route("/send_verification_email/<users_email>")
def send_verification_email_route(users_email):
    next_route = request.args.get('next', 'login')  # Default to 'login' if 'next' is not provided
    user = Users.query.filter_by(users_email=users_email).first_or_404()
    if user.users_email_verified == 0:
        # Check for existing email verification records
        existing_verification = EmailVerification.query.filter_by(
            email_verification_users_id=user.users_id,
            email_verification_new_email=users_email
        ).first()

        if existing_verification:
            flash("A verification email has already been sent to this email address. Please check your email.", "error")
        else:
            send_verification_email(user.users_email)
            flash("A verification email has been sent to your email.", "success")
    else:
        flash("This email is already verified.", "info")

    # Redirect to the appropriate route based on the 'next' query parameter
    if next_route == 'email_settings':
        return redirect(url_for("email_settings"))
    else:
        return redirect(url_for("login"))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        users_email = request.form.get("users-email")
        user = Users.query.filter_by(users_email=users_email).first()
        if user:
            # Check for existing password reset records
            existing_reset = PasswordReset.query.filter_by(
                password_reset_users_id=user.users_id
            ).first()

            if existing_reset:
                flash("A password reset email has already been sent to this email address. Please check your email.", "error")
                return redirect(url_for("login"))

            send_reset_password_email(user.users_email)
            flash("A password reset link has been sent to your email.", "success")
            return redirect(url_for("login"))
        else:
            flash("Email address not found.", "error")
            return redirect(url_for("forgot_password"))
    return render_template("forgot-password.html")

@app.route("/reset-password/<selector>/<token>", methods=["GET", "POST"])
def reset_password(selector, token):
    password_reset = PasswordReset.query.filter_by(password_reset_selector=selector).first()

    # Check if there is a password reset record
    if not password_reset:
        flash("The password reset link is invalid or has expired.", "error")
        return redirect(url_for("login"))

    # Convert password_reset_expires to a datetime object
    expires = datetime.strptime(password_reset.password_reset_expires, '%Y-%m-%d %H:%M:%S.%f')

    # Check if the token matches and is not expired
    if password_reset.password_reset_token != token or expires < datetime.utcnow():
        flash("The password reset link is invalid or has expired.", "error")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        users_password = request.form.get("users-password")
        users_repeat_password = request.form.get("users-repeat-password")

        if users_password != users_repeat_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("reset_password", selector=selector, token=token))

        user = Users.query.filter_by(users_id=password_reset.password_reset_users_id).first_or_404()
        user.set_password(users_password)
        db.session.commit()

        # Delete the password reset record
        db.session.delete(password_reset)
        db.session.commit()

        flash("Your password has been reset. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("reset-password.html", selector=selector, token=token)

@app.route("/account")
@login_required
def account():
    return render_template("account.html")

@app.route("/upload-profile-picture", methods=["POST"])
@login_required
def upload_profile_picture():
    profile_picture = request.files.get("profile-picture")
    if (profile_picture):
        # Server-side validation for image file types
        valid_image_types = ['image/jpeg', 'image/png', 'image/jpg']
        if (profile_picture.mimetype not in valid_image_types):
            flash("Invalid file type. Please upload an image file.", "error")
            return redirect(url_for("account"))

        # Delete the previous profile picture from Cloudinary if it exists
        if (current_user.users_profile_picture):
            public_id = current_user.users_profile_picture_cloudinary_public_id
            if (public_id):
                cloudinary.uploader.destroy(public_id)

        # Upload the new profile picture to Cloudinary
        upload_result = cloudinary.uploader.upload(profile_picture)
        profile_picture_url = upload_result["secure_url"]
        profile_picture_public_id = upload_result["public_id"]

        # Update the user's profile picture URL and public ID
        current_user.users_profile_picture = profile_picture_url
        current_user.users_profile_picture_cloudinary_public_id = profile_picture_public_id

        db.session.commit()

        flash("Your profile picture has been updated successfully.", "success")
    else:
        flash("No file selected. Please choose a file to upload.", "error")

    return redirect(url_for("account"))

@app.route("/account-settings", methods=["GET", "POST"])
@login_required
def account_settings():
    if request.method == "POST":
        users_first_name = request.form.get("users-first-name")
        users_last_name = request.form.get("users-last-name")
        users_username = request.form.get("users-username")
        users_departments_id = request.form.get("users-department")
        users_role = request.form.get("users-role")
        users_student_organization = request.form.get("users-student-organization")
        users_student_organization_position = request.form.get("users-student-organization-position")
        users_home_address = request.form.get("users-home-address")
        users_contact_number = request.form.get("users-contact-number")
        users_current_password = request.form.get("users-current-password")

        # Validate the current password
        if not current_user.check_password(users_current_password):
            flash("Current password is incorrect.", "error")
            return redirect(url_for("account_settings"))

        # Ensure the role, student organization, and position are valid Enum values
        if users_role not in Users.users_role.type.enums:
            flash("Invalid role.", "error")
            return redirect(url_for("account_settings"))
        if users_student_organization and not db.session.get(StudentOrganizations, users_student_organization):
            flash("Invalid student organization.", "error")
            return redirect(url_for("account_settings"))
        if users_student_organization_position and users_student_organization_position not in Users.users_student_organization_position.type.enums:
            flash("Invalid student organization position.", "error")
            return redirect(url_for("account_settings"))

        # Get the departments_id through the departments_id
        department = Departments.query.filter_by(departments_id=users_departments_id).first()
        if not department:
            flash("Department not found.", "error")
            return redirect(url_for("account_settings"))

        # Clear student organization fields if the role is Faculty or Staff
        if users_role in ["Faculty", "Staff"]:
            users_student_organization = None
            users_student_organization_position = None

        # Handle file upload for the user's signature using Cloudinary
        users_signature = request.files.get("users-signature")
        if users_signature:
            # Server-side validation for image file types
            valid_image_types = ['image/jpeg', 'image/jpg', 'image/png']
            if users_signature.mimetype not in valid_image_types:
                flash("Invalid file type. Please upload an image file.", "error")
                return redirect(url_for("account_settings"))

            # Delete the previous image from Cloudinary if it exists
            if current_user.users_signature:
                public_id = current_user.users_signature_cloudinary_public_id
                if public_id:
                    cloudinary.uploader.destroy(public_id)

            # Upload the new image to Cloudinary
            upload_result = cloudinary.uploader.upload(users_signature)
            signature_url = upload_result["secure_url"]
            signature_public_id = upload_result["public_id"]

            # Update the user's signature URL and public ID
            current_user.users_signature = signature_url
            current_user.users_signature_cloudinary_public_id = signature_public_id

        # Update the user's information in the database
        user = Users.query.filter_by(users_id=current_user.users_id).first()
        user.users_first_name = users_first_name
        user.users_last_name = users_last_name
        user.users_username = users_username
        user.users_departments_id = users_departments_id
        user.users_role = users_role
        user.users_student_organization = users_student_organization
        user.users_student_organization_position = users_student_organization_position
        user.users_home_address = users_home_address
        user.users_contact_number = users_contact_number

        db.session.commit()

        flash("Your account settings have been updated successfully.", "success")
        return redirect(url_for("account_settings"))

    # Query all departments and student organizations to pass to the template
    departments = Departments.query.all()
    student_organizations = StudentOrganizations.query.all()
    return render_template("account-settings.html", departments=departments, student_organizations=student_organizations)

@app.route("/delete-user-account", methods=["POST"])
@login_required
def delete_user_account():
    users_current_password = request.form.get("users-current-password-account-deletion")

    # Validate the current password
    if not current_user.check_password(users_current_password):
        flash("Current password is incorrect.", "error")
        return redirect(url_for("account_settings"))

    # Send account deletion notification email
    send_account_deletion_notification_email(current_user.users_email)

    # Delete the user's signature image from Cloudinary if it exists
    if current_user.users_signature:
        public_id = current_user.users_signature_cloudinary_public_id
        if public_id:
            cloudinary.uploader.destroy(public_id)

    # Delete the user's profile picture from Cloudinary if it exists
    if current_user.users_profile_picture:
        profile_picture_public_id = current_user.users_profile_picture_cloudinary_public_id
        if profile_picture_public_id:
            cloudinary.uploader.destroy(profile_picture_public_id)

    # Delete the user account from the database
    user = Users.query.filter_by(users_id=current_user.users_id).first()
    db.session.delete(user)
    db.session.commit()

    # Log the user out
    logout_user()

    flash("Your account has been deleted successfully.", "success")
    return redirect(url_for("login"))

@app.route("/email-settings", methods=["GET", "POST"])
@login_required
def email_settings():
    if request.method == "POST":
        users_new_email = request.form.get("users-new-email")
        current_password = request.form.get("users-current-password")

        # Validate the current password
        if not current_user.check_password(current_password):
            flash("Current password is incorrect.", "error")
            return redirect(url_for("email_settings"))

        # Check if the new email is the same as the current email
        if users_new_email == current_user.users_email:
            flash("The new email address is the same as the current email address.", "error")
            return redirect(url_for("email_settings"))

        # Check if the new email is already in use
        if Users.query.filter_by(users_email=users_new_email).first():
            flash("The new email address is already in use.", "error")
            return redirect(url_for("email_settings"))

        # Check for existing email verification records
        existing_verification = EmailVerification.query.filter_by(
            email_verification_users_id=current_user.users_id
        ).first()

        if existing_verification:
            flash("A verification email has already been sent to this email address. Please check your email.", "error")
            return redirect(url_for("email_settings"))

        # Send verification email to the new email address
        send_new_email_verification(users_new_email)

        flash("A verification email has been sent to your new email address. Please check your email to confirm the change.", "success")
        return redirect(url_for("email_settings"))

    return render_template("email-settings.html")

@app.route("/confirm_new_email/<token>")
@login_required
def confirm_new_email(token):
    try:
        users_new_email = s.loads(token, salt='email-change', max_age=3600)
    except SignatureExpired:
        flash("The email confirmation link has expired.", "error")
        return redirect(url_for("email_settings"))
    except BadSignature:
        flash("The email confirmation link is invalid.", "error")
        return redirect(url_for("email_settings"))

    # Retrieve the email verification record
    email_verification = EmailVerification.query.filter_by(email_verification_token=token).first()
    if not email_verification:
        flash("The email confirmation link is invalid.", "error")
        return redirect(url_for("email_settings"))

    # Retrieve the current email from the database
    user = Users.query.filter_by(users_id=current_user.users_id).first()
    users_old_email = user.users_email

    # Send an email change notification to the old email address
    send_email_change_notification(users_old_email, users_new_email)

    # Update the user's email in the database
    user.users_email = users_new_email
    db.session.commit()

    # Send confirmation email to the new email address
    send_email_change_confirmation(users_old_email, users_new_email)

    # Delete the email verification record
    db.session.delete(email_verification)
    db.session.commit()

    flash("Your email has been updated successfully.", "success")
    return redirect(url_for("email_settings"))

@app.route("/password-security-settings", methods=["GET", "POST"])
@login_required
def password_security_settings():
    if request.method == "POST":
        users_password = request.form.get("users-password")
        users_repeat_password = request.form.get("users-repeat-password")

        # Validate the new password
        if users_password != users_repeat_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("password_security_settings"))

        if len(users_password) < 8:
            flash("Password must be at least 8 characters long.", "error")
            return redirect(url_for("password_security_settings"))

        if not any(char.isupper() for char in users_password):
            flash("Password must contain at least one uppercase letter.", "error")
            return redirect(url_for("password_security_settings"))

        if not any(char.islower() for char in users_password):
            flash("Password must contain at least one lowercase letter.", "error")
            return redirect(url_for("password_security_settings"))

        if not any(char.isdigit() for char in users_password):
            flash("Password must contain at least one number.", "error")
            return redirect(url_for("password_security_settings"))

        if not any(char in "!@#$%^&*(),.?\":{}|<>" for char in users_password):
            flash("Password must contain at least one special character.", "error")
            return redirect(url_for("password_security_settings"))

        # Update the user's password in the database
        current_user.users_password = generate_password_hash(users_password)
        db.session.commit()
        
        # Send password change update email
        send_password_change_notification_email(current_user.users_email)

        flash("Your password has been updated successfully.", "success")
        return redirect(url_for("password_security_settings"))

    return render_template("password-security-settings.html")

@app.route("/council-overview")
@login_required
def council_overview():
    return render_template("council-overview.html")

@app.route("/events-overview", methods=["GET", "POST"])
@login_required
def events_overview():
    # Get the current user's department ID
    users_departments_id = current_user.users_departments_id

    # Set default sorting to recent-to-old if not provided
    sort_by_date = "recent-to-old"

    # Query distinct academic years
    academic_years = db.session.query(Events.events_academic_year).distinct().order_by(Events.events_academic_year.desc()).all()

    # Set default academic year to "All" if not provided
    academic_year = "All"

    # Base query for events associated with the user's department
    query = db.session.query(Events).join(DepartmentsEvents).filter(DepartmentsEvents.departments_id == users_departments_id)

    # Execute the query
    events = query.all()

    # Fetch transaction history and calculate expenses, income, and remaining budget
    event_data = []

    for event in events:
        transactions = TransactionHistory.query.filter_by(events_id=event.events_id).all()
        total_income = sum(safe_decimal_conversion(t.transaction_total) for t in transactions if t.transaction_type == 'Income')
        total_expense = sum(safe_decimal_conversion(t.transaction_total) for t in transactions if t.transaction_type == 'Expense')
        events_budget = safe_decimal_conversion(event.events_budget) if event.events_budget else Decimal('0.00')
        if isinstance(events_budget, Decimal):
            remaining_budget = total_income - total_expense + events_budget
        else:
            remaining_budget = "N/A"
        
        event_data.append({
            'event_id': event.events_id,
            'total_income': total_income,
            'total_expense': total_expense,
            'remaining_budget': remaining_budget,
            'events_budget': events_budget
        })

    return render_template("events-overview.html", events=events, academic_years=academic_years, sort_by_date=sort_by_date, event_data=event_data)

@app.route("/update-event/<int:event_id>", methods=["POST", "GET"])
@login_required
def update_event(event_id):
    if request.method == "GET":
        # Query distinct academic years
        academic_years = db.session.query(Events.events_academic_year).distinct().order_by(Events.events_academic_year.desc()).all()
        
        # Render the template with the event and academic years
        return render_template("update-event.html", event=Events.query.get_or_404(event_id), academic_years=academic_years)
    
    elif request.method == "POST":
        # Get the event by ID
        event = Events.query.get_or_404(event_id)

        # Get form data
        event_name = request.form.get("events-name")
        event_semester = request.form.get("events-semester")
        event_academic_year = request.form.get("events-academic-year")
        event_start_date_and_time = request.form.get("events-start-date-and-time")
        event_end_date_and_time = request.form.get("events-end-date-and-time")
        event_venue = request.form.get("events-venue")
        event_budget = request.form.get("events-budget")
        event_status = request.form.get("events-status")
        event_description = request.form.get("events-description")
        event_remarks = request.form.get("events-remarks")

        # Update event details
        event.events_name = event_name
        event.events_semester = event_semester
        event.events_academic_year = event_academic_year
        event.events_start_date_and_time = datetime.strptime(event_start_date_and_time, '%Y-%m-%dT%H:%M')
        event.events_end_date_and_time = datetime.strptime(event_end_date_and_time, '%Y-%m-%dT%H:%M')
        event.events_venue = event_venue
        event.events_budget = event_budget
        event.events_status = event_status
        event.events_description = event_description
        event.events_remarks = event_remarks

        # Commit changes to the database
        db.session.commit()

        flash("Event updated successfully.", "success")

        return redirect(url_for("events_overview"))

@app.route("/update-event-status/<int:event_id>", methods=["POST"])
@login_required
def update_event_status(event_id):
    data = request.get_json()
    new_status = data.get('status')

    # Find the event by ID
    event = Events.query.get_or_404(event_id)

    # Update the event status
    event.events_status = new_status
    db.session.commit()

    return jsonify(success=True)

@app.route("/add-event", methods=["GET", "POST"])
@login_required
def add_event():
    if request.method == "POST":
        creation_method = request.form.get("creation-method")
        concept_paper_forms_id = request.form.get("concept-paper-forms-id")
        events_name = request.form.get("events-name")
        events_semester = request.form.get("events-semester")
        events_academic_year = request.form.get("events-academic-year")
        other_academic_year = request.form.get("other-academic-year")
        events_start_date_and_time = request.form.get("events-start-date-and-time")
        events_end_date_and_time = request.form.get("events-end-date-and-time")
        events_venue = request.form.get("events-venue")
        events_budget = request.form.get("events-budget")
        events_status = request.form.get("events-status")
        events_description = request.form.get("events-description")
        events_remarks = request.form.get("events-remarks")

        # Use the value from the additional input field if "Other A.Y." is selected
        if events_academic_year == "Other":
            events_academic_year = other_academic_year

        # Validation
        if creation_method == "scratch":
            if not events_name or not events_semester or not events_academic_year or not events_start_date_and_time or not events_end_date_and_time:
                flash("Please fill out all required fields.", "modal-error")
                return render_template("add-event.html", academic_years=get_distinct_academic_years(), concept_papers=get_concept_papers())

            # Check if event name already exists
            existing_event = Events.query.filter_by(events_name=events_name).first()
            if existing_event:
                flash("An event with this name already exists. Please choose a different name.", "modal-error")
                return render_template("add-event.html", academic_years=get_distinct_academic_years(), concept_papers=get_concept_papers())

            # Validate date format
            try:
                events_start_date_and_time = datetime.strptime(events_start_date_and_time, '%Y-%m-%dT%H:%M')
                events_end_date_and_time = datetime.strptime(events_end_date_and_time, '%Y-%m-%dT%H:%M')
            except ValueError:
                flash("Invalid date format. Please use the format YYYY-MM-DDTHH:MM.", "modal-error")
                return render_template("add-event.html", academic_years=get_distinct_academic_years(), concept_papers=get_concept_papers())

            # Validate budget format
            if events_budget:
                try:
                    events_budget = float(events_budget)
                except ValueError:
                    flash("Invalid budget format. Please enter a valid number.", "modal-error")
                    return render_template("add-event.html", academic_years=get_distinct_academic_years(), concept_papers=get_concept_papers())

        # If creating from an existing concept paper, retrieve the concept paper details
        if creation_method == "existing" and concept_paper_forms_id:
            concept_paper = ConceptPaperForms.query.get(concept_paper_forms_id)
            if concept_paper:
                events_name = concept_paper.concept_paper_forms_subject
                events_semester = concept_paper.concept_paper_forms_semester
                events_academic_year = concept_paper.concept_paper_forms_academic_year
                events_start_date_and_time = concept_paper.concept_paper_forms_event_start_date_and_time
                events_end_date_and_time = concept_paper.concept_paper_forms_event_end_date_and_time
                events_venue = concept_paper.concept_paper_forms_location
                events_budget = concept_paper.concept_paper_forms_budget
                events_description = concept_paper.concept_paper_forms_descriptions

        # Create event
        event = Events(
            events_concept_paper_forms_id=concept_paper_forms_id,
            events_name=events_name,
            events_semester=events_semester,
            events_academic_year=events_academic_year,
            events_start_date_and_time=events_start_date_and_time,
            events_end_date_and_time=events_end_date_and_time,
            events_venue=events_venue,
            events_budget=events_budget,
            events_status=events_status,
            events_description=events_description,
            events_remarks=events_remarks
        )
        
        db.session.add(event)
        db.session.commit()

        # Insert into departments_events table
        departments_id = current_user.users_departments_id
        departments_event = DepartmentsEvents(
            departments_id=departments_id,
            events_id=event.events_id
        )
        db.session.add(departments_event)
        db.session.commit()

        flash("Event added successfully!", "success")
        return redirect(url_for("events_overview"))

    # Query distinct academic years and concept papers
    academic_years = get_distinct_academic_years()
    concept_papers = get_concept_papers()
    return render_template("add-event.html", academic_years=academic_years, concept_papers=concept_papers)

@app.route("/delete-event/<int:event_id>", methods=["GET", "POST"])
@login_required
def delete_event(event_id):
    # Find the event by ID
    event = Events.query.get_or_404(event_id)

    if request.method == "POST":
        # Delete related records in the departments_events table
        DepartmentsEvents.query.filter_by(events_id=event_id).delete()

        # Delete related records in the event_invitations table
        EventInvitations.query.filter_by(event_invitations_events_id=event_id).delete()

        # Delete the event
        db.session.delete(event)
        db.session.commit()

        flash("Event deleted successfully.", "success")
        return redirect(url_for("events_overview"))

    return render_template("delete-event.html", event=event)

@app.route("/event-dashboard/<int:event_id>", methods=["GET", "POST"])
@login_required
def event_dashboard(event_id):
    # Fetch the event details based on the event_id
    event = Events.query.get_or_404(event_id)
    
    # Fetch the transaction history for the given event_id, sorted by most recent
    transactions = TransactionHistory.query.filter_by(events_id=event_id).order_by(TransactionHistory.transaction_date.desc()).all()

    # Query top 5 income transactions grouped by category
    top5_income = db.session.query(
        TransactionHistory.transaction_category,
        db.func.sum(TransactionHistory.transaction_total).label('transaction_total')
    ).filter_by(events_id=event_id, transaction_type='Income').group_by(TransactionHistory.transaction_category).order_by(db.func.sum(TransactionHistory.transaction_total).desc()).limit(5).all()

    # Query top 5 expense transactions grouped by category
    top5_expense = db.session.query(
        TransactionHistory.transaction_category,
        db.func.sum(TransactionHistory.transaction_total).label('transaction_total')
    ).filter_by(events_id=event_id, transaction_type='Expense').group_by(TransactionHistory.transaction_category).order_by(db.func.sum(TransactionHistory.transaction_total).desc()).limit(5).all()

    # Convert TransactionHistory objects to dictionaries
    def transaction_to_dict(transaction):
        return {
            'transaction_category': transaction.transaction_category,
            'transaction_total': float(transaction.transaction_total)
        }

    top5_income_dicts = [transaction_to_dict(transaction) for transaction in top5_income]
    top5_expense_dicts = [transaction_to_dict(transaction) for transaction in top5_expense]

    # Calculate total income and total expense
    total_income = sum(transaction['transaction_total'] for transaction in top5_income_dicts) or 0
    total_expense = sum(transaction['transaction_total'] for transaction in top5_expense_dicts) or 0

    # Calculate remaining budget
    events_budget = float(event.events_budget or 0)
    remaining_budget = total_income - total_expense + events_budget

    return render_template("event-dashboard.html", event=event, transactions=transactions, top5_income=top5_income_dicts, top5_expense=top5_expense_dicts, total_income=total_income, total_expense=total_expense, remaining_budget=remaining_budget)

@app.route("/add-transaction/<int:event_id>", methods=["GET", "POST"])
@login_required
def add_transaction(event_id):
    # Fetch the event details based on the event_id
    event = Events.query.get_or_404(event_id)

    if request.method == "POST":
        # Get form data
        transaction_name = request.form.get("transaction-name")
        transaction_date = request.form.get("transaction-date")
        unit_amount = request.form.get("transaction-unit-amount")
        unit_price = request.form.get("transaction-unit-price")
        transaction_total = request.form.get("transaction-total")
        transaction_category = request.form.get("transaction-category")
        other_transaction_category = request.form.get("other-transaction-category")
        transaction_type = request.form.get("transaction-type")
        transaction_receipt = request.files.get("transaction-receipt")

        # Use the value from the additional input field if "Other" is selected
        if transaction_category == "Other":
            transaction_category = other_transaction_category

        # Handle file upload to Cloudinary
        receipt_url = None
        receipt_public_id = None
        if transaction_receipt:
            upload_result = cloudinary.uploader.upload(transaction_receipt)
            receipt_url = upload_result.get('secure_url')
            receipt_public_id = upload_result.get('public_id')

        # Create a new transaction
        new_transaction = TransactionHistory(
            events_id=event_id,
            transaction_name=transaction_name,
            transaction_date=datetime.strptime(transaction_date, '%Y-%m-%dT%H:%M'),
            transaction_unit_amount=unit_amount,
            transaction_unit_price=unit_price,
            transaction_total=transaction_total,
            transaction_category=transaction_category,
            transaction_type=transaction_type,
            transaction_receipt_cloudinary_url=receipt_url,
            transaction_receipt_cloudinary_public_id=receipt_public_id
        )

        # Add the transaction to the database
        db.session.add(new_transaction)
        db.session.commit()

        flash("Transaction added successfully.", "success")
        return redirect(url_for("event_dashboard", event_id=event_id))

    # Query distinct transaction categories
    transaction_categories = db.session.query(TransactionHistory.transaction_category).distinct().order_by(TransactionHistory.transaction_category).all()

    return render_template("add-transaction.html", event=event, transaction_categories=transaction_categories)

@app.route("/update-transaction/<int:event_id>/<int:transaction_id>", methods=["GET", "POST"])
@login_required
def update_transaction(event_id, transaction_id):
    # Fetch the event details based on the event_id
    event = Events.query.get_or_404(event_id)
    transaction = TransactionHistory.query.get_or_404(transaction_id)

    if request.method == "POST":
        # Get form data
        transaction_name = request.form.get("transaction-name")
        transaction_date = request.form.get("transaction-date")
        unit_amount = request.form.get("transaction-unit-amount")
        unit_price = request.form.get("transaction-unit-price")
        transaction_total = request.form.get("transaction-total")
        transaction_category = request.form.get("transaction-category")
        other_transaction_category = request.form.get("other-transaction-category")
        transaction_type = request.form.get("transaction-type")
        transaction_receipt = request.files.get("transaction-receipt")

        # Use the value from the additional input field if "Other" is selected
        if transaction_category == "Other":
            transaction_category = other_transaction_category

        # Handle file upload to Cloudinary
        receipt_url = transaction.transaction_receipt_cloudinary_url
        receipt_public_id = transaction.transaction_receipt_cloudinary_public_id
        if transaction_receipt:
            if receipt_public_id:
                cloudinary.uploader.destroy(receipt_public_id)
            upload_result = cloudinary.uploader.upload(transaction_receipt)
            receipt_url = upload_result.get('secure_url')
            receipt_public_id = upload_result.get('public_id')

        # Update the transaction details
        transaction.transaction_name = transaction_name
        transaction.transaction_date = datetime.strptime(transaction_date, '%Y-%m-%dT%H:%M')
        transaction.transaction_unit_amount = unit_amount
        transaction.transaction_unit_price = unit_price
        transaction.transaction_total = transaction_total
        transaction.transaction_category = transaction_category
        transaction.transaction_type = transaction_type
        transaction.transaction_receipt_cloudinary_url = receipt_url
        transaction.transaction_receipt_cloudinary_public_id = receipt_public_id

        # Commit the changes to the database
        db.session.commit()

        flash("Transaction updated successfully.", "success")
        return redirect(url_for("event_dashboard", event_id=event_id))

    # Query distinct transaction categories
    transaction_categories = [category[0] for category in db.session.query(TransactionHistory.transaction_category).distinct().all()]

    return render_template("update-transaction.html", event=event, transaction=transaction, transaction_categories=transaction_categories)

@app.route("/invite-user/<int:event_id>", methods=["GET", "POST"])
@login_required
def invite_user(event_id):
    # Get the event by ID
    event = Events.query.get_or_404(event_id)

    if request.method == "POST":
        # Get form data
        users_email = request.form.get("users-email")
        source = request.form.get("source")

        # Find the user by email
        user = Users.query.filter_by(users_email=users_email).first_or_404()

        # Get the user's department ID
        users_department_id = user.users_departments_id

        # Check if the departments_id and events_id pair already exists
        existing_entry = db.session.query(DepartmentsEvents).join(Departments).filter(
            DepartmentsEvents.departments_id == users_department_id,
            DepartmentsEvents.events_id == event_id
        ).first()

        if existing_entry:
            department_name = existing_entry.department.departments_name
            flash(f"The department of the user {users_email} ({department_name}) is already managing the event '{event.events_name}'.", "error")
            return redirect(url_for(source, event_id=event_id) if source == "event_dashboard" else url_for("events_overview"))

        # Check if there is an existing invitation
        existing_invitation = EventInvitations.query.filter_by(event_invitations_events_id=event_id, event_invitations_email=users_email).first()
        if existing_invitation:
            flash(f"An invitation for the event '{event.events_name}' has already been sent to {users_email}.", "error")
            return redirect(url_for(source, event_id=event_id) if source == "event_dashboard" else url_for("events_overview"))

        # Send invite email
        send_invite_email(users_email, event.events_name, event_id)

        flash(f"Invitation email for the event '{event.events_name}' to {users_email} has been sent successfully.", "success")
        return redirect(url_for(source, event_id=event_id) if source == "event_dashboard" else url_for("events_overview"))

    # Get the source from the query parameters
    source = request.args.get("source", "events_overview")
    return render_template("invite-user.html", event=event, source=source)

@app.route("/accept-invite/<token>")
@login_required
def accept_invite(token):
    try:
        # Decode the token
        users_email = s.loads(token, salt='invite-user', max_age=3600)
    except SignatureExpired:
        flash("The invitation link has expired.", "error")
        return redirect(url_for("login"))
    except BadSignature:
        flash("The invitation link is invalid.", "error")
        return redirect(url_for("login"))

    # Find the invitation by token
    invitation = EventInvitations.query.filter_by(event_invitations_token=token).first()
    if not invitation:
        flash("The invitation link is invalid or has expired.", "error")
        return redirect(url_for("events_overview"))

    # Check if the invitation email matches the current user's email
    if invitation.event_invitations_email != current_user.users_email:
        flash("You are not authorized to accept this invitation.", "error")
        return redirect(url_for("events_overview"))

    # Find the user by email
    user = Users.query.filter_by(users_email=users_email).first_or_404()

    # Get the user's department ID
    users_department_id = user.users_departments_id

    # Get the event ID from the invitation
    event_id = invitation.event_invitations_events_id

    # Link the user's department to the event in the departments_events junction table
    departments_event = DepartmentsEvents(departments_id=users_department_id, events_id=event_id)
    db.session.add(departments_event)

    # Delete the invitation record from the event_invitations table
    db.session.delete(invitation)

    # Commit changes to the database
    db.session.commit()

    flash("You have successfully accepted the invitation to manage the event.", "success")
    return redirect(url_for("events_overview"))

@app.route("/reject-invite/<token>")
@login_required
def reject_invite(token):
    try:
        # Decode the token
        users_email = s.loads(token, salt='invite-user', max_age=3600)
    except SignatureExpired:
        flash("The invitation link has expired.", "error")
        return redirect(url_for("login"))
    except BadSignature:
        flash("The invitation link is invalid.", "error")
        return redirect(url_for("login"))

    # Find the invitation by token
    invitation = EventInvitations.query.filter_by(event_invitations_token=token).first()
    if not invitation:
        flash("The invitation link is invalid or has expired.", "error")
        return redirect(url_for("events_overview"))

    # Check if the invitation email matches the current user's email
    if invitation.event_invitations_email != current_user.users_email:
        flash("You are not authorized to reject this invitation.", "error")
        return redirect(url_for("events_overview"))

    # Get the event and department details
    event = Events.query.get_or_404(invitation.event_invitations_events_id)
    department_event = DepartmentsEvents.query.filter_by(events_id=event.events_id).first()
    department = Departments.query.get_or_404(department_event.departments_id)

    # Delete the invitation record from the event_invitations table
    db.session.delete(invitation)
    db.session.commit()

    flash(f"You have successfully rejected the invitation to manage the event '{event.events_name}' from the department '{department.departments_name}'.", "success")
    return redirect(url_for("events_overview"))

@app.route("/event-invite-rejected")
@login_required
def event_invite_rejected():
    return render_template("event-invite-rejected.html")

@app.route("/event-invite-accepted")
@login_required
def event_invite_accepted():
    return render_template("event-invite-accepted.html")

@app.route("/concept-papers-overview")
@login_required
def concept_papers_overview():
    # Query for all concept papers
    concept_papers = ConceptPaperForms.query.all()

    # Determine the sorting order
    sort_by_date = request.args.get('sort_by_date', 'recent-to-old')

    return render_template("concept-papers-overview.html", concept_papers=concept_papers, sort_by_date=sort_by_date)

@app.route('/add-concept-paper', methods=['GET', 'POST'])
@login_required
def add_concept_paper():
    if request.method == 'POST':
        concept_paper_date = request.form.get('concept-paper-date')
        concept_paper_subject = request.form.get('concept-paper-subject')
        concept_paper_academic_year = request.form.get('concept-paper-academic-year')
        other_academic_year = request.form.get('other-academic-year')
        concept_paper_semester = request.form.get('concept-paper-semester')
        concept_paper_status = request.form.get('concept-paper-status')
        concept_paper_event_start_date_and_time = request.form.get('concept-paper-event-start-date-and-time')
        concept_paper_event_end_date_and_time = request.form.get('concept-paper-event-end-date-and-time')
        concept_paper_location = request.form.get('concept-paper-location')
        concept_paper_participants = request.form.get('concept-paper-participants')
        concept_paper_budget = request.form.get('concept-paper-budget')
        concept_paper_descriptions = request.form.get('concept-paper-descriptions')
        concept_paper_expected_number_of_participants = request.form.get('concept-paper-expected-number-of-participants')
        concept_paper_body = request.form.get('concept-paper-body')
        concept_paper_objectives = request.form.getlist('concept-paper-objectives')
        concept_paper_learning_outcomes = request.form.getlist('concept-paper-learning-outcomes')
        concept_paper_prepared_by = request.form.get('concept-paper-prepared-by')
        concept_paper_signed_and_reviewed_by = request.form.get('concept-paper-signed-and-reviewed-by')
        concept_paper_endorsed_by = request.form.get('concept-paper-endorsed-by')
        concept_paper_recommending_approval_by = request.form.get('concept-paper-recommending-approval-by')
        concept_paper_approved_by = request.form.get('concept-paper-approved-by')

        # Use the value from the additional input field if "Other A.Y." is selected
        if concept_paper_academic_year == "Other":
            concept_paper_academic_year = other_academic_year

        # Convert date and time fields to datetime objects
        concept_paper_date = datetime.strptime(concept_paper_date, '%Y-%m-%dT%H:%M')
        concept_paper_event_start_date_and_time = datetime.strptime(concept_paper_event_start_date_and_time, '%Y-%m-%dT%H:%M')
        concept_paper_event_end_date_and_time = datetime.strptime(concept_paper_event_end_date_and_time, '%Y-%m-%dT%H:%M')

        # Excuse Letter Form data
        excuse_letter_department_office_unit = request.form.get('excuse-letter-department-office-unit')
        excuse_letter_faculty_in_charge = request.form.get('excuse-letter-faculty-in-charge')
        excuse_letter_dean = request.form.get('excuse-letter-dean')
        excuse_letter_noted_by = request.form.get('excuse-letter-noted-by')

        # Create a new concept paper
        new_concept_paper = ConceptPaperForms(
            concept_paper_forms_date=concept_paper_date,
            concept_paper_forms_subject=concept_paper_subject,
            concept_paper_forms_academic_year=concept_paper_academic_year,
            concept_paper_forms_semester=concept_paper_semester,
            concept_paper_forms_status=concept_paper_status,
            concept_paper_forms_event_start_date_and_time=concept_paper_event_start_date_and_time,
            concept_paper_forms_event_end_date_and_time=concept_paper_event_end_date_and_time,
            concept_paper_forms_location=concept_paper_location,
            concept_paper_forms_participants=concept_paper_participants,
            concept_paper_forms_budget=concept_paper_budget,
            concept_paper_forms_descriptions=concept_paper_descriptions,
            concept_paper_forms_expected_number_of_participants=concept_paper_expected_number_of_participants,
            concept_paper_forms_body=concept_paper_body,
            concept_paper_forms_prepared_by=concept_paper_prepared_by,
            concept_paper_forms_signed_and_reviewed_by=concept_paper_signed_and_reviewed_by,
            concept_paper_forms_endorsed_by=concept_paper_endorsed_by,
            concept_paper_forms_recommending_approval_by=concept_paper_recommending_approval_by,
            concept_paper_forms_approved_by=concept_paper_approved_by
        )

        # Add the new concept paper to the database
        db.session.add(new_concept_paper)
        db.session.commit()

        # Add objectives of the activity to the objectives_of_the_activity table
        for objective_content in concept_paper_objectives:
            new_objective = ObjectivesOfTheActivity(
                objectives_of_the_activity_content=objective_content
            )
            db.session.add(new_objective)
            db.session.commit()

            # Link the objective to the concept paper
            concept_paper_objective_link = ConceptPaperFormObjectivesOfTheActivity(
                concept_paper_forms_id=new_concept_paper.concept_paper_forms_id,
                objectives_of_the_activity_id=new_objective.objectives_of_the_activity_id
            )
            db.session.add(concept_paper_objective_link)
            db.session.commit()

        # Add learning outcomes to the learning_outcomes table
        for outcome_content in concept_paper_learning_outcomes:
            new_outcome = LearningOutcomes(
                learning_outcomes_content=outcome_content
            )
            db.session.add(new_outcome)
            db.session.commit()

            # Link the learning outcome to the concept paper
            concept_paper_outcome_link = ConceptPaperFormLearningOutcomes(
                concept_paper_forms_id=new_concept_paper.concept_paper_forms_id,
                learning_outcomes_id=new_outcome.learning_outcomes_id
            )
            db.session.add(concept_paper_outcome_link)
            db.session.commit()

        # Excuse Letter Form data
        excuse_letter_department_office_unit = request.form.get('excuse-letter-department-office-unit')
        excuse_letter_faculty_in_charge = request.form.get('excuse-letter-faculty-in-charge')
        excuse_letter_dean = request.form.get('excuse-letter-dean')
        excuse_letter_noted_by = request.form.get('excuse-letter-noted-by')

        # Add Excuse Letter Form to the excuse_letter_forms table
        new_excuse_letter_form = ExcuseLetterForms(
            excuse_letter_forms_concept_paper_forms_id=new_concept_paper.concept_paper_forms_id,
            excuse_letter_forms_department_office_unit=excuse_letter_department_office_unit,
            excuse_letter_forms_faculty_in_charge=excuse_letter_faculty_in_charge,
            excuse_letter_forms_dean=excuse_letter_dean,
            excuse_letter_forms_noted_by=excuse_letter_noted_by
        )
        db.session.add(new_excuse_letter_form)
        db.session.commit()

        # Activity Report Form data
        activity_report_date_submission = request.form.get('activity-report-date-submission')
        activity_report_contact_numbers = request.form.get('activity-report-contact-numbers')
        activity_report_prepared_by = request.form.get('activity-report-prepared-by')
        activity_report_noted_by = request.form.get('activity-report-noted-by')

        # Add Activity Report Form
        if activity_report_date_submission:
            new_activity_report = ActivityReportForms(
                activity_report_forms_concept_paper_forms_id=new_concept_paper.concept_paper_forms_id,
                activity_report_forms_contact_numbers=activity_report_contact_numbers,
                activity_report_forms_prepared_by=activity_report_prepared_by,
                activity_report_forms_noted_by=activity_report_noted_by,
                activity_report_date_submission=datetime.strptime(activity_report_date_submission, '%Y-%m-%d')
            )
            db.session.add(new_activity_report)
            db.session.commit()

        # Personnel In Charge Form data
        personnel_in_charge = request.form.get('personnel-in-charge')
        personnel_in_charge_noted_by_college_dean = request.form.get('personnel-in-charge-noted-by-college-dean')
        personnel_in_charge_noted_by_sas = request.form.get('personnel-in-charge-noted-by-sas')
        
        # Create Personnel In Charge Form
        if personnel_in_charge:
            new_personnel_in_charge = PersonnelInChargeForms(
                personnel_in_charge_forms_concept_paper_forms_id=new_concept_paper.concept_paper_forms_id,
                personnel_in_charge_forms_name_of_personnel_in_charge=personnel_in_charge,
                personnel_in_charge_forms_noted_by_college_dean=personnel_in_charge_noted_by_college_dean,
                personnel_in_charge_forms_noted_by_sas=personnel_in_charge_noted_by_sas
            )
            db.session.add(new_personnel_in_charge)
            db.session.commit()
        
            # Create Activity Report Form with personnel in charge reference
            if activity_report_date_submission:
                new_activity_report = ActivityReportForms(
                    activity_report_forms_concept_paper_forms_id=new_concept_paper.concept_paper_forms_id,
                    activity_report_forms_personnel_in_charge_forms_id=new_personnel_in_charge.personnel_in_charge_forms_id,
                    activity_report_forms_contact_numbers=activity_report_contact_numbers,
                    activity_report_forms_prepared_by=activity_report_prepared_by,
                    activity_report_forms_noted_by=activity_report_noted_by,
                    activity_report_date_submission=datetime.strptime(activity_report_date_submission, '%Y-%m-%d')
                )
                db.session.add(new_activity_report)
                db.session.commit()

        # Learning Journal Form data
        learning_journal_date = request.form.get('learning-journal-date')
        learning_journal_checked_by = request.form.get('learning-journal-checked-by')

        # Convert date fields to datetime objects
        learning_journal_date = datetime.strptime(learning_journal_date, '%Y-%m-%d')

        # Create a new learning journal form
        new_learning_journal_form = LearningJournalForms(
            learning_journal_forms_concept_paper_forms_id=new_concept_paper.concept_paper_forms_id,
            learning_journal_forms_date=learning_journal_date,
            learning_journal_forms_checked_by=learning_journal_checked_by
        )

        # Add the new learning journal form to the database
        db.session.add(new_learning_journal_form)
        db.session.commit()

        # Parent/Guardian Consent Form data
        concept_paper_forms_id = new_concept_paper.concept_paper_forms_id
        parent_guardian_consent_department_office_unit = request.form.get('parent-guardian-consent-department-office-unit')
        parent_guardian_consent_dean_immediate_supervisor = request.form.get('parent-guardian-consent-dean-immediate-supervisor')
        parent_guardian_consent_checked_by = request.form.get('parent-guardian-consent-checked-by')
        parent_guardian_consent_content = request.form.get('parent-guardian-consent-content')
        parent_guardian_consent_prepared_by = request.form.get('parent-guardian-consent-prepared-by')
        parent_guardian_consent_noted_by = request.form.get('parent-guardian-consent-noted-by')

        # Create a new Parent/Guardian Consent Form
        parent_guardian_consent_form = ParentGuardianConsentForms(
            parent_guardian_consent_forms_concept_paper_forms_id=concept_paper_forms_id,
            parent_guardian_consent_forms_personnel_in_charge_forms_id=new_personnel_in_charge.personnel_in_charge_forms_id,
            parent_guardian_consent_forms_department_office_unit=parent_guardian_consent_department_office_unit,
            parent_guardian_consent_forms_dean_immediate_supervisor=parent_guardian_consent_dean_immediate_supervisor,
            parent_guardian_consent_forms_checked_by=parent_guardian_consent_checked_by,
            parent_guardian_consent_forms_content=parent_guardian_consent_content,
            parent_guardian_consent_forms_prepared_by=parent_guardian_consent_prepared_by,
            parent_guardian_consent_forms_noted_by=parent_guardian_consent_noted_by
        )

        db.session.add(parent_guardian_consent_form)
        db.session.commit()

        flash('Concept paper added successfully!', 'success')
        return redirect(url_for('concept_papers_overview'))

    # Query for distinct academic years
    academic_years = db.session.query(ConceptPaperForms.concept_paper_forms_academic_year).distinct().all()
    academic_years = [year[0] for year in academic_years]

    # Query for users
    users = Users.query.all()

    # Query for signatories
    signatories = Signatories.query.all()

    return render_template('add-concept-paper.html', academic_years=academic_years, users=users, signatories=signatories)

@app.route("/update-concept-paper-status/<int:paper_id>", methods=["POST"])
@login_required
def update_concept_paper_status(paper_id):
    data = request.get_json()
    new_status = data.get('status')

    # Find the concept paper by ID
    concept_paper = ConceptPaperForms.query.get_or_404(paper_id)

    # Update the concept paper status
    concept_paper.concept_paper_forms_status = new_status
    db.session.commit()

    return jsonify(success=True)

@app.route('/update-concept-paper/<int:paper_id>', methods=['GET', 'POST'])
@login_required
def update_concept_paper(paper_id):
    concept_paper = ConceptPaperForms.query.get_or_404(paper_id)
    learning_journal = LearningJournalForms.query.filter_by(learning_journal_forms_concept_paper_forms_id=paper_id).first()
    parent_guardian_consent_form = ParentGuardianConsentForms.query.filter_by(parent_guardian_consent_forms_concept_paper_forms_id=paper_id).first()
    personnel_in_charge_form = PersonnelInChargeForms.query.filter_by(personnel_in_charge_forms_concept_paper_forms_id=paper_id).first()

    if request.method == 'POST':
        concept_paper_date = request.form.get('concept-paper-date')
        concept_paper_subject = request.form.get('concept-paper-subject')
        concept_paper_academic_year = request.form.get('concept-paper-academic-year')
        other_academic_year = request.form.get('other-academic-year')
        concept_paper_semester = request.form.get('concept-paper-semester')
        concept_paper_status = request.form.get('concept-paper-status')
        concept_paper_event_start_date_and_time = request.form.get('concept-paper-event-start-date-and-time')
        concept_paper_event_end_date_and_time = request.form.get('concept-paper-event-end-date-and-time')
        concept_paper_location = request.form.get('concept-paper-location')
        concept_paper_participants = request.form.get('concept-paper-participants')
        concept_paper_budget = request.form.get('concept-paper-budget')
        concept_paper_descriptions = request.form.get('concept-paper-descriptions')
        concept_paper_expected_number_of_participants = request.form.get('concept-paper-expected-number-of-participants')
        concept_paper_body = request.form.get('concept-paper-body')
        concept_paper_objectives = request.form.getlist('concept-paper-objectives')
        concept_paper_learning_outcomes = request.form.getlist('concept-paper-learning-outcomes')
        concept_paper_prepared_by = request.form.get('concept-paper-prepared-by')
        concept_paper_signed_and_reviewed_by = request.form.get('concept-paper-signed-and-reviewed-by')
        concept_paper_endorsed_by = request.form.get('concept-paper-endorsed-by')
        concept_paper_recommending_approval_by = request.form.get('concept-paper-recommending-approval-by')
        concept_paper_approved_by = request.form.get('concept-paper-approved-by')
        concept_paper_observations = request.form.getlist('learning-journal-observations')
        concept_paper_learnings = request.form.getlist('learning-journal-learnings')

        # Use the value from the additional input field if "Other A.Y." is selected
        if concept_paper_academic_year == "Other":
            concept_paper_academic_year = other_academic_year

        # Convert date and time fields to datetime objects
        concept_paper_date = datetime.strptime(concept_paper_date, '%Y-%m-%dT%H:%M')
        concept_paper_event_start_date_and_time = datetime.strptime(concept_paper_event_start_date_and_time, '%Y-%m-%dT%H:%M')
        concept_paper_event_end_date_and_time = datetime.strptime(concept_paper_event_end_date_and_time, '%Y-%m-%dT%H:%M')

        # Excuse Letter Form data
        excuse_letter_department_office_unit = request.form.get('excuse-letter-department-office-unit')
        excuse_letter_faculty_in_charge = request.form.get('excuse-letter-faculty-in-charge')
        excuse_letter_dean = request.form.get('excuse-letter-dean')
        excuse_letter_noted_by = request.form.get('excuse-letter-noted-by')

        # Update the concept paper
        concept_paper.concept_paper_forms_date = concept_paper_date
        concept_paper.concept_paper_forms_subject = concept_paper_subject
        concept_paper.concept_paper_forms_academic_year = concept_paper_academic_year
        concept_paper.concept_paper_forms_semester = concept_paper_semester
        concept_paper.concept_paper_forms_status = concept_paper_status
        concept_paper.concept_paper_forms_event_start_date_and_time = concept_paper_event_start_date_and_time
        concept_paper.concept_paper_forms_event_end_date_and_time = concept_paper_event_end_date_and_time
        concept_paper.concept_paper_forms_location = concept_paper_location
        concept_paper.concept_paper_forms_participants = concept_paper_participants
        concept_paper.concept_paper_forms_budget = concept_paper_budget
        concept_paper.concept_paper_forms_descriptions = concept_paper_descriptions
        concept_paper.concept_paper_forms_expected_number_of_participants = concept_paper_expected_number_of_participants
        concept_paper.concept_paper_forms_body = concept_paper_body
        concept_paper.concept_paper_forms_prepared_by = concept_paper_prepared_by
        concept_paper.concept_paper_forms_signed_and_reviewed_by = concept_paper_signed_and_reviewed_by
        concept_paper.concept_paper_forms_endorsed_by = concept_paper_endorsed_by
        concept_paper.concept_paper_forms_recommending_approval_by = concept_paper_recommending_approval_by
        concept_paper.concept_paper_forms_approved_by = concept_paper_approved_by

        # Update objectives of the activity
        # First delete existing objectives
        for objective_link in concept_paper.objectives_of_the_activity:
            db.session.delete(objective_link.objective_of_the_activity)
            db.session.delete(objective_link)
        
        # Add new objectives
        for objective_content in concept_paper_objectives:
            new_objective = ObjectivesOfTheActivity(
                objectives_of_the_activity_content=objective_content
            )
            db.session.add(new_objective)
            db.session.commit()

            # Link the objective to the concept paper
            concept_paper_objective_link = ConceptPaperFormObjectivesOfTheActivity(
                concept_paper_forms_id=paper_id,
                objectives_of_the_activity_id=new_objective.objectives_of_the_activity_id
            )
            db.session.add(concept_paper_objective_link)
            db.session.commit()

        # Update learning outcomes
        # First delete existing learning outcomes
        for outcome_link in concept_paper.learning_outcomes:
            db.session.delete(outcome_link.learning_outcome)
            db.session.delete(outcome_link)
        
        # Add new learning outcomes
        for outcome_content in concept_paper_learning_outcomes:
            new_outcome = LearningOutcomes(
                learning_outcomes_content=outcome_content
            )
            db.session.add(new_outcome)
            db.session.commit()

            # Link the learning outcome to the concept paper
            concept_paper_outcome_link = ConceptPaperFormLearningOutcomes(
                concept_paper_forms_id=paper_id,
                learning_outcomes_id=new_outcome.learning_outcomes_id
            )
            db.session.add(concept_paper_outcome_link)
            db.session.commit()

        # Update observations in the observations table
        LearningJournalFormsObservations.query.filter_by(learning_journal_forms_id=learning_journal.learning_journal_forms_id).delete()
        for observation_content in concept_paper_observations:
            observation = Observations(observations_content=observation_content)
            db.session.add(observation)
            db.session.commit()
            learning_journal_observation = LearningJournalFormsObservations(
                learning_journal_forms_id=learning_journal.learning_journal_forms_id,
                observations_id=observation.observations_id
            )
            db.session.add(learning_journal_observation)
            db.session.commit()

        # Update learnings in the learnings table
        LearningJournalFormsLearnings.query.filter_by(learning_journal_forms_id=learning_journal.learning_journal_forms_id).delete()
        for learning_content in concept_paper_learnings:
            learning = Learnings(learnings_content=learning_content)
            db.session.add(learning)
            db.session.commit()
            learning_journal_learning = LearningJournalFormsLearnings(
                learning_journal_forms_id=learning_journal.learning_journal_forms_id,
                learnings_id=learning.learnings_id
            )
            db.session.add(learning_journal_learning)
            db.session.commit()

        # Update Excuse Letter Form
        if concept_paper.excuse_letter_forms:
            excuse_letter_form = concept_paper.excuse_letter_forms[0]
            excuse_letter_form.excuse_letter_forms_department_office_unit = excuse_letter_department_office_unit
            excuse_letter_form.excuse_letter_forms_faculty_in_charge = excuse_letter_faculty_in_charge
            excuse_letter_form.excuse_letter_forms_dean = excuse_letter_dean
            excuse_letter_form.excuse_letter_forms_noted_by = excuse_letter_noted_by
        else:
            new_excuse_letter_form = ExcuseLetterForms(
                excuse_letter_forms_concept_paper_forms_id=concept_paper.concept_paper_forms_id,
                excuse_letter_forms_department_office_unit=excuse_letter_department_office_unit,
                excuse_letter_forms_faculty_in_charge=excuse_letter_faculty_in_charge,
                excuse_letter_forms_dean=excuse_letter_dean,
                excuse_letter_forms_noted_by=excuse_letter_noted_by
            )
            db.session.add(new_excuse_letter_form)

        # Activity Report Form data
        activity_report_date_submission = request.form.get('activity-report-date-submission')
        activity_report_contact_numbers = request.form.get('activity-report-contact-numbers')
        activity_report_prepared_by = request.form.get('activity-report-prepared-by')
        activity_report_noted_by = request.form.get('activity-report-noted-by')
        activity_strengths = request.form.getlist('activity-strengths')
        activity_weaknesses = request.form.getlist('activity-weaknesses')
        activity_recommendations = request.form.getlist('activity-recommendations')

        # Update or create Activity Report Form
        activity_report = ActivityReportForms.query.filter_by(
            activity_report_forms_concept_paper_forms_id=paper_id
        ).first()

        if activity_report_date_submission:
            if not activity_report:
                activity_report = ActivityReportForms(
                    activity_report_forms_concept_paper_forms_id=paper_id
                )
                db.session.add(activity_report)

            activity_report.activity_report_date_submission = datetime.strptime(activity_report_date_submission, '%Y-%m-%d')
            activity_report.activity_report_forms_contact_numbers = activity_report_contact_numbers
            activity_report.activity_report_forms_prepared_by = activity_report_prepared_by
            activity_report.activity_report_forms_noted_by = activity_report_noted_by
            db.session.commit()

            # Update strengths
            ActivityReportFormsActivityStrengths.query.filter_by(
                activity_report_forms_id=activity_report.activity_report_forms_id
            ).delete()
            
            for strength in activity_strengths:
                new_strength = ActivityStrengths(activity_strengths_content=strength)
                db.session.add(new_strength)
                db.session.commit()
                
                strength_link = ActivityReportFormsActivityStrengths(
                    activity_report_forms_id=activity_report.activity_report_forms_id,
                    activity_strengths_id=new_strength.activity_strengths_id
                )
                db.session.add(strength_link)

            # Update weaknesses
            ActivityReportFormsActivityWeaknesses.query.filter_by(
                activity_report_forms_id=activity_report.activity_report_forms_id
            ).delete()
            
            for weakness in activity_weaknesses:
                new_weakness = ActivityWeaknesses(activity_weaknesses_content=weakness)
                db.session.add(new_weakness)
                db.session.commit()
                
                weakness_link = ActivityReportFormsActivityWeaknesses(
                    activity_report_forms_id=activity_report.activity_report_forms_id,
                    activity_weaknesses_id=new_weakness.activity_weaknesses_id
                )
                db.session.add(weakness_link)

            # Update recommendations
            ActivityReportFormsActivityRecommendations.query.filter_by(
                activity_report_forms_id=activity_report.activity_report_forms_id
            ).delete()
            
            for recommendation in activity_recommendations:
                new_recommendation = ActivityRecommendations(activity_recommendations_content=recommendation)
                db.session.add(new_recommendation)
                db.session.commit()
                
                recommendation_link = ActivityReportFormsActivityRecommendations(
                    activity_report_forms_id=activity_report.activity_report_forms_id,
                    activity_recommendations_id=new_recommendation.activity_recommendations_id
                )
                db.session.add(recommendation_link)

        # Personnel In Charge Form data
        personnel_in_charge = request.form.get('personnel-in-charge')
        personnel_in_charge_noted_by_college_dean = request.form.get('personnel-in-charge-noted-by-college-dean')
        personnel_in_charge_noted_by_sas = request.form.get('personnel-in-charge-noted-by-sas')
        
        # Update or create Personnel In Charge Form
        if personnel_in_charge:
            personnel_in_charge_form = PersonnelInChargeForms.query.filter_by(
                personnel_in_charge_forms_concept_paper_forms_id=paper_id
            ).first()
        
            if not personnel_in_charge_form:
                personnel_in_charge_form = PersonnelInChargeForms(
                    personnel_in_charge_forms_concept_paper_forms_id=paper_id
                )
                db.session.add(personnel_in_charge_form)
        
            personnel_in_charge_form.personnel_in_charge_forms_name_of_personnel_in_charge = personnel_in_charge
            personnel_in_charge_form.personnel_in_charge_noted_by_college_dean = personnel_in_charge_noted_by_college_dean
            personnel_in_charge_form.personnel_in_charge_noted_by_sas = personnel_in_charge_noted_by_sas
            db.session.commit()
        
            # Update Activity Report Form with personnel in charge reference
            if activity_report:
                activity_report.activity_report_forms_personnel_in_charge_forms_id = personnel_in_charge_form.personnel_in_charge_forms_id
                db.session.commit()

        # Learning Journal Form data
        learning_journal_name_of_student = request.form.get('learning-journal-name-of-student')
        learning_journal_course_year_level = request.form.get('learning-journal-course-year-level')
        learning_journal_id_number = request.form.get('learning-journal-id-number')
        learning_journal_date = request.form.get('learning-journal-date')
        learning_journal_overall_reflection = request.form.get('learning-journal-overall-reflection')
        learning_journal_prepared_by = request.form.get('learning-journal-prepared-by')
        learning_journal_seen_and_read_by = request.form.get('learning-journal-seen-and-read-by')
        learning_journal_checked_by = request.form.get('learning-journal-checked-by')

        # Convert date and time fields to datetime objects
        learning_journal_date = datetime.strptime(learning_journal_date, '%Y-%m-%d')

        # Update the learning journal form
        learning_journal.learning_journal_forms_name_of_student = learning_journal_name_of_student
        learning_journal.learning_journal_forms_course_year_level = learning_journal_course_year_level
        learning_journal.learning_journal_forms_id_number = learning_journal_id_number
        learning_journal.learning_journal_forms_date = learning_journal_date
        learning_journal.learning_journal_forms_overall_reflection = learning_journal_overall_reflection
        learning_journal.learning_journal_forms_prepared_by = learning_journal_prepared_by
        learning_journal.learning_journal_forms_seen_and_read_by = learning_journal_seen_and_read_by
        learning_journal.learning_journal_forms_checked_by = learning_journal_checked_by

        db.session.commit()

        # Parent/Guardian Consent Form data
        parent_guardian_consent_name_of_student = request.form.get('parent-guardian-consent-name-of-student')
        parent_guardian_consent_course_year_level = request.form.get('parent-guardian-consent-course-year-level')
        parent_guardian_consent_id_number = request.form.get('parent-guardian-consent-id-number')
        parent_guardian_consent_department_office_unit = request.form.get('parent-guardian-consent-department-office-unit')
        parent_guardian_consent_dean_immediate_supervisor = request.form.get('parent-guardian-consent-dean-immediate-supervisor')
        parent_guardian_consent_checked_by = request.form.get('parent-guardian-consent-checked-by')
        parent_guardian_consent_content = request.form.get('parent-guardian-consent-content')
        parent_guardian_consent_prepared_by = request.form.get('parent-guardian-consent-prepared-by')
        parent_guardian_consent_noted_by = request.form.get('parent-guardian-consent-noted-by')

        # Update Parent/Guardian Consent Form
        if parent_guardian_consent_form:
            parent_guardian_consent_form.parent_guardian_consent_forms_name_of_student = parent_guardian_consent_name_of_student
            parent_guardian_consent_form.parent_guardian_consent_forms_course_year_level = parent_guardian_consent_course_year_level
            parent_guardian_consent_form.parent_guardian_consent_forms_id_number = parent_guardian_consent_id_number
            parent_guardian_consent_form.parent_guardian_consent_forms_department_office_unit = parent_guardian_consent_department_office_unit
            parent_guardian_consent_form.parent_guardian_consent_forms_dean_immediate_supervisor = parent_guardian_consent_dean_immediate_supervisor
            parent_guardian_consent_form.parent_guardian_consent_forms_checked_by = parent_guardian_consent_checked_by
            parent_guardian_consent_form.parent_guardian_consent_forms_content = parent_guardian_consent_content
            parent_guardian_consent_form.parent_guardian_consent_forms_prepared_by = parent_guardian_consent_prepared_by
            parent_guardian_consent_form.parent_guardian_consent_forms_noted_by = parent_guardian_consent_noted_by
        else:
            parent_guardian_consent_form = ParentGuardianConsentForms(
                parent_guardian_consent_forms_concept_paper_forms_id=paper_id,
                parent_guardian_consent_forms_name_of_student=parent_guardian_consent_name_of_student,
                parent_guardian_consent_forms_course_year_level=parent_guardian_consent_course_year_level,
                parent_guardian_consent_forms_id_number=parent_guardian_consent_id_number,
                parent_guardian_consent_forms_department_office_unit=parent_guardian_consent_department_office_unit,
                parent_guardian_consent_forms_dean_immediate_supervisor=parent_guardian_consent_dean_immediate_supervisor,
                parent_guardian_consent_forms_checked_by=parent_guardian_consent_checked_by,
                parent_guardian_consent_forms_content=parent_guardian_consent_content,
                parent_guardian_consent_forms_prepared_by=parent_guardian_consent_prepared_by,
                parent_guardian_consent_forms_noted_by=parent_guardian_consent_noted_by
            )
            db.session.add(parent_guardian_consent_form)

        db.session.commit()

        flash('Concept paper updated successfully!', 'success')
        return redirect(url_for('concept_papers_overview'))

    # Query for distinct academic years
    academic_years = db.session.query(ConceptPaperForms.concept_paper_forms_academic_year).distinct().all()
    academic_years = [year[0] for year in academic_years]

    # Query for users
    users = Users.query.all()

    # Query for signatories
    signatories = Signatories.query.all()

    # Fetch objectives of the activity and learning outcomes
    objectives_of_the_activity = [
        obj.objective_of_the_activity.objectives_of_the_activity_content
        for obj in ConceptPaperFormObjectivesOfTheActivity.query.filter_by(concept_paper_forms_id=paper_id).all()
    ]
    learning_outcomes = [
        outcome.learning_outcome.learning_outcomes_content
        for outcome in ConceptPaperFormLearningOutcomes.query.filter_by(concept_paper_forms_id=paper_id).all()
    ]

    # Fetch noted by college dean and noted by head of sas for the personnel in charge form
    noted_by_college_dean = personnel_in_charge_form.personnel_in_charge_forms_noted_by_college_dean if personnel_in_charge_form else None
    noted_by_sas = personnel_in_charge_form.personnel_in_charge_forms_noted_by_sas if personnel_in_charge_form else None

    return render_template('update-concept-paper.html', concept_paper=concept_paper, academic_years=academic_years, users=users, signatories=signatories, objectives_of_the_activity=objectives_of_the_activity, learning_outcomes=learning_outcomes, learning_journal=learning_journal, parent_guardian_consent_form=parent_guardian_consent_form, noted_by_college_dean=noted_by_college_dean, noted_by_sas=noted_by_sas)

@app.route('/delete-concept-paper/<int:paper_id>', methods=['GET', 'POST'])
@login_required
def delete_concept_paper(paper_id):
    concept_paper = ConceptPaperForms.query.get_or_404(paper_id)

    if request.method == 'POST':
        # Delete associated learning outcomes
        ConceptPaperFormLearningOutcomes.query.filter_by(concept_paper_forms_id=paper_id).delete()
        
        # Delete associated objectives of the activity
        ConceptPaperFormObjectivesOfTheActivity.query.filter_by(concept_paper_forms_id=paper_id).delete()
        
        # Delete the concept paper
        db.session.delete(concept_paper)
        db.session.commit()

        flash('Concept paper deleted successfully!', 'success')
        return redirect(url_for('concept_papers_overview'))

    return render_template('delete-concept-paper.html', concept_paper=concept_paper)

@app.route("/documentation-overview")
@login_required
def documentation_overview():
    # Query for all documentation
    documentations = Documentation.query.all()

    return render_template("documentation-overview.html", documentations=documentations)

@app.route('/add-documentation', methods=['GET', 'POST'])
@login_required
def add_documentation():
    if request.method == 'POST':
        documentation_events_id = request.form.get('documentation-events-id')
        documentation_status = request.form.get('documentation-status')
        documentation_type = request.form.get('documentation-type')
        documentation_activity_report_forms_id = request.form.get('documentation-activity-report-forms-id')
        documentation_prepared_by = request.form.get('documentation-prepared-by')
        documentation_learning_journal_forms_id = request.form.get('documentation-learning-journal-forms-id')
        documentation_checked_by = request.form.get('documentation-checked-by')
        documentation_noted_by = request.form.get('documentation-noted-by')
        documentation_date_of_submission = request.form.get('documentation-date-of-submission')
        documentation_rating = request.form.get('documentation-rating')
        documentation_comments_suggestions = request.form.get('documentation-comments-suggestions')
        activity_strengths = request.form.getlist('activity-strengths')
        activity_weaknesses = request.form.getlist('activity-weaknesses')
        activity_recommendations = request.form.getlist('activity-recommendations')

        # Retrieve event details using documentation_events_id
        event = Events.query.get(documentation_events_id)
        if event:
            documentation_academic_year = event.events_academic_year
            documentation_semester = event.events_semester

        # Convert date fields to datetime objects
        documentation_date_of_submission = datetime.strptime(documentation_date_of_submission, '%Y-%m-%d')

        # Create a new documentation entry
        new_documentation = Documentation(
            documentation_events_id=documentation_events_id,
            documentation_academic_year=documentation_academic_year,
            documentation_semester=documentation_semester,
            documentation_status=documentation_status,
            documentation_type=documentation_type,
            documentation_activity_report_forms_id=documentation_activity_report_forms_id,
            documentation_prepared_by=documentation_prepared_by,
            documentation_learning_journal_forms_id=documentation_learning_journal_forms_id,
            documentation_checked_by=documentation_checked_by,
            documentation_noted_by=documentation_noted_by,
            documentation_date_of_submission=documentation_date_of_submission,
            documentation_rating=documentation_rating,
            documentation_comments_suggestions=documentation_comments_suggestions
        )

        # Add the new documentation to the database
        db.session.add(new_documentation)
        db.session.flush()  # Ensure the documentation ID is available

        # Add activity strengths
        for strength_content in activity_strengths:
            if strength_content:
                strength = ActivityStrengths(activity_strengths_content=strength_content)
                db.session.add(strength)
                db.session.flush()  # Ensure the strength ID is available
                activity_report_strength = ActivityReportFormsActivityStrengths(
                    activity_report_forms_id=documentation_activity_report_forms_id,
                    activity_strengths_id=strength.activity_strengths_id
                )
                db.session.add(activity_report_strength)

        # Add activity weaknesses
        for weakness_content in activity_weaknesses:
            if weakness_content:
                weakness = ActivityWeaknesses(activity_weaknesses_content=weakness_content)
                db.session.add(weakness)
                db.session.flush()  # Ensure the weakness ID is available
                activity_report_weakness = ActivityReportFormsActivityWeaknesses(
                    activity_report_forms_id=documentation_activity_report_forms_id,
                    activity_weaknesses_id=weakness.activity_weaknesses_id
                )
                db.session.add(activity_report_weakness)

        # Add activity recommendations
        for recommendation_content in activity_recommendations:
            if recommendation_content:
                recommendation = ActivityRecommendations(activity_recommendations_content=recommendation_content)
                db.session.add(recommendation)
                db.session.flush()  # Ensure the recommendation ID is available
                activity_report_recommendation = ActivityReportFormsActivityRecommendations(
                    activity_report_forms_id=documentation_activity_report_forms_id,
                    activity_recommendations_id=recommendation.activity_recommendations_id
                )
                db.session.add(activity_report_recommendation)

        db.session.commit()
        flash("Documentation added successfully!", "success")
        return redirect(url_for('documentation_overview'))

    # Query for events
    events = Events.query.all()

    # Query for distinct academic years
    academic_years = db.session.query(Documentation.documentation_academic_year).distinct().all()
    academic_years = [year[0] for year in academic_years]

    # Query for users
    users = Users.query.all()

    # Query for signatories
    signatories = Signatories.query.all()

    # Query for activity report forms and include related events
    activity_reports = db.session.query(ActivityReportForms).join(Events, ActivityReportForms.activity_report_forms_concept_paper_forms_id == Events.events_concept_paper_forms_id).all()

    # Query for learning journal forms and include related events
    learning_journals = db.session.query(LearningJournalForms).join(Events, LearningJournalForms.learning_journal_forms_concept_paper_forms_id == Events.events_concept_paper_forms_id).all()

    return render_template('add-documentation.html', events=events, academic_years=academic_years, users=users, signatories=signatories, activity_reports=activity_reports, learning_journals=learning_journals)

@app.route("/update-documentation-status/<int:documentation_id>", methods=["POST"])
@login_required
def update_documentation_status(documentation_id):
    data = request.get_json()
    new_status = data.get('status')

    # Find the documentation by ID
    documentation = Documentation.query.get_or_404(documentation_id)

    # Update the documentation status
    documentation.documentation_status = new_status
    db.session.commit()

    return jsonify(success=True)

@app.route('/update-documentation/<int:documentation_id>', methods=['GET', 'POST'])
@login_required
def update_documentation(documentation_id):
    documentation = Documentation.query.get_or_404(documentation_id)

    if request.method == 'POST':
        documentation_events_id = request.form.get('documentation-events-id')
        documentation_academic_year = request.form.get('documentation-academic-year')
        other_academic_year = request.form.get('other-academic-year')
        documentation_semester = request.form.get('documentation-semester')
        documentation_status = request.form.get('documentation-status')
        documentation_type = request.form.get('documentation-type')
        documentation_activity_report_forms_id = request.form.get('documentation-activity-report-forms-id')
        documentation_prepared_by = request.form.get('documentation-prepared-by')
        documentation_learning_journal_forms_id = request.form.get('documentation-learning-journal-forms-id')
        documentation_checked_by = request.form.get('documentation-checked-by')
        documentation_noted_by = request.form.get('documentation-noted-by')
        documentation_date_of_submission = request.form.get('documentation-date-of-submission')
        documentation_rating = request.form.get('documentation-rating')
        documentation_comments_suggestions = request.form.get('documentation-comments-suggestions')

        # Use the value from the additional input field if "Other A.Y." is selected
        if documentation_academic_year == "Other":
            documentation_academic_year = other_academic_year

        # Convert date fields to datetime objects
        documentation_date_of_submission = datetime.strptime(documentation_date_of_submission, '%Y-%m-%d')

        # Update the documentation entry
        documentation.documentation_events_id = documentation_events_id
        documentation.documentation_academic_year = documentation_academic_year
        documentation.documentation_semester = documentation_semester
        documentation.documentation_status = documentation_status
        documentation.documentation_type = documentation_type
        documentation.documentation_activity_report_forms_id = documentation_activity_report_forms_id
        documentation.documentation_prepared_by = documentation_prepared_by
        documentation.documentation_learning_journal_forms_id = documentation_learning_journal_forms_id
        documentation.documentation_checked_by = documentation_checked_by
        documentation.documentation_noted_by = documentation_noted_by
        documentation.documentation_date_of_submission = documentation_date_of_submission
        documentation.documentation_rating = documentation_rating
        documentation.documentation_comments_suggestions = documentation_comments_suggestions

        db.session.commit()

        flash('Documentation updated successfully!', 'success')
        return redirect(url_for('documentation_overview'))

    # Query for events
    events = Events.query.all()

    # Query for distinct academic years
    academic_years = db.session.query(Documentation.documentation_academic_year).distinct().all()
    academic_years = [year[0] for year in academic_years]

    # Query for users
    users = Users.query.all()

    # Query for signatories
    signatories = Signatories.query.all()

    # Query for activity report forms
    activity_reports = ActivityReportForms.query.all()

    # Query for learning journal forms
    learning_journals = LearningJournalForms.query.all()

    return render_template('update-documentation.html', documentation=documentation, events=events, academic_years=academic_years, users=users, signatories=signatories, activity_reports=activity_reports, learning_journals=learning_journals)

@app.route('/delete-documentation/<int:documentation_id>', methods=['GET', 'POST'])
@login_required
def delete_documentation(documentation_id):
    documentation = Documentation.query.get_or_404(documentation_id)

    if request.method == 'POST':
        # Delete the documentation
        db.session.delete(documentation)
        db.session.commit()

        flash('Documentation deleted successfully!', 'success')
        return redirect(url_for('documentation_overview'))

    return render_template('delete-documentation.html', documentation=documentation)

@app.route('/get-related-forms/<int:event_id>', methods=['GET'])
@login_required
def get_related_forms(event_id):
    # Query for the concept paper form ID related to the event
    concept_paper_form_id = db.session.query(Events.events_concept_paper_forms_id).filter(Events.events_id == event_id).scalar()

    # Query for activity report forms related to the concept paper form
    activity_reports = db.session.query(ActivityReportForms).filter(ActivityReportForms.activity_report_forms_concept_paper_forms_id == concept_paper_form_id).all()

    # Query for learning journal forms related to the concept paper form
    learning_journals = db.session.query(LearningJournalForms).filter(LearningJournalForms.learning_journal_forms_concept_paper_forms_id == concept_paper_form_id).all()

    # Prepare the data to be sent as JSON
    activity_reports_data = [{'activity_report_forms_id': report.activity_report_forms_id, 'events_name': report.concept_paper_form.concept_paper_forms_subject} for report in activity_reports]
    learning_journals_data = [{'learning_journal_forms_id': journal.learning_journal_forms_id, 'events_name': journal.concept_paper_form.concept_paper_forms_subject} for journal in learning_journals]

    return jsonify(activity_reports=activity_reports_data, learning_journals=learning_journals_data)

@app.route('/get-activity-report-details/<int:activity_report_id>', methods=['GET'])
@login_required
def get_activity_report_details(activity_report_id):
    # Query for activity strengths related to the activity report form
    strengths = db.session.query(ActivityStrengths).join(ActivityReportFormsActivityStrengths).filter(ActivityReportFormsActivityStrengths.activity_report_forms_id == activity_report_id).all()

    # Query for activity weaknesses related to the activity report form
    weaknesses = db.session.query(ActivityWeaknesses).join(ActivityReportFormsActivityWeaknesses).filter(ActivityReportFormsActivityWeaknesses.activity_report_forms_id == activity_report_id).all()

    # Query for activity recommendations related to the activity report form
    recommendations = db.session.query(ActivityRecommendations).join(ActivityReportFormsActivityRecommendations).filter(ActivityReportFormsActivityRecommendations.activity_report_forms_id == activity_report_id).all()

    # Prepare the data to be sent as JSON
    strengths_data = [{'activity_strengths_content': strength.activity_strengths_content} for strength in strengths]
    weaknesses_data = [{'activity_weaknesses_content': weakness.activity_weaknesses_content} for weakness in weaknesses]
    recommendations_data = [{'activity_recommendations_content': recommendation.activity_recommendations_content} for recommendation in recommendations]

    return jsonify(strengths=strengths_data, weaknesses=weaknesses_data, recommendations=recommendations_data)

@app.route("/financial-reports-overview")
@login_required
def financial_reports_overview():
    # Query for all financial reports
    financial_reports = FinancialReports.query.all()

    # Determine the sorting order
    sort_by_date = request.args.get('sort_by_date', 'recent-to-old')

    return render_template("financial-reports-overview.html", financial_reports=financial_reports, sort_by_date=sort_by_date)

@app.route('/add-financial-report', methods=['GET', 'POST'])
@login_required
def add_financial_report():
    if request.method == 'POST':
        financial_reports_date = request.form.get('financial-reports-date')
        financial_reports_academic_year = request.form.get('financial-reports-academic-year')
        financial_reports_semester = request.form.get('financial-reports-semester')
        financial_reports_events_id = request.form.get('financial-reports-events-id')
        financial_reports_title = request.form.get('financial-reports-title')
        financial_reports_status = request.form.get('financial-reports-status')
        financial_reports_audited_and_prepared_by = request.form.get('financial-reports-audited-and-prepared-by')
        financial_reports_noted_by = request.form.get('financial-reports-noted-by')
        financial_reports_recommending_approval_by = request.form.get('financial-reports-recommending-approval-by')
        financial_reports_approved_by = request.form.get('financial-reports-approved-by')

        # Create a new financial report
        new_financial_report = FinancialReports(
            financial_reports_date=datetime.strptime(financial_reports_date, '%Y-%m-%dT%H:%M'),
            financial_reports_academic_year=financial_reports_academic_year,
            financial_reports_semester=financial_reports_semester,
            financial_reports_events_id=financial_reports_events_id,
            financial_reports_title=financial_reports_title,
            financial_reports_status=financial_reports_status,
            financial_reports_audited_and_prepared_by=financial_reports_audited_and_prepared_by,
            financial_reports_noted_by=financial_reports_noted_by,
            financial_reports_recommending_approval_by=financial_reports_recommending_approval_by,
            financial_reports_approved_by=financial_reports_approved_by
        )

        # Add the new financial report to the database
        db.session.add(new_financial_report)
        db.session.commit()

        flash('Financial report added successfully!', 'success')
        return redirect(url_for('financial_reports_overview'))

    # Query for events that do not have a financial report
    events = Events.query.outerjoin(FinancialReports, Events.events_id == FinancialReports.financial_reports_events_id) \
                         .filter(FinancialReports.financial_reports_events_id == None).all()

    # Query for users grouped by student organization
    student_organizations = StudentOrganizations.query.all()

    # Query for signatories
    signatories = Signatories.query.all()

    # Query for distinct academic years
    academic_years = db.session.query(FinancialReports.financial_reports_academic_year).distinct().all()
    academic_years = [year[0] for year in academic_years]

    return render_template('add-financial-report.html', events=events, student_organizations=student_organizations, signatories=signatories, academic_years=academic_years)

@app.route('/update-financial-report/<int:report_id>', methods=['GET', 'POST'])
@login_required
def update_financial_report(report_id):
    report = FinancialReports.query.get_or_404(report_id)

    if request.method == 'POST':
        financial_reports_date = request.form.get('financial-reports-date')
        financial_reports_academic_year = request.form.get('financial-reports-academic-year')
        financial_reports_semester = request.form.get('financial-reports-semester')
        financial_reports_events_id = request.form.get('financial-reports-events-id')
        financial_reports_title = request.form.get('financial-reports-title')
        financial_reports_status = request.form.get('financial-reports-status')
        financial_reports_audited_and_prepared_by = request.form.get('financial-reports-audited-and-prepared-by')
        financial_reports_noted_by = request.form.get('financial-reports-noted-by')
        financial_reports_recommending_approval_by = request.form.get('financial-reports-recommending-approval-by')
        financial_reports_approved_by = request.form.get('financial-reports-approved-by')

        # Update the financial report
        report.financial_reports_date = datetime.strptime(financial_reports_date, '%Y-%m-%dT%H:%M')
        report.financial_reports_academic_year = financial_reports_academic_year
        report.financial_reports_semester = financial_reports_semester
        report.financial_reports_events_id = financial_reports_events_id
        report.financial_reports_title = financial_reports_title
        report.financial_reports_status = financial_reports_status
        report.financial_reports_audited_and_prepared_by = financial_reports_audited_and_prepared_by
        report.financial_reports_noted_by = financial_reports_noted_by
        report.financial_reports_recommending_approval_by = financial_reports_recommending_approval_by
        report.financial_reports_approved_by = financial_reports_approved_by

        db.session.commit()

        flash('Financial report updated successfully!', 'success')
        return redirect(url_for('financial_reports_overview'))

    # Query for events
    events = Events.query.all()

    # Query for users grouped by student organization
    student_organizations = StudentOrganizations.query.all()

    # Query for signatories
    signatories = Signatories.query.all()

    # Query for distinct academic years
    academic_years = db.session.query(FinancialReports.financial_reports_academic_year).distinct().all()
    academic_years = [year[0] for year in academic_years]

    return render_template('update-financial-report.html', report=report, events=events, student_organizations=student_organizations, signatories=signatories, academic_years=academic_years)

@app.route("/update-financial-report-status/<int:report_id>", methods=["POST"])
@login_required
def update_financial_report_status(report_id):
    data = request.get_json()
    new_status = data.get('status')

    # Find the financial report by ID
    report = FinancialReports.query.get_or_404(report_id)

    # Update the financial report status
    report.financial_reports_status = new_status
    db.session.commit()

    return jsonify(success=True)

@app.route('/delete-financial-report/<int:report_id>', methods=['GET', 'POST'])
@login_required
def delete_financial_report(report_id):
    report = FinancialReports.query.get_or_404(report_id)

    if request.method == 'POST':
        # Delete the financial report
        db.session.delete(report)
        db.session.commit()

        flash('Financial report deleted successfully!', 'success')
        return redirect(url_for('financial_reports_overview'))

    return render_template('delete-financial-report.html', report=report)

@app.route("/board-resolutions-overview")
@login_required
def board_resolutions_overview():
    # Query for all board resolutions sorted by date (most recent first)
    board_resolutions = BoardResolutions.query.order_by(BoardResolutions.board_resolutions_date.desc()).all()

    # Determine the sorting order
    sort_by_date = request.args.get('sort_by_date', 'recent-to-old')

    return render_template("board-resolutions-overview.html", board_resolutions=board_resolutions, sort_by_date=sort_by_date)

@app.route('/add-board-resolution', methods=['GET', 'POST'])
@login_required
def add_board_resolution():
    if request.method == 'POST':
        events_id = request.form.get('board-resolutions-events-id')
        other_event_name = request.form.get('other-event-name')
        title = request.form.get('board-resolutions-title')
        description = request.form.get('board-resolutions-description')
        total_amount = request.form.get('board-resolutions-total-amount')
        academic_year = request.form.get('board-resolutions-academic-year')
        other_academic_year = request.form.get('other-academic-year')
        semester = request.form.get('board-resolutions-semester')
        status = request.form.get('board-resolutions-status')
        date = request.form.get('board-resolutions-date')
        prepared_by = request.form.get('board-resolutions-prepared-by')
        approved_by = request.form.get('board-resolutions-approved-by')
        student_signatories = request.form.getlist('board-resolutions-student-signatories')

        # Use the value from the "Other" input field if "Other" is selected for academic year
        if academic_year == 'Other':
            academic_year = other_academic_year

        # Handle the "Other" option for event name
        if events_id == 'Other':
            # Create a new event with the provided name
            new_event = Events(
                events_name=other_event_name, 
                events_academic_year=academic_year,
                events_semester=semester,
                events_description=description)
            db.session.add(new_event)
            db.session.commit()
            events_id = new_event.events_id
            
            # Link the event to the department of the current user
            departments_events = DepartmentsEvents(
                departments_id=current_user.users_departments_id,
                events_id=events_id
            )
            db.session.add(departments_events)
            db.session.commit()
        elif events_id == 'None':
            events_id = None

        # Convert date to datetime object
        date = datetime.strptime(date, '%Y-%m-%dT%H:%M')

        # Create a new board resolution
        new_resolution = BoardResolutions(
            board_resolutions_events_id=events_id,
            board_resolutions_title=title,
            board_resolutions_description=description,
            board_resolutions_total_amount=total_amount,
            board_resolutions_academic_year=academic_year,
            board_resolutions_semester=semester,
            board_resolutions_status=status,
            board_resolutions_date=date,
            board_resolutions_prepared_by=prepared_by,
            board_resolutions_approved_by=approved_by
        )

        # Add the new resolution to the database
        db.session.add(new_resolution)
        db.session.commit()

        # Add student signatories to the board_resolutions_student_signatories table
        for signatory_id in student_signatories:
            new_signatory = BoardResolutionsStudentSignatories(
                board_resolutions_id=new_resolution.board_resolutions_id,
                board_resolutions_users_id=signatory_id
            )
            db.session.add(new_signatory)
        db.session.commit()

        flash('Board resolution added successfully!', 'success')
        return redirect(url_for('board_resolutions_overview'))

    # Query for events that are not yet linked to any board resolutions
    events = Events.query.outerjoin(BoardResolutions, Events.events_id == BoardResolutions.board_resolutions_events_id) \
                        .filter(BoardResolutions.board_resolutions_events_id == None).all()

    # Query for distinct academic years
    academic_years = db.session.query(BoardResolutions.board_resolutions_academic_year).distinct().all()
    academic_years = [year[0] for year in academic_years]

    student_organizations = StudentOrganizations.query.all()
    signatories = Signatories.query.all()

    return render_template('add-board-resolution.html', events=events, academic_years=academic_years, student_organizations=student_organizations, signatories=signatories)

@app.route("/delete-board-resolution/<int:resolution_id>", methods=["GET", "POST"])
@login_required
def delete_board_resolution(resolution_id):
    # Find the board resolution by ID
    resolution = BoardResolutions.query.get_or_404(resolution_id)

    if request.method == "POST":
        # Delete related records in the departments_events table
        DepartmentsEvents.query.filter_by(events_id=resolution.board_resolutions_events_id).delete()

        # Delete the board resolution
        db.session.delete(resolution)
        db.session.commit()

        flash("Board resolution deleted successfully.", "success")
        return redirect(url_for("board_resolutions_overview"))

    return render_template("delete-board-resolution.html", resolution=resolution)

@app.route('/update-board-resolution/<int:resolution_id>', methods=['GET', 'POST'])
@login_required
def update_board_resolution(resolution_id):
    resolution = BoardResolutions.query.get_or_404(resolution_id)

    if request.method == 'POST':
        events_id = request.form.get('board-resolutions-events-id')
        other_event_name = request.form.get('other-event-name')
        title = request.form.get('board-resolutions-title')
        description = request.form.get('board-resolutions-description')
        total_amount = request.form.get('board-resolutions-total-amount')
        academic_year = request.form.get('board-resolutions-academic-year')
        other_academic_year = request.form.get('other-academic-year')
        semester = request.form.get('board-resolutions-semester')
        status = request.form.get('board-resolutions-status')
        date = request.form.get('board-resolutions-date')
        prepared_by = request.form.get('board-resolutions-prepared-by')
        approved_by = request.form.get('board-resolutions-approved-by')
        student_signatories = request.form.getlist('board-resolutions-student-signatories')

        # Use the value from the "Other" input field if "Other" is selected for academic year
        if academic_year == 'Other':
            academic_year = other_academic_year

        # Handle the "Other" option for event name
        if events_id == 'Other':
            # Create a new event with the provided name
            new_event = Events(
                events_name=other_event_name, 
                events_academic_year=academic_year,
                events_semester=semester,
                events_description=description)
            db.session.add(new_event)
            db.session.commit()
            events_id = new_event.events_id
            
            # Link the event to the department of the current user
            departments_events = DepartmentsEvents(
                departments_id=current_user.users_departments_id,
                events_id=events_id
            )
            db.session.add(departments_events)
            db.session.commit()
        elif events_id == 'None':
            events_id = None

        # Convert date to datetime object
        date = datetime.strptime(date, '%Y-%m-%dT%H:%M')

        # Update the board resolution
        resolution.board_resolutions_events_id = events_id
        resolution.board_resolutions_title = title
        resolution.board_resolutions_description = description
        resolution.board_resolutions_total_amount = total_amount
        resolution.board_resolutions_academic_year = academic_year
        resolution.board_resolutions_semester = semester
        resolution.board_resolutions_status = status
        resolution.board_resolutions_date = date
        resolution.board_resolutions_prepared_by = prepared_by
        resolution.board_resolutions_approved_by = approved_by

        db.session.commit()

        # Update student signatories in the board_resolutions_student_signatories table
        BoardResolutionsStudentSignatories.query.filter_by(board_resolutions_id=resolution_id).delete()
        for signatory_id in student_signatories:
            new_signatory = BoardResolutionsStudentSignatories(
                board_resolutions_id=resolution_id,
                board_resolutions_users_id=signatory_id
            )
            db.session.add(new_signatory)
        db.session.commit()

        flash('Board resolution updated successfully!', 'success')
        return redirect(url_for('board_resolutions_overview'))

    # Query for events that are not yet linked to any board resolutions
    events = Events.query.outerjoin(BoardResolutions, Events.events_id == BoardResolutions.board_resolutions_events_id) \
                        .filter(BoardResolutions.board_resolutions_events_id == None).all()

    # Query for distinct academic years
    academic_years = db.session.query(BoardResolutions.board_resolutions_academic_year).distinct().all()
    academic_years = [year[0] for year in academic_years]

    student_organizations = StudentOrganizations.query.all()
    signatories = Signatories.query.all()

    # Query for existing student signatories
    existing_signatories = [signatory.board_resolutions_users_id for signatory in resolution.student_signatories]

    return render_template('update-board-resolution.html', resolution=resolution, events=events, academic_years=academic_years, student_organizations=student_organizations, signatories=signatories, existing_signatories=existing_signatories)

@app.route("/update-board-resolution-status/<int:resolution_id>", methods=["POST"])
@login_required
def update_board_resolution_status(resolution_id):
    data = request.get_json()
    new_status = data.get('status')

    # Find the board resolution by ID
    resolution = BoardResolutions.query.get_or_404(resolution_id)

    # Update the board resolution status
    resolution.board_resolutions_status = new_status
    db.session.commit()

    return jsonify(success=True)

@app.route("/minutes-of-the-meeting-overview")
@login_required
def minutes_of_the_meeting_overview():
    # Query for all minutes of the meeting sorted by date (most recent first)
    minutes_of_the_meeting = db.session.query(
        MinutesOfTheMeeting,
        Users.users_first_name,
        Users.users_last_name
    ).join(
        Users, MinutesOfTheMeeting.minutes_of_the_meeting_presiding_officer == Users.users_id
    ).order_by(
        MinutesOfTheMeeting.minutes_of_the_meeting_date.desc()
    ).all()

    # Determine the sorting order
    sort_by_date = request.args.get('sort_by_date', 'recent-to-old')

    # Extract only the MinutesOfTheMeeting objects for filtering
    meetings_only = [meeting for meeting, _, _ in minutes_of_the_meeting]

    return render_template("minutes-of-the-meeting-overview.html", minutes_of_the_meeting=minutes_of_the_meeting, sort_by_date=sort_by_date, meetings_only=meetings_only)

@app.route('/add-minutes-of-the-meeting', methods=['GET', 'POST'])
@login_required
def add_minutes_of_the_meeting():
    if request.method == 'POST':
        date = request.form.get('minutes-of-the-meeting-date')
        semester = request.form.get('minutes-of-the-meeting-semester')
        academic_year = request.form.get('minutes-of-the-meeting-academic-year')
        other_academic_year = request.form.get('other-academic-year')
        status = request.form.get('minutes-of-the-meeting-status')
        presiding_officer = request.form.get('minutes-of-the-meeting-presiding-officer')
        agenda = request.form.get('minutes-of-the-meeting-agenda')
        notes = request.form.get('minutes-of-the-meeting-notes')
        adjourned = request.form.get('minutes-of-the-meeting-adjourned')
        approved_by = request.form.get('minutes-of-the-meeting-approved-by')
        prepared_by = request.form.get('minutes-of-the-meeting-prepared-by')
        noted_by = request.form.get('minutes-of-the-meeting-noted-by')
        attendees = request.form.getlist('minutes-of-the-meeting-attendees')
        photo_documentations = request.files.getlist('photo-documentation')

        # Use the value from the additional input field if "Other A.Y." is selected
        if academic_year == "Other":
            academic_year = other_academic_year

        # Convert date to datetime object
        date = datetime.strptime(date, '%Y-%m-%dT%H:%M')
        adjourned = datetime.strptime(adjourned, '%Y-%m-%dT%H:%M') if adjourned else None

        # Create a new minutes of the meeting
        new_meeting = MinutesOfTheMeeting(
            minutes_of_the_meeting_date=date,
            minutes_of_the_meeting_semester=semester,
            minutes_of_the_meeting_academic_year=academic_year,
            minutes_of_the_meeting_status=status,
            minutes_of_the_meeting_presiding_officer=presiding_officer,
            minutes_of_the_meeting_agenda=agenda,
            minutes_of_the_meeting_notes=notes,
            minutes_of_the_meeting_adjourned=adjourned,
            minutes_of_the_meeting_approved_by=approved_by,
            minutes_of_the_meeting_prepared_by=prepared_by,
            minutes_of_the_meeting_noted_by=noted_by
        )

        # Add the new meeting to the database
        db.session.add(new_meeting)
        db.session.commit()

        # Add attendees to the minutes_of_the_meeting_attendees table
        for attendee_id in attendees:
            new_attendee = MinutesOfTheMeetingAttendees(
                minutes_of_the_meeting_id=new_meeting.minutes_of_the_meeting_id,
                users_id=attendee_id
            )
            db.session.add(new_attendee)
        db.session.commit()

        # Handle multiple file uploads to Cloudinary
        for photo_documentation in photo_documentations:
            if photo_documentation:
                upload_result = cloudinary.uploader.upload(photo_documentation)
                photo_url = upload_result.get('secure_url')
                photo_public_id = upload_result.get('public_id')

                # Create a new photo documentation record
                new_photo_documentation = MinutesOfTheMeetingPhotoDocumentation(
                    minutes_of_the_meeting_id=new_meeting.minutes_of_the_meeting_id,
                    minutes_of_the_meeting_photo_documentation_cloudinary_url=photo_url,
                    minutes_of_the_meeting_photo_documentation_cloudinary_public_id=photo_public_id
                )

                # Add the new photo documentation to the database
                db.session.add(new_photo_documentation)
                db.session.commit()

        flash('Minutes of the meeting added successfully!', 'success')
        return redirect(url_for('minutes_of_the_meeting_overview'))

    # Query for distinct academic years
    academic_years = db.session.query(MinutesOfTheMeeting.minutes_of_the_meeting_academic_year).distinct().all()
    academic_years = [year[0] for year in academic_years]

    # Query for users to populate the approved by and prepared by fields
    users = Users.query.all()

    # Query for signatories to populate the presiding officer and noted by fields
    signatories = Signatories.query.all()

    # Query for student organizations and their members
    student_organizations = StudentOrganizations.query.all()

    return render_template('add-minutes-of-the-meeting.html', academic_years=academic_years, users=users, signatories=signatories, student_organizations=student_organizations)

@app.route('/update-minutes-of-the-meeting/<int:meeting_id>', methods=['GET', 'POST'])
@login_required
def update_minutes_of_the_meeting(meeting_id):
    meeting = MinutesOfTheMeeting.query.get_or_404(meeting_id)

    if request.method == 'POST':
        date = request.form.get('minutes-of-the-meeting-date')
        semester = request.form.get('minutes-of-the-meeting-semester')
        academic_year = request.form.get('minutes-of-the-meeting-academic-year')
        other_academic_year = request.form.get('other-academic-year')
        status = request.form.get('minutes-of-the-meeting-status')
        presiding_officer = request.form.get('minutes-of-the-meeting-presiding-officer')
        agenda = request.form.get('minutes-of-the-meeting-agenda')
        notes = request.form.get('minutes-of-the-meeting-notes')
        adjourned = request.form.get('minutes-of-the-meeting-adjourned')
        approved_by = request.form.get('minutes-of-the-meeting-approved-by')
        prepared_by = request.form.get('minutes-of-the-meeting-prepared-by')
        noted_by = request.form.get('minutes-of-the-meeting-noted-by')
        attendees = request.form.getlist('minutes-of-the-meeting-attendees')
        photo_documentations = request.files.getlist('photo-documentation')

        # Use the value from the additional input field if "Other A.Y." is selected
        if academic_year == "Other":
            academic_year = other_academic_year

        # Convert date to datetime object
        date = datetime.strptime(date, '%Y-%m-%dT%H:%M')
        adjourned = datetime.strptime(adjourned, '%Y-%m-%dT%H:%M') if adjourned else None

        # Update the minutes of the meeting
        meeting.minutes_of_the_meeting_date = date
        meeting.minutes_of_the_meeting_semester = semester
        meeting.minutes_of_the_meeting_academic_year = academic_year
        meeting.minutes_of_the_meeting_status = status
        meeting.minutes_of_the_meeting_presiding_officer = presiding_officer
        meeting.minutes_of_the_meeting_agenda = agenda
        meeting.minutes_of_the_meeting_notes = notes
        meeting.minutes_of_the_meeting_adjourned = adjourned
        meeting.minutes_of_the_meeting_approved_by = approved_by
        meeting.minutes_of_the_meeting_prepared_by = prepared_by
        meeting.minutes_of_the_meeting_noted_by = noted_by

        db.session.commit()

        # Update attendees in the minutes_of_the_meeting_attendees table
        MinutesOfTheMeetingAttendees.query.filter_by(minutes_of_the_meeting_id=meeting_id).delete()
        for attendee_id in attendees:
            new_attendee = MinutesOfTheMeetingAttendees(
                minutes_of_the_meeting_id=meeting_id,
                users_id=attendee_id
            )
            db.session.add(new_attendee)
        db.session.commit()

        # Handle multiple file uploads to Cloudinary
        if photo_documentations:
            # Delete existing photo documentation records and photos from Cloudinary
            existing_photos = MinutesOfTheMeetingPhotoDocumentation.query.filter_by(minutes_of_the_meeting_id=meeting_id).all()
            for photo in existing_photos:
                cloudinary.uploader.destroy(photo.minutes_of_the_meeting_photo_documentation_cloudinary_public_id)
                db.session.delete(photo)
            db.session.commit()

            # Upload new photos to Cloudinary
            for photo_documentation in photo_documentations:
                if photo_documentation:
                    upload_result = cloudinary.uploader.upload(photo_documentation)
                    photo_url = upload_result.get('secure_url')
                    photo_public_id = upload_result.get('public_id')

                    # Create a new photo documentation record
                    new_photo_documentation = MinutesOfTheMeetingPhotoDocumentation(
                        minutes_of_the_meeting_id=meeting.minutes_of_the_meeting_id,
                        minutes_of_the_meeting_photo_documentation_cloudinary_url=photo_url,
                        minutes_of_the_meeting_photo_documentation_cloudinary_public_id=photo_public_id
                    )

                    # Add the new photo documentation to the database
                    db.session.add(new_photo_documentation)
                    db.session.commit()

        flash('Minutes of the meeting updated successfully!', 'success')
        return redirect(url_for('minutes_of_the_meeting_overview'))

    # Query for distinct academic years
    academic_years = db.session.query(MinutesOfTheMeeting.minutes_of_the_meeting_academic_year).distinct().all()
    academic_years = [year[0] for year in academic_years]

    # Query for existing photo documentations
    photo_documentations = MinutesOfTheMeetingPhotoDocumentation.query.filter_by(minutes_of_the_meeting_id=meeting_id).all()

    # Query for users to populate the approved by and prepared by fields
    users = Users.query.all()

    # Query for signatories to populate the presiding officer and noted by fields
    signatories = Signatories.query.all()

    # Query for existing attendees
    meeting_attendees = [attendee.users_id for attendee in MinutesOfTheMeetingAttendees.query.filter_by(minutes_of_the_meeting_id=meeting_id).all()]

    # Query for student organizations and their members
    student_organizations = StudentOrganizations.query.all()

    return render_template('update-minutes-of-the-meeting.html', meeting=meeting, academic_years=academic_years, photo_documentations=photo_documentations, users=users, signatories=signatories, meeting_attendees=meeting_attendees, student_organizations=student_organizations)

@app.route("/update-minutes-of-the-meeting-status/<int:meeting_id>", methods=["POST"])
@login_required
def update_minutes_of_the_meeting_status(meeting_id):
    data = request.get_json()
    new_status = data.get('status')

    # Find the minutes of the meeting by ID
    meeting = MinutesOfTheMeeting.query.get_or_404(meeting_id)

    # Update the minutes of the meeting status
    meeting.minutes_of_the_meeting_status = new_status
    db.session.commit()

    return jsonify(success=True)

@app.route('/delete-minutes-of-the-meeting/<int:meeting_id>', methods=['GET', 'POST'])
@login_required
def delete_minutes_of_the_meeting(meeting_id):
    meeting = MinutesOfTheMeeting.query.get_or_404(meeting_id)

    if request.method == 'POST':
        # First, delete related attendees records (many-to-many relation)
        attendees = MinutesOfTheMeetingAttendees.query.filter_by(minutes_of_the_meeting_id=meeting_id).all()
        for attendee in attendees:
            db.session.delete(attendee)

        # Delete related photo documentation records
        photo_documentations = MinutesOfTheMeetingPhotoDocumentation.query.filter_by(minutes_of_the_meeting_id=meeting_id).all()
        for photo_documentation in photo_documentations:
            # Delete the photo from Cloudinary
            cloudinary.uploader.destroy(photo_documentation.minutes_of_the_meeting_photo_documentation_cloudinary_public_id)
            db.session.delete(photo_documentation)

        # Finally, delete the meeting
        db.session.delete(meeting)
        db.session.commit()

        flash('Minutes of the meeting deleted successfully!', 'success')
        return redirect(url_for('minutes_of_the_meeting_overview'))

    return render_template('delete-minutes-of-the-meeting.html', meeting=meeting)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)