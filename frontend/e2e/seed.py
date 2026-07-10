"""Seed a verified admin user for E2E tests."""

import os
import sys

# Add the repository root to the path so the `api` and `models` packages can be imported.
repo_root = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.abspath(repo_root))

from api.database import create_tables, SessionLocal
from repositories.users import UserRepository


def seed() -> None:
    create_tables()
    session = SessionLocal()
    try:
        existing = UserRepository.get_by_username(session, "e2eadmin")
        if existing:
            print("E2E admin user already exists")
            return

        UserRepository.create(
            session,
            users_first_name="E2E",
            users_last_name="Admin",
            users_username="e2eadmin",
            users_email="e2e@example.com",
            users_password="Password123",
            users_department_name="IT",
            users_role="Admin",
            users_email_verified=1,
        )
        session.commit()
        print("Created E2E admin user")
    finally:
        session.close()


if __name__ == "__main__":
    seed()
