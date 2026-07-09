"""Pydantic schemas for the FastAPI account endpoints."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, EmailStr, Field, model_validator

from api.schemas.auth import POSITION_CHOICES, ROLE_CHOICES


class AccountUpdate(BaseModel):
    """Request body for updating account settings."""

    users_first_name: str = Field(..., min_length=1, max_length=50)
    users_last_name: str = Field(..., min_length=1, max_length=50)
    users_username: str = Field(..., min_length=3, max_length=50)
    users_departments_id: int
    users_role: Literal[ROLE_CHOICES]
    users_student_organization: int | None = None
    users_student_organization_position: Literal[POSITION_CHOICES] | None = None
    users_home_address: str | None = Field(None, max_length=255)
    users_contact_number: str | None = Field(None, max_length=20)
    users_current_password: str

    @model_validator(mode="after")
    def _check_student_organization(self) -> "AccountUpdate":
        """Student organization and position are required for Student Council Officers."""
        if self.users_role == "Student Council Officer":
            if self.users_student_organization is None:
                raise ValueError("Student organization is required for Student Council Officers.")
            if self.users_student_organization_position is None:
                raise ValueError("Student organization position is required for Student Council Officers.")
        return self


class PasswordChange(BaseModel):
    """Request body for changing the current user's password."""

    users_current_password: str
    users_new_password: str = Field(..., min_length=8, max_length=128)
    users_repeat_password: str = Field(..., min_length=8, max_length=128)

    @model_validator(mode="after")
    def _check_passwords(self) -> "PasswordChange":
        if self.users_new_password != self.users_repeat_password:
            raise ValueError("Passwords do not match.")
        return self


class EmailChange(BaseModel):
    """Request body for changing the user's email address."""

    users_new_email: EmailStr
    users_current_password: str


class AccountDelete(BaseModel):
    """Request body for deleting the current user's account."""

    users_current_password: str
