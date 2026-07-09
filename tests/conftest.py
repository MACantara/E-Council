"""
Shared test configuration and fixtures for E-Council tests.
"""

import pytest
import sys
import os

# Add the directory containing app.py to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db, limiter


@pytest.fixture
def app():
    """Create a fresh Flask application configured for testing."""
    app = create_app('testing')
    # Disable rate limiting by default so non-rate-limit tests are not affected.
    # Rate-limit tests explicitly enable it.
    limiter.enabled = False
    limiter.reset()
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.drop_all()
    limiter.enabled = False
    limiter.reset()


@pytest.fixture
def client(app):
    """Flask test client for the testing app."""
    return app.test_client()


@pytest.fixture
def app_context(app):
    """Application context for database operations."""
    with app.app_context():
        yield


@pytest.fixture
def sample_user(app_context):
    """Create a sample user for testing."""
    from models import Users, Departments
    
    # Create a department first
    department = Departments(departments_name="Test Department")
    db.session.add(department)
    db.session.commit()
    
    # Create a user
    user = Users(
        users_first_name="Test",
        users_last_name="User",
        users_username="testuser",
        users_email="test@example.com",
        users_departments_id=department.departments_id,
        users_role="Student Council Officer",
        users_email_verified=1
    )
    user.set_password("Password123!")
    db.session.add(user)
    db.session.commit()
    
    return user


@pytest.fixture
def other_user(app_context):
    """Create another user and department for cross-department tests."""
    from models import Users, Departments

    other_department = Departments(departments_name="Other Department")
    db.session.add(other_department)
    db.session.commit()

    user = Users(
        users_first_name="Other",
        users_last_name="User",
        users_username="otheruser",
        users_email="other@example.com",
        users_departments_id=other_department.departments_id,
        users_role="Student Council Officer",
        users_email_verified=1
    )
    user.set_password("Password123!")
    db.session.add(user)
    db.session.commit()

    return user


@pytest.fixture
def admin_user(app_context):
    """Create an admin user for authorization tests."""
    from models import Users, Departments

    department = Departments(departments_name="Admin Department")
    db.session.add(department)
    db.session.commit()

    user = Users(
        users_first_name="Admin",
        users_last_name="User",
        users_username="adminuser",
        users_email="admin@example.com",
        users_departments_id=department.departments_id,
        users_role="Admin",
        users_email_verified=1
    )
    user.set_password("Password123!")
    db.session.add(user)
    db.session.commit()

    return user