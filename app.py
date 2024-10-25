import os
import re
from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_migrate import Migrate
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from markupsafe import Markup
from datetime import datetime, timedelta
from sqlalchemy import Enum

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
        name='role_enum'
    ), nullable=False)

    users_student_organization = db.Column(db.Enum(
        'College of Computer Studies - Student Council',
        'Junior Philippine Computer Society',
        name='organization_enum'
    ), nullable=False)

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
    ), nullable=False)

    users_home_address = db.Column(db.String(255), nullable=True)
    users_contact_number = db.Column(db.String(20), nullable=True)
    users_signature = db.Column(db.String(255), nullable=True)
    users_signature_cloudinary_public_id = db.Column(db.String(255), nullable=True)
    users_password = db.Column(db.String(255), nullable=False)
    users_email_verified = db.Column(db.Integer, nullable=False)

    # Relationship to Departments
    department = db.relationship('Departments', backref='users')

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
    events_name = db.Column(db.String(255), nullable=True)
    events_semester = db.Column(db.String(50), nullable=False)
    events_academic_year = db.Column(db.String(50), nullable=False)
    events_start_date_and_time = db.Column(db.DateTime, nullable=True)
    events_end_date_and_time = db.Column(db.DateTime, nullable=True)
    events_venue = db.Column(db.String(255), nullable=True)
    events_budget = db.Column(db.Numeric(20, 2), nullable=True)
    events_status = db.Column(db.String(50), nullable=True)
    events_description = db.Column(db.Text, nullable=True)
    events_remarks = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"Events({self.events_id}, {self.events_name}, {self.events_semester}, {self.events_academic_year}, {self.events_start_date_and_time}, {self.events_end_date_and_time}, {self.events_venue}, {self.events_budget}, {self.events_status}, {self.events_description}, {self.events_remarks})"

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
    token = s.dumps(users_email, salt='invite-user')
    link = url_for('accept_invite', token=token, _external=True)
    msg = Message('Invitation to Manage Event', recipients=[users_email])
    
    # HTML email body
    msg.html = f"""
    <html>
    <body style="font-family: 'Arial', 'Helvetica', sans-serif; background-color: #f5f5f5; color: #1e1e1e; padding: 20px;">
        <h1 style="color: #00578a;">Invitation to Manage Event</h1>
        <p>You have been invited to help manage the event "{event_name}". Please click the button below to accept the invitation:</p>
        <a href="{link}" style="background-color: #00578a; color: #ffffff; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 8px;">Accept Invitation</a>
        <p style="font-size: 0.8em; color: gray;">Or copy and paste this link into your browser: <br><a href="{link}" style="color: #00578a;">{link}</a></p>
        <p>If you didn't expect this invitation, you can safely ignore this email.</p>
        <p>Sincerely,<br>E-Council Team</p>
    </body>
    </html>
    """
    
    # Plain text email body as a fallback
    msg.body = f"""
    You have been invited to help manage the event "{event_name}". Please click the link below to accept the invitation:
    {link}

    Or copy and paste this link into your browser:
    {link}

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

# Routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")
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
        
        users_student_organization = request.form.get("users-student-organization") if request.form.get("users-student-organization") else ""
        users_student_organization_position = request.form.get("users-student-organization-position") if request.form.get("users-student-organization-position") else ""

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
        if users_student_organization and users_student_organization not in Users.users_student_organization.type.enums:
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
    if profile_picture:
        # Server-side validation for image file types
        valid_image_types = ['image/jpeg', 'image/png', 'image/jpg']
        if profile_picture.mimetype not in valid_image_types:
            flash("Invalid file type. Please upload an image file.", "error")
            return redirect(url_for("account"))

        # Delete the previous profile picture from Cloudinary if it exists
        if current_user.users_profile_picture:
            public_id = current_user.users_profile_picture_cloudinary_public_id
            if public_id:
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
        if users_student_organization and users_student_organization not in Users.users_student_organization.type.enums:
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

    # Query all departments to pass to the template
    departments = Departments.query.all()
    return render_template("account-settings.html", departments=departments)

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

    # Query distinct academic years
    academic_years = db.session.query(Events.events_academic_year).distinct().order_by(Events.events_academic_year.desc()).all()

    # Get filter and sort parameters from the request
    academic_year = request.args.get("events-overview-academic-year")
    status = request.args.get("events-overview-filter-by-status")
    semester = request.args.get("events-overview-filter-by-semester")
    sort_by_date = request.args.get("events-overview-sort-by-date")

    # Set default academic year to the most recent one if not provided
    if not academic_year and academic_years:
        academic_year = academic_years[0].events_academic_year

    # Set default sorting to recent-to-old if not provided
    if not sort_by_date:
        sort_by_date = "recent-to-old"

    # Base query for events associated with the user's department
    query = db.session.query(Events).join(DepartmentsEvents).filter(DepartmentsEvents.departments_id == users_departments_id)

    # Apply filters
    if academic_year:
        query = query.filter(Events.events_academic_year == academic_year)
    if status and status != "All":
        query = query.filter(Events.events_status == status)
    if semester and semester != "All":
        query = query.filter(Events.events_semester == semester)

    # Apply sorting
    if sort_by_date == "recent-to-old":
        query = query.order_by(Events.events_start_date_and_time.desc())
    elif sort_by_date == "old-to-recent":
        query = query.order_by(Events.events_start_date_and_time.asc())

    # Execute the query
    events = query.all()

    return render_template("events-overview.html", events=events, academic_years=academic_years)

@app.route("/update-event/<int:event_id>", methods=["POST"])
@login_required
def update_event(event_id):
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

@app.route("/add-event", methods=["GET", "POST"])
@login_required
def add_event():
    if request.method == "POST":
        events_name = request.form.get("events-name")
        events_semester = request.form.get("events-semester")
        events_academic_year = request.form.get("events-academic-year")
        events_start_date_and_time = request.form.get("events-start-date-and-time")
        events_end_date_and_time = request.form.get("events-end-date-and-time")
        events_venue = request.form.get("events-venue")
        events_budget = request.form.get("events-budget")
        events_status = request.form.get("events-status")
        events_description = request.form.get("events-description")
        events_remarks = request.form.get("events-remarks")

        # Validation
        if not events_name or not events_semester or not events_academic_year or not events_start_date_and_time or not events_end_date_and_time:
            flash("Please fill out all required fields.", "modal-error")
            return render_template("events-overview.html", show_modal=True)

        # Check if event name already exists
        existing_event = Events.query.filter_by(events_name=events_name).first()
        if existing_event:
            flash("An event with this name already exists. Please choose a different name.", "modal-error")
            return render_template("events-overview.html", show_modal=True)

        # Validate date format
        try:
            events_start_date_and_time = datetime.strptime(events_start_date_and_time, '%Y-%m-%dT%H:%M')
            events_end_date_and_time = datetime.strptime(events_end_date_and_time, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash("Invalid date format. Please use the format YYYY-MM-DDTHH:MM.", "modal-error")
            return render_template("events-overview.html", show_modal=True)

        # Validate budget format
        if events_budget:
            try:
                events_budget = float(events_budget)
            except ValueError:
                flash("Invalid budget format. Please enter a valid number.", "modal-error")
                return render_template("events-overview.html", show_modal=True)

        event = Events(
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

    return render_template("events-overview.html")

@app.route("/event-dashboard")
@login_required
def event_dashboard():
    return render_template("event-dashboard.html")

@app.route("/add-transaction")
@login_required
def add_transaction():
    return render_template("add-transaction.html")

@app.route("/invite-user/<int:event_id>", methods=["POST"])
@login_required
def invite_user(event_id):
    # Get the event by ID
    event = Events.query.get_or_404(event_id)

    # Get form data
    users_email = request.form.get("users-email")

    # Find the user by email
    user = Users.query.filter_by(users_email=users_email).first_or_404()

    # Get the user's department ID
    users_department_id = user.users_departments_id

    # Check if the departments_id and events_id pair already exists
    existing_entry = DepartmentsEvents.query.filter_by(departments_id=users_department_id, events_id=event_id).first()
    if existing_entry:
        flash("This department of this user is already managing the event.", "error")
        return redirect(url_for("events_overview"))

    # Send invite email
    send_invite_email(users_email, event.events_name, event_id)

    flash("Invitation email sent successfully.", "success")
    return redirect(url_for("events_overview"))

@app.route("/accept-invite/<token>")
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
    invitation = EventInvitations.query.filter_by(event_invitations_token=token).first_or_404()

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
    return render_template("concept-papers-overview.html")

@app.route("/documentation-overview")
@login_required
def documentation_overview():
    return render_template("documentation-overview.html")

@app.route("/financial-reports-overview")
@login_required
def financial_reports_overview():
    return render_template("financial-reports-overview.html")

@app.route("/accreditation-requirements-overview")
@login_required
def accreditation_requirements_overview():
    return render_template("accreditation-requirements-overview.html")

@app.route("/board-resolutions-overview")
@login_required
def board_resolutions_overview():
    return render_template("board-resolutions-overview.html")

@app.route("/notable-achievement-reports-overview")
@login_required
def notable_achievement_reports_overview():
    return render_template("notable-achievement-reports-overview.html")

@app.route("/society-achievement-and-compliance-reports-overview")
@login_required
def society_accomplishment_and_compliance_reports_overview():
    return render_template("society-accomplishment-and-compliance-reports-overview.html")

@app.route("/minutes-of-the-meeting-overview")
@login_required
def minutes_of_the_meeting_overview():
    return render_template("minutes-of-the-meeting-overview.html")

@app.route("/student-enrichment-activity-reports-overview")
@login_required
def student_enrichment_activity_reports_overview():
    return render_template("student-enrichment-activity-reports-overview.html")

@app.route("/end-of-semester-reports-overview")
@login_required
def end_of_semester_reports_overview():
    return render_template("end-of-semester-reports-overview.html")

@app.route("/calendar-of-activities-overview")
@login_required
def calendar_of_activities_overview():
    return render_template("calendar-of-activities-overview.html")

@app.route("/semestral-clearance-overview")
@login_required
def semestral_clearance_overview():
    return render_template("semestral-clearance-overview.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)