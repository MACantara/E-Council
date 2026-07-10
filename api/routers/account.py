"""FastAPI account endpoints for the E-Council API prototype."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies import get_current_user, get_email, get_storage
from api.emails import (
    confirm_new_email,
    send_account_deletion_notification,
    send_email_change_confirmation,
    send_email_change_notification,
    send_new_email_verification,
    send_password_change_notification,
)
from api.schemas.account import (
    AccountDelete,
    AccountUpdate,
    EmailChange,
    PasswordChange,
)
from api.schemas.auth import UserResponse
from api.schemas.common import MessageResponse
from models import Departments, EmailVerification, StudentOrganizations, Users
from services.email import EmailBackend
from services.storage import StorageBackend

router = APIRouter(prefix="/account", tags=["account"])


def _valid_image_type(file: UploadFile) -> bool:
    """Return True if the uploaded file is an allowed image type."""
    return file.content_type in ["image/jpeg", "image/jpg", "image/png"]


def _upload_image(
    storage: StorageBackend,
    file: UploadFile,
    existing: dict,
    *,
    folder: str | None = None,
) -> dict[str, str]:
    """Upload an image to storage and delete the previous asset if present."""
    if not _valid_image_type(file):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Please upload an image file.",
        )

    if existing.get("public_id"):
        storage.delete(existing["public_id"])

    result = storage.upload(file.file, folder=folder, resource_type="image")
    return {"url": result["url"], "public_id": result.get("public_id", "")}


@router.get("/me", response_model=UserResponse)
def me(current_user: Users = Depends(get_current_user)):
    """Return the current authenticated user's account details."""
    return current_user


@router.put("/", response_model=UserResponse)
def update_account(
    payload: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
):
    """Update the current user's account settings."""
    if not current_user.check_password(payload.users_current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    department = db.query(Departments).filter_by(departments_id=payload.users_departments_id).first()
    if department is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found.",
        )

    if (
        payload.users_student_organization is not None
        and db.query(StudentOrganizations)
        .filter_by(student_organizations_id=payload.users_student_organization)
        .first()
        is None
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student organization not found.",
        )

    if payload.users_role in ["Faculty", "Staff"]:
        student_organization = None
        student_organization_position = None
    else:
        student_organization = payload.users_student_organization
        student_organization_position = payload.users_student_organization_position

    current_user.users_first_name = payload.users_first_name
    current_user.users_last_name = payload.users_last_name
    current_user.users_username = payload.users_username
    current_user.users_departments_id = payload.users_departments_id
    current_user.users_role = payload.users_role
    current_user.users_student_organization = student_organization
    current_user.users_student_organization_position = student_organization_position
    current_user.users_home_address = payload.users_home_address
    current_user.users_contact_number = payload.users_contact_number
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/profile-picture", response_model=UserResponse)
def upload_profile_picture(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
    storage: StorageBackend = Depends(get_storage),
):
    """Upload or update the current user's profile picture."""
    current_user.profile_picture = _upload_image(
        storage,
        file,
        current_user.profile_picture or {},
        folder="profile_pictures",
    )
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/signature", response_model=UserResponse)
def upload_signature(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
    storage: StorageBackend = Depends(get_storage),
):
    """Upload or update the current user's signature image."""
    current_user.signature = _upload_image(
        storage,
        file,
        current_user.signature or {},
        folder="signatures",
    )
    db.commit()
    db.refresh(current_user)
    return current_user


@router.put("/password", response_model=MessageResponse)
def change_password(
    payload: PasswordChange,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
    backend: EmailBackend = Depends(get_email),
):
    """Change the current user's password."""
    if not current_user.check_password(payload.users_current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    current_user.set_password(payload.users_new_password)
    db.commit()

    send_password_change_notification(backend, current_user.users_email)
    return MessageResponse(message="Your password has been updated successfully.")


@router.put("/email", response_model=MessageResponse)
def change_email(
    payload: EmailChange,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
    backend: EmailBackend = Depends(get_email),
):
    """Request an email change by sending a verification to the new address."""
    if not current_user.check_password(payload.users_current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    if payload.users_new_email == current_user.users_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The new email address is the same as the current email address.",
        )

    existing_user = db.query(Users).filter_by(users_email=payload.users_new_email).first()
    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The new email address is already in use.",
        )

    existing_verification = (
        db.query(EmailVerification).filter_by(email_verification_users_id=current_user.users_id).first()
    )
    if existing_verification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A verification email has already been sent to this email address. Please check your email.",
        )

    send_new_email_verification(db, backend, current_user, payload.users_new_email)
    return MessageResponse(
        message="A verification email has been sent to your new email address. Please check your email to confirm the change."
    )


@router.get("/confirm-new-email/{token}", response_model=MessageResponse)
def confirm_new_email_endpoint(
    token: str,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
    backend: EmailBackend = Depends(get_email),
):
    """Confirm a new email address using the verification token."""
    try:
        old_email = confirm_new_email(db, token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    send_email_change_notification(backend, old_email, current_user.users_email)
    send_email_change_confirmation(backend, current_user.users_email)
    return MessageResponse(message="Your email has been updated successfully.")


@router.delete("/", response_model=MessageResponse)
def delete_account(
    payload: AccountDelete,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_user),
    storage: StorageBackend = Depends(get_storage),
    backend: EmailBackend = Depends(get_email),
):
    """Delete the current user's account."""
    if not current_user.check_password(payload.users_current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    send_account_deletion_notification(backend, current_user.users_email)

    if current_user.signature.get("public_id"):
        storage.delete(current_user.signature["public_id"])
    if current_user.profile_picture.get("public_id"):
        storage.delete(current_user.profile_picture["public_id"])

    db.delete(current_user)
    db.commit()
    return MessageResponse(message="Your account has been deleted successfully.")
