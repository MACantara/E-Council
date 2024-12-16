import os
import re
import requests
from flask import Flask, render_template, request, flash, redirect, url_for, session, jsonify, send_file, make_response
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

from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageTemplate, Frame, HRFlowable, Flowable, PageBreak
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch

import cloudinary
import cloudinary.uploader
import cloudinary.api
from cloudinary.exceptions import Error as CloudinaryError
from cloudinary.utils import cloudinary_url

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import tempfile

import pandas as pd

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

# Gemini AI Configuration
genai.configure(api_key=os.getenv("GOOGLE_GEMINI_AI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')
model_gemini_flash = genai.GenerativeModel('gemini-1.5-flash')

safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

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

class CustomUnderline(Flowable):
    def __init__(self, width, thickness, y_offset=0, gap=2):
        Flowable.__init__(self)
        self.width = width
        self.thickness = thickness
        self.y_offset = y_offset  # Add vertical offset parameter
        self.gap = gap
        
    def draw(self):
        # Draw a shorter line (30% of the cell width)
        shortened_width = self.width * 0.3
        start_x = (self.width - shortened_width) / 2  # Center the line
        self.canv.setLineWidth(self.thickness)
        self.canv.line(start_x, self.y_offset, start_x + shortened_width, self.y_offset)

# Database models
class Users(db.Model, UserMixin):
    __tablename__ = "users"

    users_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    users_profile_picture_cloudinary_url = db.Column(db.String(255), nullable=True)
    users_profile_picture_cloudinary_public_id = db.Column(db.String(255), nullable=True)
    users_title = db.Column(db.String(50), nullable=True)
    users_first_name = db.Column(db.String(50), nullable=False)
    users_middle_name = db.Column(db.String(50), nullable=True)
    users_last_name = db.Column(db.String(50), nullable=False)
    users_suffix = db.Column(db.String(50), nullable=True)
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
    users_signature_cloudinary_url = db.Column(db.String(255), nullable=True)
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
        return f"Users({self.users_id}, {self.users_profile_picture_cloudinary_url}, {self.users_first_name}, {self.users_last_name}, {self.users_username}, {self.users_email}, {self.users_departments_id}, {self.users_role}, {self.users_student_organization}, {self.users_student_organization_position}, {self.users_password}, {self.users_email_verified}, {self.users_home_address}, {self.users_contact_number}, {self.users_signature})"

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

    # Relationship to the Documentation model
    documentation = db.relationship('Documentation', back_populates='events')

    # Relationship to the FinancialReports model
    financial_reports = db.relationship('FinancialReports', back_populates='events')

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
    transaction_events_id = db.Column(db.Integer, db.ForeignKey('events.events_id'), index=True, nullable=True)
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
    board_resolutions_departments_id = db.Column(db.Integer, db.ForeignKey('departments.departments_id'), nullable=True)
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
    department = db.relationship('Departments', foreign_keys=[board_resolutions_departments_id])

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
    minutes_of_the_meeting_departments_id = db.Column(db.Integer, db.ForeignKey('departments.departments_id'), nullable=True)
    minutes_of_the_meeting_presiding_officer = db.Column(db.String(100), nullable=False)
    minutes_of_the_meeting_agenda = db.Column(db.Text, nullable=False)
    minutes_of_the_meeting_notes = db.Column(db.Text, nullable=True)
    minutes_of_the_meeting_adjourned = db.Column(db.DateTime, nullable=True)
    minutes_of_the_meeting_approved_by = db.Column(db.Integer, db.ForeignKey('users.users_id'), nullable=True)
    minutes_of_the_meeting_prepared_by = db.Column(db.Integer, db.ForeignKey('users.users_id'), nullable=True)
    minutes_of_the_meeting_noted_by = db.Column(db.Integer, db.ForeignKey('signatories.signatory_id'), nullable=True)

    # Relationships
    approved_by_user = db.relationship('Users', foreign_keys=[minutes_of_the_meeting_approved_by])
    prepared_by_user = db.relationship('Users', foreign_keys=[minutes_of_the_meeting_prepared_by])
    noted_by_signatory = db.relationship('Signatories', foreign_keys=[minutes_of_the_meeting_noted_by])
    department = db.relationship('Departments', foreign_keys=[minutes_of_the_meeting_departments_id])

    def __repr__(self):
        return f'<MinutesOfTheMeeting {self.minutes_of_the_meeting_id}: {self.minutes_of_the_meeting_agenda}>'

class Signatories(db.Model):
    __tablename__ = 'signatories'

    signatory_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    signatory_title = db.Column(db.String(50), nullable=False)
    signatory_first_name = db.Column(db.String(50), nullable=False)
    signatory_middle_name = db.Column(db.String(50), nullable=True)
    signatory_last_name = db.Column(db.String(50), nullable=False)
    signatory_suffix = db.Column(db.String(50), nullable=True)
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
    financial_reports_status = db.Column(db.String(50), nullable=False)
    financial_reports_events_id = db.Column(db.Integer, db.ForeignKey('events.events_id'), nullable=True)
    financial_reports_departments_id = db.Column(db.Integer, db.ForeignKey('departments.departments_id'), nullable=True)
    financial_reports_title = db.Column(db.String(255), nullable=False)
    financial_reports_audited_and_prepared_by = db.Column(db.Integer, db.ForeignKey('users.users_id'), nullable=True)
    financial_reports_noted_by = db.Column(db.Integer, db.ForeignKey('signatories.signatory_id'), nullable=True)
    financial_reports_recommending_approval_by = db.Column(db.Integer, db.ForeignKey('signatories.signatory_id'), nullable=True)
    financial_reports_approved_by = db.Column(db.Integer, db.ForeignKey('signatories.signatory_id'), nullable=True)

    # Relationships
    events = db.relationship('Events', back_populates='financial_reports')
    prepared_by_user = db.relationship('Users', foreign_keys=[financial_reports_audited_and_prepared_by])
    noted_by_signatory = db.relationship('Signatories', foreign_keys=[financial_reports_noted_by])
    recommending_signatory = db.relationship('Signatories', foreign_keys=[financial_reports_recommending_approval_by])
    approved_by_signatory = db.relationship('Signatories', foreign_keys=[financial_reports_approved_by])
    department = db.relationship('Departments', foreign_keys=[financial_reports_departments_id])

    def __repr__(self):
        return f'<FinancialReports {self.financial_reports_id}: {self.financial_reports_title}>'

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

    # Relationships
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

class ActivityStrengths(db.Model):
    __tablename__ = 'activity_strengths'

    activity_strengths_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    activity_strengths_documentation_id = db.Column(db.Integer, db.ForeignKey('documentation.documentation_id'), nullable=False)
    activity_strengths_content = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<ActivityStrengths {self.activity_strengths_id}: {self.activity_strengths_content}>'

class ActivityWeaknesses(db.Model):
    __tablename__ = 'activity_weaknesses'

    activity_weaknesses_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    activity_weaknesses_documentation_id = db.Column(db.Integer, db.ForeignKey('documentation.documentation_id'), nullable=False)
    activity_weaknesses_content = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<ActivityWeaknesses {self.activity_weaknesses_id}: {self.activity_weaknesses_content}>'

class ActivityRecommendations(db.Model):
    __tablename__ = 'activity_recommendations'

    activity_recommendations_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    activity_recommendations_documentation_id = db.Column(db.Integer, db.ForeignKey('documentation.documentation_id'), nullable=False)
    activity_recommendations_content = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<ActivityRecommendations {self.activity_recommendations_id}: {self.activity_recommendations_content}>'

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
    observations_learning_journal_forms_id = db.Column(db.Integer, db.ForeignKey('learning_journal_forms.learning_journal_forms_id'), nullable=False)
    observations_content = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Observations {self.observations_id}: {self.observations_content}>'

class Learnings(db.Model):
    __tablename__ = 'learnings'

    learnings_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    learnings_learning_journal_forms_id = db.Column(db.Integer, db.ForeignKey('learning_journal_forms.learning_journal_forms_id'), nullable=False)
    learnings_content = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Learnings {self.learnings_id}: {self.learnings_content}>'

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
    documentation_departments_id = db.Column(db.Integer, db.ForeignKey('departments.departments_id'), nullable=True)
    documentation_type = db.Column(db.String(50), nullable=True)
    documentation_activity_report_forms_id = db.Column(db.Integer, db.ForeignKey('activity_report_forms.activity_report_forms_id'), nullable=True)
    documentation_prepared_by = db.Column(db.Integer, db.ForeignKey('users.users_id'), nullable=True)
    documentation_learning_journal_forms_id = db.Column(db.Integer, db.ForeignKey('learning_journal_forms.learning_journal_forms_id'), nullable=True)
    documentation_checked_by = db.Column(db.Integer, db.ForeignKey('signatories.signatory_id'), nullable=True)
    documentation_noted_by = db.Column(db.Integer, db.ForeignKey('signatories.signatory_id'), nullable=True)
    documentation_date_of_submission = db.Column(db.DateTime, nullable=True)
    documentation_rating = db.Column(db.Float, nullable=True)
    documentation_comments_suggestions = db.Column(db.Text, nullable=True)

    # Relationships
    events = db.relationship('Events', foreign_keys=[documentation_events_id])
    prepared_by_user = db.relationship('Users', foreign_keys=[documentation_prepared_by])
    checked_by_signatory = db.relationship('Signatories', foreign_keys=[documentation_checked_by])
    noted_by_signatory = db.relationship('Signatories', foreign_keys=[documentation_noted_by])
    department = db.relationship('Departments', foreign_keys=[documentation_departments_id])

    def __repr__(self):
        return f'<Documentation {self.documentation_id}: {self.documentation_type}>'

class TallyItems(db.Model):
    __tablename__ = 'tally_items'

    tally_items_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tally_items_documentation_id = db.Column(db.Integer, db.ForeignKey('documentation.documentation_id'), nullable=True)
    tally_items_name = db.Column(db.String(255), nullable=True)
    tally_items_extremely_satisfied_rating_total = db.Column(db.Integer, nullable=True)
    tally_items_satisfied_rating_total = db.Column(db.Integer, nullable=True)
    tally_items_neutral_rating_total = db.Column(db.Integer, nullable=True)
    tally_items_dissatisfied_rating_total = db.Column(db.Integer, nullable=True)
    tally_items_extremely_dissatisfied_rating_total = db.Column(db.Integer, nullable=True)
    
    documentation = db.relationship('Documentation', backref='tally_items', lazy=True)

    def __repr__(self):
        return f'<TallyItems {self.tally_items_id}>'

class ResultsOfTheEvaluationImages(db.Model):
    __tablename__ = 'results_of_the_evaluation_images'

    results_of_the_evaluation_images_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    results_of_the_evaluation_images_documentation_id = db.Column(db.Integer, db.ForeignKey('documentation.documentation_id'), nullable=True)
    results_of_the_evaluation_images_cloudinary_url = db.Column(db.String(255), nullable=True)
    results_of_the_evaluation_images_cloudinary_public_id = db.Column(db.String(255), nullable=True)
    

    documentation = db.relationship('Documentation', backref='results_of_the_evaluation_images', lazy=True)

    def __repr__(self):
        return f'<ResultsOfTheEvaluationImages {self.results_of_the_evaluation_images_id}>'

class EvaluationForm(db.Model):
    evaluation_form_id = db.Column(db.Integer, primary_key=True)
    evaluation_form_documentation_id = db.Column(db.Integer, db.ForeignKey('documentation.documentation_id', ondelete='CASCADE'))
    evaluation_form_name = db.Column(db.String(255))
    evaluation_form_extremely_satisfied_rating = db.Column(db.Integer, default=0)
    evaluation_form_satisfied_rating = db.Column(db.Integer, default=0)
    evaluation_form_neutral_rating = db.Column(db.Integer, default=0)
    evaluation_form_dissatisfied_rating = db.Column(db.Integer, default=0)
    evaluation_form_extremely_dissatisfied_rating = db.Column(db.Integer, default=0)

    # Relationship
    documentation = db.relationship('Documentation', backref=db.backref('evaluation_forms', lazy=True))

    def to_dict(self):
        return {
            'evaluation_form_id': self.evaluation_form_id,
            'evaluation_form_documentation_id': self.evaluation_form_documentation_id,
            'evaluation_form_name': self.evaluation_form_name,
            'evaluation_form_extremely_satisfied_rating': self.evaluation_form_extremely_satisfied_rating,
            'evaluation_form_satisfied_rating': self.evaluation_form_satisfied_rating,
            'evaluation_form_neutral_rating': self.evaluation_form_neutral_rating,
            'evaluation_form_dissatisfied_rating': self.evaluation_form_dissatisfied_rating,
            'evaluation_form_extremely_dissatisfied_rating': self.evaluation_form_extremely_dissatisfied_rating
        }

class SummaryOfAttendanceImages(db.Model):
    __tablename__ = 'summary_of_attendance_images'

    summary_of_attendance_images_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    summary_of_attendance_images_documentation_id = db.Column(db.Integer, db.ForeignKey('documentation.documentation_id'), nullable=True)
    summary_of_attendance_images_cloudinary_url = db.Column(db.String(255), nullable=True)
    summary_of_attendance_images_cloudinary_public_id = db.Column(db.String(255), nullable=True)
    
    documentation = db.relationship('Documentation', backref='summary_of_attendance_images', lazy=True)

    def __repr__(self):
        return f'<SummaryOfAttendanceImages {self.summary_of_attendance_images_id}>'

class EvaluationListOfStudentNames(db.Model):
    __tablename__ = 'evaluation_list_of_student_names'

    evaluation_list_of_student_names_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    evaluation_list_of_student_names_documentation_id = db.Column(
        db.Integer, 
        db.ForeignKey('documentation.documentation_id', ondelete='CASCADE'),
        nullable=True
    )
    evaluation_list_of_student_names_student = db.Column(db.String(255), nullable=True)
    
    documentation = db.relationship(
        'Documentation',
        backref=db.backref('evaluation_list_of_student_names', passive_deletes=True),
        lazy=True
    )

    def __repr__(self):
        return f'<EvaluationListOfStudentNames {self.evaluation_list_of_student_names_id}>'

class EventPhotoDocumentationImages(db.Model):
    __tablename__ = 'event_photo_documentation_images'

    event_photo_documentation_images_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_photo_documentation_images_documentation_id = db.Column(db.Integer, db.ForeignKey('documentation.documentation_id'), nullable=True)
    event_photo_documentation_images_cloudinary_url = db.Column(db.String(255), nullable=True)
    event_photo_documentation_images_cloudinary_public_id = db.Column(db.String(255), nullable=True)
    
    documentation = db.relationship('Documentation', backref='event_photo_documentation_images', lazy=True)

    def __repr__(self):
        return f'<EventPhotoDocumentationImages {self.event_photo_documentation_images_id}>'

# Custom Jinja2 Filters
@app.template_filter('truncate')
def truncate_text(text, length=100, suffix='...'):
    if text is None:
        return ''
    if len(text) > length:
        return text[:length].rsplit(' ', 1)[0] + suffix
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
    return any(doc[0].documentation_semester == semester and doc[0].documentation_academic_year == academic_year for doc in documentations)

# Error handlers
@app.errorhandler(CloudinaryError)
def handle_cloudinary_error(error):
    app.logger.error(f"Cloudinary error: {str(error)}")
    flash("An error occurred while processing images.", "error")
    return redirect(url_for('documentation_overview'))

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

def allowed_image_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_tally_items(documentation_id, tally_names, extremely_satisfied, satisfied, neutral, dissatisfied, extremely_dissatisfied):
    # First, delete all existing tally items
    TallyItems.query.filter_by(tally_items_documentation_id=documentation_id).delete()
    
    # Process new tally items
    for i in range(len(tally_names)):
        if tally_names[i].strip():  # Only process if name is not empty
            tally_name = tally_names[i].strip()
            
            # Get the rating counts for tally
            es_count = int(extremely_satisfied[i] or 0)
            s_count = int(satisfied[i] or 0)
            n_count = int(neutral[i] or 0)
            d_count = int(dissatisfied[i] or 0)
            ed_count = int(extremely_dissatisfied[i] or 0)
            
            # Create new tally item
            new_tally = TallyItems(
                tally_items_documentation_id=documentation_id,
                tally_items_name=tally_name,
                tally_items_extremely_satisfied_rating_total=es_count,
                tally_items_satisfied_rating_total=s_count,
                tally_items_neutral_rating_total=n_count,
                tally_items_dissatisfied_rating_total=d_count,
                tally_items_extremely_dissatisfied_rating_total=ed_count
            )
            db.session.add(new_tally)

def process_evaluation_forms(documentation_id, tally_names, request):
    # First, delete all existing evaluation forms
    EvaluationForm.query.filter_by(evaluation_form_documentation_id=documentation_id).delete()
    
    # Process new evaluation forms
    for i in range(len(tally_names)):
        if tally_names[i].strip():  # Only process if name is not empty
            tally_name = tally_names[i].strip()
            
            # Get the evaluation rating for this item
            eval_rating_key = f'eval-tally-{i}'
            rating_value = request.form.get(eval_rating_key)
            
            # Convert radio button value to rating counts
            eval_es_count = 1 if rating_value == '5' else 0
            eval_s_count = 1 if rating_value == '4' else 0
            eval_n_count = 1 if rating_value == '3' else 0
            eval_d_count = 1 if rating_value == '2' else 0
            eval_ed_count = 1 if rating_value == '1' else 0
            
            # Create new evaluation form entry
            new_evaluation = EvaluationForm(
                evaluation_form_documentation_id=documentation_id,
                evaluation_form_name=tally_name,
                evaluation_form_extremely_satisfied_rating=eval_es_count,
                evaluation_form_satisfied_rating=eval_s_count,
                evaluation_form_neutral_rating=eval_n_count,
                evaluation_form_dissatisfied_rating=eval_d_count,
                evaluation_form_extremely_dissatisfied_rating=eval_ed_count
            )
            db.session.add(new_evaluation)

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
        if (current_user.users_profile_picture_cloudinary_url):
            public_id = current_user.users_profile_picture_cloudinary_public_id
            if (public_id):
                cloudinary.uploader.destroy(public_id)

        # Upload the new profile picture to Cloudinary
        upload_result = cloudinary.uploader.upload(profile_picture)
        profile_picture_url = upload_result["secure_url"]
        profile_picture_public_id = upload_result["public_id"]

        # Update the user's profile picture URL and public ID
        current_user.users_profile_picture_cloudinary_url = profile_picture_url
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
    if current_user.users_profile_picture_cloudinary_url:
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
        transactions = TransactionHistory.query.filter_by(transaction_events_id=event.events_id).all()
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
    transactions = TransactionHistory.query.filter_by(transaction_events_id=event_id).order_by(TransactionHistory.transaction_date.desc()).all()

    # Query top 5 income transactions grouped by category
    top5_income = db.session.query(
        TransactionHistory.transaction_category,
        db.func.sum(TransactionHistory.transaction_total).label('transaction_total')
    ).filter_by(transaction_events_id=event_id, transaction_type='Income').group_by(TransactionHistory.transaction_category).order_by(db.func.sum(TransactionHistory.transaction_total).desc()).limit(5).all()

    # Query top 5 expense transactions grouped by category
    top5_expense = db.session.query(
        TransactionHistory.transaction_category,
        db.func.sum(TransactionHistory.transaction_total).label('transaction_total')
    ).filter_by(transaction_events_id=event_id, transaction_type='Expense').group_by(TransactionHistory.transaction_category).order_by(db.func.sum(TransactionHistory.transaction_total).desc()).limit(5).all()

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

    # Safely convert the event budget to a float if possible
    try:
        events_budget = float(event.events_budget or 0)
    except (ValueError, TypeError):
        events_budget = event.events_budget  # Keep it as a string or handle it as needed

    # Calculate remaining budget
    if isinstance(events_budget, float):
        remaining_budget = total_income - total_expense + events_budget
    else:
        remaining_budget = f"Budget: {events_budget}"  # Return as string if not a float

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
            transaction_events_id=event_id,
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
        concept_paper_date_of_submission = request.form.get('concept-paper-date-of-submission')
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
        concept_paper_date_of_submission = datetime.strptime(concept_paper_date_of_submission, '%Y-%m-%dT%H:%M')
        concept_paper_event_start_date_and_time = datetime.strptime(concept_paper_event_start_date_and_time, '%Y-%m-%dT%H:%M')
        concept_paper_event_end_date_and_time = datetime.strptime(concept_paper_event_end_date_and_time, '%Y-%m-%dT%H:%M')

        # Excuse Letter Form data
        excuse_letter_department_office_unit = request.form.get('excuse-letter-department-office-unit')
        excuse_letter_faculty_in_charge = request.form.get('excuse-letter-faculty-in-charge')
        excuse_letter_dean = request.form.get('excuse-letter-dean')
        excuse_letter_noted_by = request.form.get('excuse-letter-noted-by')

        # Create a new concept paper
        new_concept_paper = ConceptPaperForms(
            concept_paper_forms_date=concept_paper_date_of_submission,
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
                objectives_of_the_activity_concept_paper_forms_id=new_concept_paper.concept_paper_forms_id,
                objectives_of_the_activity_content=objective_content,
            )
            db.session.add(new_objective)
            db.session.commit()

        # Add learning outcomes to the learning_outcomes table
        for outcome_content in concept_paper_learning_outcomes:
            new_outcome = LearningOutcomes(
                learning_outcomes_concept_paper_forms_id=new_concept_paper.concept_paper_forms_id,
                learning_outcomes_content=outcome_content
            )
            db.session.add(new_outcome)
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
            excuse_letter_forms_personnel_in_charge_forms_id=excuse_letter_faculty_in_charge,
            excuse_letter_forms_dean=excuse_letter_dean,
            excuse_letter_forms_noted_by=excuse_letter_noted_by
        )
        db.session.add(new_excuse_letter_form)
        db.session.commit()

        # Activity Report Form data
        activity_report_nature_of_the_activity = request.form.get('activity-report-nature-of-the-activity')
        activity_report_date_submission = request.form.get('activity-report-date-submission')
        activity_report_contact_numbers = request.form.get('activity-report-contact-numbers')
        activity_report_prepared_by = request.form.get('activity-report-prepared-by')
        activity_report_noted_by = request.form.get('activity-report-noted-by')

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
                    activity_report_forms_nature_of_the_activity=activity_report_nature_of_the_activity,
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
        # First, delete existing objectives
        ObjectivesOfTheActivity.query.filter_by(
            objectives_of_the_activity_concept_paper_forms_id=concept_paper.concept_paper_forms_id
        ).delete()

        # Then add new objectives
        for objective in concept_paper_objectives:
            new_objective = ObjectivesOfTheActivity(
                objectives_of_the_activity_concept_paper_forms_id=concept_paper.concept_paper_forms_id,
                objectives_of_the_activity_content=objective
            )
            db.session.add(new_objective)

        # Update learning outcomes
        # First delete existing learning outcomes
        LearningOutcomes.query.filter_by(
            learning_outcomes_concept_paper_forms_id=concept_paper.concept_paper_forms_id
        ).delete()

        # Then add new learning outcomes
        for outcome in concept_paper_learning_outcomes:
            new_outcome = LearningOutcomes(
                learning_outcomes_concept_paper_forms_id=concept_paper.concept_paper_forms_id,
                learning_outcomes_content=outcome
            )
            db.session.add(new_outcome)

        # Update observations in the observations table
        Observations.query.filter_by(observations_learning_journal_forms_id=learning_journal.learning_journal_forms_id).delete()
        for observation_content in concept_paper_observations:
            observation = Observations(observations_content=observation_content)
            db.session.add(observation)
            db.session.commit()
            learning_journal_observation = Observations(
                observations_learning_journal_forms_id=learning_journal.learning_journal_forms_id,
                observations_id=observation.observations_id
            )
            db.session.add(learning_journal_observation)
            db.session.commit()

        # Update learnings in the learnings table
        Learnings.query.filter_by(learnings_learning_journal_forms_id=learning_journal.learning_journal_forms_id).delete()
        for learning_content in concept_paper_learnings:
            learning = Learnings(learnings_content=learning_content)
            db.session.add(learning)
            db.session.commit()
            learning_journal_learning = Learnings(
                learnings_learning_journal_forms_id=learning_journal.learning_journal_forms_id,
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
            ActivityStrengths.query.filter_by(
                activity_strengths_documentation_id=activity_report.activity_report_forms_id
            ).delete()

            for strength in activity_strengths:
                new_strength = ActivityStrengths(
                    activity_strengths_documentation_id=activity_report.activity_report_forms_id,
                    activity_strengths_content=strength
                )
                db.session.add(new_strength)

            # Update weaknesses
            ActivityWeaknesses.query.filter_by(
                activity_weaknesses_documentation_id=activity_report.activity_report_forms_id
            ).delete()

            for weakness in activity_weaknesses:
                new_weakness = ActivityWeaknesses(
                    activity_weaknesses_documentation_id=activity_report.activity_report_forms_id,
                    activity_weaknesses_content=weakness
                )
                db.session.add(new_weakness)

            # Update recommendations
            ActivityRecommendations.query.filter_by(
                activity_recommendations_documentation_id=activity_report.activity_report_forms_id
            ).delete()

            for recommendation in activity_recommendations:
                new_recommendation = ActivityRecommendations(
                    activity_recommendations_documentation_id=activity_report.activity_report_forms_id,
                    activity_recommendations_content=recommendation
                )
                db.session.add(new_recommendation)

            # Single commit at the end for better performance
            db.session.commit()

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
        obj.objectives_of_the_activity_content
        for obj in ObjectivesOfTheActivity.query.filter_by(objectives_of_the_activity_concept_paper_forms_id=paper_id).all()
    ]
    learning_outcomes = [
        outcome.learning_outcomes_content
        for outcome in LearningOutcomes.query.filter_by(learning_outcomes_concept_paper_forms_id=paper_id).all()
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
        LearningOutcomes.query.filter_by(learning_outcomes_concept_paper_forms_id=paper_id).delete()
        
        # Delete associated objectives of the activity
        ObjectivesOfTheActivity.query.filter_by(objectives_of_the_activity_concept_paper_forms_id=paper_id).delete()
        
        # Delete the concept paper
        db.session.delete(concept_paper)
        db.session.commit()

        flash('Concept paper deleted successfully!', 'success')
        return redirect(url_for('concept_papers_overview'))

    return render_template('delete-concept-paper.html', concept_paper=concept_paper)

@app.route('/generate-concept-body', methods=['POST'])
@login_required
def generate_concept_body():
    if not request.is_json:
        return make_response(jsonify({'error': 'Content-Type must be application/json'}), 400)
        
    try:
        data = request.json
        subject = data.get('subject')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        location = data.get('location')
        
        if not all([subject, start_date, end_date, location]):
            return make_response(jsonify({'error': 'Missing required fields'}), 400)
        
        # Format dates
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')
            formatted_start = start_date_obj.strftime('%B %d, %Y at %I:%M %p')
            formatted_end = end_date_obj.strftime('%B %d, %Y at %I:%M %p')
        except ValueError as e:
            return make_response(jsonify({'error': 'Invalid date format'}), 400)
        
        prompt = f"""Generate a formal body text for a concept paper with the following details:
        Event: {subject}
        Date and Time: From {formatted_start} to {formatted_end}
        Location: {location}
        
        Requirements:
        1. Use formal and professional language
        2. Explain the purpose and significance of the event
        3. Highlight key activities or components
        4. Keep it concise but informative
        5. Include relevant details about timing and location
        6. Make it engaging and well-structured
        7. Avoid any unnecessary jargon
        8. Format as a single cohesive paragraph"""
        
        response = model.generate_content(prompt, safety_settings=safety_settings)
        return make_response(jsonify({'content': response.text.strip()}), 200)
        
    except Exception as e:
        app.logger.error(f"Error generating concept paper body: {str(e)}")
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/generate-concept-descriptions', methods=['POST'])
@login_required
def generate_concept_descriptions():
    if not request.is_json:
        return make_response(jsonify({'error': 'Content-Type must be application/json'}), 400)
        
    try:
        data = request.json
        subject = data.get('subject')
        
        if not subject:
            return make_response(jsonify({'error': 'Missing subject'}), 400)
        
        prompt = f"""Generate a detailed description for a concept paper about {subject}.
        
        Requirements:
        1. Write as a single cohesive paragraph
        2. Provide a comprehensive overview of the event/activity
        3. Include the rationale and importance
        4. Describe the target audience and potential impact
        5. Keep language formal but accessible
        6. Focus on practical and measurable aspects
        7. Do not use any text formatting or special characters
        8. Do not use bullet points or line breaks
        9. Include potential benefits to participants
        10. Keep it concise but informative"""
        
        response = model.generate_content(prompt, safety_settings=safety_settings)
        return make_response(jsonify({'content': response.text.strip()}), 200)
        
    except Exception as e:
        app.logger.error(f"Error generating descriptions: {str(e)}")
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/generate-concept-objectives', methods=['POST'])
@login_required
def generate_concept_objectives():
    if not request.is_json:
        return make_response(jsonify({'error': 'Content-Type must be application/json'}), 400)
        
    try:
        data = request.json
        subject = data.get('subject')
        
        if not subject:
            return make_response(jsonify({'error': 'Missing subject'}), 400)
        
        prompt = f"""Generate specific objectives for {subject}.
        
        Requirements:
        1. Create 3-5 SMART objectives (Specific, Measurable, Achievable, Relevant, Time-bound)
        2. Focus on concrete outcomes
        3. Use action verbs
        4. Make them relevant to the event purpose
        5. Ensure they are realistic and achievable
        6. Format as a bullet-point list
        7. Keep each objective concise
        8. Align with academic/educational goals"""
        
        response = model.generate_content(prompt, safety_settings=safety_settings)
        return make_response(jsonify({'content': response.text.strip()}), 200)
        
    except Exception as e:
        app.logger.error(f"Error generating objectives: {str(e)}")
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/generate-concept-learning-outcomes', methods=['POST'])
@login_required
def generate_concept_learning_outcomes():
    if not request.is_json:
        return make_response(jsonify({'error': 'Content-Type must be application/json'}), 400)
        
    try:
        data = request.json
        subject = data.get('subject')
        
        if not subject:
            return make_response(jsonify({'error': 'Missing subject'}), 400)
        
        prompt = f"""Generate learning outcomes for {subject}.
        
        Requirements:
        1. Create 3-5 specific learning outcomes
        2. Use Bloom's Taxonomy verbs
        3. Focus on knowledge, skills, and attitudes
        4. Make them measurable and observable
        5. Align with event objectives
        6. Keep language clear and specific
        7. Format as a bullet-point list
        8. Consider both immediate and long-term learning"""
        
        response = model.generate_content(prompt, safety_settings=safety_settings)
        return make_response(jsonify({'content': response.text.strip()}), 200)
        
    except Exception as e:
        app.logger.error(f"Error generating learning outcomes: {str(e)}")
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/generate-concept-participants', methods=['POST'])
@login_required
def generate_concept_participants():
    if not request.is_json:
        return make_response(jsonify({'error': 'Content-Type must be application/json'}), 400)
        
    try:
        data = request.json
        subject = data.get('subject')
        
        if not subject:
            return make_response(jsonify({'error': 'Missing subject'}), 400)
        
        prompt = f"""Suggest a reasonable number of expected participants for {subject}.
        
        Requirements:
        1. Consider the type of event
        2. Account for venue capacity
        3. Think about resource management
        4. Ensure meaningful participation
        5. Consider typical attendance patterns
        6. Return only a number between 20 and 200"""
        
        response = model.generate_content(prompt, safety_settings=safety_settings)
        # Extract just the number from the response
        number = ''.join(filter(str.isdigit, response.text))
        return make_response(jsonify({'content': number}), 200)
        
    except Exception as e:
        app.logger.error(f"Error generating participant number: {str(e)}")
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/generate-concept-consent', methods=['POST'])
@login_required
def generate_concept_consent():
    if not request.is_json:
        return make_response(jsonify({'error': 'Content-Type must be application/json'}), 400)
        
    try:
        data = request.json
        subject = data.get('subject')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        location = data.get('location')
        
        if not all([subject, start_date, end_date, location]):
            return make_response(jsonify({'error': 'Missing required fields'}), 400)
        
        # Format dates
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')
            formatted_start = start_date_obj.strftime('%B %d, %Y at %I:%M %p')
            formatted_end = end_date_obj.strftime('%B %d, %Y at %I:%M %p')
        except ValueError as e:
            return make_response(jsonify({'error': 'Invalid date format'}), 400)
        
        prompt = f"""Generate a parent/guardian consent form content for {subject}.
        
        Event Details:
        - Event: {subject}
        - Date and Time: From {formatted_start} to {formatted_end}
        - Location: {location}
        
        Requirements:
        1. Use formal and professional language
        2. Include clear permission statement
        3. Specify event details and purpose
        4. Mention safety measures and supervision
        5. Include contact information section
        6. Add emergency contact section
        7. Include medical information section
        8. Add signature lines for parent/guardian
        9. Keep it concise but comprehensive
        10. Include any relevant waivers or disclaimers"""
        
        response = model.generate_content(prompt, safety_settings=safety_settings)
        return make_response(jsonify({'content': response.text.strip()}), 200)
        
    except Exception as e:
        app.logger.error(f"Error generating consent form: {str(e)}")
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/generate-concept-paper-pdf/<int:concept_paper_id>')
@login_required
def generate_concept_paper_pdf(concept_paper_id):
    buffer = BytesIO()
    
    def header(canvas, doc):
        canvas.saveState()
        
        # Add header images with manual positioning
        # PERPS header - left side
        header_perps = Image('./static/img/HEADER-PERPS.png', width=325, height=75)
        perps_x = doc.leftMargin - 35
        header_perps.drawOn(canvas, perps_x, doc.height + doc.topMargin)
        
        # CCS Logo - center
        header_ccs = Image('./static/img/CCS-LOGO.png', width=35, height=50)
        ccs_x = doc.leftMargin + (doc.width - 35)/2 + 125
        header_ccs.drawOn(canvas, ccs_x, doc.height + doc.topMargin + 15)
        
        # ISO Logo - right side
        header_iso = Image('./static/img/ISO.png', width=100, height=50)
        iso_x = doc.leftMargin + doc.width - 80
        header_iso.drawOn(canvas, iso_x, doc.height + doc.topMargin + 15)
        
        # Add text below ISO logo
        canvas.setFont("Helvetica-Bold", 10)
        text = "College of Computer Studies"
        text_width = canvas.stringWidth(text, "Helvetica-Bold", 10)
        text_x = iso_x + (50 - text_width)/2
        canvas.drawString(text_x, doc.height + doc.topMargin, text)
        
        # Add red line after text
        canvas.setStrokeColorRGB(0x8c/255, 0x04/255, 0x04/255)  # #8c0404
        canvas.setLineWidth(2)
        line_y = doc.height + doc.topMargin - 10
        line_length = 510
        line_start_x = (doc.width - line_length) / 2 + doc.leftMargin
        line_end_x = line_start_x + line_length
        canvas.line(line_start_x - 5, line_y, line_end_x, line_y)
        
        # Add footer
        canvas.setStrokeColorRGB(0, 0, 0)
        canvas.setLineWidth(1)
        footer_y = doc.bottomMargin - 20
        canvas.line(doc.leftMargin, footer_y, doc.leftMargin + doc.width, footer_y)
        
        # Add footer text
        canvas.setFont("Helvetica", 12)
        canvas.drawString(doc.leftMargin, footer_y - 15, "UPHMO-CCS-GEN-912/rev0")
        right_text = "Concept Paper"
        right_text_width = canvas.stringWidth(right_text, "Helvetica", 12)
        canvas.drawString(doc.leftMargin + doc.width - right_text_width, footer_y - 15, right_text)
        
        canvas.restoreState()

    # Define Folio size (8.5 x 13 inches)
    FOLIO = (8.5 * inch, 13 * inch)

    doc = SimpleDocTemplate(
        buffer,
        pagesize=FOLIO,  # Use custom FOLIO size
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    story = []
    doc.build(story, onFirstPage=header, onLaterPages=header)
    
    buffer.seek(0)
    return send_file(
        buffer,
        download_name=f'Concept_Paper_{concept_paper_id}.pdf',
        mimetype='application/pdf'
    )

@app.route("/documentation-overview")
@login_required
def documentation_overview():
    # Query for all documentation with concept paper subject, ordered by academic year (desc) and semester
    documentations = db.session.query(
        Documentation,
        ConceptPaperForms.concept_paper_forms_subject
    ).outerjoin(
        ActivityReportForms,
        Documentation.documentation_activity_report_forms_id == ActivityReportForms.activity_report_forms_id
    ).outerjoin(
        LearningJournalForms,
        Documentation.documentation_learning_journal_forms_id == LearningJournalForms.learning_journal_forms_id
    ).outerjoin(
        ConceptPaperForms,
        db.or_(
            ActivityReportForms.activity_report_forms_concept_paper_forms_id == ConceptPaperForms.concept_paper_forms_id,
            LearningJournalForms.learning_journal_forms_concept_paper_forms_id == ConceptPaperForms.concept_paper_forms_id
        )
    ).order_by(
        Documentation.documentation_academic_year.desc(),
        Documentation.documentation_semester.desc()
    ).all()

    return render_template("documentation-overview.html", 
                         documentations=documentations, 
                         sort_by_date='recent-to-old')

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
        documentation_noted_by = request.form.get('documentation-noted-by')
        documentation_date_of_submission = request.form.get('documentation-date-of-submission')
        documentation_checked_by = request.form.get('learning-journal-forms-checked-by')
        documentation_rating = request.form.get('documentation-rating')
        documentation_comments_suggestions = request.form.get('documentation-comments-suggestions')

        # Retrieve activity strengths, weaknesses, and recommendations
        activity_strengths = request.form.getlist('activity-strengths')
        activity_weaknesses = request.form.getlist('activity-weaknesses')
        activity_recommendations = request.form.getlist('activity-recommendations')

        # Get Learning Journal Form fields
        learning_journal_forms_name_of_student = request.form.get('learning-journal-forms-name-of-student')
        learning_journal_forms_course_year_level = request.form.get('learning-journal-forms-course-year-level')
        learning_journal_forms_id_number = request.form.get('learning-journal-forms-id-number')
        learning_journal_forms_overall_reflection = request.form.get('learning-journal-forms-overall-reflection')
        learning_journal_forms_prepared_by = request.form.get('learning-journal-forms-prepared-by')
        learning_journal_forms_seen_and_read_by = request.form.get('learning-journal-forms-seen-and-read-by')

        # Retrieve event details using documentation_events_id
        event = Events.query.get(documentation_events_id)
        if event:
            documentation_academic_year = event.events_academic_year
            documentation_semester = event.events_semester
            concept_paper_id = event.events_concept_paper_forms_id

            # Get the learning journal form linked to the concept paper
            concept_paper_learning_journal = LearningJournalForms.query.filter_by(
                learning_journal_forms_concept_paper_forms_id=concept_paper_id
            ).first()

        # Convert date fields to datetime objects
        documentation_date_of_submission = datetime.strptime(documentation_date_of_submission, '%Y-%m-%d')

        # Update learning journal form details if it exists
        if concept_paper_learning_journal and learning_journal_forms_name_of_student and learning_journal_forms_course_year_level:
            concept_paper_learning_journal.learning_journal_forms_name_of_student = learning_journal_forms_name_of_student
            concept_paper_learning_journal.learning_journal_forms_course_year_level = learning_journal_forms_course_year_level
            concept_paper_learning_journal.learning_journal_forms_id_number = learning_journal_forms_id_number
            concept_paper_learning_journal.learning_journal_forms_overall_reflection = learning_journal_forms_overall_reflection
            concept_paper_learning_journal.learning_journal_forms_prepared_by = learning_journal_forms_prepared_by
            concept_paper_learning_journal.learning_journal_forms_seen_and_read_by = learning_journal_forms_seen_and_read_by
            learning_journal_forms_id = concept_paper_learning_journal.learning_journal_forms_id

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
        documentation_id = new_documentation.documentation_id  # Get the documentation ID

        # Add activity strengths
        for strength_content in activity_strengths:
            if strength_content:
                strength = ActivityStrengths(
                    activity_strengths_documentation_id=documentation_id,
                    activity_strengths_content=strength_content
                )
                db.session.add(strength)

        # Add activity weaknesses
        for weakness_content in activity_weaknesses:
            if weakness_content:
                weakness = ActivityWeaknesses(
                    activity_weaknesses_documentation_id=documentation_id,
                    activity_weaknesses_content=weakness_content
                )
                db.session.add(weakness)

        # Add activity recommendations
        for recommendation_content in activity_recommendations:
            if recommendation_content:
                recommendation = ActivityRecommendations(
                    activity_recommendations_documentation_id=documentation_id,
                    activity_recommendations_content=recommendation_content
                )
                db.session.add(recommendation)

        # Get learnings and observations
        learnings = request.form.getlist('learnings')
        observations = request.form.getlist('observations')

        # Add learnings
        for learning_content in learnings:
            if learning_content.strip():  # Only add non-empty learnings
                new_learning = Learnings(
                    learnings_learning_journal_forms_id=learning_journal_forms_id,
                    learnings_content=learning_content
                )
                db.session.add(new_learning)

        # Add observations
        for observation_content in observations:
            if observation_content.strip():  # Only add non-empty observations
                new_observation = Observations(
                    observations_learning_journal_forms_id=learning_journal_forms_id,
                    observations_content=observation_content
                )
                db.session.add(new_observation)

        # Get tally items data
        tally_items_names = request.form.getlist('tally-items-name[]')
        tally_items_extremely_satisfied = request.form.getlist('tally-items-extremely-satisfied-rating-total[]')
        tally_items_satisfied = request.form.getlist('tally-items-satisfied-rating-total[]')
        tally_items_neutral = request.form.getlist('tally-items-neutral-rating-total[]')
        tally_items_dissatisfied = request.form.getlist('tally-items-dissatisfied-rating-total[]')
        tally_items_extremely_dissatisfied = request.form.getlist('tally-items-extremely-dissatisfied-rating-total[]')
        
        # Add tally items
        for i in range(len(tally_items_names)):
            if tally_items_names[i].strip():  # Only add if name is not empty
                new_tally_item = TallyItems(
                    tally_items_documentation_id=documentation_id,
                    tally_items_name=tally_items_names[i],
                    tally_items_extremely_satisfied_rating_total=int(tally_items_extremely_satisfied[i]),
                    tally_items_satisfied_rating_total=int(tally_items_satisfied[i]),
                    tally_items_neutral_rating_total=int(tally_items_neutral[i]),
                    tally_items_dissatisfied_rating_total=int(tally_items_dissatisfied[i]),
                    tally_items_extremely_dissatisfied_rating_total=int(tally_items_extremely_dissatisfied[i])
                )
                db.session.add(new_tally_item)

        # Handle evaluation images upload
        evaluation_images = request.files.getlist('evaluation-images[]')
        for image in evaluation_images:
            if image and allowed_image_file(image.filename):
                try:
                    # Upload to Cloudinary
                    upload_result = cloudinary.uploader.upload(
                        image,
                        folder="evaluation_images",  # Optional: organize in folders
                        resource_type="auto"
                    )
                    
                    # Create database entry for the image
                    new_image = ResultsOfTheEvaluationImages(
                        results_of_the_evaluation_images_documentation_id=documentation_id,
                        results_of_the_evaluation_images_cloudinary_url=upload_result['secure_url'],
                        results_of_the_evaluation_images_cloudinary_public_id=upload_result['public_id']
                    )
                    db.session.add(new_image)
                except Exception as e:
                    app.logger.error(f"Failed to upload image: {str(e)}")
                    flash("Failed to upload one or more images.", "error")

        # Get the evaluation form data from the form
        evaluation_names = request.form.getlist('evaluation-form-name[]')
        extremely_satisfied = request.form.getlist('evaluation-form-extremely-satisfied[]')
        satisfied = request.form.getlist('evaluation-form-satisfied[]')
        neutral = request.form.getlist('evaluation-form-neutral[]')
        dissatisfied = request.form.getlist('evaluation-form-dissatisfied[]')
        extremely_dissatisfied = request.form.getlist('evaluation-form-extremely-dissatisfied[]')

        # Create evaluation form entries
        for i in range(len(evaluation_names)):
            if evaluation_names[i].strip():  # Only add if name is not empty
                new_evaluation = EvaluationForm(
                    evaluation_form_documentation_id=documentation_id,
                    evaluation_form_name=evaluation_names[i].strip(),
                    evaluation_form_extremely_satisfied_rating=int(extremely_satisfied[i] or 0),
                    evaluation_form_satisfied_rating=int(satisfied[i] or 0),
                    evaluation_form_neutral_rating=int(neutral[i] or 0),
                    evaluation_form_dissatisfied_rating=int(dissatisfied[i] or 0),
                    evaluation_form_extremely_dissatisfied_rating=int(extremely_dissatisfied[i] or 0)
                )
                db.session.add(new_evaluation)

        # Handle summary of attendance images upload
        attendance_images = request.files.getlist('attendance-images[]')
        for image in attendance_images:
            if image and allowed_image_file(image.filename):
                try:
                    # Upload to Cloudinary
                    upload_result = cloudinary.uploader.upload(
                        image,
                        folder="attendance_images",
                        resource_type="auto"
                    )
                    
                    # Create database entry for the image
                    new_image = SummaryOfAttendanceImages(
                        summary_of_attendance_images_documentation_id=documentation_id,
                        summary_of_attendance_images_cloudinary_url=upload_result['secure_url'],
                        summary_of_attendance_images_cloudinary_public_id=upload_result['public_id']
                    )
                    db.session.add(new_image)
                except Exception as e:
                    app.logger.error(f"Failed to upload attendance image: {str(e)}")
                    flash("Failed to upload one or more attendance images.", "error")

        # Process student list Excel file
        if 'student-list-excel' in request.files:
            file = request.files['student-list-excel']
            if file and file.filename.endswith('.xlsx'):
                try:
                    df = pd.read_excel(file)
                    name_column = None
                    for col in df.columns:
                        if 'full name' in col.lower():
                            name_column = col
                            break
                    
                    if name_column:
                        student_names = df[name_column].dropna().tolist()
                        for student_name in student_names:
                            new_student = EvaluationListOfStudentNames(
                                evaluation_list_of_student_names_documentation_id=documentation_id,
                                evaluation_list_of_student_names_student=student_name
                            )
                            db.session.add(new_student)
                except Exception as e:
                    app.logger.error(f"Failed to process student list: {str(e)}")
                    flash("Failed to process student list Excel file.", "error")

        # Handle photo documentation images upload
        photo_doc_images = request.files.getlist('photo-documentation-images[]')
        for image in photo_doc_images:
            if image and allowed_image_file(image.filename):
                try:
                    # Upload to Cloudinary
                    upload_result = cloudinary.uploader.upload(
                        image,
                        folder="event_photo_documentation_images",
                        resource_type="auto"
                    )
                    
                    # Create database entry for the image
                    new_image = EventPhotoDocumentationImages(
                        event_photo_documentation_images_documentation_id=documentation_id,
                        event_photo_documentation_images_cloudinary_url=upload_result['secure_url'],
                        event_photo_documentation_images_cloudinary_public_id=upload_result['public_id']
                    )
                    db.session.add(new_image)
                except Exception as e:
                    app.logger.error(f"Failed to upload event photo documentation image: {str(e)}")
                    flash("Failed to upload one or more event photo documentation images.", "error")

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

    # Get or create learning journal
    learning_journal = None
    if documentation.documentation_learning_journal_forms_id:
        learning_journal = LearningJournalForms.query.get(documentation.documentation_learning_journal_forms_id)
    else:
        learning_journal = LearningJournalForms()
        db.session.add(learning_journal)
        documentation.documentation_learning_journal_forms_id = learning_journal.learning_journal_forms_id

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

        # Update strengths
        # First, delete existing strengths
        ActivityStrengths.query.filter_by(
            activity_strengths_documentation_id=documentation_id
        ).delete()
        
        # Add new strengths
        strengths = request.form.getlist('activity-strengths[]')
        for strength in strengths:
            if strength.strip():  # Only add non-empty strengths
                new_strength = ActivityStrengths(
                    activity_strengths_documentation_id=documentation_id,
                    activity_strengths_content=strength.strip()
                )
                db.session.add(new_strength)

        # Update weaknesses
        ActivityWeaknesses.query.filter_by(
            activity_weaknesses_documentation_id=documentation_id
        ).delete()
        
        weaknesses = request.form.getlist('activity-weaknesses[]')
        for weakness in weaknesses:
            if weakness.strip():
                new_weakness = ActivityWeaknesses(
                    activity_weaknesses_documentation_id=documentation_id,
                    activity_weaknesses_content=weakness.strip()
                )
                db.session.add(new_weakness)

        # Update recommendations
        ActivityRecommendations.query.filter_by(
            activity_recommendations_documentation_id=documentation_id
        ).delete()
        
        recommendations = request.form.getlist('activity-recommendations[]')
        for recommendation in recommendations:
            if recommendation.strip():
                new_recommendation = ActivityRecommendations(
                    activity_recommendations_documentation_id=documentation_id,
                    activity_recommendations_content=recommendation.strip()
                )
                db.session.add(new_recommendation)

        # Update Learning Journal fields
        learning_journal.learning_journal_forms_name_of_student = request.form.get('student-name')
        learning_journal.learning_journal_forms_course_year_level = request.form.get('course-year-level')
        learning_journal.learning_journal_forms_id_number = request.form.get('id-number')
        learning_journal.learning_journal_forms_overall_reflection = request.form.get('overall-reflection')
        learning_journal.learning_journal_forms_seen_and_read_by = request.form.get('seen-read-by')
        learning_journal.learning_journal_forms_prepared_by = request.form.get('documentation-prepared-by')
        learning_journal.learning_journal_forms_checked_by = request.form.get('documentation-checked-by')

        # Update learnings
        Learnings.query.filter_by(
            learnings_learning_journal_forms_id=learning_journal.learning_journal_forms_id
        ).delete()
        
        learnings = request.form.getlist('learnings[]')
        for learning in learnings:
            if learning.strip():
                new_learning = Learnings(
                    learnings_learning_journal_forms_id=learning_journal.learning_journal_forms_id,
                    learnings_content=learning.strip()
                )
                db.session.add(new_learning)

        # Update observations
        Observations.query.filter_by(
            observations_learning_journal_forms_id=learning_journal.learning_journal_forms_id
        ).delete()
        
        observations = request.form.getlist('observations[]')
        for observation in observations:
            if observation.strip():
                new_observation = Observations(
                    observations_learning_journal_forms_id=learning_journal.learning_journal_forms_id,
                    observations_content=observation.strip()
                )
                db.session.add(new_observation)

        # Get the list of images to delete
        deleted_image_ids = request.form.get('deleted_evaluation_images', '').split(',')
        if deleted_image_ids and deleted_image_ids[0]:  # Check if there are any deleted images
            for image_id in deleted_image_ids:
                image = ResultsOfTheEvaluationImages.query.get(int(image_id))
                if image:
                    try:
                        # Delete from Cloudinary
                        if image.results_of_the_evaluation_images_cloudinary_public_id:
                            cloudinary.uploader.destroy(
                                image.results_of_the_evaluation_images_cloudinary_public_id
                            )
                        # Delete from database
                        db.session.delete(image)
                    except Exception as e:
                        flash('Error deleting some evaluation images', 'error')
        
        # Handle new evaluation image uploads
        evaluation_images = request.files.getlist('evaluation-images[]')
        if evaluation_images:
            for image in evaluation_images:
                if image and allowed_image_file(image.filename):
                    try:
                        # Upload to Cloudinary
                        upload_result = cloudinary.uploader.upload(image)
                        
                        # Create new evaluation image record
                        new_image = ResultsOfTheEvaluationImages(
                            results_of_the_evaluation_images_documentation_id=documentation_id,
                            results_of_the_evaluation_images_cloudinary_url=upload_result['secure_url'],
                            results_of_the_evaluation_images_cloudinary_public_id=upload_result['public_id']
                        )
                        db.session.add(new_image)
                    except Exception as e:
                        flash('Error uploading some evaluation images', 'error')
                        return redirect(url_for('update_documentation', documentation_id=documentation_id))
        
        # Handle attendance images deletion
        deleted_attendance_image_ids = request.form.get('deleted_attendance_images', '').split(',')
        if deleted_attendance_image_ids and deleted_attendance_image_ids[0]:
            for image_id in deleted_attendance_image_ids:
                image = SummaryOfAttendanceImages.query.get(int(image_id))
                if image:
                    try:
                        if image.summary_of_attendance_images_cloudinary_public_id:
                            cloudinary.uploader.destroy(
                                image.summary_of_attendance_images_cloudinary_public_id
                            )
                        db.session.delete(image)
                    except Exception as e:
                        flash('Error deleting some attendance images', 'error')

        # Handle event photo documentation images deletion
        deleted_event_photo_doc_image_ids = request.form.get('deleted_event_photo_doc_images', '').split(',')
        if deleted_event_photo_doc_image_ids and deleted_event_photo_doc_image_ids[0]:
            for image_id in deleted_event_photo_doc_image_ids:
                image = EventPhotoDocumentationImages.query.get(int(image_id))
                if image:
                    try:
                        if image.event_photo_documentation_images_cloudinary_public_id:
                            cloudinary.uploader.destroy(
                                image.event_photo_documentation_images_cloudinary_public_id
                            )
                        db.session.delete(image)
                    except Exception as e:
                        flash('Error deleting some event photo documentation images', 'error')

        # Handle new attendance image uploads
        attendance_images = request.files.getlist('attendance-images[]')
        if attendance_images:
            for image in attendance_images:
                if image and allowed_image_file(image.filename):
                    try:
                        upload_result = cloudinary.uploader.upload(image)
                        new_image = SummaryOfAttendanceImages(
                            summary_of_attendance_images_documentation_id=documentation_id,
                            summary_of_attendance_images_cloudinary_url=upload_result['secure_url'],
                            summary_of_attendance_images_cloudinary_public_id=upload_result['public_id']
                        )
                        db.session.add(new_image)
                    except Exception as e:
                        flash('Error uploading some attendance images', 'error')
                        return redirect(url_for('update_documentation', documentation_id=documentation_id))

        # Handle new event photo documentation image uploads
        event_photo_doc_images = request.files.getlist('event-photo-documentation-images[]')
        if event_photo_doc_images:
            for image in event_photo_doc_images:
                if image and allowed_image_file(image.filename):
                    try:
                        upload_result = cloudinary.uploader.upload(image)
                        new_image = EventPhotoDocumentationImages(
                            event_photo_documentation_images_documentation_id=documentation_id,
                            event_photo_documentation_images_cloudinary_url=upload_result['secure_url'],
                            event_photo_documentation_images_cloudinary_public_id=upload_result['public_id']
                        )
                        db.session.add(new_image)
                    except Exception as e:
                        flash('Error uploading some event photo documentation images', 'error')
                        return redirect(url_for('update_documentation', documentation_id=documentation_id))

        # Get the list of student names from the form
        student_names = request.form.getlist('evaluation-student-names[]')

        # Delete existing student names
        EvaluationListOfStudentNames.query.filter_by(
            evaluation_list_of_student_names_documentation_id=documentation_id
        ).delete()

        # Add new student names
        for student_name in student_names:
            if student_name.strip():  # Only add if name is not empty
                new_student = EvaluationListOfStudentNames(
                    evaluation_list_of_student_names_documentation_id=documentation_id,
                    evaluation_list_of_student_names_student=student_name.strip()
                )
                db.session.add(new_student)

        # Get the tally items data
        tally_names = request.form.getlist('tally-items-name[]')
        extremely_satisfied = request.form.getlist('tally-items-extremely-satisfied-rating-total[]')
        satisfied = request.form.getlist('tally-items-satisfied-rating-total[]')
        neutral = request.form.getlist('tally-items-neutral-rating-total[]')
        dissatisfied = request.form.getlist('tally-items-dissatisfied-rating-total[]')
        extremely_dissatisfied = request.form.getlist('tally-items-extremely-dissatisfied-rating-total[]')
        
        # First, delete all existing tally items and evaluation forms
        TallyItems.query.filter_by(tally_items_documentation_id=documentation_id).delete()
        EvaluationForm.query.filter_by(evaluation_form_documentation_id=documentation_id).delete()
    
        # Process tally items and evaluation forms separately
        process_tally_items(documentation_id, tally_names, extremely_satisfied, satisfied, neutral, dissatisfied, extremely_dissatisfied)
        process_evaluation_forms(documentation_id, tally_names, request)

        # Update documentation rating
        documentation = Documentation.query.get_or_404(documentation_id)
        documentation.documentation_rating = float(request.form.get('documentation-rating', 0))
        documentation.documentation_comments_suggestions = request.form.get('documentation-comments-suggestions', '')

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

    # Query for activity report forms with concept paper subject
    activity_reports = db.session.query(
        ActivityReportForms, ConceptPaperForms.concept_paper_forms_subject
    ).join(
        ConceptPaperForms,
        ActivityReportForms.activity_report_forms_concept_paper_forms_id == ConceptPaperForms.concept_paper_forms_id
    ).all()

    # Prepare activity reports data
    activity_reports_data = [{
        'activity_report_forms_id': report.ActivityReportForms.activity_report_forms_id,
        'events_name': report.concept_paper_forms_subject
    } for report in activity_reports]

    # Query for learning journal forms with concept paper subject
    learning_journals = db.session.query(
        LearningJournalForms, ConceptPaperForms.concept_paper_forms_subject
    ).join(
        ConceptPaperForms,
        LearningJournalForms.learning_journal_forms_concept_paper_forms_id == ConceptPaperForms.concept_paper_forms_id
    ).all()

    # Prepare learning journals data
    learning_journals_data = [{
        'learning_journal_forms_id': journal.LearningJournalForms.learning_journal_forms_id,
        'events_name': journal.concept_paper_forms_subject,
        'learning_journal_forms_name_of_student': journal.LearningJournalForms.learning_journal_forms_name_of_student,
        'learning_journal_forms_course_year_level': journal.LearningJournalForms.learning_journal_forms_course_year_level,
        'learning_journal_forms_id_number': journal.LearningJournalForms.learning_journal_forms_id_number,
        'learning_journal_forms_date': journal.LearningJournalForms.learning_journal_forms_date,
        'learning_journal_forms_overall_reflection': journal.LearningJournalForms.learning_journal_forms_overall_reflection,
        'learning_journal_forms_prepared_by': journal.LearningJournalForms.learning_journal_forms_prepared_by,
        'learning_journal_forms_seen_and_read_by': journal.LearningJournalForms.learning_journal_forms_seen_and_read_by,
        'learning_journal_forms_checked_by': journal.LearningJournalForms.learning_journal_forms_checked_by
    } for journal in learning_journals]

    # Get strengths, weaknesses, and recommendations
    strengths = ActivityStrengths.query.filter_by(
        activity_strengths_documentation_id=documentation_id
    ).all()

    weaknesses = ActivityWeaknesses.query.filter_by(
        activity_weaknesses_documentation_id=documentation_id
    ).all()

    recommendations = ActivityRecommendations.query.filter_by(
        activity_recommendations_documentation_id=documentation_id
    ).all()

    # Query for existing data
    learning_journal = None
    learnings = []
    observations = []

    if documentation.documentation_learning_journal_forms_id:
        learning_journal = LearningJournalForms.query.get(documentation.documentation_learning_journal_forms_id)
        if learning_journal:
            learnings = Learnings.query.filter_by(
                learnings_learning_journal_forms_id=learning_journal.learning_journal_forms_id
            ).all()
            observations = Observations.query.filter_by(
                observations_learning_journal_forms_id=learning_journal.learning_journal_forms_id
            ).all()

    # Get tally items data
    tally_items = TallyItems.query.filter_by(
        tally_items_documentation_id=documentation_id
    ).all()
    
    # Convert tally items to a list of dictionaries
    tally_items_data = [{
        'tally_items_id': item.tally_items_id,
        'tally_items_name': item.tally_items_name,
        'tally_items_extremely_satisfied_rating_total': item.tally_items_extremely_satisfied_rating_total,
        'tally_items_satisfied_rating_total': item.tally_items_satisfied_rating_total,
        'tally_items_neutral_rating_total': item.tally_items_neutral_rating_total,
        'tally_items_dissatisfied_rating_total': item.tally_items_dissatisfied_rating_total,
        'tally_items_extremely_dissatisfied_rating_total': item.tally_items_extremely_dissatisfied_rating_total
    } for item in tally_items]

    # Get existing evaluation images
    evaluation_images = ResultsOfTheEvaluationImages.query.filter_by(
        results_of_the_evaluation_images_documentation_id=documentation_id
    ).all()

    event_photo_documentation_images = EventPhotoDocumentationImages.query.filter_by(
        event_photo_documentation_images_documentation_id=documentation_id
    ).all()

    evaluation_student_list = EvaluationListOfStudentNames.query.filter_by(
        evaluation_list_of_student_names_documentation_id=documentation_id
    ).all()

    evaluation_forms = EvaluationForm.query.filter_by(
        evaluation_form_documentation_id=documentation_id
    ).all()
    evaluation_forms_dict = [form.to_dict() for form in evaluation_forms]

    return render_template('update-documentation.html', 
                         documentation=documentation, 
                         events=events, 
                         academic_years=academic_years, 
                         users=users, 
                         signatories=signatories, 
                         activity_reports=activity_reports_data, 
                         learning_journals=learning_journals_data,
                         strengths=strengths,
                         weaknesses=weaknesses,
                         recommendations=recommendations,
                         learnings=learnings,
                         observations=observations,
                         tally_items=tally_items_data,
                         evaluation_images=evaluation_images,
                         event_photo_documentation_images=event_photo_documentation_images,
                         evaluation_student_list=evaluation_student_list,
                         evaluation_forms=evaluation_forms_dict
    )

@app.route('/delete-documentation/<int:documentation_id>', methods=['GET', 'POST'])
@login_required
def delete_documentation(documentation_id):
    documentation = Documentation.query.get_or_404(documentation_id)

    if request.method == 'POST':
        try:
            # Get the documentation and its associated images
            documentation = Documentation.query.get_or_404(documentation_id)
            evaluation_images = ResultsOfTheEvaluationImages.query.filter_by(
                results_of_the_evaluation_images_documentation_id=documentation_id
            ).all()

            # Delete images from Cloudinary and database
            for image in evaluation_images:
                try:
                    # Delete from Cloudinary
                    if image.results_of_the_evaluation_images_cloudinary_public_id:
                        cloudinary.uploader.destroy(
                            image.results_of_the_evaluation_images_cloudinary_public_id,
                            resource_type="image"
                        )
                    # Delete database entry
                    db.session.delete(image)
                except Exception as e:
                    app.logger.error(f"Failed to delete image: {str(e)}")
                    # Continue with deletion even if one image fails

            # Get and delete attendance images
            attendance_images = SummaryOfAttendanceImages.query.filter_by(
                summary_of_attendance_images_documentation_id=documentation_id
            ).all()

            # Delete attendance images from Cloudinary and database
            for image in attendance_images:
                try:
                    if image.summary_of_attendance_images_cloudinary_public_id:
                        cloudinary.uploader.destroy(
                            image.summary_of_attendance_images_cloudinary_public_id,
                            resource_type="image"
                        )
                    db.session.delete(image)
                except Exception as e:
                    app.logger.error(f"Failed to delete attendance image: {str(e)}")

            # Get and delete event photo documentation images
            event_photos = EventPhotoDocumentationImages.query.filter_by(
                event_photo_documentation_images_documentation_id=documentation_id
            ).all()

            # Delete event photo documentation images from Cloudinary and database
            for image in event_photos:
                try:
                    if image.event_photo_documentation_images_cloudinary_public_id:
                        cloudinary.uploader.destroy(
                            image.event_photo_documentation_images_cloudinary_public_id,
                            resource_type="image"
                        )
                    db.session.delete(image)
                except Exception as e:
                    app.logger.error(f"Failed to delete event photo documentation image: {str(e)}")

            # Delete the documentation entry
            db.session.delete(documentation)
            db.session.commit()
            
            flash('Documentation deleted successfully!', 'success')
            return redirect(url_for('documentation_overview'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Failed to delete documentation: {str(e)}")
            flash('Failed to delete documentation.', 'error')

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

    # Get unique signatory IDs from learning_journal_forms_checked_by
    checked_by_ids = set()
    for journal in learning_journals:
        if journal.learning_journal_forms_checked_by:
            checked_by_ids.add(journal.learning_journal_forms_checked_by)

    # Query for filtered signatories
    signatories = db.session.query(Signatories).filter(Signatories.signatory_id.in_(checked_by_ids)).all()

    # Prepare the data to be sent as JSON
    activity_reports_data = [{'activity_report_forms_id': report.activity_report_forms_id, 'events_name': report.concept_paper_form.concept_paper_forms_subject} for report in activity_reports]

    learning_journals_data = [{
        'learning_journal_forms_id': journal.learning_journal_forms_id, 
        'events_name': journal.concept_paper_form.concept_paper_forms_subject,
        'learning_journal_forms_checked_by': journal.learning_journal_forms_checked_by
    } for journal in learning_journals]

    signatories_data = [{
        'signatory_id': signatory.signatory_id,
        'signatory_first_name': signatory.signatory_first_name,
        'signatory_last_name': signatory.signatory_last_name,
        'signatory_position': signatory.signatory_position,
        'signatory_department': signatory.signatory_department
    } for signatory in signatories]

    return jsonify(activity_reports=activity_reports_data, learning_journals=learning_journals_data, signatories=signatories_data)

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

@app.route('/process-student-excel', methods=['POST'])
@login_required
def process_student_excel():
    if 'excel_file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'})
    
    file = request.files['excel_file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    
    if not file.filename.endswith('.xlsx'):
        return jsonify({'success': False, 'error': 'Please upload an Excel (.xlsx) file'})
    
    try:
        # Read the Excel file
        df = pd.read_excel(file)
        
        # Find column containing 'full name' (case insensitive)
        name_column = None
        for col in df.columns:
            if 'full name' in col.lower():
                name_column = col
                break
        
        if name_column is None:
            return jsonify({'success': False, 'error': 'No column containing "full name" found'})
        
        # Get student names
        student_names = df[name_column].dropna().tolist()
        
        return jsonify({
            'success': True,
            'students': student_names
        })
    
    except Exception as e:
        app.logger.error(f"Error processing Excel file: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to process Excel file'})

@app.route('/generate-documentation-pdf/<int:documentation_id>')
@login_required
def generate_documentation_pdf(documentation_id):
    buffer = BytesIO()
    
    def header(canvas, doc):
        canvas.saveState()
        
        # Add header images with manual positioning
        # PERPS header - left side
        header_perps = Image('./static/img/HEADER-PERPS.png', width=325, height=75)
        perps_x = doc.leftMargin - 35
        header_perps.drawOn(canvas, perps_x, doc.height + doc.topMargin)
        
        # CCS Logo - center
        header_ccs = Image('./static/img/CCS-LOGO.png', width=35, height=50)
        ccs_x = doc.leftMargin + (doc.width - 35)/2 + 125
        header_ccs.drawOn(canvas, ccs_x, doc.height + doc.topMargin + 15)
        
        # ISO Logo - right side
        header_iso = Image('./static/img/ISO.png', width=100, height=50)
        iso_x = doc.leftMargin + doc.width - 80
        header_iso.drawOn(canvas, iso_x, doc.height + doc.topMargin + 15)
        
        # Add text below ISO logo
        canvas.setFont("Helvetica-Bold", 10)
        text = "College of Computer Studies"
        text_width = canvas.stringWidth(text, "Helvetica-Bold", 10)
        text_x = iso_x + (50 - text_width)/2
        canvas.drawString(text_x, doc.height + doc.topMargin, text)
        
        # Add red line after text
        canvas.setStrokeColorRGB(0x8c/255, 0x04/255, 0x04/255)  # #8c0404
        canvas.setLineWidth(2)
        line_y = doc.height + doc.topMargin - 10
        line_length = 510
        line_start_x = (doc.width - line_length) / 2 + doc.leftMargin
        line_end_x = line_start_x + line_length
        canvas.line(line_start_x - 5, line_y, line_end_x, line_y)
        
        # Add footer
        canvas.setStrokeColorRGB(0, 0, 0)
        canvas.setLineWidth(1)
        footer_y = doc.bottomMargin - 20
        canvas.line(doc.leftMargin, footer_y, doc.leftMargin + doc.width, footer_y)
        
        # Add footer text
        canvas.setFont("Helvetica", 12)
        canvas.drawString(doc.leftMargin, footer_y - 15, "UPHMO-CCS-GEN-912/rev0")
        right_text = "Activity Report"
        right_text_width = canvas.stringWidth(right_text, "Helvetica", 12)
        canvas.drawString(doc.leftMargin + doc.width - right_text_width, footer_y - 15, right_text)
        
        canvas.restoreState()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=100,
        bottomMargin=72
    )
    
    story = []

    documentation = Documentation.query.get_or_404(documentation_id)
    event = documentation.events

    # Get activity report form if it exists
    activity_report = ActivityReportForms.query.get(documentation.documentation_activity_report_forms_id)

    # Get personnel in charge through concept paper
    personnel_in_charge = None
    if event.events_concept_paper_forms_id:
        personnel_form = PersonnelInChargeForms.query.filter_by(
            personnel_in_charge_forms_concept_paper_forms_id=event.events_concept_paper_forms_id
        ).first()
        if personnel_form and personnel_form.personnel_in_charge_signatory:
            signatory = personnel_form.personnel_in_charge_signatory
            # Format full name with title and position
            personnel_in_charge = f"{signatory.signatory_title} {signatory.signatory_first_name} "
            if signatory.signatory_middle_name:
                personnel_in_charge += f"{signatory.signatory_middle_name} "
            personnel_in_charge += f"{signatory.signatory_last_name}"
            if signatory.signatory_suffix:
                personnel_in_charge += f" {signatory.signatory_suffix}"
            personnel_in_charge += f", {signatory.signatory_position}"

    # Format date and time from the combined fields
    events_date = event.events_start_date_and_time.strftime("%A, %B %d, %Y") if event.events_start_date_and_time else "N/A"
    events_time = (
        f"{event.events_start_date_and_time.strftime('%I:%M %p')} - {event.events_end_date_and_time.strftime('%I:%M %p')}"
        if event.events_start_date_and_time and event.events_end_date_and_time
        else "N/A"
    )

    # Get department name through departments_events table
    department_name = "N/A"
    department_event = DepartmentsEvents.query.filter_by(events_id=event.events_id).first()
    if department_event and department_event.department:
        department_name = department_event.department.departments_name

    # Get nature of activity from activity report form
    nature_of_activity = activity_report.activity_report_forms_nature_of_the_activity if activity_report else "N/A"

    # Get contact number from activity report form
    contact_number = activity_report.activity_report_forms_contact_numbers if activity_report else "N/A"

    # Get total participants from concept paper form
    total_participants = "N/A"
    if event.events_concept_paper_forms_id:
        concept_paper = ConceptPaperForms.query.get(event.events_concept_paper_forms_id)
        if concept_paper and concept_paper.concept_paper_forms_expected_number_of_participants:
            total_participants = concept_paper.concept_paper_forms_expected_number_of_participants

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        alignment=1,  # Center alignment
        spaceAfter=20,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    )

    section_header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=12,
        spaceBefore=15,
        fontName='Helvetica'
    )

    # Add title and section header to the story list
    story.append(Paragraph("ACTIVITY REPORT FORM", title_style))
    story.append(Paragraph("I. ACTIVITY DETAILS", section_header_style))

    # Create a custom style for the cells without padding
    cell_style = ParagraphStyle(
        'CellStyle',
        parent=styles['Normal'],
        spaceBefore=0,
        spaceAfter=0,
        leading=14,  # Keep this to maintain readability between lines
        fontSize=12
    )

    data = [
        # First Column, First Row
        [
            Paragraph(f"<b>Title of the Activity:</b><br/>{event.events_name}", cell_style),
            Paragraph(f"<b>Date:</b><br/>{events_date}", cell_style)
        ],
        # First Column, Second Row
        [
            Paragraph(f"<b>Nature of Activity:</b><br/>{nature_of_activity}", cell_style),
            Paragraph(f"<b>Time:</b><br/>{events_time}", cell_style)
        ],
        # Second Column, First Row
        [
            Paragraph(f"<b>College/Department:</b><br/>{department_name}", cell_style),
            Paragraph(f"<b>Venue:</b><br/>{event.events_venue}", cell_style)
        ],
        # Second Column, Second Row
        [
            Paragraph(f"<b>Dean/Faculty in-charge/Officer in- charge:</b><br/>{personnel_in_charge or 'N/A'}", cell_style),
            Paragraph(f"<b>Contact Numbers:</b><br/>{contact_number}", cell_style)
        ],
        # Last Row, spans both columns
        [
            Paragraph(f"<b>Total number of participants:</b><br/>{total_participants}", cell_style),
            ''  # Empty cell for alignment
        ]
    ]

    # Create table with adjusted column widths
    table = Table(data, colWidths=[235, 235])

    # Update table style with minimal padding
    table_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),  
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),    
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),   
    ])

    table.setStyle(table_style)

    # Add some space before the table
    story.append(Spacer(1, 10))
    story.append(table)

    # After the first table, add a section header for Objectives
    story.append(Spacer(1, 20))
    story.append(Paragraph("II. OBJECTIVES", section_header_style))

    # Fetch objectives and learning outcomes
    objectives = []
    learning_outcomes = []

    # Get concept_paper_forms_id from the event
    concept_paper_forms_id = event.events_concept_paper_forms_id if event else None

    if concept_paper_forms_id:
        # Get objectives
        objectives_query = db.session.query(ObjectivesOfTheActivity).filter(
            ObjectivesOfTheActivity.objectives_of_the_activity_concept_paper_forms_id == concept_paper_forms_id
        ).all()
        objectives = [obj.objectives_of_the_activity_content for obj in objectives_query if obj.objectives_of_the_activity_content]
        objectives = [f"{i+1}. {obj}" for i, obj in enumerate(objectives)]

        # Get learning outcomes
        outcomes_query = db.session.query(LearningOutcomes).filter(
            LearningOutcomes.learning_outcomes_concept_paper_forms_id == concept_paper_forms_id
        ).all()
        learning_outcomes = [outcome.learning_outcomes_content for outcome in outcomes_query if outcome.learning_outcomes_content]
        learning_outcomes = [f"{i+1}. {outcome}" for i, outcome in enumerate(learning_outcomes)]
    
    # Create header style for the columns
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        spaceBefore=0,
        spaceAfter=6,
        leading=14,
        alignment=1
    )
    
    # Create the objectives table data
    objectives_data = [
        # Headers row
        [
            Paragraph("<b>Objective/s</b>", header_style),
            Paragraph("<b>Outcomes (Benefits of Clients)</b>", header_style)
        ]
    ]
    
    # Calculate the maximum length of both lists to determine number of rows
    max_length = max(len(objectives), len(learning_outcomes))
    
    # Add content rows, using 'N/A' for empty entries
    for i in range(max_length):
        objective = objectives[i] if i < len(objectives) else "N/A"
        outcome = learning_outcomes[i] if i < len(learning_outcomes) else "N/A"
        objectives_data.append([
            Paragraph(objective, cell_style),
            Paragraph(outcome, cell_style)
        ])
    
    # Create the objectives table
    objectives_table = Table(objectives_data, colWidths=[235, 235])
    
    # Style for the objectives table
    objectives_table_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # Center align the header row
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
    ])
    
    objectives_table.setStyle(objectives_table_style)
    
    # Add some space before the objectives table
    story.append(Spacer(1, 10))
    story.append(objectives_table)

    # After the objectives table, add the Evaluation section
    story.append(Spacer(1, 20))
    story.append(Paragraph("III. EVALUATION: (Make sure to have three answers for the strengths and weakness.) Weaknesses must have corresponding recommendations.", section_header_style))
    
    # After getting the concept_paper_forms_id, add this:
    documentation_data = None

    if event:
        # Get documentation information using events_id
        documentation_data = db.session.query(Documentation).filter(
            Documentation.documentation_events_id == event.events_id
        ).first()

    # Fetch evaluation data from database
    strengths = []
    weaknesses = []
    recommendations = []
    
    if documentation_data:
        # Get strengths
        strengths_query = db.session.query(ActivityStrengths).filter(
            ActivityStrengths.activity_strengths_documentation_id == documentation_data.documentation_id
        ).all()
        strengths = [strength.activity_strengths_content for strength in strengths_query if strength.activity_strengths_content]
    
        # Get weaknesses
        weaknesses_query = db.session.query(ActivityWeaknesses).filter(
            ActivityWeaknesses.activity_weaknesses_documentation_id == documentation_data.documentation_id
        ).all()
        weaknesses = [weakness.activity_weaknesses_content for weakness in weaknesses_query if weakness.activity_weaknesses_content]
    
        # Get recommendations
        recommendations_query = db.session.query(ActivityRecommendations).filter(
            ActivityRecommendations.activity_recommendations_documentation_id == documentation_data.documentation_id
        ).all()
        recommendations = [recommendation.activity_recommendations_content for recommendation in recommendations_query if recommendation.activity_recommendations_content]
    
    # Create the evaluation table data
    evaluation_data = [
        # Headers row
        [
            Paragraph("<b>Strengths</b>", header_style),
            Paragraph("<b>Weaknesses</b>", header_style),
            Paragraph("<b>Recommendation</b>", header_style)
        ]
    ]
    
    # Calculate maximum length of the lists
    max_length = max(len(strengths), len(weaknesses), len(recommendations))
    
    # Add content rows with numbering
    for i in range(max_length):
        strength = f"{i+1}. {strengths[i]}" if i < len(strengths) else f"{i+1}. N/A"
        weakness = f"{i+1}. {weaknesses[i]}" if i < len(weaknesses) else f"{i+1}. N/A"
        recommendation = f"{i+1}. {recommendations[i]}" if i < len(recommendations) else f"{i+1}. N/A"
        
        evaluation_data.append([
            Paragraph(strength, cell_style),
            Paragraph(weakness, cell_style),
            Paragraph(recommendation, cell_style)
        ])
    
    # Create the evaluation table
    evaluation_table = Table(evaluation_data, colWidths=[157, 157, 157])  # Adjusted widths to fit the page
    
    # Style for the evaluation table
    evaluation_table_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # Center align the header row
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
    ])
    
    evaluation_table.setStyle(evaluation_table_style)
    
    # Add some space before the evaluation table
    story.append(Spacer(1, 10))
    story.append(evaluation_table)

    # After the evaluation table, add the signature section
    story.append(Spacer(1, 30))  # Add more space before signatures
    
    # After the evaluation table and before the signature section, add these queries
    documentation_data = None
    
    if event:
        # Get documentation information using events_id
        documentation_data = db.session.query(Documentation).filter(
            Documentation.documentation_events_id == event.events_id
        ).first()
    
    # Create signatory style for names and positions
    signatory_style = ParagraphStyle(
        'SignatoryStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        spaceBefore=20,  # Add space before the signatory section
        alignment=0  # 0 for left alignment
    )

    # Create position style with less spacing
    position_style = ParagraphStyle(
        'PositionStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        spaceBefore=0,  # No extra space before position
        alignment=0  # 0 for left alignment
    )

    # Update the signature_data to use position_style for the position rows
    signature_data = [
        [
            Paragraph("Prepared by:", signatory_style),
            Paragraph("Noted by:", signatory_style)
        ],
        [
            Paragraph(
                "<b>" + 
                (documentation_data.prepared_by_user.users_first_name + " " + 
                (documentation_data.prepared_by_user.users_middle_name + " " if documentation_data.prepared_by_user.users_middle_name else "") +
                documentation_data.prepared_by_user.users_last_name +
                (", " + documentation_data.prepared_by_user.users_suffix if documentation_data.prepared_by_user.users_suffix else "")) +
                "</b>"
                if documentation_data and documentation_data.prepared_by_user 
                else "<b>Name</b>", 
                signatory_style
            ),
            Paragraph(
                "<b>" + 
                documentation_data.noted_by_signatory.signatory_first_name + " " + documentation_data.noted_by_signatory.signatory_last_name +
                "</b>"
                if documentation_data and documentation_data.noted_by_signatory 
                else "<b>Name</b>", 
                signatory_style
            )
        ],
        [
            Paragraph(
                f"{documentation_data.prepared_by_user.users_student_organization_position if documentation_data and documentation_data.prepared_by_user else 'Position'}, "
                f"{documentation_data.prepared_by_user.student_organization.student_organizations_name if documentation_data and documentation_data.prepared_by_user and documentation_data.prepared_by_user.student_organization else 'Student Council'}",
                position_style
            ),
            Paragraph(
                f"{documentation_data.noted_by_signatory.signatory_position if documentation_data and documentation_data.noted_by_signatory else 'Position'}, "
                f"{documentation_data.noted_by_signatory.signatory_department if documentation_data and documentation_data.noted_by_signatory else 'Department'}", 
                position_style
            )
        ]
    ]

    # Create signature table
    signature_table = Table(signature_data, colWidths=[235, 235])

    # Style for signature table
    signature_table_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 20),  # Space after headers
        ('TOPPADDING', (0, 2), (-1, 2), 0),    # No extra space before position row
    ])
    
    signature_table.setStyle(signature_table_style)
    
    # Add signature table to story
    story.append(signature_table)

    # Add Learning Journal Form section
    story.append(PageBreak())  # Start on a new page
    story.append(Paragraph("LEARNING JOURNAL FORM", title_style))
    
    story.append(Paragraph("I. Activity Details:", section_header_style))
    story.append(Spacer(1, 10))
    
    # After getting documentation_data, add this:
    learning_journal_form = None
    if documentation_data:
        learning_journal_form = db.session.query(LearningJournalForms).filter(
            LearningJournalForms.learning_journal_forms_id == documentation_data.documentation_learning_journal_forms_id
        ).first()

    # Format the period covered from event start and end times
    period_covered = ""
    if event and event.events_start_date_and_time and event.events_end_date_and_time:
        start_time = event.events_start_date_and_time.strftime("%I:%M %p")
        end_time = event.events_end_date_and_time.strftime("%I:%M %p")
        period_covered = f"{start_time} – {end_time}"

    learning_journal_data = [
        # First row - 3 columns
        [
            Paragraph(f"<b>Name of Student:</b><br/>{learning_journal_form.learning_journal_forms_name_of_student if learning_journal_form else ''}", cell_style),
            Paragraph(f"<b>Course/Year level:</b><br/>{learning_journal_form.learning_journal_forms_course_year_level if learning_journal_form else ''}", cell_style),
            Paragraph(f"<b>ID Number:</b><br/>{learning_journal_form.learning_journal_forms_id_number if learning_journal_form else ''}", cell_style)
        ],
        # Second row - 2 columns (2nd and 3rd merged)
        [
            Paragraph(f"<b>College/Department:</b><br/>College of Computer Studies", cell_style),
            Paragraph(f"<b>Faculty in-charge:</b><br/>{personnel_in_charge if learning_journal_form else ''}", cell_style),
        ],
        # Third row - 3 columns
        [
            Paragraph(f"<b>Period Covered:</b><br/>{period_covered}", cell_style),
            Paragraph(f"<b>Day:</b><br/>{learning_journal_form.learning_journal_forms_date.strftime('%A, %B %d, %Y') if learning_journal_form and learning_journal_form.learning_journal_forms_date else ''}", cell_style),
            Paragraph(f"<b>Venue:</b><br/>{event.events_venue if event else ''}", cell_style)
        ],
        # Fourth row - 3 columns merged
        [Paragraph(f"<b>Title of the Activity:</b><br/>{event.events_name if event else ''}", cell_style)]
    ]
    
    # Create table for learning journal details with 3 columns
    learning_journal_table = Table(learning_journal_data, colWidths=[157, 157, 157])
    
    # Style for learning journal table with merged cells
    learning_journal_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Changed from 'MIDDLE' to 'TOP'
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('SPAN', (1, 1), (2, 1)),  # Merge 2nd and 3rd columns in row 2
        ('SPAN', (0, 3), (2, 3)),  # Merge all columns in row 4
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),  
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ])
    
    learning_journal_table.setStyle(learning_journal_style)
    story.append(learning_journal_table)

    # Add Activity Progress Notes section
    story.append(Spacer(1, 20))
    story.append(Paragraph("II. Activity Progress Notes:", section_header_style))
    story.append(Spacer(1, 10))

    # Format the date string
    if learning_journal_form and learning_journal_form.learning_journal_forms_date:
        date_str = learning_journal_form.learning_journal_forms_date.strftime("%A, %B %d, %Y")
    else:
        date_str = ""

    # Fetch observations and learnings from the database
    observations = []
    learnings = []
    if learning_journal_form:
        # Get observations
        observations_query = db.session.query(Observations).filter(
            Observations.observations_learning_journal_forms_id == learning_journal_form.learning_journal_forms_id
        ).all()
        observations = [obs.observations_content for obs in observations_query if obs.observations_content]

        # Get learnings
        learnings_query = db.session.query(Learnings).filter(
            Learnings.learnings_learning_journal_forms_id == learning_journal_form.learning_journal_forms_id
        ).all()
        learnings = [learn.learnings_content for learn in learnings_query if learn.learnings_content]

    # Format observations and learnings with numbers
    observations_text = ""
    for i, obs in enumerate(observations, 1):
        observations_text += f"{i}. {obs}<br/><br/>"

    learnings_text = ""
    for i, learn in enumerate(learnings, 1):
        learnings_text += f"{i}. {learn}<br/><br/>"

    progress_notes_data = [
        # Header row with three columns
        [
            Paragraph("Date: <b>" + date_str + "</b>", cell_style),
            Paragraph("<b>Observations</b><br/>(not less than 3)", header_style),
            Paragraph("<b>Learnings</b><br/>(not less than 3)", header_style),
        ],
        # Content row
        [
            # Empty cell for date column
            Paragraph("", cell_style),
            # Observations column
            Paragraph(observations_text if observations else "", cell_style),
            # Learnings column
            Paragraph(learnings_text if learnings else "", cell_style),
        ]
    ]

    # Create and style the progress notes table with three columns
    progress_notes_table = Table(progress_notes_data, colWidths=[115, 180, 180])
    progress_notes_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ])

    progress_notes_table.setStyle(progress_notes_style)
    story.append(progress_notes_table)

    # Add Overall Reflection section
    story.append(Spacer(1, 20))
    story.append(Paragraph("III. Over-all Reflection (The reflection must be written in a narrative form not less than 5 sentences.)", section_header_style))
    story.append(Spacer(1, 10))

    # Get the reflection content from the learning journal form
    reflection_text = ""
    if learning_journal_form and learning_journal_form.learning_journal_forms_overall_reflection:
        reflection_text = learning_journal_form.learning_journal_forms_overall_reflection

    # Create reflection paragraph with justified alignment
    reflection_style = ParagraphStyle(
        'ReflectionStyle',
        parent=cell_style,
        alignment=4,  # 4 is for justified alignment
        spaceBefore=6,
        spaceAfter=6,
        leading=16  # Increase line spacing for better readability
    )

    # Add the reflection text in a bordered table for consistent formatting
    reflection_table = Table([[Paragraph(reflection_text if reflection_text else "", reflection_style)]], 
                            colWidths=[475])  # Full width for the reflection
    reflection_table_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ])
    reflection_table.setStyle(reflection_table_style)
    story.append(reflection_table)

    # Add signature section
    story.append(Spacer(1, 30))
    
    # Create styles for signature text
    signature_style = ParagraphStyle(
        'SignatureStyle',
        parent=styles['Normal'],
        fontSize=12,
        leading=14,
    )
    position_style = ParagraphStyle(
        'PositionStyle',
        parent=styles['Normal'],
        fontSize=12,
        leading=12,
    )
    
    # Get user objects for signatures
    prepared_by_user = None
    seen_and_read_by_user = None
    checked_by_signatory = None
    if learning_journal_form:
        if learning_journal_form.learning_journal_forms_prepared_by:
            prepared_by_user = db.session.query(Users).filter(
                Users.users_id == learning_journal_form.learning_journal_forms_prepared_by
            ).first()
        if learning_journal_form.learning_journal_forms_seen_and_read_by:
            seen_and_read_by_user = db.session.query(Users).filter(
                Users.users_id == learning_journal_form.learning_journal_forms_seen_and_read_by
            ).first()

    # Get the checked by user from documentation
    if documentation:
        if documentation.documentation_checked_by:
            checked_by_signatory = db.session.query(Signatories).filter(
                Signatories.signatory_id == documentation.documentation_checked_by
            ).first()

    # Create signature table data
    signature_data = [
        # First row - Labels
        [
            Paragraph("Prepared by:", signature_style),
            Paragraph("Seen and read by:", signature_style),
        ],
        # Second row - Signatures
        [
            Image(prepared_by_user.users_signature_cloudinary_url, width=100, height=40) if prepared_by_user and prepared_by_user.users_signature_cloudinary_url else Paragraph("___________________", signature_style),
            Image(seen_and_read_by_user.users_signature_cloudinary_url, width=100, height=40) if seen_and_read_by_user and seen_and_read_by_user.users_signature_cloudinary_url else Paragraph("__________________________", signature_style),
        ],
        # Third row - Titles
        [
            Paragraph("Signature of Student", position_style),
            Paragraph("Signature over Name of Parent/Guardian", position_style),
        ],
        # Fourth row - Empty space
        ["", ""],
        # Fifth row - Checked by label
        [
            Paragraph("Checked by:", signature_style),
            "",
        ],
        # Sixth row - Dean's signature
        [
            Paragraph("_____________________________", signature_style),
            "",
        ],
        # Seventh row - Dean's name and position
        [
            Paragraph("<b>" + (checked_by_signatory.signatory_first_name.upper() if checked_by_signatory else "") + " " + (checked_by_signatory.signatory_last_name.upper() if checked_by_signatory else "") + "</b><br/>" + (checked_by_signatory.signatory_position if checked_by_signatory else "") + ", " + (checked_by_signatory.signatory_department if checked_by_signatory else ""), position_style),
            "",
        ],
    ]

    # Create signature table with two columns
    signature_table = Table(signature_data, colWidths=[237, 238])  # Adjusted widths to fill the page
    signature_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ])
    
    signature_table.setStyle(signature_style)
    story.append(signature_table)

    # Create centered style for title and date
    centered_header_style = ParagraphStyle(
        'CenteredHeader',
        parent=section_header_style,
        alignment=1,  # 1 is for center alignment
    )

    centered_cell_style = ParagraphStyle(
        'CenteredCell',
        parent=cell_style,
        alignment=1,  # 1 is for center alignment
    )

    # Add Tally Section
    story.append(PageBreak())
    story.append(Paragraph("<b>TALLY – " + event.events_name.upper() + "</b>", centered_header_style))

    # Combine start and end date/time
    event_date_str = event.events_start_date_and_time.strftime("%B %d, %Y")
    if event.events_end_date_and_time and event.events_end_date_and_time.date() != event.events_start_date_and_time.date():
        event_date_str = f"<b>{event.events_start_date_and_time.strftime('%B %d')} - {event.events_end_date_and_time.strftime('%B %d, %Y')}</b>"

    story.append(Paragraph(event_date_str, centered_cell_style))

    story.append(Spacer(1, 20))
    story.append(Paragraph("<b>Please rate your level of satisfaction:</b>", cell_style))
    story.append(Spacer(1, 10))
    
    # First, get the tally items data from the database
    tally_items = db.session.query(
        TallyItems
    ).filter(
        TallyItems.tally_items_documentation_id == documentation_id
    ).all()

    # Create table header data
    tally_header = [
        ['EXTREMELY\nSATISFIED', 'SATISFIED', 'NEUTRAL', 'DISSATISFIED', 'EXTREMELY\nDISSATISFIED'],
    ]
    
    # Create table data with criteria spanning rows
    tally_data = []
    for index, item in enumerate(tally_items):
        tally_letter = chr(65 + index)  # 65 is ASCII for 'A'
        # Add the criteria row
        tally_data.append([f"{tally_letter}. {item.tally_items_name}", '', '', '', ''])
        # Add the ratings row
        tally_data.append([
            str(item.tally_items_extremely_satisfied_rating_total or 0),
            str(item.tally_items_satisfied_rating_total or 0),
            str(item.tally_items_neutral_rating_total or 0),
            str(item.tally_items_dissatisfied_rating_total or 0),
            str(item.tally_items_extremely_dissatisfied_rating_total or 0)
        ])
    
    # Combine header and data
    full_tally_data = tally_header + tally_data
    
    # Create tally table with equal column widths
    available_width = 475  # Total available width
    col_width = available_width // 5  # Equal width for all 5 columns
    col_widths = [col_width] * 5  # Five columns of equal width
    tally_table = Table(full_tally_data, colWidths=col_widths)
    
    # Style the tally table
    tally_style = TableStyle([
        # Header styling
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        
        # Criteria rows (odd rows after header)
        ('SPAN', (0, 1), (-1, 1)),
        ('SPAN', (0, 3), (-1, 3)),
        ('SPAN', (0, 5), (-1, 5)),
        ('SPAN', (0, 7), (-1, 7)),
        ('SPAN', (0, 9), (-1, 9)),
        ('SPAN', (0, 11), (-1, 11)),
        
        # Alignment for criteria rows (odd numbered rows)
        ('ALIGN', (0, 1), (-1, 1), 'LEFT'),
        ('ALIGN', (0, 3), (-1, 3), 'LEFT'),
        ('ALIGN', (0, 5), (-1, 5), 'LEFT'),
        ('ALIGN', (0, 7), (-1, 7), 'LEFT'),
        ('ALIGN', (0, 9), (-1, 9), 'LEFT'),
        ('ALIGN', (0, 11), (-1, 11), 'LEFT'),
        
        # Alignment for value rows (even numbered rows)
        ('ALIGN', (0, 2), (-1, 2), 'CENTER'),  # Values for A
        ('ALIGN', (0, 4), (-1, 4), 'CENTER'),  # Values for B
        ('ALIGN', (0, 6), (-1, 6), 'CENTER'),  # Values for C
        ('ALIGN', (0, 8), (-1, 8), 'CENTER'),  # Values for D
        ('ALIGN', (0, 10), (-1, 10), 'CENTER'),  # Values for E
        ('ALIGN', (0, 12), (-1, 12), 'CENTER'),  # Values for F
        
        # Font settings
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        
        # Padding and alignment
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ])

    tally_table.setStyle(tally_style)
    story.append(tally_table)
    story.append(Spacer(1, 10))
    
    # Get prepared by user (student)
    prepared_by_student = None
    if documentation.documentation_prepared_by:
        prepared_by_student = db.session.query(Users).filter(
            Users.users_id == documentation.documentation_prepared_by
        ).first()
    
    # Get noted by signatory
    noted_by_signatory = None
    if documentation.documentation_noted_by:
        noted_by_signatory = db.session.query(Signatories).filter(
            Signatories.signatory_id == documentation.documentation_noted_by
        ).first()
    
    # Get student's organization details
    student_org_position = ""
    student_org_name = ""
    if prepared_by_student:
        student_org_position = prepared_by_student.users_student_organization_position
        # Get organization name from StudentOrganizations table
        student_org = db.session.query(StudentOrganizations).filter(
            StudentOrganizations.student_organizations_id == prepared_by_student.users_student_organization
        ).first()
        student_org_name = student_org.student_organizations_name if student_org else "Student Organization"
    
    # Create signature table data for tally with date of submission
    tally_signature_data = [
        # First row - Labels
        [
            "Prepared by:",
            "Noted by:",
        ],
        # Second row - Signatures
        [
            "___________________",
            "___________________",
        ],
        # Third row - Names and Positions
        [
            Paragraph("<b>" + (prepared_by_student.users_first_name.upper() if prepared_by_student else "") + " " + 
                    (prepared_by_student.users_last_name.upper() if prepared_by_student else "") + "</b><br/>" +
                    (student_org_position if student_org_position else "Member") + ", " +
                    student_org_name, position_style),
            Paragraph("<b>" + (noted_by_signatory.signatory_first_name.upper() if noted_by_signatory else "") + " " + 
                    (noted_by_signatory.signatory_last_name.upper() if noted_by_signatory else "") + "</b><br/>" + 
                    (noted_by_signatory.signatory_position if noted_by_signatory else "") + ", " + 
                    (noted_by_signatory.signatory_department if noted_by_signatory else ""), position_style),
        ],
        # Fourth row - Empty space
        ["", ""],
        # Fifth row - Date of submission
        [
            "Date of Submission: " + documentation.documentation_date_of_submission.strftime("%B %d, %Y"),
            "",
        ],
    ]

    # Create signature table for tally
    tally_signature_table = Table(tally_signature_data, colWidths=[237, 238])
    tally_signature_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
    ])

    tally_signature_table.setStyle(tally_signature_style)
    story.append(Spacer(1, 30))
    story.append(tally_signature_table)
    story.append(Spacer(1, 20))

    # Add Results of the Evaluation Images section
    story.append(PageBreak())
    story.append(Paragraph("<b>RESULTS OF THE EVALUATION IMAGES</b>", centered_header_style))
    story.append(Spacer(1, 20))
    
    # Get evaluation images from the database
    evaluation_images = ResultsOfTheEvaluationImages.query.filter_by(
        results_of_the_evaluation_images_documentation_id=documentation_id
    ).all()
    
    # Create an array to store image elements
    image_elements = []
    image_max_width = 500  # Maximum width for images
    image_max_height = 400  # Maximum height for images
    
    # Process each image
    for img in evaluation_images:
        if img.results_of_the_evaluation_images_cloudinary_url:
            try:
                # Create image element
                img_elem = Image(
                    img.results_of_the_evaluation_images_cloudinary_url,
                    width=image_max_width,
                    height=image_max_height,
                    kind='proportional'
                )
                image_elements.append(img_elem)
                # Add spacing after each image
                image_elements.append(Spacer(1, 20))
            except Exception as e:
                # Log error if image cannot be loaded
                print(f"Error loading image: {e}")
    
    # Add all images to the story
    for element in image_elements:
        story.append(element)
    
    story.append(Spacer(1, 20))

    # Add Evaluation Form section
    story.append(PageBreak())
    story.append(Paragraph("<b>EVALUATION FORM</b>", centered_header_style))
    
    # Add event name
    story.append(Paragraph(f"<b><u>{event.events_name.upper()}</u></b>", centered_header_style))
    
    # Add date
    event_date = event.events_start_date_and_time.strftime("%A, %B %d %Y") if event.events_start_date_and_time else "N/A"
    story.append(Paragraph(f"<b>Date</b>: {event_date}", centered_header_style))
    story.append(Spacer(1, 20))
    
    # Create an invisible table for instructions and rating scale
    instruction_text = Paragraph("Please indicate your rating of the program in the categories below by circling the appropriate number, using the following scale:", cell_style)
    rating_scale = [
        ["5 – Extremely Satisfied", "2 – Dissatisfied"],
        ["4 – Satisfied", "1 – Extremely Dissatisfied"],
        ["3 – Neutral", ""],
    ]
    rating_table = Table(rating_scale, colWidths=[250, 250])
    rating_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))

    # Combine instruction and rating scale in an invisible table
    instruction_container = Table(
        [[instruction_text], [rating_table]],
        colWidths=[500],
        style=TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ])
    )
    story.append(instruction_container)
    story.append(Spacer(1, 20))
    
    # Get evaluation forms for this documentation
    evaluation_forms = EvaluationForm.query.filter_by(
        evaluation_form_documentation_id=documentation_id
    ).all()

    # Create evaluation table data
    evaluation_data = []

    # Add each evaluation form to the table
    for item in evaluation_forms:
        row = [
            item.evaluation_form_name,  # Just the name in first column
            # For each rating column, show the rating number (5,4,3,2,1)
            "5",  # Extremely Satisfied
            "4",  # Satisfied
            "3",  # Neutral
            "2",  # Dissatisfied
            "1",  # Extremely Dissatisfied
        ]
        evaluation_data.append(row)

    # If no evaluation forms exist, add a placeholder row
    if not evaluation_forms:
        evaluation_data.append(['No evaluation data available', '', '', '', '', ''])
    
    # Calculate overall rating
    total_responses = sum(
        (item.evaluation_form_extremely_satisfied_rating or 0) * 5 +
        (item.evaluation_form_satisfied_rating or 0) * 4 +
        (item.evaluation_form_neutral_rating or 0) * 3 +
        (item.evaluation_form_dissatisfied_rating or 0) * 2 +
        (item.evaluation_form_extremely_dissatisfied_rating or 0)
        for item in evaluation_forms
    )

    total_participants = sum(
        (item.evaluation_form_extremely_satisfied_rating or 0) +
        (item.evaluation_form_satisfied_rating or 0) +
        (item.evaluation_form_neutral_rating or 0) +
        (item.evaluation_form_dissatisfied_rating or 0) +
        (item.evaluation_form_extremely_dissatisfied_rating or 0)
        for item in evaluation_forms
    )

    overall_rating = round(total_responses / total_participants, 2) if total_participants > 0 else 0
    
    # Create evaluation table
    col_widths = [250] + [50] * 5  # First column wider for criteria text
    evaluation_table = Table(evaluation_data, colWidths=col_widths)

    # Initialize table style with basic formatting
    table_style = [
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Left align first column
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),  # Center align rating columns
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]

    # Add blue background only to cells with ratings
    for row_idx, item in enumerate(evaluation_forms):
        if item.evaluation_form_extremely_satisfied_rating:
            table_style.append(('BACKGROUND', (1, row_idx), (1, row_idx), colors.lightblue))
        if item.evaluation_form_satisfied_rating:
            table_style.append(('BACKGROUND', (2, row_idx), (2, row_idx), colors.lightblue))
        if item.evaluation_form_neutral_rating:
            table_style.append(('BACKGROUND', (3, row_idx), (3, row_idx), colors.lightblue))
        if item.evaluation_form_dissatisfied_rating:
            table_style.append(('BACKGROUND', (4, row_idx), (4, row_idx), colors.lightblue))
        if item.evaluation_form_extremely_dissatisfied_rating:
            table_style.append(('BACKGROUND', (5, row_idx), (5, row_idx), colors.lightblue))

    evaluation_table.setStyle(TableStyle(table_style))
    
    story.append(evaluation_table)
    story.append(Spacer(1, 10))
    
    # Create result and comments section using invisible table
    result_text = Paragraph(f"<b>Result: {overall_rating}</b>", cell_style)
    comments_header = Paragraph("<b>Comments/Suggestions:</b>", cell_style)
    comments_intro = Paragraph("Here are some personal comments and suggestion from the participants:", cell_style)
    comments_text = Paragraph(documentation.documentation_comments_suggestions if documentation.documentation_comments_suggestions else "", cell_style)

    footer_data = [
        [result_text],
        [comments_header],
        [comments_intro],
        [comments_text]
    ]

    footer_table = Table(
        footer_data,
        colWidths=[500],
        style=TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ])
    )

    story.append(footer_table)
    story.append(Spacer(1, 20))

    # Create signatory section using invisible table
    prepared_by_text = Paragraph("Prepared by:", cell_style)
    noted_by_text = Paragraph("Noted by:", cell_style)

    # Add spacing for signature
    signature_space = Paragraph("<br/><br/>", cell_style)

    # Get the prepared by user's name and position from the relationship
    if documentation.prepared_by_user:
        preparer_name = f"{documentation.prepared_by_user.users_first_name} {documentation.prepared_by_user.users_last_name}".upper()
        preparer_position = f"{documentation.prepared_by_user.users_student_organization_position if documentation.prepared_by_user.users_student_organization_position else ''}, {documentation.prepared_by_user.student_organization.student_organizations_name if documentation.prepared_by_user.student_organization else ''}"
    else:
        preparer_name = "N/A"
        preparer_position = "N/A"

    # Get the noted by signatory's name and position from the relationship
    if documentation.noted_by_signatory:
        noter_name = f"{documentation.noted_by_signatory.signatory_first_name} {documentation.noted_by_signatory.signatory_last_name}".upper()
        noter_position = f"{documentation.noted_by_signatory.signatory_position}, {documentation.noted_by_signatory.signatory_department}" if documentation.noted_by_signatory.signatory_position else "N/A"
    else:
        noter_name = "N/A"
        noter_position = "N/A"

    # Add names and positions using data from the database
    secretary_name = Paragraph(f"<b>{preparer_name}</b>", cell_style)
    secretary_position = Paragraph(preparer_position, cell_style)

    dean_name = Paragraph(f"<b>{noter_name}</b>", cell_style)
    dean_position = Paragraph(noter_position, cell_style)

    # Create signatory table
    signatory_data = [
        [prepared_by_text, noted_by_text],
        [signature_space, signature_space],
        [secretary_name, dean_name],
        [secretary_position, dean_position]
    ]

    signatory_table = Table(
        signatory_data,
        colWidths=[237, 238],
        style=TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ])
    )
    
    story.append(Spacer(1, 30))  # Add extra space before signatory section
    story.append(signatory_table)
    
    # Add Summary of Attendance Images section
    story.append(PageBreak())
    
    # Define centered header style for Summary of Attendance section
    bold_centered_header_style = ParagraphStyle(
        'CenteredHeader',
        parent=styles['Heading1'],
        fontSize=32,
        alignment=1,  # 1 = Center alignment 
        spaceAfter=30,
        spaceBefore=30,
        fontName='Helvetica-Bold',
        leading=40     # Added leading for line spacing
    )
    
    centered_header_style = ParagraphStyle(
        'CenteredHeader',
        parent=styles['Heading1'],
        fontSize=24,
        alignment=1,  # 1 = Center alignment
        spaceAfter=20,
        spaceBefore=20,
        fontName='Helvetica'
    )

    # Add event details before images
    story.append(Spacer(1, 140))
    
    # Get event name and format date
    event_name = event.events_name.upper()
    event_date = event.events_start_date_and_time.strftime("%A, %B %d, %Y").upper()
    
    # Add to story with appropriate styles
    story.append(Paragraph(event_name, bold_centered_header_style))
    story.append(Paragraph(event_date, centered_header_style))
    
    story.append(Spacer(1, 20))
    story.append(Paragraph("SUMMARY OF ATTENDANCE", centered_header_style))

    # Force page break before images
    story.append(PageBreak())
    
    # Get attendance images from the database
    attendance_images = SummaryOfAttendanceImages.query.filter_by(
        summary_of_attendance_images_documentation_id=documentation_id
    ).all()
    
    # Create an array to store image elements
    attendance_image_elements = []
    
    # Process each attendance image
    for img in attendance_images:
        if img.summary_of_attendance_images_cloudinary_url:
            try:
                # Create image element with same dimensions as evaluation images
                img_elem = Image(
                    img.summary_of_attendance_images_cloudinary_url,
                    width=image_max_width,
                    height=image_max_height,
                    kind='proportional'
                )
                attendance_image_elements.append(img_elem)
                # Add spacing after each image
                attendance_image_elements.append(Spacer(1, 20))
            except Exception as e:
                print(f"Error loading attendance image: {e}")
    
    # Add all attendance images to the story
    for element in attendance_image_elements:
        story.append(element)
    
    story.append(Spacer(1, 20))
    
    # Define centered header style for Summary of Attendance section
    bold_centered_header_style = ParagraphStyle(
        'CenteredHeader',
        parent=styles['Heading1'],
        fontSize=12,
        alignment=1,  # 1 = Center alignment 
        fontName='Helvetica-Bold',
    )
    
    # Add Evaluation Student List section 
    story.append(PageBreak())
    story.append(Paragraph("EVALUATION", bold_centered_header_style))
    story.append(Paragraph(event_name, bold_centered_header_style))
    story.append(Spacer(1, 20))
    
    # Get student names from database
    evaluation_students = EvaluationListOfStudentNames.query.filter_by(
        evaluation_list_of_student_names_documentation_id=documentation_id
    ).all()
    
    # Find longest name to determine width
    max_width = max(
        len(student.evaluation_list_of_student_names_student) 
        for student in evaluation_students
    ) if evaluation_students else 0
    
    # Add padding for comfortable reading (12pt font * max chars + margins)
    col_width = (max_width * 7) + 20  # Approximate width calculation
    
    # Format student names into single column with left alignment
    student_data = []
    for student in evaluation_students:
        student_data.append([Paragraph(student.evaluation_list_of_student_names_student, cell_style)])
    
    # Create table with left alignment
    student_table = Table(student_data, colWidths=[col_width], hAlign='LEFT')
    student_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    story.append(student_table)
    story.append(Spacer(1, 20))
    
    # Add Documentation section
    story.append(PageBreak())
    story.append(Paragraph("PHOTO DOCUMENTATION", bold_centered_header_style))
    story.append(Paragraph(event_name, bold_centered_header_style))
    story.append(Paragraph(event_date, bold_centered_header_style))
    story.append(Spacer(1, 20))
    
    # Get documentation images from database
    documentation_images = EventPhotoDocumentationImages.query.filter_by(
        event_photo_documentation_images_documentation_id=documentation_id
    ).all()
    
    # Process documentation images
    for img in documentation_images:
        if img.event_photo_documentation_images_cloudinary_url:
            try:
                # Create image element with consistent sizing
                img_elem = Image(
                    img.event_photo_documentation_images_cloudinary_url,
                    width=image_max_width,
                    height=image_max_height,
                    kind='proportional'
                )
                story.append(img_elem)
                story.append(Spacer(1, 20))
            except Exception as e:
                print(f"Error loading documentation image: {e}")
    
    story.append(Spacer(1, 20))

    doc.build(story, onFirstPage=header, onLaterPages=header)
    
    buffer.seek(0)
    return send_file(
        buffer,
        download_name=f'Documentation_{documentation_id}.pdf',
        mimetype='application/pdf'
    )

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

@app.route('/generate-financial-report-pdf/<int:financial_report_id>')
@login_required
def generate_financial_report_pdf(financial_report_id):
    # Get financial report with event details
    report = db.session.query(FinancialReports, Events)\
        .outerjoin(Events, FinancialReports.financial_reports_events_id == Events.events_id)\
        .filter(FinancialReports.financial_reports_id == financial_report_id)\
        .first_or_404()
    
    # Get all transactions for this event
    transactions = TransactionHistory.query\
        .filter_by(transaction_events_id=report[0].financial_reports_events_id)\
        .order_by(TransactionHistory.transaction_date)\
        .all()

    buffer = BytesIO()
    
    def header(canvas, doc):
        canvas.saveState()
        
        # Add header images with manual positioning
        # PERPS header - left side
        header_perps = Image('./static/img/HEADER-PERPS.png', width=325, height=75)
        perps_x = doc.leftMargin - 35
        header_perps.drawOn(canvas, perps_x, doc.height + doc.topMargin)
        
        # CCS Logo - center
        header_ccs = Image('./static/img/CCS-LOGO.png', width=35, height=50)
        ccs_x = doc.leftMargin + (doc.width - 35)/2 + 125
        header_ccs.drawOn(canvas, ccs_x, doc.height + doc.topMargin + 15)
        
        # ISO Logo - right side
        header_iso = Image('./static/img/ISO.png', width=100, height=50)
        iso_x = doc.leftMargin + doc.width - 80
        header_iso.drawOn(canvas, iso_x, doc.height + doc.topMargin + 15)
        
        # Add text below ISO logo
        canvas.setFont("Helvetica-Bold", 10)
        text = "College of Computer Studies"
        text_width = canvas.stringWidth(text, "Helvetica-Bold", 10)
        text_x = iso_x + (50 - text_width)/2
        canvas.drawString(text_x, doc.height + doc.topMargin, text)
        
        # Add red line after text
        canvas.setStrokeColorRGB(0x8c/255, 0x04/255, 0x04/255)  # #8c0404
        canvas.setLineWidth(2)
        line_y = doc.height + doc.topMargin - 10
        line_length = 510
        line_start_x = (doc.width - line_length) / 2 + doc.leftMargin
        line_end_x = line_start_x + line_length
        canvas.line(line_start_x - 5, line_y, line_end_x, line_y)
        
        # Add footer
        canvas.setStrokeColorRGB(0, 0, 0)
        canvas.setLineWidth(1)
        footer_y = doc.bottomMargin - 20
        canvas.line(doc.leftMargin, footer_y, doc.leftMargin + doc.width, footer_y)
        
        # Add footer text
        canvas.setFont("Helvetica", 12)
        canvas.drawString(doc.leftMargin, footer_y - 15, "UPHMO-CCS-GEN-912/rev0")
        right_text = "Financial Report"
        right_text_width = canvas.stringWidth(right_text, "Helvetica", 12)
        canvas.drawString(doc.leftMargin + doc.width - right_text_width, footer_y - 15, right_text)
        
        canvas.restoreState()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=100,
        bottomMargin=72
    )
    
    # Create the story (content) for the PDF
    story = []
    styles = getSampleStyleSheet()
    
    # Add title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=1
    )

    story.append(Paragraph("Financial Report Form (FPF)", title_style))
    story.append(Spacer(1, 12))
    
    # Add Activity Details header
    section_header_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Normal'],
        fontSize=12,
        fontName='Helvetica-Bold',
        spaceAfter=10
    )
    story.append(Paragraph("I. Activity Details", section_header_style))
    story.append(Spacer(1, 10))

    # Get event details
    event = Events.query.get(report[0].financial_reports_events_id)
    
    # Get department through DepartmentsEvents
    dept_event = DepartmentsEvents.query.filter_by(events_id=event.events_id).first()
    department = Departments.query.get(dept_event.departments_id) if dept_event else None
    
    # Get activity report form
    activity_report = ActivityReportForms.query.filter_by(
        activity_report_forms_concept_paper_forms_id=event.events_concept_paper_forms_id
    ).first()

    # Format dates and times
    start_datetime = event.events_start_date_and_time
    end_datetime = event.events_end_date_and_time
    
    date_str = f"{start_datetime.strftime('%B %d, %Y')}"
    if start_datetime.date() != end_datetime.date():
        date_str += f" - {end_datetime.strftime('%B %d, %Y')}"
    
    # Remove leading zeros by converting to int
    start_hour = int(start_datetime.strftime('%I'))
    end_hour = int(end_datetime.strftime('%I'))
    time_str = f"{start_hour}:{start_datetime.strftime('%M %p')} - {end_hour}:{end_datetime.strftime('%M %p')}"

    # Create table data with two columns, combining title and content
    table_data = [
        [
            Paragraph("<b>Title of the Activity:</b><br/>" + event.events_name, styles['Normal']),
            Paragraph("<b>Date:</b><br/>" + date_str, styles['Normal'])
        ],
        [
            Paragraph("<b>Nature of the Activity:</b><br/>" + (activity_report.activity_report_forms_nature_of_the_activity if activity_report else ""), styles['Normal']),
            Paragraph("<b>Time:</b><br/>" + time_str, styles['Normal'])
        ],
        [
            Paragraph("<b>College/Department:</b><br/>" + (department.departments_name if department else ""), styles['Normal']),
            Paragraph("<b>Venue:</b><br/>" + event.events_venue, styles['Normal'])
        ]
    ]

    # Create table style
    table_style = TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Changed to TOP alignment for better spacing
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        # Add borders
        ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Add grid lines
        ('BOX', (0, 0), (-1, -1), 1, colors.black),   # Add outer border
    ])

    # Create and add table with two equal columns
    col_widths = [230, 230]  # Adjust these values to match your needs
    table = Table(table_data, colWidths=col_widths)
    table.setStyle(table_style)
    story.append(table)
    story.append(Spacer(1, 20))

    # Add Collection and Expenses header
    story.append(Spacer(1, 20))
    story.append(Paragraph("II. Collection and Expenses", section_header_style))
    story.append(Spacer(1, 10))

    # Get transactions for this event
    transactions = TransactionHistory.query.filter_by(transaction_events_id=event.events_id).all()
    total_expenses = sum(float(t.transaction_total) for t in transactions)
    budget = float(event.events_budget)  # Convert to float first
    remaining_money = budget - total_expenses

    # Create a right-aligned style for totals
    right_aligned_style = ParagraphStyle(
        'RightAligned',
        parent=styles['Normal'],
        alignment=TA_RIGHT
    )

    # Register DejaVu Sans font with the correct path
    font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'DejaVuSans.ttf')
    pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))

    # Create a style that uses the Unicode-compatible font
    amount_style = ParagraphStyle(
        'Amount',
        parent=styles['Normal'],
        fontName='DejaVuSans'
    )

    # Create combined data for a single table
    table_data = [
        # Source of Fund section
        [Paragraph("<b>Source of Fund:</b>", styles['Normal']), Paragraph("", styles['Normal'])],
        [Paragraph("CCS Bankbook", styles['Normal']), Paragraph(f"₱{budget:,.2f}", amount_style)],
        [Paragraph("<b>Total Budget:</b>", right_aligned_style), Paragraph(f"<b>₱{budget:,.2f}</b>", amount_style)],
        ["", [CustomUnderline(180, 0.5, y_offset=8),  # Thin line slightly above
            CustomUnderline(180, 0.5, y_offset=6)]],   # Thick line at base  # Right-aligned total
        
        # Less Expense section
        [Paragraph("<b>Less Expense:</b>", styles['Normal']), Paragraph("", styles['Normal'])],
    ]

    # Add expenses
    for transaction in transactions:
        transaction_total = float(transaction.transaction_total)
        table_data.append([
            Paragraph(transaction.transaction_name, styles['Normal']),
            Paragraph(f"₱{transaction_total:,.2f}", amount_style)
        ])

    # Add empty row before totals
    table_data.append([Paragraph("", styles['Normal']), Paragraph("", styles['Normal'])])

    table_data.extend([
        [Paragraph("<b>Total Expenses:</b>", right_aligned_style), 
            Paragraph(f"<b>₱{total_expenses:,.2f}</b>", amount_style)],
        ["", [CustomUnderline(180, 0.5, y_offset=8),  # Thin line slightly above
            CustomUnderline(180, 0.5, y_offset=6)]],   # Thick line at base
        [Paragraph("", styles['Normal']), Paragraph("", styles['Normal'])],  # Empty row for spacing
        [Paragraph("<b>Total Remaining Money:</b>", styles['Normal']), 
            Paragraph(f"<b>₱{remaining_money:,.2f}</b>", amount_style)]
    ])

    # Create table style with selective borders
    table_style = TableStyle([
        # General alignment
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),  # Right align all amounts
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        
        # Padding
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        
        # Add line above total expenses (assuming last two rows are totals)
        ('LINEABOVE', (0, -4), (-1, -4), 1, colors.black),
        
        # Add more space after headers
        ('TOPPADDING', (0, 4), (-1, 4), 8),  # Adjusted for new row
        
        # Add outer border
        ('BOX', (0, 0), (-1, -1), 1, colors.black),  # Add outer border to entire table
        
        # Add line above Total Budget row (now row 2)
        ('LINEABOVE', (0, 2), (-1, 2), 1, colors.black),
        
        # Add line above Total Remaining Money (last row)
        ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
    ])

    # Create and add table
    financial_table = Table(table_data, colWidths=[340, 125])
    financial_table.setStyle(table_style)
    story.append(financial_table)

    # Add signature section after the financial table
    story.append(Spacer(1, 30))  # Add space between table and signatures

    # Create styles for signature sections
    signature_style = ParagraphStyle(
        'Signature',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=30  # Space between signature blocks
    )

    name_style = ParagraphStyle(
        'SignatureName',
        parent=styles['Normal'],
        fontSize=12,
        fontName='Helvetica-Bold'
    )

    position_style = ParagraphStyle(
        'Position',
        parent=styles['Normal'],
        fontSize=12
    )

    # Get user data for each position from Users table
    auditor = Users.query.get(report[0].financial_reports_audited_and_prepared_by)
    treasurer = Users.query.get(report[0].financial_reports_noted_by)
    president = Users.query.get(report[0].financial_reports_recommending_approval_by)
    
    # Get adviser data from Signatories table
    adviser = Signatories.query.get(report[0].financial_reports_approved_by)

    # Get organization data from the first user's student organization
    organization = auditor.student_organization

    # Add signature blocks with dynamic data
    # Auditor section
    story.append(Paragraph("AUDITED AND PREPARED BY:", signature_style))
    story.append(Paragraph(f"{auditor.users_first_name} {auditor.users_middle_name if auditor.users_middle_name else ''} {auditor.users_last_name}", name_style))
    story.append(Paragraph(f"{auditor.users_student_organization_position}, {organization.student_organizations_name}", position_style))
    story.append(Spacer(1, 30))

    # Treasurer section
    story.append(Paragraph("NOTED BY:", signature_style))
    story.append(Paragraph(f"{treasurer.users_first_name} {treasurer.users_middle_name if treasurer.users_middle_name else ''} {treasurer.users_last_name}", name_style))
    story.append(Paragraph(f"{treasurer.users_student_organization_position}, {organization.student_organizations_name}", position_style))
    story.append(Spacer(1, 30))

    # President section
    story.append(Paragraph("RECOMMENDING APPROVAL BY:", signature_style))
    story.append(Paragraph(f"{president.users_first_name} {president.users_middle_name if president.users_middle_name else ''} {president.users_last_name}", name_style))
    story.append(Paragraph(f"{president.users_student_organization_position}, {organization.student_organizations_name}", position_style))
    story.append(Spacer(1, 30))

    # Adviser section
    story.append(Paragraph("APPROVED BY:", signature_style))
    story.append(Paragraph(f"{adviser.signatory_title} {adviser.signatory_first_name} {adviser.signatory_middle_name if adviser.signatory_middle_name else ''} {adviser.signatory_last_name}", name_style))
    story.append(Paragraph(f"Adviser, {organization.student_organizations_name}", position_style))

    # Add a page break before the receipt
    story.append(PageBreak())

    # Add the receipt image if it exists
    if transactions:       
        # Add each receipt image
        for idx, transaction in enumerate(transactions, 1):
            if transaction.transaction_receipt_cloudinary_url:
                # Add receipt number if there are multiple receipts
                if len(transactions) > 1:
                    story.append(Paragraph(f"Receipt {idx}", ParagraphStyle(
                        'ReceiptNumber',
                        parent=styles['Normal'],
                        fontSize=12,
                        alignment=1,
                        spaceAfter=10
                    )))
                
                # Get the image from Cloudinary URL
                receipt_image = Image(transaction.transaction_receipt_cloudinary_url)
                
                # Calculate available space (leaving margins)
                available_width = letter[0] - 2*inch  # Letter width minus 2-inch margins
                available_height = letter[1] - 4*inch  # Letter height minus 4-inch margins
                
                # Calculate scaling ratios for both width and height
                width_ratio = available_width / receipt_image.imageWidth
                height_ratio = available_height / receipt_image.imageHeight
                
                # Use the smaller ratio to ensure image fits both dimensions
                scale_ratio = min(width_ratio, height_ratio)
                
                # Apply the scaling
                receipt_image.drawWidth = receipt_image.imageWidth * scale_ratio
                receipt_image.drawHeight = receipt_image.imageHeight * scale_ratio
                
                story.append(receipt_image)
                
                # Add space between receipts
                if idx < len(transactions):
                    story.append(Spacer(1, 30))
    else:
        story.append(Paragraph("Transaction Receipts", receipt_title_style))
        # Add a message if no receipts are available
        no_receipt_style = ParagraphStyle(
            'NoReceipt',
            parent=styles['Normal'],
            fontSize=12,
            alignment=1  # Center alignment
        )
        story.append(Paragraph("No transaction receipts available", no_receipt_style))
    
    doc.build(story, onFirstPage=header, onLaterPages=header)
    
    buffer.seek(0)
    return send_file(
        buffer,
        download_name=f'Financial_Report_{financial_report_id}.pdf',
        mimetype='application/pdf'
    )

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
        # Retrieve and delete related BoardResolutionsStudentSignatories entries
        related_signatories = BoardResolutionsStudentSignatories.query.filter_by(board_resolutions_id=resolution_id).all()
        for signatory in related_signatories:
            db.session.delete(signatory)
        
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

@app.route('/generate-description', methods=['POST'])
@login_required
def generate_description():
    if not request.is_json:
        return make_response(jsonify({'error': 'Content-Type must be application/json'}), 400)
        
    try:
        data = request.json
        if not data:
            return make_response(jsonify({'error': 'No JSON data provided'}), 400)
            
        event_name = data.get('event_name')
        title = data.get('title')
        date = data.get('date')
        total_amount = data.get('total_amount')
        
        if not event_name or not title:
            return make_response(jsonify({'error': 'Missing event_name or title'}), 400)
        
        app.logger.info(f"Generating description for event: {event_name}, title: {title}, date: {date}, amount: {total_amount}")
        
        # Convert date to proper format
        try:
            if date:
                date_obj = datetime.strptime(date, '%Y-%m-%dT%H:%M')
                formatted_date = f"Signed this {date_obj.day}th of {date_obj.strftime('%B')} in the name of the Lord Jesus Christ {date_obj.year}"
            else:
                formatted_date = "Signed this 13th of May in the name of the Lord Jesus Christ 2024"  # Default date
        except ValueError as e:
            app.logger.error(f"Date parsing error: {str(e)}")
            formatted_date = "Signed this 13th of May in the name of the Lord Jesus Christ 2024"  # Default date
        
        # Format amount with commas and two decimal places if provided
        formatted_amount = f"₱{float(total_amount):,.2f}" if total_amount else "the specified amount"
        
        prompt = f"""Generate a formal description for a proposed board resolution with the following details:
                Event: {event_name}
                Title: {title}
                Total Amount: {formatted_amount}
                
                Requirements:
                1. Use clear, formal language in present tense
                2. Focus only on describing the purpose, scope, and proposed decisions
                3. Keep it concise and straightforward
                4. Do not include any signatories
                5. Do not use any text formatting
                6. Do not include the board resolution title
                7. Do not include any resolution numbers
                8. Do not use 'WHEREAS' statements
                9. Begin with 'The College of Computer Studies Student Council proposes to'
                10. Use language that indicates the resolution is pending approval (e.g., 'seeks to allocate', 'proposes to implement')
                11. Explicitly mention the total amount in the main paragraph using the phrase 'with a proposed budget of {formatted_amount}'
                12. Include a financial breakdown section with the following format:
                    Proposed Financial Breakdown:
                    [List all relevant expense categories based on the event type and purpose]
                    Proposed Total Amount: {formatted_amount}
                13. The description should be 1 paragraph only, followed by the financial breakdown
                14. End with exactly this date: '{formatted_date}'
        
                Note: Create a comprehensive list of expense categories appropriate for this specific event"""
        
        app.logger.info("Sending request to Gemini API")
        try:
            response = model.generate_content(
                prompt,
                safety_settings=safety_settings
            )
            app.logger.info("Received response from Gemini API")
            
            if response and hasattr(response, 'text'):
                description = response.text.strip()
                app.logger.info(f"Generated description: {description[:100]}...")
                return make_response(jsonify({'description': description}), 200)
            else:
                app.logger.error("Invalid response format from Gemini API")
                return make_response(jsonify({'error': 'Invalid response from AI model'}), 500)
                
        except Exception as gemini_error:
            app.logger.error(f"Gemini API error: {str(gemini_error)}")
            return make_response(jsonify({'error': f'AI generation error: {str(gemini_error)}'}), 500)
            
    except Exception as e:
        app.logger.error(f"Error generating description: {str(e)}")
        return make_response(jsonify({'error': str(e)}), 500)

@app.route('/generate-board-resolution-pdf/<int:resolution_id>')
@login_required
def generate_board_resolution_pdf(resolution_id):
    # Get the resolution data
    resolution = BoardResolutions.query.get_or_404(resolution_id)
    
    # Get prepared by and approved by users
    prepared_by = Users.query.get(resolution.board_resolutions_prepared_by)
    approved_by = Signatories.query.get(resolution.board_resolutions_approved_by)
    
    # Get student signatories
    student_signatories = db.session.query(
        BoardResolutionsStudentSignatories, 
        Users,
        StudentOrganizations
    )\
        .join(Users, BoardResolutionsStudentSignatories.board_resolutions_users_id == Users.users_id)\
        .join(StudentOrganizations, Users.users_student_organization == StudentOrganizations.student_organizations_id)\
        .filter(BoardResolutionsStudentSignatories.board_resolutions_id == resolution_id)\
        .order_by(StudentOrganizations.student_organizations_name)\
        .all()
    
    # Create BytesIO buffer for PDF
    buffer = BytesIO()
    
    def header(canvas, doc):
        canvas.saveState()
        
        # Add header images with manual positioning
        # PERPS header - left side
        header_perps = Image('./static/img/HEADER-PERPS.png', width=325, height=75)
        perps_x = doc.leftMargin - 35
        header_perps.drawOn(canvas, perps_x, doc.height + doc.topMargin)
        
        # CCS Logo - center
        header_ccs = Image('./static/img/CCS-LOGO.png', width=35, height=50)
        ccs_x = doc.leftMargin + (doc.width - 35)/2 + 125
        header_ccs.drawOn(canvas, ccs_x, doc.height + doc.topMargin + 15)
        
        # ISO Logo - right side
        header_iso = Image('./static/img/ISO.png', width=100, height=50)
        iso_x = doc.leftMargin + doc.width - 80
        header_iso.drawOn(canvas, iso_x, doc.height + doc.topMargin + 15)
        
        # Add text below ISO logo
        canvas.setFont("Helvetica-Bold", 10)
        text = "College of Computer Studies"
        text_width = canvas.stringWidth(text, "Helvetica-Bold", 10)
        text_x = iso_x + (50 - text_width)/2
        canvas.drawString(text_x, doc.height + doc.topMargin, text)
        
        # Add red line after text
        canvas.setStrokeColorRGB(0x8c/255, 0x04/255, 0x04/255)  # #8c0404
        canvas.setLineWidth(2)
        line_y = doc.height + doc.topMargin - 10
        line_length = 510
        line_start_x = (doc.width - line_length) / 2 + doc.leftMargin
        line_end_x = line_start_x + line_length
        canvas.line(line_start_x - 5, line_y, line_end_x, line_y)
        
        # Add "Continuation of the Board Resolution" text if not the first page
        if doc.page > 1:  # Check if this is not the first page
            canvas.setFont("Helvetica", 12)
            continuation_text = "Continuation of the Board Resolution"
            # Use doc.leftMargin for left alignment
            text_x = doc.leftMargin
            # Increase space after the text by adjusting the y-coordinate (from -30 to -40)
            canvas.drawString(text_x, doc.height + doc.topMargin - 30, continuation_text)

        # Add footer
        canvas.setStrokeColorRGB(0, 0, 0)
        canvas.setLineWidth(1)
        footer_y = doc.bottomMargin - 20
        canvas.line(doc.leftMargin, footer_y, doc.leftMargin + doc.width, footer_y)
        
        # Add footer text
        canvas.setFont("Helvetica", 12)
        # Left aligned text
        canvas.drawString(doc.leftMargin, footer_y - 15, "UPHMO-CCS-GEN-912/rev0")
        # Right aligned text
        right_text = "Board Resolution"
        right_text_width = canvas.stringWidth(right_text, "Helvetica", 12)
        canvas.drawString(doc.leftMargin + doc.width - right_text_width, footer_y - 15, right_text)
        
        canvas.restoreState()

    # Create the PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=110,
        bottomMargin=72
    )
    
    # Create the story (content) for the PDF
    story = []
    styles = getSampleStyleSheet()
    
    # Add title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=12,
        alignment=1,
        spaceBefore=5,
        spaceAfter=-15
    )

    # Add the academic year subtitle
    academic_year_style = ParagraphStyle(
        'AcademicYear',
        parent=styles['Heading1'],
        fontSize=11,
        alignment=1,
        spaceAfter=20
    )

    # Add resolution title style
    resolution_style = ParagraphStyle(
        'Resolution',
        parent=styles['Heading1'],
        fontSize=12,
        alignment=1,
        spaceAfter=20
    )

    story.append(Paragraph("College of Computer Studies Council", title_style))
    story.append(Paragraph(f"A.Y. {resolution.board_resolutions_academic_year}", academic_year_style))
    story.append(Paragraph("Resolution", resolution_style))
    
    # Create a style for the main content
    content_style = ParagraphStyle(
        'Content',
        parent=styles['Normal'],
        fontSize=12,
        leading=14,
        alignment=4,  # Justified alignment
        firstLineIndent=36  # Add indentation for paragraph
    )

    # Add resolution details
    story.append(Paragraph(resolution.board_resolutions_description, content_style))
    story.append(Spacer(1, 15))
    
    # Add signatories section
    signature_style = ParagraphStyle(
        'Signature',
        parent=styles['Normal'],
        fontSize=12,
        alignment=0,
        spaceAfter=20
    )
    
    # Student signatories
    # Group signatories by organization
    org_signatories = {}
    for signatory, user, org in student_signatories:
        if org.student_organizations_name not in org_signatories:
            org_signatories[org.student_organizations_name] = []
        org_signatories[org.student_organizations_name].append((signatory, user))

    # Create styles for organization headers and signatures
    org_header_style = ParagraphStyle(
        'OrgHeader',
        parent=styles['Normal'],
        fontSize=12,
        alignment=0,
        fontName='Helvetica-Bold',
        spaceAfter=10
    )

    # Organization acronyms mapping
    org_acronyms = {
        'College of Computer Studies - Student Council': 'CCSC',
        'Junior Philippine Computer Society': 'JPCS'
    }

    # Add grouped signatories to the story
    for org_name, signatories in org_signatories.items():
        # Add organization header
        story.append(Paragraph(org_name, org_header_style))
        
        # Add signatories for this organization
        for signatory, user in signatories:
            # Make name bold using <b> tag
            signature_text = f"<b>{user.users_first_name} {user.users_last_name}</b>"
            if user.users_student_organization_position:  # Add position if available
                # Get organization acronym, default to org_name if not in mapping
                org_acronym = org_acronyms.get(org_name, org_name)
                signature_text += f"<br/><i>{org_acronym}, {user.users_student_organization_position}</i>"
            
            story.append(Paragraph(signature_text, signature_style))
            story.append(Spacer(1, 5))
    
    # Prepared by
    story.append(Paragraph("Prepared by:", signature_style))
    prepared_by_text = f"<b>{prepared_by.users_first_name} {prepared_by.users_last_name}</b>"
    if prepared_by.users_student_organization_position:
        org_acronym = org_acronyms.get('College of Computer Studies - Student Council', 'CCSC')
        prepared_by_text += f"<br/><i>{org_acronym}, {prepared_by.users_student_organization_position}</i>"
    story.append(Paragraph(prepared_by_text, signature_style))
    story.append(Spacer(1, 20))

    # Approved by
    story.append(Paragraph("Approved by:", signature_style))
    approved_by_text = f"<b>{approved_by.signatory_first_name} {approved_by.signatory_last_name}</b>"
    approved_by_text += "<br/><i>Adviser, College of Computer Studies - Student Council</i>"
    story.append(Paragraph(approved_by_text, signature_style))

    # Build the PDF
    doc.build(story, onFirstPage=header, onLaterPages=header)
    
    # Prepare the response
    buffer.seek(0)
    return send_file(
        buffer,
        download_name=f'Board_Resolution_{resolution_id}.pdf',
        mimetype='application/pdf'
    )

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

@app.route('/generate-mom-pdf/<int:minutes_of_the_meeting_id>')
@login_required
def generate_mom_pdf(minutes_of_the_meeting_id):
    # Get the meeting data with presiding officer
    meeting = db.session.query(MinutesOfTheMeeting, Users.users_first_name, Users.users_last_name)\
        .join(Users, MinutesOfTheMeeting.minutes_of_the_meeting_presiding_officer == Users.users_id)\
        .filter(MinutesOfTheMeeting.minutes_of_the_meeting_id == minutes_of_the_meeting_id)\
        .first_or_404()
    
    # Get attendees
    attendees = db.session.query(MinutesOfTheMeetingAttendees, Users)\
        .join(Users, MinutesOfTheMeetingAttendees.users_id == Users.users_id)\
        .filter(MinutesOfTheMeetingAttendees.minutes_of_the_meeting_id == minutes_of_the_meeting_id)\
        .all()
    
    # Get photo documentation
    photos = MinutesOfTheMeetingPhotoDocumentation.query\
        .filter_by(minutes_of_the_meeting_id=minutes_of_the_meeting_id)\
        .all()
    
    # Get prepared by, approved by, and noted by users
    prepared_by = Users.query.get(meeting[0].minutes_of_the_meeting_prepared_by)
    approved_by = Users.query.get(meeting[0].minutes_of_the_meeting_approved_by)
    noted_by = Signatories.query.get(meeting[0].minutes_of_the_meeting_noted_by)
    
    # Create BytesIO buffer to receive PDF data
    buffer = BytesIO()

    # Create the PDF object
    class NumberedCanvas(canvas.Canvas):
        def __init__(self, *args, **kwargs):
            canvas.Canvas.__init__(self, *args, **kwargs)
            self._saved_page_states = []
            self._page_count = 0

        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._page_count += 1
            canvas.Canvas.showPage(self)

        def save(self):
            """Add page info to each page (page x of y)"""
            num_pages = self._page_count
            for state in self._saved_page_states:
                self.__dict__.update(state)
                self.draw_page_number(num_pages)
                canvas.Canvas.showPage(self)
            canvas.Canvas.save(self)

        def draw_page_number(self, page_count):
            self._doc.page_count = page_count

    # Create the PDF object using ReportLab
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=100,
        bottomMargin=72
    )
    doc.page_count = 3  # Initialize page count

    def header(canvas, doc):
        canvas.saveState()
        
        # Add header images with manual positioning
        # PERPS header - left side
        header_perps = Image('./static/img/HEADER-PERPS.png', width=325, height=75)
        perps_x = doc.leftMargin - 35
        header_perps.drawOn(canvas, perps_x, doc.height + doc.topMargin)
        
        # CCS Logo - center
        header_ccs = Image('./static/img/CCS-LOGO.png', width=35, height=50)
        # Calculate center position: leftMargin + (pageWidth - imageWidth)/2
        ccs_x = doc.leftMargin + (doc.width - 35)/2 + 125
        header_ccs.drawOn(canvas, ccs_x, doc.height + doc.topMargin + 15)
        
        # ISO Logo - right side
        header_iso = Image('./static/img/ISO.png', width=100, height=50)
        # Calculate right position: leftMargin + pageWidth - imageWidth
        iso_x = doc.leftMargin + doc.width - 80
        header_iso.drawOn(canvas, iso_x, doc.height + doc.topMargin + 15)
        
        # Add text below ISO logo
        canvas.setFont("Helvetica-Bold", 10)
        text = "College of Computer Studies"
        text_width = canvas.stringWidth(text, "Helvetica-Bold", 10)
        # Center the text below the ISO logo
        text_x = iso_x + (50 - text_width)/2
        canvas.drawString(text_x, doc.height + doc.topMargin, text)
        
        # Add red line after text
        canvas.setStrokeColorRGB(0x8c/255, 0x04/255, 0x04/255)  # #8c0404
        canvas.setLineWidth(2)
        line_y = doc.height + doc.topMargin - 10
        line_length = 510  # Adjust this value to control line length
        # Calculate start and end points to center the line
        line_start_x = (doc.width - line_length) / 2 + doc.leftMargin
        line_end_x = line_start_x + line_length
        canvas.line(line_start_x - 5, line_y, line_end_x, line_y)
        
        # Add footer
        # Draw black line
        canvas.setStrokeColorRGB(0, 0, 0)  # Black color
        canvas.setLineWidth(1)
        footer_y = doc.bottomMargin - 20  # Position the line above the footer text
        canvas.line(doc.leftMargin, footer_y, doc.leftMargin + doc.width, footer_y)
        
        # Add footer text
        canvas.setFont("Helvetica", 12)
        
        # Left aligned text
        canvas.drawString(doc.leftMargin, footer_y - 15, "UPHMO-CCS-GEN-912/rev0")
        
        # Right aligned text with page numbers
        page_text = f"Council Meeting | Page {canvas.getPageNumber()} of {doc.page_count}"
        text_width = canvas.stringWidth(page_text, "Helvetica", 12)
        canvas.drawString(doc.leftMargin + doc.width - text_width, footer_y - 15, page_text)
        
        canvas.restoreState()
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Get styles
    styles = getSampleStyleSheet()
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        alignment=1  # 1 is for center alignment
    )
    
    # Custom style for centered sections
    centered_section_style = ParagraphStyle(
        'CenteredSection',
        parent=styles['Normal'],
        spaceAfter=6,
        fontSize=12,
        textColor=colors.black,
        alignment=1  # 1 is for center alignment
    )

    # Custom style for sections
    section_style = ParagraphStyle(
        'SectionStyle',
        parent=styles['Normal'],
        spaceAfter=6,
        leftIndent=0,
        fontSize=12,
        textColor=colors.black,
    )
    
    # Add meeting details
    meeting_data = meeting[0]

    # Add title
    elements.append(Paragraph(f'Council Meeting SY {meeting_data.minutes_of_the_meeting_academic_year}', title_style))
    
    elements.append(Paragraph(
        f'Date & Time: {meeting_data.minutes_of_the_meeting_date.strftime("%B %d, %Y, %I:%M %p")}' + 
        (f' - {meeting_data.minutes_of_the_meeting_adjourned.strftime("%I:%M %p")}' if meeting_data.minutes_of_the_meeting_adjourned else ''),
        centered_section_style
    ))
    elements.append(Spacer(1, 12))

    # Presiding Officer
    elements.append(Paragraph(
        f'Presiding Officer: {meeting[1]} {meeting[2]}',
        section_style
    ))

    # Add Attendees section
    elements.append(Paragraph('Attendees', heading_style))
    for attendee in attendees:
        elements.append(Paragraph(
            f'• {attendee[1].users_first_name} {attendee[1].users_last_name} - {attendee[1].users_student_organization_position}',
            section_style
        ))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f'Agenda:', heading_style))
    elements.append(Paragraph(meeting_data.minutes_of_the_meeting_agenda, section_style))
    elements.append(Spacer(1, 12))
    elements.append(HRFlowable(
        width="100%",
        thickness=1,
        color=colors.black,
        spaceBefore=6,
        spaceAfter=6
    ))
    
    # Split notes into sections
    notes = meeting_data.minutes_of_the_meeting_notes
    
    # Helper function to extract section content
    def extract_section(text, section_name):
        pattern = f"{section_name}:(.*?)(?=(?:Summary:|Key Discussion Points:|Action Items:|Next Steps:|$))"
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else ""
    
    # Helper function to split numbered points
    def format_numbered_points(text):
        # Split text into lines and process each line
        lines = text.split('\n')
        formatted_lines = []
        
        current_point = ""
        for line in lines:
            line = line.strip()
            if line:
                # Check for numbered format (e.g., "2.1", "3.2", etc.)
                if re.match(r'^\d+\.\d+\s', line):
                    # If we have a previous point, add it
                    if current_point:
                        formatted_lines.append(Paragraph(current_point, section_style))
                    current_point = line
                else:
                    # If it's a continuation of the current point
                    if current_point:
                        current_point += " " + line
                    else:
                        current_point = line
        
        # Add the last point if exists
        if current_point:
            formatted_lines.append(Paragraph(current_point, section_style))
            formatted_lines.append(Spacer(1, 6))
        
        return formatted_lines
    
    # Extract each section
    summary = extract_section(notes, "Summary")
    key_points = extract_section(notes, "Key Discussion Points")
    action_items = extract_section(notes, "Action Items")
    next_steps = extract_section(notes, "Next Steps")
    
    # Add Summary
    if summary:
        elements.append(Paragraph("Summary", heading_style))
        elements.extend(format_numbered_points(summary))
        elements.append(Spacer(1, 12))
    
    # Add Key Discussion Points
    if key_points:
        elements.append(Paragraph("Key Discussion Points", heading_style))
        elements.extend(format_numbered_points(key_points))
        elements.append(Spacer(1, 12))
    
    # Add Action Items
    if action_items:
        elements.append(Paragraph("Action Items", heading_style))
        elements.extend(format_numbered_points(action_items))
        elements.append(Spacer(1, 12))
    
    # Add Next Steps
    if next_steps:
        elements.append(Paragraph("Next Steps", heading_style))
        elements.extend(format_numbered_points(next_steps))
        elements.append(Spacer(1, 12))
    
    if meeting_data.minutes_of_the_meeting_adjourned:
        elements.append(Paragraph(f'Meeting Adjourned: {meeting_data.minutes_of_the_meeting_adjourned.strftime("%I:%M %p")}', section_style))
    elements.append(Spacer(1, 12))

    # Get the student organizations for prepared_by and approved_by
    prepared_by_org = None
    approved_by_org = None
    
    if prepared_by:
        prepared_by_org = StudentOrganizations.query.get(prepared_by.users_student_organization)
    if approved_by:
        approved_by_org = StudentOrganizations.query.get(approved_by.users_student_organization)

    # Create data for the signatures table
    signature_data = []
    
    # Prepare the signature blocks
    if prepared_by:
        prepared_block = [
            Paragraph('Prepared By:', heading_style),
            Spacer(1, 20),
            Paragraph(f'{prepared_by.users_first_name} {prepared_by.users_last_name}', section_style),
            Paragraph(f'{prepared_by.users_student_organization_position}, {prepared_by_org.student_organizations_name if prepared_by_org else ""}', section_style)
        ]
    else:
        prepared_block = []

    if approved_by:
        approved_block = [
            Paragraph('Approved By:', heading_style),
            Spacer(1, 20),
            Paragraph(f'{approved_by.users_first_name} {approved_by.users_last_name}', section_style),
            Paragraph(f'{approved_by.users_student_organization_position}, {approved_by_org.student_organizations_name if approved_by_org else ""}', section_style)
        ]
    else:
        approved_block = []

    # Create table with signatures side by side
    if prepared_by or approved_by:
        signature_table = Table(
            [[prepared_block, approved_block]],
            colWidths=[doc.width/2]*2,  # Equal width columns without padding
            spaceAfter=30
        )
        
        # Add table style
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0)
        ]))
        
        elements.append(signature_table)
    
    # Noted By
    if noted_by:
        noted_block = [
            Paragraph('Noted By:', heading_style),
            Spacer(1, 20),
            Paragraph(f'{noted_by.signatory_first_name} {noted_by.signatory_last_name}', section_style),
            Paragraph(f'{noted_by.signatory_position}, {noted_by.signatory_department}', section_style)
        ]
        
        noted_table = Table(
            [[noted_block]],
            colWidths=[doc.width/2],  # Use half width for consistent sizing
            spaceAfter=30
        )
        
        # Add table style for centering
        noted_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0)
        ]))
        
        elements.append(noted_table)
    
    # Add Photo Documentation section if there are photos
    if photos:
        elements.append(Paragraph('Photo Documentation', heading_style))
        elements.append(Spacer(1, 12))
        
        for photo in photos:
            try:
                # Download image from Cloudinary URL
                response = requests.get(photo.minutes_of_the_meeting_photo_documentation_cloudinary_url)
                if response.status_code == 200:
                    # Use BytesIO instead of temporary file
                    image_data = BytesIO(response.content)
                    img = Image(image_data, width=400, height=300, kind='proportional')
                    elements.append(img)
                    elements.append(Spacer(1, 12))
                    
            except Exception as e:
                # If image fails to load, fall back to URL
                elements.append(Paragraph(
                    f'• {photo.minutes_of_the_meeting_photo_documentation_cloudinary_url}',
                    section_style
                ))
        elements.append(Spacer(1, 12))

    # Build PDF with header on all pages
    doc.build(elements, onFirstPage=header, onLaterPages=header)
    
    # Reset buffer position
    buffer.seek(0)
    
    # Return the PDF as a download
    return send_file(
        buffer,
        download_name=f'minutes-of-meeting-{meeting_data.minutes_of_the_meeting_id}.pdf',
        mimetype='application/pdf'
    )

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

        # Process meeting recording with Gemini Pro if provided
        meeting_recording = request.files.get('meeting-recording')
        if meeting_recording:
            filename = meeting_recording.filename.lower()
            if not (filename.endswith(('.mp4', '.avi', '.mov', '.mp3', '.wav', '.m4a'))):
                flash('Invalid file format. Please upload a video or audio file.', 'error')
                return redirect(request.url)

            try:
                notes = ''
                # Save file temporarily
                temp_path = os.path.join(tempfile.gettempdir(), secure_filename(filename))
                meeting_recording.save(temp_path)

                # Use Gemini's File API to upload
                uploaded_file = genai.upload_file(temp_path)

                # Wait for file to be ready (add a small delay)
                import time
                time.sleep(10)  # Wait 10 seconds for file processing

                # Create prompt for Gemini
                prompt = f"""Please analyze this meeting transcript and provide a response with only:
                1. Summary:
                   Use a single paragraph for the summary
                2. Key Discussion Points:
                   Use sub-numbering (2.1, 2.2, etc.) for each distinct point
                3. Action Items:
                   Use sub-numbering (3.1, 3.2, etc.) for each action item
                4. Next Steps:
                   Use sub-numbering (4.1, 4.2, etc.) for each step

                No text formatting, markdown, or other formatting. No additional analysis or comments."""

                # Process with Gemini Flash
                response = model_gemini_flash.generate_content([
                    uploaded_file,
                    prompt
                ])
                
                # Combine AI-generated notes with user input
                ai_generated_notes = response.text
                notes = f"{notes}\n\nAI-Generated Summary:\n{ai_generated_notes}" if notes else ai_generated_notes

            except Exception as e:
                flash(f'Error processing recording with AI: {str(e)}', 'error')
                return redirect(request.url)

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

    student_org = StudentOrganizations.query.get(current_user.users_student_organization)
    student_org_name = student_org.student_organizations_name if student_org else "Unknown Organization"
    org_dict = {org.student_organizations_id: org.student_organizations_name for org in student_organizations}

    return render_template('add-minutes-of-the-meeting.html', academic_years=academic_years, users=users, signatories=signatories, student_organizations=student_organizations, student_org_name=student_org_name, current_user=current_user, org_dict=org_dict)

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