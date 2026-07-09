"""
User repository for E-Council.

This module is the only place in the codebase that imports SQLAlchemy session
internals for the ``Users`` model. All other layers operate on the ``Users``
model instance or Pydantic DTOs.
"""

from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from models import Departments, Users


def _with_department(query):
    """Eager load the department relationship for a user query."""
    return query.options(joinedload(Users.department))


class UserRepository:
    """Repository for user persistence and authentication."""

    @staticmethod
    def get_by_id(session: Any, user_id: int) -> Users | None:
        """Return a user by primary key, or None."""
        return _with_department(session.query(Users)).filter_by(users_id=user_id).first()

    @staticmethod
    def get_by_username(session: Any, username: str) -> Users | None:
        """Return a user by username, or None."""
        return _with_department(session.query(Users)).filter_by(users_username=username).first()

    @staticmethod
    def get_by_email(session: Any, email: str) -> Users | None:
        """Return a user by email, or None."""
        return _with_department(session.query(Users)).filter_by(users_email=email).first()

    @staticmethod
    def get_by_username_or_email(session: Any, username_or_email: str) -> Users | None:
        """Return a user by username or email, or None."""
        return (
            _with_department(session.query(Users))
            .filter(
                or_(
                    Users.users_username == username_or_email,
                    Users.users_email == username_or_email,
                )
            )
            .first()
        )

    @staticmethod
    def create(
        session: Any,
        *,
        users_first_name: str,
        users_last_name: str,
        users_username: str,
        users_email: str,
        users_password: str,
        users_department_name: str,
        users_role: str = "Student Council Officer",
        **kwargs: Any,
    ) -> Users:
        """Create a new user and department if needed.

        Args:
            session: SQLAlchemy session.
            users_first_name: First name.
            users_last_name: Last name.
            users_username: Unique username.
            users_email: Unique email address.
            users_password: Plain text password to hash.
            users_department_name: Department name; created if it does not exist.
            users_role: User role.
            kwargs: Additional fields passed to the ``Users`` constructor.

        Returns:
            Newly created ``Users`` instance.
        """
        department = session.query(Departments).filter_by(departments_name=users_department_name).first()
        if department is None:
            department = Departments(departments_name=users_department_name)
            session.add(department)
            session.flush()

        user = Users(
            users_first_name=users_first_name,
            users_last_name=users_last_name,
            users_username=users_username,
            users_email=users_email,
            users_departments_id=department.departments_id,
            users_role=users_role,
            users_email_verified=kwargs.pop("users_email_verified", 1),
            **kwargs,
        )
        user.set_password(users_password)
        session.add(user)
        session.flush()
        session.refresh(user)

        return _with_department(session.query(Users)).filter_by(users_id=user.users_id).first()

    @staticmethod
    def authenticate(session: Any, username_or_email: str, password: str) -> Users | None:
        """Authenticate a user and return the user if valid, otherwise None."""
        user = UserRepository.get_by_username_or_email(session, username_or_email)
        if user is None:
            return None
        if not user.check_password(password):
            return None
        return user
