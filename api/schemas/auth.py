"""Pydantic request/response models for the FastAPI auth prototype."""

from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Shared user fields."""

    users_first_name: str = Field(..., min_length=1, max_length=50)
    users_last_name: str = Field(..., min_length=1, max_length=50)
    users_username: str = Field(..., min_length=3, max_length=50)
    users_email: EmailStr
    users_role: Literal[
        "Student Council Officer",
        "Faculty",
        "Staff",
        "Admin",
    ] = "Student Council Officer"
    users_department_name: str = Field(..., min_length=1, max_length=255)


class UserCreate(UserBase):
    """User registration request."""

    users_password: str = Field(..., min_length=8, max_length=128)


class UserResponse(UserBase):
    """User response model."""

    users_id: int

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
