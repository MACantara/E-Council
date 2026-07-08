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
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping

import cloudinary
import cloudinary.uploader
import cloudinary.api
from cloudinary.exceptions import Error as CloudinaryError
from cloudinary.utils import cloudinary_url

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import tempfile
from string import ascii_lowercase

import pandas as pd

# Load environment variables from .env file
load_dotenv()

# Import new configuration and utilities
from config import DatabaseConfig, EmailConfig, CloudinaryConfig, AIConfig
from utils import register_filters, register_error_handlers
from utils.helpers import get_distinct_academic_years, get_concept_papers, safe_decimal_conversion, allowed_image_file
from utils.processing import process_tally_items, process_evaluation_forms
from utils.auth import load_user, unauthorized
from utils.email import (
    send_verification_email,
    send_reset_password_email,
    send_password_change_notification_email,
    send_email_change_notification,
    send_email_change_confirmation,
    send_new_email_verification,
    send_account_deletion_notification_email,
    send_invite_email
)

# Import blueprints
from routes.dashboard import dashboard_bp

# Import all models from models package
from models import (
    db,
    Departments,
    StudentOrganizations,
    Users,
    EmailVerification,
    PasswordReset,
    LoginAttempts,
    Events,
    DepartmentsEvents,
    EventInvitations,
    TransactionHistory,
    ConceptPaperForms,
    ObjectivesOfTheActivity,
    LearningOutcomes,
    ExcuseLetterForms,
    ActivityReportForms,
    Documentation,
    TallyItems,
    ResultsOfTheEvaluationImages,
    EvaluationForm,
    SummaryOfAttendanceImages,
    EvaluationListOfStudentNames,
    EventPhotoDocumentationImages,
    ActivityStrengths,
    ActivityWeaknesses,
    ActivityRecommendations,
    FinancialReports,
    BoardResolutions,
    BoardResolutionsStudentSignatories,
    MinutesOfTheMeeting,
    Signatories,
    MinutesOfTheMeetingPhotoDocumentation,
    MinutesOfTheMeetingAttendees
)

# Flask Configuration using new config classes
app = Flask(__name__, template_folder="templates")

# Use configuration classes
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = DatabaseConfig.SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = DatabaseConfig.SQLALCHEMY_TRACK_MODIFICATIONS
app.config["SQLALCHEMY_ECHO"] = DatabaseConfig.SQLALCHEMY_ECHO

# Flask Mail Configuration using EmailConfig
app.config["MAIL_SERVER"] = EmailConfig.MAIL_SERVER
app.config["MAIL_PORT"] = EmailConfig.MAIL_PORT
app.config["MAIL_USE_TLS"] = EmailConfig.MAIL_USE_TLS
app.config["MAIL_USE_SSL"] = EmailConfig.MAIL_USE_SSL
app.config["MAIL_USERNAME"] = EmailConfig.MAIL_USERNAME
app.config["MAIL_PASSWORD"] = EmailConfig.MAIL_PASSWORD
app.config["MAIL_DEFAULT_SENDER"] = EmailConfig.MAIL_DEFAULT_SENDER

s = URLSafeTimedSerializer(app.config["SECRET_KEY"])

db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"

# Cloudinary Configuration using CloudinaryConfig
cloudinary.config(
    cloud_name=CloudinaryConfig.CLOUDINARY_CLOUD_NAME,
    api_key=CloudinaryConfig.CLOUDINARY_API_KEY,
    api_secret=CloudinaryConfig.CLOUDINARY_API_SECRET,
    secure=CloudinaryConfig.CLOUDINARY_SECURE
)

# Gemini AI Configuration using AIConfig
genai.configure(api_key=AIConfig.GOOGLE_GEMINI_AI_API_KEY)
model = genai.GenerativeModel(AIConfig.GEMINI_MODEL)
model_gemini_flash = genai.GenerativeModel(AIConfig.GEMINI_MODEL)

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

# Use imported auth functions
login_manager.user_loader(load_user)
login_manager.unauthorized_handler(unauthorized)

# Note: Database models are now imported from models package
# All 36 models have been extracted to models/ directory

# Routes

# Register custom Jinja2 filters and error handlers from utils
register_filters(app)
register_error_handlers(app)

# Register blueprints
from routes.account import account_bp
from routes.dashboard import dashboard_bp
from routes.documentation import documentation_bp
from routes.financial import financial_bp
from routes.meetings import meetings_bp
from routes.board_resolutions import board_resolutions_bp
from routes.events import events_bp
from routes.auth import auth_bp
app.register_blueprint(account_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(documentation_bp)
app.register_blueprint(financial_bp)
app.register_blueprint(meetings_bp)
app.register_blueprint(board_resolutions_bp)
app.register_blueprint(events_bp)
app.register_blueprint(auth_bp)

# Initialize serializer for events blueprint
events_bp.init_serializer(app.config["SECRET_KEY"])

# Routes
@app.route("/")
def index():
    return render_template("index.html")






    










@app.route("/concept-papers-overview")
@login_required
def concept_papers_overview():
    # Query for all concept papers
    concept_papers = ConceptPaperForms.query.all()

    # Determine the sorting order
    sort_by_date = request.args.get('sort_by_date', 'recent-to-old')

    return render_template("concept-papers/concept-papers-overview.html", concept_papers=concept_papers, sort_by_date=sort_by_date)

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

    return render_template('concept-papers/add-concept-paper.html', academic_years=academic_years, users=users, signatories=signatories)

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

    return render_template('concept-papers/update-concept-paper.html', concept_paper=concept_paper, academic_years=academic_years, users=users, signatories=signatories, objectives_of_the_activity=objectives_of_the_activity, learning_outcomes=learning_outcomes, learning_journal=learning_journal, parent_guardian_consent_form=parent_guardian_consent_form, noted_by_college_dean=noted_by_college_dean, noted_by_sas=noted_by_sas)

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

    return render_template('concept-papers/delete-concept-paper.html', concept_paper=concept_paper)

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
        topMargin=100,
        bottomMargin=72
    )
    
    # Calculate available width for content
    available_width = FOLIO[0] - (72 * 2)  # Folio width (8.5") minus left and right margins
    
    story = []
    
    # Concept Paper Body Section
    # Define styles
    styles = getSampleStyleSheet()
    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontSize=12,
        leading=14,
        spaceAfter=12
    )
    
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontSize=12,
        leading=14,
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    
    # Define wrapped text style
    wrapped_style = ParagraphStyle(
        'WrappedStyle',
        parent=styles['Normal'],
        fontSize=12,
        leading=14,
        spaceBefore=0,
        spaceAfter=0
    )
    
    concept_paper = ConceptPaperForms.query.get_or_404(concept_paper_id)
    
    routing_data = [
        ["FOR:", Paragraph(f"<b>{concept_paper.approved_by_signatory.signatory_first_name} {concept_paper.approved_by_signatory.signatory_last_name}</b>", wrapped_style)],
        ["", Paragraph(f"{concept_paper.approved_by_signatory.signatory_position}{', ' + concept_paper.approved_by_signatory.signatory_department if concept_paper.approved_by_signatory.signatory_department else ''}", wrapped_style)],
        ["", ""],
        ["THRU:", Paragraph(f"<b>{concept_paper.recommending_approval_by_signatory.signatory_first_name} {concept_paper.recommending_approval_by_signatory.signatory_last_name}</b>", wrapped_style)],
        ["", Paragraph(f"{concept_paper.recommending_approval_by_signatory.signatory_position}{', ' + concept_paper.recommending_approval_by_signatory.signatory_department if concept_paper.recommending_approval_by_signatory.signatory_department else ''}", wrapped_style)],
        ["", ""],
        ["FROM:", Paragraph(f"<b>{concept_paper.endorsed_by_signatory.signatory_first_name} {concept_paper.endorsed_by_signatory.signatory_last_name}</b>", wrapped_style)],
        ["", Paragraph(f"{concept_paper.endorsed_by_signatory.signatory_position}{', ' + concept_paper.endorsed_by_signatory.signatory_department if concept_paper.endorsed_by_signatory.signatory_department else ''}", wrapped_style)],
        ["", ""],
        ["SUBJECT:", Paragraph(f"{concept_paper.concept_paper_forms_subject}", wrapped_style)],
        ["", ""],
        ["DATE:", Paragraph(f"{concept_paper.concept_paper_forms_date.strftime('%B %d, %Y')}" if concept_paper.concept_paper_forms_date else "", wrapped_style)]
    ]
    
    # Create table with automatic wrapping
    routing_table = Table(routing_data, colWidths=[80, available_width - 80])
    routing_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))

    story.append(routing_table)
    story.append(Spacer(1, 20))
    
    # Update normal style with justified alignment
    normal_style = ParagraphStyle(
        'NormalStyle',
        parent=styles['Normal'],
        fontSize=12,
        leading=14,
        spaceAfter=12,
        alignment=4  # 4 = justify alignment
    )
    
    # Split text into paragraphs and format each
    paragraphs = concept_paper.concept_paper_forms_body.split('\n')
    for i, paragraph in enumerate(paragraphs):
        if paragraph.strip():  # Skip empty paragraphs
            if i == 0:  # First paragraph - no indent
                story.append(Paragraph(paragraph.strip(), normal_style))
            else:  # All other paragraphs - add indent
                main_text = f"""<para firstLineIndent="36">{paragraph.strip()}</para>"""
                story.append(Paragraph(main_text, normal_style))
    
    # Create bullet style
    bullet_style = ParagraphStyle(
        'BulletStyle',
        parent=normal_style,
        leftIndent=30,
        firstLineIndent=-12,
        spaceAfter=6
    )
    
    story.append(Paragraph("Significant details are as follows:", normal_style))
    
    # Create details table data with wrapped text
    details_data = [
        [Paragraph("<b>DURATION OF THE EVENT</b>", normal_style), 
        ":", 
        Paragraph(f"{concept_paper.concept_paper_forms_event_start_date_and_time.strftime('%A, %B %d, %Y')} (Tentative), {concept_paper.concept_paper_forms_event_start_date_and_time.strftime('%I:%M %p')} - {concept_paper.concept_paper_forms_event_end_date_and_time.strftime('%I:%M %p')}", wrapped_style)],
        [Paragraph("<b>LOCATION</b>", normal_style), 
        ":", 
        Paragraph(f"{concept_paper.concept_paper_forms_location}", wrapped_style)],
        [Paragraph("<b>PARTICIPANTS</b>", normal_style), 
        ":", 
        Paragraph(f"{concept_paper.concept_paper_forms_participants}", wrapped_style)],
        [Paragraph("<b>BUDGET</b>", normal_style), 
        ":", 
        Paragraph(f"{concept_paper.concept_paper_forms_budget}", wrapped_style)]
    ]
    
    # Create table with aligned columns and text wrapping
    details_table = Table(details_data, colWidths=[200, 20, available_width - 250])
    details_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Left align properties
        ('ALIGN', (1, 0), (1, -1), 'CENTER'), # Center align colons
        ('ALIGN', (2, 0), (2, -1), 'LEFT'),  # Left align values
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Changed to TOP for wrapped text
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6)
    ]))
    story.append(details_table)
    story.append(Spacer(1, 12))
    
    story.append(Paragraph("Please see attached proposed concept paper for the complete details.", normal_style))
    story.append(Paragraph("Thank you.", normal_style))
    story.append(Spacer(1, 30))
    
    # Update signature block width
    signature_style = ParagraphStyle(
        'SignatureStyle',
        parent=styles['Normal'],
        fontSize=12,
        alignment=1,
        spaceAfter=0,
        width=available_width
    )
    
    story.append(Spacer(1, 20))
    
    # Create signature styling for left-aligned text
    left_signature_style = ParagraphStyle(
        'LeftSignatureStyle',
        parent=styles['Normal'],
        fontSize=12,
        alignment=0,  # 0 = left alignment
        spaceAfter=0
    )
    
    row1_table = Table([
        [
            [
                Paragraph("Endorsed by:", normal_style),
                Spacer(1, 30),
                Paragraph(f"<b>{concept_paper.endorsed_by_signatory.signatory_first_name} {concept_paper.endorsed_by_signatory.signatory_last_name}</b>", left_signature_style),
                Paragraph(f"{concept_paper.endorsed_by_signatory.signatory_position}{', ' + concept_paper.endorsed_by_signatory.signatory_department if concept_paper.endorsed_by_signatory.signatory_department else ''}", left_signature_style)
            ],
            [
                Paragraph("Recommending Approval by:", normal_style),
                Spacer(1, 30),
                Paragraph(f"<b>{concept_paper.recommending_approval_by_signatory.signatory_first_name} {concept_paper.recommending_approval_by_signatory.signatory_last_name}</b>", left_signature_style),
                Paragraph(f"{concept_paper.recommending_approval_by_signatory.signatory_position}{', ' + concept_paper.recommending_approval_by_signatory.signatory_department if concept_paper.recommending_approval_by_signatory.signatory_department else ''}", left_signature_style)
            ]
        ]
    ], colWidths=[available_width/2, available_width/1.8])
    
    row1_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    
    story.append(row1_table)
    story.append(Spacer(1, 30))
    
    # Create centered header style
    centered_header_style = ParagraphStyle(
        'CenteredHeader',
        parent=styles['Normal'],
        fontSize=12,
        alignment=1,  # Center alignment
        spaceAfter=0
    )
    
    # Create inner table width (about 30% of available width)
    inner_width = available_width * 0.3
    
    # Second row - nested tables for centering with left-aligned text
    approved_table = Table([
        [Paragraph("Approved by:", centered_header_style)],
        [Spacer(1, 30)],
        [
            Table(
                [[Paragraph(f"<b>{concept_paper.approved_by_signatory.signatory_first_name} {concept_paper.approved_by_signatory.signatory_last_name}</b>", centered_header_style)]],
                colWidths=[inner_width]
            )
        ],
        [
            Table(
                [[Paragraph(f"{concept_paper.approved_by_signatory.signatory_position}{', ' + concept_paper.approved_by_signatory.signatory_department if concept_paper.approved_by_signatory.signatory_department else ''}", centered_header_style)]],
                colWidths=[inner_width]
            )
        ]
    ], colWidths=[available_width])
    
    approved_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    
    story.append(approved_table)
    
    # Concept Paper Form Section
    story.append(PageBreak())
    story.append(Paragraph("<b>CONCEPT PAPER FORM</b>", centered_header_style))
    story.append(Paragraph(f"{concept_paper.concept_paper_forms_subject}", centered_header_style))
    story.append(Paragraph(
        f"{concept_paper.concept_paper_forms_event_start_date_and_time.strftime('%A, %B %d, %Y')} (Tentative) | "
        f"{concept_paper.concept_paper_forms_event_start_date_and_time.strftime('%I:%M %p')} – "
        f"{concept_paper.concept_paper_forms_event_end_date_and_time.strftime('%I:%M %p')} | "
        f"{concept_paper.concept_paper_forms_location}", 
        centered_header_style
    ))
    story.append(Spacer(1, 20))
    
    bold_centered_header_style = ParagraphStyle(
        'CenteredHeader',
        parent=styles['Normal'],
        fontSize=12,
        alignment=1,  # Center alignment
        spaceAfter=0,
        fontName='Helvetica-Bold'
    )
    
    # Create paragraph style with smaller leading and proper wrapping
    cell_style = ParagraphStyle(
        'CellStyle',
        parent=normal_style,
        leading=12,
        spaceBefore=6,
        spaceAfter=6
    )
    
    # Create main structure table with null checks and defaults
    objectives = ObjectivesOfTheActivity.query.filter_by(
        objectives_of_the_activity_concept_paper_forms_id=concept_paper.concept_paper_forms_id
    ).order_by(ObjectivesOfTheActivity.objectives_of_the_activity_id).all() or []
    
    learning_outcomes = LearningOutcomes.query.filter_by(
        learning_outcomes_concept_paper_forms_id=concept_paper.concept_paper_forms_id
    ).order_by(LearningOutcomes.learning_outcomes_id).all() or []
    
    structure_data = [
        [
            Paragraph("DESCRIPTIONS", bold_centered_header_style),
            Paragraph(str(concept_paper.concept_paper_forms_descriptions or ""), cell_style),
            ""
        ],
        [
            Paragraph("OBJECTIVES,\nLEARNING OUTCOMES AND\nEXPECTED DELIVERABLES\nOF THE ACTIVITY", bold_centered_header_style),
            Paragraph("OBJECTIVES OF\nTHE ACTIVITY", bold_centered_header_style),
            Paragraph("LEARNING\nOUTCOMES", bold_centered_header_style)
        ],
        [
            "",
            Paragraph("<br/>".join([f"{i+1}. {str(obj.objectives_of_the_activity_content or '')}" 
                      for i, obj in enumerate(objectives)]) or "No objectives listed", cell_style),
            Paragraph("<br/>".join([f"{i+1}. {str(outcome.learning_outcomes_content or '')}" 
                      for i, outcome in enumerate(learning_outcomes)]) or "No learning outcomes listed", cell_style)
        ],
        [
            Paragraph("EXPECTED NO. OF PARTICIPANTS", bold_centered_header_style),
            Paragraph(str(concept_paper.concept_paper_forms_expected_number_of_participants or ""), normal_style),
            None
        ],
        [
            Paragraph("BUDGET", bold_centered_header_style),
            Paragraph(str(concept_paper.concept_paper_forms_budget or ""), normal_style),
            None
        ]
    ]
    
    structure_table = Table(
        structure_data, 
        colWidths=[available_width * 0.3, available_width * 0.35, available_width * 0.35],
        splitByRow=True,
        repeatRows=2,
        minRowHeights=[30] * len(structure_data)
    )
    
    structure_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('VALIGN', (0, 0), (0, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (1, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('SPAN', (1, 0), (2, 0)),  # Description spans
        ('SPAN', (0, 1), (0, 2)),  # Objectives header spans
        ('SPAN', (1, 3), (2, 3)),  # Expected participants spans
        ('SPAN', (1, 4), (2, 4)),  # Budget spans
        ('PADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3)
    ]))
    
    story.append(structure_table)
    story.append(Spacer(1, 20))
    
    # Create centered signature style
    centered_signature_style = ParagraphStyle(
        'CenteredSignature',
        parent=styles['Normal'],
        fontSize=12,
        alignment=1,  # Center alignment
        spaceAfter=0
    )
    
    # Function to get organization acronym
    def get_org_acronym(org_name):
        acronyms = {
            'Junior Philippine Computer Society': 'JPCS',
            'College of Computer Studies - Student Council': 'CCS-SC'
        }
        return acronyms.get(org_name, org_name)
    
    signatories_data = [
        # Prepared by and Reviewed by
        [Paragraph("PREPARED BY:", centered_signature_style), 
        Paragraph("SIGNED AND REVIEWED BY:", centered_signature_style)],
        [Spacer(1, 30), Spacer(1, 30)],
        [Paragraph(f"<b>{concept_paper.prepared_by_user.users_first_name} {concept_paper.prepared_by_user.users_last_name}</b>", 
                centered_signature_style),
        Paragraph(f"<b>{concept_paper.signed_and_reviewed_by_user.users_first_name} {concept_paper.signed_and_reviewed_by_user.users_last_name}</b>", 
                centered_signature_style)],
        [Paragraph(f"{concept_paper.prepared_by_user.users_student_organization_position}, {get_org_acronym(StudentOrganizations.query.get(concept_paper.prepared_by_user.users_student_organization).student_organizations_name) if concept_paper.prepared_by_user.users_student_organization else ''}", centered_signature_style),
        Paragraph(f"{concept_paper.signed_and_reviewed_by_user.users_student_organization_position}, {get_org_acronym(StudentOrganizations.query.get(concept_paper.signed_and_reviewed_by_user.users_student_organization).student_organizations_name) if concept_paper.signed_and_reviewed_by_user.users_student_organization else ''}", centered_signature_style)],
        ["", ""],
        
        # Endorsed by
        [Paragraph("NOTED AND ENDORSED BY:", centered_signature_style), ""],
        [Spacer(1, 30), ""],
        [Paragraph(f"<b>{concept_paper.endorsed_by_signatory.signatory_first_name} {concept_paper.endorsed_by_signatory.signatory_last_name}</b>", 
                  centered_signature_style), ""],
        [Paragraph(f"{concept_paper.endorsed_by_signatory.signatory_position}{', ' + concept_paper.endorsed_by_signatory.signatory_department if concept_paper.endorsed_by_signatory.signatory_department else ''}", 
                  centered_signature_style), ""],
        ["", ""],
        
        # Recommending and Final Approval
        [Paragraph("RECOMMENDING APPROVAL BY:", centered_signature_style), 
         Paragraph("APPROVED BY:", centered_signature_style)],
        [Spacer(1, 30), Spacer(1, 30)],
        [Paragraph(f"<b>{concept_paper.recommending_approval_by_signatory.signatory_first_name} {concept_paper.recommending_approval_by_signatory.signatory_last_name}</b>", 
                  centered_signature_style),
         Paragraph(f"<b>{concept_paper.approved_by_signatory.signatory_first_name} {concept_paper.approved_by_signatory.signatory_last_name}</b>", 
                  centered_signature_style)],
        [Paragraph(f"{concept_paper.recommending_approval_by_signatory.signatory_position}{', ' + concept_paper.recommending_approval_by_signatory.signatory_department if concept_paper.recommending_approval_by_signatory.signatory_department else ''}", centered_signature_style),
         Paragraph(f"{concept_paper.approved_by_signatory.signatory_position}{', ' + concept_paper.approved_by_signatory.signatory_department if concept_paper.approved_by_signatory.signatory_department else ''}", centered_signature_style)]
    ]
    
    signatories_table = Table(signatories_data, colWidths=[available_width/1.5] * 2)
    signatories_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('SPAN', (0, 5), (1, 5)),  # Span "NOTED AND ENDORSED BY"
        ('SPAN', (0, 6), (1, 6)),  # Span spacer
        ('SPAN', (0, 7), (1, 7)),  # Span name
        ('SPAN', (0, 8), (1, 8)),  # Span position
        ('TOPPADDING', (0, 4), (-1, 4), 30),  # Space after first block
        ('TOPPADDING', (0, 9), (-1, 9), 30),  # Space after second block
    ]))
    
    story.append(signatories_table)
    story.append(Spacer(1, 20))
    
    # Add Excuse Letter Form Section
    story.append(PageBreak())
    story.append(Paragraph("<b>EXCUSE LETTER FORM</b>", centered_header_style))
    story.append(Spacer(1, 20))
    
    # I. Activity Details Section 
    story.append(Paragraph("I. Activity Details:", header_style))
    story.append(Spacer(1, 12))
    
    # Format date and time
    start_datetime = concept_paper.concept_paper_forms_event_start_date_and_time
    end_datetime = concept_paper.concept_paper_forms_event_end_date_and_time
    
    date_str = start_datetime.strftime("%A, %B %d, %Y")
    time_str = f"{start_datetime.strftime('%I:%M %p')} to {end_datetime.strftime('%I:%M %p')}"
    
    activity_details = [
        [Paragraph(f"<b>Title of Activity:</b><br/>{concept_paper.concept_paper_forms_subject}", normal_style),
         "", ""],  # Empty cells for spanning
        [Paragraph(f"<b>Day/Date:</b><br/>{date_str}", normal_style),
         Paragraph(f"<b>Time:</b><br/>{time_str}", normal_style),
         Paragraph(f"<b>Venue:</b><br/>{concept_paper.concept_paper_forms_location}", normal_style)]
    ]
    
    activity_table = Table(activity_details, colWidths=[available_width * 0.4, available_width * 0.3, available_width * 0.3])
    activity_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BOX', (0, 0), (-1, -1), 1, colors.black), 
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('SPAN', (0, 0), (2, 0)),  # Span title across all columns
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(activity_table)
    story.append(Spacer(1, 20))
    
    # Department Info Table
    excuse_letter = ExcuseLetterForms.query.filter_by(excuse_letter_forms_concept_paper_forms_id=concept_paper.concept_paper_forms_id).first()

    if not excuse_letter:
        # Create default values if no excuse letter exists
        personnel_name = ""
        dean_name = ""
        department_unit = concept_paper.department.departments_name if concept_paper.department else ""
    else:
        # Get related signatory names
        personnel_name = excuse_letter.personnel_in_charge_signatory.signatory_first_name + " " + excuse_letter.personnel_in_charge_signatory.signatory_last_name if excuse_letter.personnel_in_charge_signatory else ""
        dean_name = excuse_letter.dean_signatory.signatory_first_name + " " + excuse_letter.dean_signatory.signatory_last_name if excuse_letter.dean_signatory else ""
        department_unit = excuse_letter.excuse_letter_forms_department_office_unit

    story.append(Paragraph("RESPONSIBLE DEPARTMENT", header_style))
    story.append(Spacer(1, 12))
    
    dept_info = [
        [Paragraph(f"<b>Department/Office Unit:</b><br/>{excuse_letter.excuse_letter_forms_department_office_unit}", normal_style),
         Paragraph("<b>Landline:</b><br/>", normal_style)],
        [Paragraph(f"<b>Faculty In-Charge:</b><br/>{personnel_name}", normal_style),
         ""],
        [Paragraph(f"<b>Dean:</b><br/>{dean_name}", normal_style),
         ""]
    ]
    
    dept_table = Table(dept_info, colWidths=[available_width * 0.7, available_width * 0.3])
    dept_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('SPAN', (0, 1), (1, 1)),  # Span Faculty In-Charge
        ('SPAN', (0, 2), (1, 2))   # Span Dean
    ]))
    
    story.append(dept_table)
    story.append(Spacer(1, 20))
    
    # Letter Body Section
    letter_data = [
        ["Dear: ____________________________________", "", "Subject: ____________________", ""],
        ["", Paragraph("Name of Professor", normal_style), "", ""],
        ["Day/Date/Time of Class Affected: ______________", "", "Room Number: ______________", ""]
    ]
    
    letter_table = Table(letter_data, colWidths=[
        available_width * 0.20,
        available_width * 0.40,
        available_width * 0.20,
        available_width * 0.20
    ])
    
    letter_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(letter_table)
    story.append(Spacer(1, 12))
    
    # Letter Content
    letter_content = """<para firstLineIndent='32'>Please excuse the following students to your class for they will be attending an activity sponsored by our college. Rest assured that they will be responsible in studying the lesson they had missed during their absence. Kindly see the attached list of the students.<br/><br/>Thank you!</para>"""
    story.append(Paragraph(letter_content, normal_style))
    story.append(Spacer(1, 20))
    
    # Signature Section
    signature_data = [
        ["Truly yours,", ""],
        [Spacer(1, 30), ""],
        ["____________________________", ""],
        ["Signature of Personnel In-Charge", ""],
        [Spacer(1, 10), ""],
        ["Noted by:", ""],
        [Spacer(1, 30), ""],
        ["____________________________", ""],
        [Paragraph(f"<b>{dean_name.upper()}</b>", normal_style), ""],
        ["Dean, College of Computer Studies", ""]
    ]
    
    signature_table = Table(signature_data, colWidths=[available_width * 0.5] * 2)
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(signature_table)
    
    concept_paper = ConceptPaperForms.query.get_or_404(concept_paper_id)
    
    # Get activity report form using concept paper id
    activity_report = ActivityReportForms.query.filter_by(
        activity_report_forms_concept_paper_forms_id=concept_paper.concept_paper_forms_id
    ).first()
    
    # Get events data using concept paper id
    event = Events.query.filter_by(
        events_concept_paper_forms_id=concept_paper.concept_paper_forms_id
    ).first()

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
    story.append(Paragraph("<b>I. ACTIVITY DETAILS</b>", section_header_style))

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
    story.append(Paragraph("<b>II. OBJECTIVES</b>", section_header_style))

    # Fetch objectives and learning outcomes
    objectives = []
    learning_outcomes = []

    concept_paper = ConceptPaperForms.query.get_or_404(concept_paper_id)
    
    # Get objectives from relationship
    objectives_query = concept_paper.objectives.all()
    objectives = [obj.objectives_of_the_activity_content for obj in objectives_query if obj.objectives_of_the_activity_content]
    objectives = [f"{i+1}. {obj}" for i, obj in enumerate(objectives)]
    
    # Get learning outcomes from relationship
    outcomes_query = concept_paper.learning_outcomes.all()
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
            Paragraph("<b>OBJECTIVES OF THE ACTIVITY</b>", header_style),
            Paragraph("<b>LEARNING OUTCOMES</b>", header_style)
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
    story.append(Paragraph("III. <b>EVALUATION</b>: (Make sure to have three answers for the strengths and weakness.) Weaknesses must have corresponding recommendations.", section_header_style))
    
    # Initialize empty lists for evaluation data
    strengths = []
    weaknesses = []
    recommendations = []

    # Query activity data if activity report exists
    if activity_report:
        # Get strengths from database
        strengths_query = ActivityStrengths.query.filter_by(
            activity_strengths_documentation_id=activity_report.activity_report_forms_id
        ).all()
        strengths = [s.activity_strengths_content for s in strengths_query if s.activity_strengths_content]

        # Get weaknesses from database
        weaknesses_query = ActivityWeaknesses.query.filter_by(
            activity_weaknesses_documentation_id=activity_report.activity_report_forms_id
        ).all()
        weaknesses = [w.activity_weaknesses_content for w in weaknesses_query if w.activity_weaknesses_content]

        # Get recommendations from database
        recommendations_query = ActivityRecommendations.query.filter_by(
            activity_recommendations_documentation_id=activity_report.activity_report_forms_id
        ).all()
        recommendations = [r.activity_recommendations_content for r in recommendations_query if r.activity_recommendations_content]
    
    # Create base evaluation table structure
    evaluation_data = [
        # Headers row
        [
            Paragraph("<b>Strengths</b>", header_style),
            Paragraph("<b>Weaknesses</b>", header_style),
            Paragraph("<b>Recommendation</b>", header_style)
        ]
    ]
    
    # Check if there's evaluation data
    if not strengths and not weaknesses and not recommendations:
        # Add 3 empty rows with N/A
        for i in range(3):
            evaluation_data.append([
                Paragraph(f"", cell_style),
                Paragraph(f"", cell_style),
                Paragraph(f"", cell_style)
            ])
    else:
        # Calculate maximum length of the lists
        max_length = max(len(strengths), len(weaknesses), len(recommendations))
        
        # Add content rows with numbering
        for i in range(max_length):
            strength = f"{i+1}. {strengths[i]}" if i < len(strengths) else f""
            weakness = f"{i+1}. {weaknesses[i]}" if i < len(weaknesses) else f""
            recommendation = f"{i+1}. {recommendations[i]}" if i < len(recommendations) else f""
            
            evaluation_data.append([
                Paragraph(strength, cell_style),
                Paragraph(weakness, cell_style),
                Paragraph(recommendation, cell_style)
            ])
    
    # Create and style the evaluation table
    evaluation_table = Table(evaluation_data, colWidths=[157, 157, 157])
    evaluation_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
    ]))
    
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
    
    # Add date submission if activity report exists
    if activity_report and activity_report.activity_report_date_submission:
        # Format date
        formatted_date = activity_report.activity_report_date_submission.strftime("%B %d, %Y")
        
        # Add spacer and date
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"Date of Submission: {formatted_date}", position_style))
    
    # Create red text style for form number
    red_text_style = ParagraphStyle(
        'RedText',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.red,
        alignment=0  # Left alignment
    )
    
    # Add form number and main header
    story.append(PageBreak())  # Start on a new page
    story.append(Paragraph("Form 13", red_text_style))
    story.append(Paragraph("LEARNING JOURNAL FORM", title_style))
    
    story.append(Paragraph("I. Activity Details:", section_header_style))
    story.append(Spacer(1, 10))
    
    # After getting documentation_data, add this:
    learning_journal_form = None
    if concept_paper:
        learning_journal_form = db.session.query(LearningJournalForms).filter(
            LearningJournalForms.learning_journal_forms_concept_paper_forms_id == concept_paper.concept_paper_forms_id
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
            Paragraph(f"<b>Name of Student:</b><br/><br/>", cell_style),
            Paragraph(f"<b>Course/Year level:</b><br/><br/>", cell_style),
            Paragraph(f"<b>ID Number:</b><br/><br/>", cell_style)
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
    story.append(Spacer(1, 10))
    story.append(Paragraph("II. Activity Progress Notes:", section_header_style))
    story.append(Spacer(1, 10))

    # Format the date string
    if learning_journal_form and learning_journal_form.learning_journal_forms_date:
        date_str = learning_journal_form.learning_journal_forms_date.strftime("%A, %B %d, %Y")
    else:
        date_str = ""
    
    # Create empty numbered list template
    empty_list = "1.<br/><br/>2.<br/><br/>3.<br/><br/>"
    
    progress_notes_data = [
        # Header row with three columns
        [
            Paragraph("Date: <b>" + date_str + "</b>", cell_style),
            Paragraph("<b>Observations</b><br/>(not less than 3)", header_style),
            Paragraph("<b>Learnings</b><br/>(not less than 3)", header_style),
        ],
        # Content row
        [
            Paragraph("", cell_style),
            Paragraph(empty_list, cell_style),
            Paragraph(empty_list, cell_style),
        ]
    ]
    
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
    story.append(Spacer(1, 10))
    story.append(Paragraph("III. Over-all Reflection (The reflection must be written in a narrative form not less than 5 sentences.)", section_header_style))
    story.append(Spacer(1, 10))
    
    # Create reflection paragraph with justified alignment and line breaks
    reflection_style = ParagraphStyle(
        'ReflectionStyle',
        parent=cell_style,
        alignment=4,  # 4 is for justified alignment
        spaceBefore=6,
        spaceAfter=6,
        leading=16  # Increase line spacing for better readability
    )
    
    # Add empty reflection table with border and line breaks
    reflection_table = Table([[Paragraph("<br/><br/><br/>", reflection_style)]], colWidths=[475])
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
    story.append(Spacer(1, 10))
    
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

    # Get the checked by signatory from concept paper
    checked_by_signatory = None
    if concept_paper and concept_paper.concept_paper_forms_approved_by:
        checked_by_signatory = db.session.query(Signatories).filter(
            Signatories.signatory_id == concept_paper.concept_paper_forms_approved_by
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
    
    # Add Personnel In-Charge Form
    story.append(PageBreak())
    story.append(Paragraph("Form 10", red_text_style))
    story.append(Paragraph("PERSONNEL IN-CHARGE FORM (PICF)", title_style))
    story.append(Spacer(1, 20))
    
    # Format period covered
    semester = concept_paper.concept_paper_forms_semester
    academic_year = concept_paper.concept_paper_forms_academic_year
    period_covered = f"{semester}, {concept_paper.concept_paper_forms_date.strftime('%B %d, %Y')} (Tentative)"
    
    # Format time
    time_str = f"{concept_paper.concept_paper_forms_event_start_date_and_time.strftime('%I:%M %p')} to {concept_paper.concept_paper_forms_event_end_date_and_time.strftime('%I:%M %p')}"
    
    picf_details = [
        # Row 1: Title spans 2 columns, Period Covered in last column
        [
            Paragraph(f"<b>Title of the Activity:</b><br/>{concept_paper.concept_paper_forms_subject}", normal_style),
            "",  # Empty cell for spanning
            Paragraph(f"<b>Period Covered:</b><br/>{period_covered}", normal_style)
        ],
        # Row 2: Three separate cells
        [
            Paragraph(f"<b>Time:</b><br/>{time_str}", normal_style),
            Paragraph(f"<b>Venue:</b><br/>{concept_paper.concept_paper_forms_location}", normal_style),
            Paragraph(f"<b>College/Department:</b><br/>{concept_paper.department.departments_name if concept_paper.department else ''}", normal_style)
        ]
    ]
    
    picf_table = Table(picf_details, colWidths=[available_width/3] * 3)
    picf_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('SPAN', (0, 0), (1, 0)),  # Span title across first two columns
    ]))
    
    story.append(picf_table)
    story.append(Spacer(1, 20))
    
    # Create styles for different text sections
    list_style = ParagraphStyle(
        'ListStyle',
        parent=normal_style,
        leftIndent=20,
        spaceBefore=6,
        spaceAfter=6
    )
    
    # Query personnel in charge form
    pic_form = PersonnelInChargeForms.query.filter_by(personnel_in_charge_forms_concept_paper_forms_id=concept_paper.concept_paper_forms_id).first()

    if pic_form:
        personnel_name = f"{pic_form.personnel_in_charge_signatory.signatory_first_name} {pic_form.personnel_in_charge_signatory.signatory_last_name}" if pic_form.personnel_in_charge_signatory else ""
        dean_name = f"{pic_form.noted_by_dean_signatory.signatory_first_name} {pic_form.noted_by_dean_signatory.signatory_last_name}" if pic_form.noted_by_dean_signatory else ""
        sas_name = f"{pic_form.noted_by_sas_signatory.signatory_first_name} {pic_form.noted_by_sas_signatory.signatory_last_name}" if pic_form.noted_by_sas_signatory else ""
    else:
        personnel_name = ""
        dean_name = ""
        sas_name = ""

    # Update intro text with dynamic name
    intro_text = f"""<para firstLineIndent='32'>I, <b>{personnel_name}</b>, of the College of Computer Studies will voluntarily accompany my students during the activity. I understand my responsibilities and role as the Dean in-charge and will diligently follow all protocols needed for the safety of the participating students. I am committed to do the following to ensure the safety of the students during the activity.</para>"""

    # List items remain the same
    list_items = [
        "Remind the students about the ground rules of activity during the preparation stage...",
        "Rules and regulations of the school on liquors, drugs will be strictly implemented...",
        "Makes sure that the schedule is followed and will guide the students in all activities...",
        "Submit the activity report form two weeks after the conduct of the activity..."
    ]

    closing_text = """<para firstLineIndent='32'>I will be accompanying the students during the activity and can be contacted on the following contact number as indicated below:</para>"""

    # Add text sections to story
    story.append(Paragraph(intro_text, normal_style))

    for i, item in enumerate(list_items):
        story.append(Paragraph(f"{ascii_lowercase[i]}. {item}", list_style))

    story.append(Spacer(1, 12))
    story.append(Paragraph(closing_text, normal_style))
    story.append(Spacer(1, 20))

    # Update signature section with dynamic names
    signature_data = [
        ["By:", Paragraph(f"<b>{personnel_name}</b>", normal_style), "____________________"],
        ["", "Name of Personnel-in-charge/Signature", "Date/Time"],
        ["", "", ""],
        ["Noted by:", Paragraph(f"<b>{dean_name}</b>", normal_style), "____________________"],
        ["", "OIC Dean of the College/Signature", "Date/Time"],
        ["", "", ""],
        ["", Paragraph(f"<b>{sas_name}</b>", normal_style), "____________________"],
        ["", "Head, Student Affairs & Services", "Date/Time"]
    ]

    signature_table = Table(signature_data, colWidths=[available_width * 0.2, available_width * 0.5, available_width * 0.3])
    signature_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))

    story.append(signature_table)

    # Add Parent/Guardian Consent Form
    story.append(PageBreak())
    story.append(Paragraph("Form 8", red_text_style))
    story.append(Paragraph("PARENT/GUARDIAN CONSENT FORM", title_style))
    
    # Query parent guardian consent form
    pg_form = ParentGuardianConsentForms.query.filter_by(parent_guardian_consent_forms_concept_paper_forms_id=concept_paper.concept_paper_forms_id).first()
    
    # Format date and time
    event_date = concept_paper.concept_paper_forms_event_start_date_and_time.strftime("%A, %B %d, %Y")
    event_time = f"{concept_paper.concept_paper_forms_event_start_date_and_time.strftime('%I:%M %p')} to {concept_paper.concept_paper_forms_event_end_date_and_time.strftime('%I:%M %p')}"
    
    if pg_form:
        student_name = pg_form.parent_guardian_consent_forms_name_of_student or ""
        course_year = pg_form.parent_guardian_consent_forms_course_year_level or ""
        id_number = pg_form.parent_guardian_consent_forms_id_number or ""
        department = pg_form.parent_guardian_consent_forms_department_office_unit or ""
        dean_name = f"{pg_form.dean_immediate_supervisor_signatory.signatory_first_name} {pg_form.dean_immediate_supervisor_signatory.signatory_last_name}" if pg_form.dean_immediate_supervisor_signatory else ""
    else:
        student_name = ""
        course_year = ""
        id_number = ""
        department = concept_paper.department.departments_name if concept_paper.department else ""
        dean_name = ""
    
    # Student Details Table
    student_details = [
        [Paragraph(f"<b>Name of Student:</b><br/><br/>{student_name}", normal_style), 
         Paragraph(f"<b>Course/Year level:</b><br/><br/>{course_year}", normal_style),
         Paragraph(f"<b>ID Number:</b><br/><br/>{id_number}", normal_style)],
        [Paragraph(f"<b>Day/Date:</b><br/>{event_date} (Tentative)", normal_style),
         Paragraph(f"<b>Time:</b><br/>{event_time}", normal_style),
         Paragraph(f"<b>Venue:</b><br/>{concept_paper.concept_paper_forms_location}", normal_style)],
        [Paragraph(f"<b>Title of the Activity:</b><br/>{concept_paper.concept_paper_forms_subject}", normal_style),
         "", ""]  # Empty cells for spanning
    ]
    
    student_table = Table(student_details, colWidths=[available_width/3] * 3)
    student_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('SPAN', (0, 2), (2, 2)),  # Span title across all three columns
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(student_table)
    story.append(Spacer(1, 20))
    
    # Department Info Table
    dept_info = [
        [Paragraph("<b>RESPONSIBLE DEPARTMENT</b>", header_style)],
        [Paragraph(f"<b>Department/Office Unit:</b><br/>{department}", normal_style),
         Paragraph("<b>Landline:</b><br/>", normal_style)],
        [Paragraph(f"<b>Faculty In-Charge:</b><br/>{personnel_name if 'personnel_name' in locals() else ''}", normal_style),
         Paragraph("<b>Mobile Number:</b><br/>", normal_style)],
        [Paragraph(f"<b>Dean/Immediate Supervisor:</b><br/>{dean_name}", normal_style),
         Paragraph("<b>Mobile Number:</b><br/>", normal_style)]
    ]
    
    dept_table = Table(dept_info, colWidths=[available_width/2] * 2)
    dept_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('SPAN', (0, 0), (1, 0)),  # Span header across columns
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(dept_table)
    story.append(Spacer(1, 20))
    
        # Consent Section
    story.append(Paragraph("<b>CONSENT</b>", header_style))
    story.append(Spacer(1, 10))
    
    # Format event details
    event_date = concept_paper.concept_paper_forms_event_start_date_and_time.strftime("%A, %B %d, %Y")
    event_time = f"{concept_paper.concept_paper_forms_event_start_date_and_time.strftime('%I:%M %p')} - {concept_paper.concept_paper_forms_event_end_date_and_time.strftime('%I:%M %p')}"
    
    consent_items = [
        f"I understand that UPH-Molino together with this administrators, faculty and staff did everything with due diligence to ensure the safety by of my son/daughter during the conduct of the activity.",
        f"I understand that the duration of the activity is on {event_date} (Tentative) from {event_time} and I expect my son/daughter to participate at {concept_paper.concept_paper_forms_subject}.",
        "The activity is for enhancement of skills of my son/daughter and we need not to pay for a certain amount to cover registration fee, food, seminar kits, certificates, and transportation expenses.",
        "We understand that the activity is not compulsory/mandatory and an alternative activity can be done if ever my son/daughter will not join the activity.",
        "We voluntary allow our son/daughter to join the activity and needs to adhere to all the safety measures being done by the administration, faculty and staff of UPH-Molino."
    ]
    
    for item in consent_items:
        story.append(Paragraph(f"• {item}", normal_style))
    
    # Signature Section
    story.append(Spacer(1, 20))
    story.append(Paragraph("Seen and read by:", normal_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph("________________________________", normal_style))
    story.append(Paragraph("Signature over Name of Parent/ Guardian", normal_style))
    
    story.append(Spacer(1, 20))
    story.append(Paragraph("Checked by:", normal_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph("_____________________________________", normal_style))
    
    # Get dean name from parent guardian form
    if pg_form and pg_form.dean_immediate_supervisor_signatory:
        dean_name = f"{pg_form.dean_immediate_supervisor_signatory.signatory_first_name} {pg_form.dean_immediate_supervisor_signatory.signatory_last_name}"
        story.append(Paragraph(f"<b>{dean_name.upper()}</b>", normal_style))
        story.append(Paragraph(pg_form.parent_guardian_consent_forms_department_office_unit or "OIC Dean, College of Computer Studies", normal_style))
    
        # Letter to Parents
    story.append(PageBreak())
    story.append(Paragraph(f"<b>{department}</b>", ParagraphStyle(
        'CenteredStyle',
        parent=normal_style,
        alignment=1
    )))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Dear Parents,", normal_style))
    story.append(Paragraph("Greetings!", normal_style))
    story.append(Spacer(1, 12))
    
    # Dynamic letter content using parent guardian consent form content if available
    if pg_form and pg_form.parent_guardian_consent_forms_content:
        letter_text = f"""<para firstLineIndent='32'>{pg_form.parent_guardian_consent_forms_content}</para>"""
    else:
        # Fallback to default template
        letter_text = f"""<para firstLineIndent='32'></para>"""
    
    story.append(Paragraph(letter_text, normal_style))
    story.append(Spacer(1, 20))
    
    # Signature Section with dynamic signatories
    story.append(Paragraph("Prepared By:", normal_style))
    story.append(Spacer(1, 20))
    if pg_form and pg_form.prepared_by_user:
        prepared_by_name = f"{pg_form.prepared_by_user.users_first_name} {pg_form.prepared_by_user.users_last_name}"
        org_name = StudentOrganizations.query.get(pg_form.prepared_by_user.users_student_organization).student_organizations_name if pg_form.prepared_by_user.users_student_organization else ''
        org_acronym = get_org_acronym(org_name)
        story.append(Paragraph(f"<b>{prepared_by_name.upper()}</b>", normal_style))
        story.append(Paragraph(f"{pg_form.prepared_by_user.users_student_organization_position}, {org_acronym}", normal_style))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("Noted By:", normal_style))
    story.append(Spacer(1, 20))
    if pg_form and pg_form.noted_by_signatory:
        noted_by_name = f"{pg_form.noted_by_signatory.signatory_first_name} {pg_form.noted_by_signatory.signatory_last_name}"
        story.append(Paragraph(f"<b>{noted_by_name.upper()}</b>", normal_style))
        story.append(Paragraph(f"{pg_form.noted_by_signatory.signatory_position}, {pg_form.parent_guardian_consent_forms_department_office_unit}", normal_style))
    
    # Reply Slip with full-width line
    story.append(Spacer(1, 20))
    story.append(HRFlowable(
        width="100%",
        thickness=1,
        lineCap='round',
        color=colors.black,
        spaceBefore=1,
        spaceAfter=1,
        hAlign='CENTER',
    ))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Reply Slip", ParagraphStyle(
        'CenteredStyle',
        parent=normal_style,
        alignment=1
    )))
    story.append(Spacer(1, 12))
    
    # Create checkbox style with ZapfDingbats
    checkbox_style = ParagraphStyle(
        'CheckboxStyle',
        parent=normal_style,
        leftIndent=20
    )
    
    # Dynamic reply options using concept paper subject
    reply_options = [
        f"I allow my son/daughter to attend the {concept_paper.concept_paper_forms_subject}",
        f"I do not allow my son/daughter to attend the {concept_paper.concept_paper_forms_subject}"
    ]
    
    for option in reply_options:
        story.append(Paragraph("<font face='ZapfDingbats' size='16'>❏</font> " + option, checkbox_style))
        story.append(Spacer(1, 12))
    
    story.append(Spacer(1, 30))
    story.append(Table([[
        Paragraph("__________________________________", normal_style),
        Paragraph("___________________", normal_style)
    ]], colWidths=[available_width * 0.7, available_width * 0.3]))
    story.append(Table([[
        Paragraph("Signature over Name of Parent/ Guardian", normal_style),
        Paragraph("Date", ParagraphStyle(
            'CenteredStyle',
            parent=normal_style,
            alignment=1  # Center alignment
        ))
    ]], colWidths=[available_width * 0.7, available_width * 0.3]))
    
    doc.build(story, onFirstPage=header, onLaterPages=header)
    
    buffer.seek(0)
    return send_file(
        buffer,
        download_name=f'Concept_Paper_{concept_paper_id}.pdf',
        mimetype='application/pdf'
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)