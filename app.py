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
from routes.concept_papers import concept_papers_bp
app.register_blueprint(account_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(documentation_bp)
app.register_blueprint(financial_bp)
app.register_blueprint(meetings_bp)
app.register_blueprint(board_resolutions_bp)
app.register_blueprint(events_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(concept_papers_bp)

# Initialize serializer for events blueprint
events_bp.init_serializer(app.config["SECRET_KEY"])

# Routes
@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)