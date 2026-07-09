"""Authentication forms for E-Council."""

from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, SelectField, StringField
from wtforms.validators import (
    AnyOf,
    Email,
    EqualTo,
    InputRequired,
    Length,
    ValidationError,
)

from forms.validators import PasswordStrength
from models import Departments, Users


class SignupForm(FlaskForm):
    """Registration form for new users."""

    users_first_name = StringField(
        "First Name",
        name="users-first-name",
        id="users-first-name",
        validators=[InputRequired()],
        render_kw={"placeholder": "First Name"},
    )
    users_last_name = StringField(
        "Last Name",
        name="users-last-name",
        id="users-last-name",
        validators=[InputRequired()],
        render_kw={"placeholder": "Last Name"},
    )
    users_username = StringField(
        "Username",
        name="users-username",
        id="users-username",
        validators=[InputRequired(), Length(min=3, max=50)],
        render_kw={"placeholder": "Username"},
    )
    users_email = EmailField(
        "Email",
        name="users-email",
        id="users-email",
        validators=[InputRequired(), Email()],
        render_kw={"placeholder": "Email"},
    )
    users_department = SelectField(
        "Department",
        name="users-department",
        id="users-department",
        validators=[InputRequired()],
        choices=[],
        default="",
        validate_choice=False,
    )
    users_role = SelectField(
        "Role",
        name="users-role",
        id="users-role",
        validators=[
            InputRequired(),
            AnyOf(Users.users_role.type.enums, message="Invalid role."),
        ],
        choices=[("", "Select a Role")] + [(role, role) for role in Users.users_role.type.enums],
        default="",
        validate_choice=False,
    )
    users_student_organization = SelectField(
        "Student Organization",
        name="users-student-organization",
        id="users-student-organization",
        validators=[],
        choices=[],
        default="",
        validate_choice=False,
    )
    users_student_organization_position = SelectField(
        "Student Organization Position",
        name="users-student-organization-position",
        id="users-student-organization-position",
        validators=[],
        choices=[("", "Select a Student Organization Position")]
        + [(position, position) for position in Users.users_student_organization_position.type.enums],
        default="",
        validate_choice=False,
    )
    users_password = PasswordField(
        "Password",
        name="users-password",
        id="users-password",
        validators=[InputRequired(), PasswordStrength()],
        render_kw={"placeholder": "Password"},
    )
    users_repeat_password = PasswordField(
        "Repeat Password",
        name="users-repeat-password",
        id="users-repeat-password",
        validators=[
            InputRequired(),
            EqualTo("users_password", message="Passwords do not match."),
        ],
        render_kw={"placeholder": "Repeat Password"},
    )

    def __init__(self, departments=None, organizations=None, **kwargs):
        super().__init__(**kwargs)
        if departments is not None:
            self.users_department.choices = [("", "Select a Department")] + departments
        if organizations is not None:
            self.users_student_organization.choices = [("", "Select a Student Organization")] + organizations

    def validate_users_username(self, users_username):
        if Users.query.filter_by(users_username=users_username.data).first():
            raise ValidationError("Username already exists.")

    def validate_users_email(self, users_email):
        if Users.query.filter_by(users_email=users_email.data).first():
            raise ValidationError("Email already exists.")

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False

        if not Departments.query.filter_by(departments_name=self.users_department.data).first():
            raise ValidationError("Department not found.")

        if self.users_role.data == "Student Council Officer":
            if not self.users_student_organization.data:
                raise ValidationError("Student Organization and Position are required for Student Council Officers.")
            if not self.users_student_organization_position.data:
                raise ValidationError("Student Organization and Position are required for Student Council Officers.")
        else:
            self.users_student_organization.data = None
            self.users_student_organization_position.data = None

        return True


class LoginForm(FlaskForm):
    """Login form for existing users."""

    users_username_email = StringField(
        "Username / Email",
        name="users-username-email",
        id="users-username-email",
        validators=[InputRequired()],
        render_kw={"placeholder": "Username or email"},
    )
    users_password = PasswordField(
        "Password",
        name="users-password",
        id="users-password",
        validators=[InputRequired()],
        render_kw={"placeholder": "Password"},
    )


class ForgotPasswordForm(FlaskForm):
    """Forgot password form for requesting a reset link."""

    users_email = EmailField(
        "Email",
        name="users-email",
        id="users-email",
        validators=[InputRequired(), Email()],
        render_kw={"placeholder": "Enter your email"},
    )


class ResetPasswordForm(FlaskForm):
    """Reset password form for creating a new password."""

    users_password = PasswordField(
        "Password",
        name="users-password",
        id="users-password",
        validators=[InputRequired(), PasswordStrength()],
        render_kw={"placeholder": "Password"},
    )
    users_repeat_password = PasswordField(
        "Repeat Password",
        name="users-repeat-password",
        id="users-repeat-password",
        validators=[
            InputRequired(),
            EqualTo("users_password", message="Passwords do not match."),
        ],
        render_kw={"placeholder": "Repeat Password"},
    )
