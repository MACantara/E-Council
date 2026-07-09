"""FastAPI auth endpoints for the E-Council API prototype."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    get_email,
    get_request_ip,
)
from api.emails import (
    reset_password,
    send_password_reset_email,
    send_verification_email,
    verify_email_token,
)
from api.schemas.auth import (
    ForgotPassword,
    ResendVerification,
    ResetPassword,
    Token,
    TokenRefresh,
    UserCreate,
    UserLogin,
    UserResponse,
    VerifyEmailToken,
)
from api.schemas.common import MessageResponse
from models import EmailVerification, LoginAttempts, PasswordReset, Users
from repositories.users import UserRepository
from services.email import EmailBackend

router = APIRouter(prefix="/auth", tags=["auth"])


def _login_attempts_exceeded(db: Session, ip_address: str) -> bool:
    """Return True if the IP address has exceeded the login attempt limit."""
    attempt = db.query(LoginAttempts).filter_by(login_attempt_ip_address=ip_address).first()
    if attempt is None:
        return False
    if attempt.login_attempt_count >= 5:
        if datetime.utcnow() - attempt.login_attempt_last_attempt_time < timedelta(minutes=15):
            return True
        attempt.login_attempt_count = 0
        db.commit()
    return False


def _record_login_attempt(
    db: Session,
    ip_address: str,
    *,
    success: bool,
) -> None:
    """Record a login attempt for rate limiting."""
    attempt = db.query(LoginAttempts).filter_by(login_attempt_ip_address=ip_address).first()
    if attempt is None:
        attempt = LoginAttempts(login_attempt_ip_address=ip_address, login_attempt_count=0)
        db.add(attempt)
    if success:
        attempt.login_attempt_count = 0
    else:
        attempt.login_attempt_count += 1
    db.commit()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user: UserCreate,
    db: Session = Depends(get_db),
    backend: EmailBackend = Depends(get_email),
):
    """Register a new user and send a verification email."""
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

    data = user.model_dump(exclude={"users_repeat_password"})
    data["users_email_verified"] = 0
    new_user = UserRepository.create(db, **data)
    db.commit()

    send_verification_email(db, backend, new_user)
    return new_user


@router.post("/login", response_model=Token)
def login(
    request: Request,
    login_data: UserLogin,
    db: Session = Depends(get_db),
):
    """Authenticate a user and return JWT tokens."""
    ip_address = get_request_ip(request)

    if _login_attempts_exceeded(db, ip_address):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )

    db_user = UserRepository.authenticate(db, login_data.users_username_or_email, login_data.users_password)
    if db_user is None:
        _record_login_attempt(db, ip_address, success=False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
        )

    if db_user.users_email_verified == 0:
        _record_login_attempt(db, ip_address, success=False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please verify your email before logging in.",
        )

    _record_login_attempt(db, ip_address, success=True)
    return {
        "access_token": create_access_token(db_user.users_id),
        "refresh_token": create_refresh_token(db_user.users_id),
        "token_type": "bearer",
    }


@router.post("/logout", response_model=MessageResponse)
def logout():
    """Log the current user out.

    JWT tokens are stateless; the client is responsible for discarding them.
    """
    return MessageResponse(message="Logged out successfully")


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


@router.post("/resend-verification", response_model=MessageResponse)
def resend_verification(
    payload: ResendVerification,
    db: Session = Depends(get_db),
    backend: EmailBackend = Depends(get_email),
):
    """Resend the email verification link for a pending account."""
    user = UserRepository.get_by_email(db, payload.users_email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if user.users_email_verified == 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified",
        )

    existing = (
        db.query(EmailVerification)
        .filter_by(email_verification_users_id=user.users_id, email_verification_new_email=user.users_email)
        .first()
    )
    if existing:
        db.delete(existing)
        db.commit()

    send_verification_email(db, backend, user)
    return MessageResponse(message="A verification email has been sent.")


@router.post("/verify-email", response_model=MessageResponse)
def verify_email(
    payload: VerifyEmailToken,
    db: Session = Depends(get_db),
):
    """Verify a user's email address using a token from the verification email."""
    try:
        verify_email_token(db, payload.token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return MessageResponse(message="Your email has been verified. Please log in.")


@router.get("/verify-email/{token}", response_model=MessageResponse)
def verify_email_link(
    token: str,
    db: Session = Depends(get_db),
):
    """Verify a user's email address using a link from the verification email."""
    try:
        verify_email_token(db, token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return MessageResponse(message="Your email has been verified. Please log in.")


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(
    payload: ForgotPassword,
    db: Session = Depends(get_db),
    backend: EmailBackend = Depends(get_email),
):
    """Send a password reset link to the user's email."""
    user = UserRepository.get_by_email(db, payload.users_email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email address not found",
        )

    existing = db.query(PasswordReset).filter_by(password_reset_users_id=user.users_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A password reset email has already been sent. Please check your email.",
        )

    send_password_reset_email(db, backend, user)
    return MessageResponse(message="A password reset link has been sent to your email.")


@router.post("/reset-password/{selector}/{token}", response_model=MessageResponse)
def reset_password_endpoint(
    selector: str,
    token: str,
    payload: ResetPassword,
    db: Session = Depends(get_db),
):
    """Reset a password using a selector and token."""
    try:
        reset_password(db, selector, token, payload.users_password)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    return MessageResponse(message="Your password has been reset. Please log in.")


@router.get("/me", response_model=UserResponse)
def me(current_user: Users = Depends(get_current_user)):
    """Return the current authenticated user."""
    return current_user
