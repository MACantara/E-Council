"""FastAPI auth endpoints for the E-Council API prototype."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
)
from api.schemas.auth import Token, TokenRefresh, UserCreate, UserLogin, UserResponse
from models import Users
from repositories.users import UserRepository

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    if UserRepository.get_by_username(db, user.users_username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )
    if UserRepository.get_by_email(db, user.users_email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )

    new_user = UserRepository.create(db, **user.model_dump())
    db.commit()
    return new_user


@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate a user and return JWT tokens."""
    db_user = UserRepository.authenticate(
        db, login_data.users_username_or_email, login_data.users_password
    )
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
        )

    return {
        "access_token": create_access_token(db_user.users_id),
        "refresh_token": create_refresh_token(db_user.users_id),
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
def refresh(token_data: TokenRefresh, db: Session = Depends(get_db)):
    """Refresh an access token using a refresh token."""
    payload = decode_token(token_data.refresh_token, "refresh")
    user_id = int(payload["sub"])
    user = UserRepository.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return {
        "access_token": create_access_token(user.users_id),
        "refresh_token": create_refresh_token(user.users_id),
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserResponse)
def me(current_user: Users = Depends(get_current_user)):
    """Return the current authenticated user."""
    return current_user
