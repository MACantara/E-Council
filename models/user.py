"""
User and authentication-related models for E-Council.
"""

from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from models.base import db


class Users(db.Model, UserMixin):
    __tablename__ = "users"

    users_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    profile_picture = db.Column(db.JSON, nullable=False, default=dict)
    users_title = db.Column(db.String(50), nullable=True)
    users_first_name = db.Column(db.String(50), nullable=False)
    users_middle_name = db.Column(db.String(50), nullable=True)
    users_last_name = db.Column(db.String(50), nullable=False)
    users_suffix = db.Column(db.String(50), nullable=True)
    users_username = db.Column(db.String(50), unique=True, nullable=False)
    users_email = db.Column(db.String(100), unique=True, nullable=False)

    # Changed users_department to reference the Departments model
    users_departments_id = db.Column(
        db.Integer, db.ForeignKey("departments.departments_id"), nullable=False, index=True
    )

    users_role = db.Column(
        db.Enum("Student Council Officer", "Faculty", "Staff", "Admin", name="role_enum"), nullable=False, index=True
    )

    users_student_organization = db.Column(
        db.Integer, db.ForeignKey("student_organizations.student_organizations_id"), nullable=True, index=True
    )

    users_student_organization_position = db.Column(
        db.Enum(
            "President",
            "Vice President",
            "Secretary",
            "Treasurer",
            "Auditor",
            "Business Manager",
            "Public Relations Officer",
            "1st Year IT Representative",
            "1st Year CS Representative",
            "2nd Year IT Representative",
            "2nd Year CS Representative",
            "3rd Year IT Representative",
            "3rd Year CS Representative",
            "4th Year IT Representative",
            "4th Year CS Representative",
            name="position_enum",
        ),
        nullable=True,
    )

    users_home_address = db.Column(db.String(255), nullable=True)
    users_contact_number = db.Column(db.String(20), nullable=True)
    signature = db.Column(db.JSON, nullable=False, default=dict)
    users_password = db.Column(db.String(255), nullable=False)
    users_email_verified = db.Column(db.Integer, nullable=False)

    # Relationship to Departments
    department = db.relationship("Departments", backref="users")

    student_organization = db.relationship("StudentOrganizations", backref="users")

    def set_password(self, password):
        self.users_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.users_password, password)

    @property
    def users_department_name(self):
        """Return the department name for API response serialization."""
        return self.department.departments_name if self.department else None

    def get_id(self):
        return str(self.users_id)

    def __repr__(self):
        return f"Users({self.users_id}, {self.users_first_name}, {self.users_last_name}, {self.users_username}, {self.users_email}, {self.users_role}, {self.users_email_verified})"


class EmailVerification(db.Model):
    __tablename__ = "email_verification"

    email_verification_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    email_verification_users_id = db.Column(db.Integer, db.ForeignKey("users.users_id"), nullable=False, index=True)
    email_verification_token = db.Column(db.String(255), nullable=False)
    email_verification_new_email = db.Column(db.String(100), nullable=False)
    email_verification_created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

    user = db.relationship("Users", backref=db.backref("email_verifications", lazy=True))


class PasswordReset(db.Model):
    __tablename__ = "password_reset"

    password_reset_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    password_reset_users_id = db.Column(db.Integer, db.ForeignKey("users.users_id"), nullable=False, index=True)
    password_reset_selector = db.Column(db.String(255), nullable=False)
    password_reset_token = db.Column(db.String(255), nullable=False)
    password_reset_expires = db.Column(db.DateTime, nullable=False)

    user = db.relationship("Users", backref=db.backref("password_resets", lazy=True))


class LoginAttempts(db.Model):
    __tablename__ = "login_attempts"

    login_attempt_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    login_attempt_ip_address = db.Column(db.String(45), nullable=False)
    login_attempt_count = db.Column(db.Integer, nullable=False, default=0)
    login_attempt_last_attempt_time = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
