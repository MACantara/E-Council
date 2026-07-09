"""
Authentication routes blueprint for E-Council.
Handles user registration, login, logout, password reset, and email verification.
"""

from datetime import datetime, timedelta

# Import current app to get SECRET_KEY for serializer
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_limiter.util import get_remote_address
from flask_login import login_required, login_user, logout_user
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from markupsafe import Markup

from extensions import limiter

# Import authentication forms
from forms.auth import ForgotPasswordForm, LoginForm, ResetPasswordForm, SignupForm

# Import database models from models package
from models import Departments, EmailVerification, LoginAttempts, PasswordReset, StudentOrganizations, Users, db

# Import email functions from utils.email
from utils.email import send_reset_password_email, send_verification_email


# Initialize URLSafeTimedSerializer
def get_serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


# Create blueprint with url_prefix='/auth'
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _flash_form_errors(form):
    """Flash form validation errors, grouping required field errors."""
    has_required = False
    for _field_name, errors in form.errors.items():
        for error in errors:
            # Treat any input-required style message as a generic required-field error
            if isinstance(error, str) and error.lower() in {
                "this field is required.",
                "input is required.",
            }:
                has_required = True
            else:
                flash(error, "error")
    if has_required:
        flash("All fields are required.", "error")


@auth_bp.route("/signup", methods=["GET", "POST"])
@limiter.limit("3 per hour")
def signup():
    department_choices = [(d.departments_name, d.departments_name) for d in Departments.query.all()]
    organization_choices = [
        (str(o.student_organizations_id), o.student_organizations_name) for o in StudentOrganizations.query.all()
    ]

    form = SignupForm(
        departments=department_choices,
        organizations=organization_choices,
    )

    if form.validate_on_submit():
        department = Departments.query.filter_by(departments_name=form.users_department.data).first()
        users_departments_id = department.departments_id

        user = Users(
            users_first_name=form.users_first_name.data,
            users_last_name=form.users_last_name.data,
            users_username=form.users_username.data,
            users_email=form.users_email.data,
            users_departments_id=users_departments_id,
            users_role=form.users_role.data,
            users_student_organization=form.users_student_organization.data,
            users_student_organization_position=form.users_student_organization_position.data,
            users_email_verified=0,
        )

        user.set_password(form.users_password.data)

        db.session.add(user)
        db.session.commit()

        send_verification_email(form.users_email.data)

        flash("Account created! Please check your email to verify your account.", "success")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        _flash_form_errors(form)

    return render_template("auth/signup.html", form=form)


@auth_bp.route("/confirm_email/<token>")
def confirm_email(token):
    s = get_serializer()
    try:
        email = s.loads(token, salt="email-confirm", max_age=3600)
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
@limiter.limit("5 per minute")
def login():
    form = LoginForm()

    if form.validate_on_submit():
        users_username_email = form.users_username_email.data
        users_password = form.users_password.data
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
                verification_link = url_for(
                    "auth.send_verification_email_route", users_email=user.users_email, next="login", _external=True
                )

                flash(
                    Markup(
                        f"Please verify your email before logging in. <a href='{verification_link}'>Click here to resend the verification email.</a>"
                    ),
                    "error",
                )
                return redirect(url_for("auth.login"))

            if user.check_password(users_password):
                login_user(user)
                # Reset login attempts on successful login
                if login_attempt:
                    login_attempt.login_attempt_count = 0
                else:
                    login_attempt = LoginAttempts(login_attempt_ip_address=ip_address, login_attempt_count=0)
                    db.session.add(login_attempt)
                db.session.commit()
                return redirect(url_for("dashboard.council_overview"))

        # Increment login attempts on failure
        if login_attempt:
            login_attempt.login_attempt_count += 1
        else:
            login_attempt = LoginAttempts(login_attempt_ip_address=ip_address, login_attempt_count=1)
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

    if request.method == "POST":
        _flash_form_errors(form)

    return render_template("auth/login.html", form=form)


@auth_bp.route("/send_verification_email/<users_email>")
def send_verification_email_route(users_email):
    next_route = request.args.get("next", "login")  # Default to 'login' if 'next' is not provided
    user = Users.query.filter_by(users_email=users_email).first_or_404()
    if user.users_email_verified == 0:
        # Check for existing email verification records
        existing_verification = EmailVerification.query.filter_by(
            email_verification_users_id=user.users_id, email_verification_new_email=users_email
        ).first()

        if existing_verification:
            flash("A verification email has already been sent to this email address. Please check your email.", "error")
        else:
            send_verification_email(user.users_email)
            flash("A verification email has been sent to your email.", "success")
    else:
        flash("This email is already verified.", "info")

    # Redirect to the appropriate route based on the 'next' query parameter
    if next_route == "email_settings":
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
@limiter.limit("3 per hour")
def forgot_password():
    form = ForgotPasswordForm()

    if form.validate_on_submit():
        users_email = form.users_email.data
        user = Users.query.filter_by(users_email=users_email).first()
        if user:
            # Check for existing password reset records
            existing_reset = PasswordReset.query.filter_by(password_reset_users_id=user.users_id).first()

            if existing_reset:
                flash(
                    "A password reset email has already been sent to this email address. Please check your email.",
                    "error",
                )
                return redirect(url_for("auth.login"))

            send_reset_password_email(user.users_email)
            flash("A password reset link has been sent to your email.", "success")
            return redirect(url_for("auth.login"))
        else:
            flash("Email address not found.", "error")
            return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        _flash_form_errors(form)

    return render_template("auth/forgot-password.html", form=form)


@auth_bp.route("/reset-password/<selector>/<token>", methods=["GET", "POST"])
@limiter.limit("5 per minute", key_func=lambda: request.view_args.get("token", get_remote_address()))
def reset_password(selector, token):
    password_reset = PasswordReset.query.filter_by(password_reset_selector=selector).first()

    # Check if there is a password reset record
    if not password_reset:
        flash("The password reset link is invalid or has expired.", "error")
        return redirect(url_for("auth.login"))

    # Convert password_reset_expires to a datetime object
    expires = datetime.strptime(password_reset.password_reset_expires, "%Y-%m-%d %H:%M:%S.%f")

    # Check if the token matches and is not expired
    if password_reset.password_reset_token != token or expires < datetime.utcnow():
        flash("The password reset link is invalid or has expired.", "error")
        return redirect(url_for("auth.forgot_password"))

    form = ResetPasswordForm()

    if form.validate_on_submit():
        user = Users.query.filter_by(users_id=password_reset.password_reset_users_id).first_or_404()
        user.set_password(form.users_password.data)
        db.session.commit()

        # Delete the password reset record
        db.session.delete(password_reset)
        db.session.commit()

        flash("Your password has been reset. Please log in.", "success")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        _flash_form_errors(form)

    return render_template("auth/reset-password.html", form=form, selector=selector, token=token)
