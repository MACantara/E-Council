"""Pydantic request/response models for the FastAPI auth prototype."""

from typing import Literal

from pydantic import BaseModel, EmailStr, Field, model_validator


# Shared role literals used in both schemas and validators.
ROLE_CHOICES = (
    "Student Council Officer",
    "Faculty",
    "Staff",
    "Admin",
)

POSITION_CHOICES = (
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
)


class UserBase(BaseModel):
    """Shared user fields."""

    users_first_name: str = Field(..., min_length=1, max_length=50)
    users_last_name: str = Field(..., min_length=1, max_length=50)
    users_username: str = Field(..., min_length=3, max_length=50)
    users_email: EmailStr
    users_role: Literal[ROLE_CHOICES] = "Student Council Officer"
    users_department_name: str = Field(..., min_length=1, max_length=255)
    users_student_organization: int | None = None
    users_student_organization_position: Literal[POSITION_CHOICES] | None = None
    users_home_address: str | None = Field(None, max_length=255)
    users_contact_number: str | None = Field(None, max_length=20)


class UserCreate(UserBase):
    """User registration request."""

    users_password: str = Field(..., min_length=8, max_length=128)
    users_repeat_password: str = Field(..., min_length=8, max_length=128)

    @model_validator(mode="after")
    def _check_passwords(self) -> "UserCreate":
        """Ensure the password and repeat password match."""
        if self.users_password != self.users_repeat_password:
            raise ValueError("Passwords do not match.")
        return self

    @model_validator(mode="after")
    def _check_student_organization(self) -> "UserCreate":
        """Student organization and position are required for Student Council Officers."""
        if self.users_role == "Student Council Officer":
            if self.users_student_organization is None:
                raise ValueError("Student organization is required for Student Council Officers.")
            if self.users_student_organization_position is None:
                raise ValueError("Student organization position is required for Student Council Officers.")
        return self


class UserResponse(UserBase):
    """User response model."""

    users_id: int
    users_email_verified: int
    profile_picture: dict | None = None
    signature: dict | None = None

    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    """User login request."""

    users_username_or_email: str = Field(..., min_length=3)
    users_password: str = Field(..., min_length=8, max_length=128)


class Token(BaseModel):
    """Token response model."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    """Refresh token request."""

    refresh_token: str


class ResendVerification(BaseModel):
    """Request body for resending a verification email."""

    users_email: EmailStr


class ForgotPassword(BaseModel):
    """Request body for requesting a password reset."""

    users_email: EmailStr


class ResetPassword(BaseModel):
    """Request body for resetting a password."""

    users_password: str = Field(..., min_length=8, max_length=128)
    users_repeat_password: str = Field(..., min_length=8, max_length=128)

    @model_validator(mode="after")
    def _check_passwords(self) -> "ResetPassword":
        if self.users_password != self.users_repeat_password:
            raise ValueError("Passwords do not match.")
        return self


class VerifyEmailToken(BaseModel):
    """Request body for confirming an email with a token."""

    token: str
