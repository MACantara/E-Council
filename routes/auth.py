"""
Authentication routes blueprint for E-Council.
Handles user registration, login, logout, password reset, and email verification.
"""

from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, flash, redirect, url_for, Markup
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from markupsafe import Markup as SafeMarkup

# Import database models from models package
from models import (
    db,
    Users,
    StudentOrganizations,
    EmailVerification,
    PasswordReset,
    LoginAttempts,
    Departments
)

# Import email functions from utils.email
from utils.email import send_verification_email, send_reset_password_email

# Import current app to get SECRET_KEY for serializer
from flask import current_app

# Initialize URLSafeTimedSerializer
def get_serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])

# Create blueprint with url_prefix='/auth'
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        student_organizations = StudentOrganizations.query.all()
        return render_template("auth/signup.html", student_organizations=student_organizations)
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
            return render_template("auth/signup.html")

        if users_role == "Student Council Officer":
            if not users_student_organization or not users_student_organization_position:
                flash("Student Organization and Position are required for Student Council Officers.", "error")
                return render_template("auth/signup.html")

        # Check if username already exists
        if Users.query.filter_by(users_username=users_username).first():
            flash("Username already exists.", "error")
            return render_template("auth/signup.html")

        # Check if passwords match
        if users_password != users_repeat_password:
            flash("Passwords do not match.", "error")
            return render_template("auth/signup.html")

        # Check password requirements
        if len(users_password) < 8:
            flash("Password must be at least 8 characters.", "error")
            return render_template("auth/signup.html")
        if not any(char.isupper() for char in users_password):
            flash("Password must contain at least one uppercase letter.", "error")
            return render_template("auth/signup.html")
        if not any(char.islower() for char in users_password):
            flash("Password must contain at least one lowercase letter.", "error")
            return render_template("auth/signup.html")
        if not any(char.isdigit() for char in users_password):
            flash("Password must contain at least one number.", "error")
            return render_template("auth/signup.html")
        if not any(char in "!@#$%^&*(),.?\":{}|<>" for char in users_password):
            flash("Password must contain at least one special character.", "error")
            return render_template("auth/signup.html")

        # Ensure the role, student organization, and position are valid Enum values
        if users_role not in Users.users_role.type.enums:
            flash("Invalid role.", "error")
            return render_template("auth/signup.html")
        if users_student_organization and not db.session.get(StudentOrganizations, users_student_organization):
            flash("Invalid student organization.", "error")
            return render_template("auth/signup.html")
        if users_student_organization_position and users_student_organization_position not in Users.users_student_organization_position.type.enums:
            flash("Invalid student organization position.", "error")
            return render_template("auth/signup.html")

        # Get the departments_id through the departments_name
        department = Departments.query.filter_by(departments_name=users_department).first()
        if not department:
            flash("Department not found.", "error")
            return render_template("auth/signup.html")
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

        return redirect(url_for("auth.login"))


@auth_bp.route("/confirm_email/<token>")
def confirm_email(token):
    s = get_serializer()
    try:
        email = s.loads(token, salt='email-confirm', max_age=3600)
    except SignatureExpired:
        flash("The email confirmation link has expired.", "error")
        return redirect(url_for("auth.signup"))
    except BadSignature:
        flash("The email confirmation link is invalid.", "error")
        return redirect(url_for("auth.signup"))

    user = Users.query.filter_by(users_email=email).first_or_404()

    # Check for the existence of the email verification record
    email_verification = EmailVerification.query.filter_by(email_verification_users_id=user.users_id).first()
    if not email_verification:
        flash("The email confirmation link is invalid.", "error")
        return redirect(url_for("auth.login"))

    if user.users_email_verified:
        flash("Account already verified. Please log in.", "error")
    else:
        user.users_email_verified = 1
        db.session.commit()
        flash("Your account has been verified. Please log in.", "success")

        # Delete the email verification record
        db.session.delete(email_verification)
        db.session.commit()

    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("auth/login.html")
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
                return redirect(url_for("auth.login"))
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
                verification_link = url_for('auth.send_verification_email_route', users_email=user.users_email, next='login', _external=True)
                
                flash(Markup(f"Please verify your email before logging in. <a href='{verification_link}'>Click here to resend the verification email.</a>"), "error")
                return redirect(url_for("auth.login"))

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
                return redirect(url_for("dashboard.council_overview"))

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

        return redirect(url_for("auth.login"))


@auth_bp.route("/send_verification_email/<users_email>")
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
        return redirect(url_for("account.email_settings"))
    else:
        return redirect(url_for("auth.login"))


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
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
                return redirect(url_for("auth.login"))

            send_reset_password_email(user.users_email)
            flash("A password reset link has been sent to your email.", "success")
            return redirect(url_for("auth.login"))
        else:
            flash("Email address not found.", "error")
            return redirect(url_for("auth.forgot_password"))
    return render_template("auth/forgot-password.html")


@auth_bp.route("/reset-password/<selector>/<token>", methods=["GET", "POST"])
def reset_password(selector, token):
    password_reset = PasswordReset.query.filter_by(password_reset_selector=selector).first()

    # Check if there is a password reset record
    if not password_reset:
        flash("The password reset link is invalid or has expired.", "error")
        return redirect(url_for("auth.login"))

    # Convert password_reset_expires to a datetime object
    expires = datetime.strptime(password_reset.password_reset_expires, '%Y-%m-%d %H:%M:%S.%f')

    # Check if the token matches and is not expired
    if password_reset.password_reset_token != token or expires < datetime.utcnow():
        flash("The password reset link is invalid or has expired.", "error")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        users_password = request.form.get("users-password")
        users_repeat_password = request.form.get("users-repeat-password")

        if users_password != users_repeat_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("auth.reset_password", selector=selector, token=token))

        user = Users.query.filter_by(users_id=password_reset.password_reset_users_id).first_or_404()
        user.set_password(users_password)
        db.session.commit()

        # Delete the password reset record
        db.session.delete(password_reset)
        db.session.commit()

        flash("Your password has been reset. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset-password.html", selector=selector, token=token)
