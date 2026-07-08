"""
Account routes blueprint for E-Council.
Handles user account management, profile settings, email settings, and password security.
"""

from flask import Blueprint, request, flash, redirect, url_for, render_template
from flask_login import login_required, current_user, logout_user
from itsdangerous import SignatureExpired, BadSignature
from werkzeug.security import generate_password_hash

import cloudinary
import cloudinary.uploader

# Import database models from models package
from models import db, Users, Departments, StudentOrganizations, EmailVerification

# Import email functions from utils.email
from utils.email import (
    send_account_deletion_notification_email,
    send_new_email_verification,
    send_email_change_notification,
    send_email_change_confirmation,
    send_password_change_notification_email
)

# Import serializer from extensions
from extensions import get_serializer

account_bp = Blueprint('account', __name__, url_prefix='/account')


@account_bp.route("/")
@login_required
def account():
    return render_template("account/account.html")


@account_bp.route("/upload-profile-picture", methods=["POST"])
@login_required
def upload_profile_picture():
    profile_picture = request.files.get("profile-picture")
    if (profile_picture):
        # Server-side validation for image file types
        valid_image_types = ['image/jpeg', 'image/png', 'image/jpg']
        if (profile_picture.mimetype not in valid_image_types):
            flash("Invalid file type. Please upload an image file.", "error")
            return redirect(url_for("account.account"))

        # Delete the previous profile picture from Cloudinary if it exists
        existing_profile = current_user.profile_picture or {}
        if existing_profile.get('public_id'):
            cloudinary.uploader.destroy(existing_profile['public_id'])

        # Upload the new profile picture to Cloudinary
        upload_result = cloudinary.uploader.upload(profile_picture)
        profile_picture_url = upload_result["secure_url"]
        profile_picture_public_id = upload_result["public_id"]

        # Update the user's profile picture as a JSON dict
        current_user.profile_picture = {'url': profile_picture_url, 'public_id': profile_picture_public_id}

        db.session.commit()

        flash("Your profile picture has been updated successfully.", "success")
    else:
        flash("No file selected. Please choose a file to upload.", "error")

    return redirect(url_for("account.account"))


@account_bp.route("/account-settings", methods=["GET", "POST"])
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
            return redirect(url_for("account.account_settings"))

        # Ensure the role, student organization, and position are valid Enum values
        if users_role not in Users.users_role.type.enums:
            flash("Invalid role.", "error")
            return redirect(url_for("account.account_settings"))
        if users_student_organization and not db.session.get(StudentOrganizations, users_student_organization):
            flash("Invalid student organization.", "error")
            return redirect(url_for("account.account_settings"))
        if users_student_organization_position and users_student_organization_position not in Users.users_student_organization_position.type.enums:
            flash("Invalid student organization position.", "error")
            return redirect(url_for("account.account_settings"))

        # Get the departments_id through the departments_id
        department = Departments.query.filter_by(departments_id=users_departments_id).first()
        if not department:
            flash("Department not found.", "error")
            return redirect(url_for("account.account_settings"))

        # Clear student organization fields if the role is Faculty or Staff
        if users_role in ["Faculty", "Staff"]:
            users_student_organization = None
            users_student_organization_position = None

        # Handle file upload for the user's signature using Cloudinary
        signature_file = request.files.get("users-signature")
        if signature_file:
            # Server-side validation for image file types
            valid_image_types = ['image/jpeg', 'image/jpg', 'image/png']
            if signature_file.mimetype not in valid_image_types:
                flash("Invalid file type. Please upload an image file.", "error")
                return redirect(url_for("account.account_settings"))

            # Delete the previous image from Cloudinary if it exists
            existing_signature = current_user.signature or {}
            if existing_signature.get('public_id'):
                cloudinary.uploader.destroy(existing_signature['public_id'])

            # Upload the new image to Cloudinary
            upload_result = cloudinary.uploader.upload(signature_file)
            signature_url = upload_result["secure_url"]
            signature_public_id = upload_result["public_id"]

            # Update the user's signature as a JSON dict
            current_user.signature = {'url': signature_url, 'public_id': signature_public_id}

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
        return redirect(url_for("account.account_settings"))

    # Query all departments and student organizations to pass to the template
    departments = Departments.query.all()
    student_organizations = StudentOrganizations.query.all()
    return render_template("account/account-settings.html", departments=departments, student_organizations=student_organizations)


@account_bp.route("/delete-user-account", methods=["POST"])
@login_required
def delete_user_account():
    users_current_password = request.form.get("users-current-password-account-deletion")

    # Validate the current password
    if not current_user.check_password(users_current_password):
        flash("Current password is incorrect.", "error")
        return redirect(url_for("account.account_settings"))

    # Send account deletion notification email
    send_account_deletion_notification_email(current_user.users_email)

    # Delete the user's signature image from Cloudinary if it exists
    existing_signature = current_user.signature or {}
    if existing_signature.get('public_id'):
        cloudinary.uploader.destroy(existing_signature['public_id'])

    # Delete the user's profile picture from Cloudinary if it exists
    existing_profile = current_user.profile_picture or {}
    if existing_profile.get('public_id'):
        cloudinary.uploader.destroy(existing_profile['public_id'])

    # Delete the user account from the database
    user = Users.query.filter_by(users_id=current_user.users_id).first()
    db.session.delete(user)
    db.session.commit()

    # Log the user out
    logout_user()

    flash("Your account has been deleted successfully.", "success")
    return redirect(url_for("auth.login"))


@account_bp.route("/email-settings", methods=["GET", "POST"])
@login_required
def email_settings():
    if request.method == "POST":
        users_new_email = request.form.get("users-new-email")
        current_password = request.form.get("users-current-password")

        # Validate the current password
        if not current_user.check_password(current_password):
            flash("Current password is incorrect.", "error")
            return redirect(url_for("account.email_settings"))

        # Check if the new email is the same as the current email
        if users_new_email == current_user.users_email:
            flash("The new email address is the same as the current email address.", "error")
            return redirect(url_for("account.email_settings"))

        # Check if the new email is already in use
        if Users.query.filter_by(users_email=users_new_email).first():
            flash("The new email address is already in use.", "error")
            return redirect(url_for("account.email_settings"))

        # Check for existing email verification records
        existing_verification = EmailVerification.query.filter_by(
            email_verification_users_id=current_user.users_id
        ).first()

        if existing_verification:
            flash("A verification email has already been sent to this email address. Please check your email.", "error")
            return redirect(url_for("account.email_settings"))

        # Send verification email to the new email address
        send_new_email_verification(users_new_email)

        flash("A verification email has been sent to your new email address. Please check your email to confirm the change.", "success")
        return redirect(url_for("account.email_settings"))

    return render_template("account/email-settings.html")


@account_bp.route("/confirm_new_email/<token>")
@login_required
def confirm_new_email(token):
    try:
        s = get_serializer()
        users_new_email = s.loads(token, salt='email-change', max_age=3600)
    except SignatureExpired:
        flash("The email confirmation link has expired.", "error")
        return redirect(url_for("account.email_settings"))
    except BadSignature:
        flash("The email confirmation link is invalid.", "error")
        return redirect(url_for("account.email_settings"))

    # Retrieve the email verification record
    email_verification = EmailVerification.query.filter_by(email_verification_token=token).first()
    if not email_verification:
        flash("The email confirmation link is invalid.", "error")
        return redirect(url_for("account.email_settings"))

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
    return redirect(url_for("account.email_settings"))


@account_bp.route("/password-security-settings", methods=["GET", "POST"])
@login_required
def password_security_settings():
    if request.method == "POST":
        users_password = request.form.get("users-password")
        users_repeat_password = request.form.get("users-repeat-password")

        # Validate the new password
        if users_password != users_repeat_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("account.password_security_settings"))

        if len(users_password) < 8:
            flash("Password must be at least 8 characters long.", "error")
            return redirect(url_for("account.password_security_settings"))

        if not any(char.isupper() for char in users_password):
            flash("Password must contain at least one uppercase letter.", "error")
            return redirect(url_for("account.password_security_settings"))

        if not any(char.islower() for char in users_password):
            flash("Password must contain at least one lowercase letter.", "error")
            return redirect(url_for("account.password_security_settings"))

        if not any(char.isdigit() for char in users_password):
            flash("Password must contain at least one number.", "error")
            return redirect(url_for("account.password_security_settings"))

        if not any(char in "!@#$%^&*(),.?\":{}|<>" for char in users_password):
            flash("Password must contain at least one special character.", "error")
            return redirect(url_for("account.password_security_settings"))

        # Update the user's password in the database
        current_user.users_password = generate_password_hash(users_password)
        db.session.commit()
        
        # Send password change update email
        send_password_change_notification_email(current_user.users_email)

        flash("Your password has been updated successfully.", "success")
        return redirect(url_for("account.password_security_settings"))

    return render_template("account/password-security-settings.html")
