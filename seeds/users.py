"""Seed sample users with realistic roles."""

from __future__ import annotations

from models import Users
from seeds import data
from seeds.core import get_session


def seed(department_map: dict) -> dict:
    """Create the demo users and return a mapping of username to user instance."""
    session = get_session()
    user_map = {}

    for user_info in data.SAMPLE_USERS:
        existing = session.query(Users).filter_by(users_email=user_info["email"]).first()
        if existing is not None:
            user_map[user_info["username"]] = existing
            continue

        department = department_map[user_info["department"]]

        user = Users(
            users_first_name=user_info["first_name"],
            users_last_name=user_info["last_name"],
            users_username=user_info["username"],
            users_email=user_info["email"],
            users_role=user_info["role"],
            users_departments_id=department.departments_id,
            users_email_verified=1,
        )
        user.set_password(data.DEMO_PASSWORD)
        session.add(user)
        session.commit()

        user_map[user_info["username"]] = user

    return user_map
