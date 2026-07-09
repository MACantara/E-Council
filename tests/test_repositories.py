"""Integration tests for the repository abstraction layer."""

import pytest

from models import Departments, Users
from repositories import get_repository, repo


class TestBaseRepository:
    """Integration tests using the in-memory SQLite database from TestingConfig."""

    def test_create_and_query_department(self, app_context):
        """A repository can create and retrieve a record using the bound model."""
        department_repo = get_repository(Departments)
        department = department_repo.create(departments_name="Repository Department")

        assert department.departments_id is not None
        found = department_repo.get(department.departments_id)
        assert found is not None
        assert found.departments_name == "Repository Department"

    def test_create_and_query_user(self, app_context):
        """The generic repo can add, commit, and retrieve a user by primary key."""
        department_repo = get_repository(Departments)
        department = department_repo.create(departments_name="User Department")

        user = Users(
            users_first_name="Repo",
            users_last_name="User",
            users_username="repouser",
            users_email="repo@example.com",
            users_departments_id=department.departments_id,
            users_role="Student Council Officer",
            users_email_verified=1,
        )
        user.set_password("Password123!")
        repo.add(user)
        repo.commit()

        found = repo.get(Users, user.users_id)
        assert found is not None
        assert found.users_username == "repouser"
        assert found.department.departments_name == "User Department"

    def test_query_filter(self, app_context):
        """repo.query(Model) supports filtering without touching db.session directly."""
        department_repo = get_repository(Departments)
        department = department_repo.create(departments_name="Filter Department")

        found = repo.query(Departments).filter_by(departments_name="Filter Department").first()
        assert found is not None
        assert found.departments_id == department.departments_id

    def test_update_and_delete(self, app_context):
        """A repository can update and delete a record."""
        department_repo = get_repository(Departments)
        department = department_repo.create(departments_name="Update Department")

        updated = department_repo.update(department, departments_name="Updated Department")
        assert updated.departments_name == "Updated Department"

        refreshed = department_repo.get(department.departments_id)
        assert refreshed.departments_name == "Updated Department"

        department_repo.delete(department)
        department_repo.commit()

        assert department_repo.get(department.departments_id) is None

    def test_get_or_404(self, app_context):
        """get_repository(Model).get_or_404 raises 404 for missing records."""
        from werkzeug.exceptions import NotFound

        with pytest.raises(NotFound):
            get_repository(Departments).get_or_404(999999)
