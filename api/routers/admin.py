"""FastAPI admin endpoints for the E-Council API prototype."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies import get_pagination_params, require_admin
from api.schemas.admin import UserListResponse, UserRoleUpdate
from api.schemas.auth import UserResponse
from api.schemas.common import MessageResponse, PaginationParams
from models import Users

router = APIRouter(prefix="/admin", tags=["admin"])


def _apply_user_search(query, search: str | None):
    """Filter a user query by a search term across names, username, and email."""
    if not search:
        return query
    term = f"%{search}%"
    return query.filter(
        or_(
            Users.users_first_name.ilike(term),
            Users.users_last_name.ilike(term),
            Users.users_username.ilike(term),
            Users.users_email.ilike(term),
        )
    )


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(require_admin),
):
    """Get a single user by id (admin only)."""
    user = db.query(Users).filter_by(users_id=user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.get("/users", response_model=UserListResponse)
def list_users(
    params: PaginationParams = Depends(get_pagination_params),
    db: Session = Depends(get_db),
    current_user: Users = Depends(require_admin),
):
    """List all users (admin only)."""
    query = db.query(Users)
    query = _apply_user_search(query, params.search)

    if params.sort:
        column = getattr(Users, params.sort, None)
        if column is not None:
            query = query.order_by(column.desc() if params.order.value == "desc" else column.asc())

    total = query.count()
    users = query.offset((params.page - 1) * params.per_page).limit(params.per_page).all()
    pages = (total + params.per_page - 1) // params.per_page if params.per_page else 0

    return UserListResponse(
        items=users,
        total=total,
        page=params.page,
        per_page=params.per_page,
        pages=pages,
    )


@router.put("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    payload: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: Users = Depends(require_admin),
):
    """Update a user's role (admin only)."""
    user = db.query(Users).filter_by(users_id=user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.users_role = payload.users_role
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", response_model=MessageResponse)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(require_admin),
):
    """Delete a user (admin only)."""
    user = db.query(Users).filter_by(users_id=user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    db.delete(user)
    db.commit()
    return MessageResponse(message="User deleted successfully")


@router.put("/users/{user_id}/activate", response_model=MessageResponse)
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(require_admin),
):
    """Activate a user by setting their email verification to 1 (admin only)."""
    user = db.query(Users).filter_by(users_id=user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.users_email_verified = 1
    db.commit()
    return MessageResponse(message="User activated successfully")


@router.put("/users/{user_id}/deactivate", response_model=MessageResponse)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Users = Depends(require_admin),
):
    """Deactivate a user by setting their email verification to 0 (admin only)."""
    user = db.query(Users).filter_by(users_id=user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.users_email_verified = 0
    db.commit()
    return MessageResponse(message="User deactivated successfully")
