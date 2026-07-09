"""FastAPI dependencies for authentication, database access, and shared infrastructure."""

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, Query, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt
from jose.exceptions import JWTError
from sqlalchemy.orm import Session

from api.database import get_db
from api.schemas.common import OrderEnum, PaginationParams
from api.settings import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    REFRESH_TOKEN_EXPIRE_DAYS,
    SECRET_KEY,
)
from models import Users
from repositories.users import UserRepository
from services.storage import StorageBackend, StorageError, get_storage as _get_storage_service

security = HTTPBearer(auto_error=False)


def create_access_token(user_id: int) -> str:
    """Create a short-lived JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire, "type": "access"}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    """Create a long-lived JWT refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": str(user_id), "exp": expire, "type": "refresh"}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str, token_type: str) -> dict[str, Any]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != token_type:
            raise JWTError("Invalid token type")
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> Users:
    """Return the current user from a JWT access token."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials, "access")
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    user = UserRepository.get_by_id(db, int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return user


def is_admin(user: Users) -> bool:
    """Return True if the user has the Admin role."""
    return user.users_role == "Admin"


def require_admin(current_user: Users = Depends(get_current_user)) -> Users:
    """Dependency that enforces the current user is an admin."""
    if not is_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def require_role(*roles: str):
    """Factory for dependencies that enforce one of the given roles."""

    def _require_role(current_user: Users = Depends(get_current_user)) -> Users:
        if current_user.users_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access restricted to roles: {', '.join(roles)}",
            )
        return current_user

    return _require_role


def get_pagination_params(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    sort: str | None = Query(None),
    order: OrderEnum = Query(OrderEnum.asc),
    search: str | None = Query(None),
) -> PaginationParams:
    """Return a PaginationParams instance from query string values."""
    return PaginationParams(
        page=page,
        per_page=per_page,
        sort=sort,
        order=order,
        search=search,
    )


def get_storage() -> StorageBackend:
    """Return the configured storage backend for the current request."""
    return _get_storage_service()


def save_upload(
    file: UploadFile,
    storage: StorageBackend,
    *,
    folder: str | None = None,
    resource_type: str = "auto",
) -> dict[str, str]:
    """Save an uploaded file to the configured storage backend.

    Returns a dict with ``url`` and ``public_id`` as returned by the backend.
    """
    try:
        return storage.upload(file.file, folder=folder, resource_type=resource_type)
    except StorageError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc.message),
        ) from exc


def check_ownership(current_user: Users, owner_id: int) -> None:
    """Raise a 403 Forbidden if the current user does not own the resource.

    Admins are treated as owners for every resource.
    """
    if not is_admin(current_user) and current_user.users_id != owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource",
        )
