"""
Shared test configuration and fixtures for E-Council tests.
"""

import pytest
import sys
import os

# Add the directory containing app.py to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db


@pytest.fixture
def app_config():
    """Application configuration for testing."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    return app


@pytest.fixture
def client(app_config):
    """Flask test client."""
    with app_config.test_client() as client:
        yield client


@pytest.fixture
def app_context(app_config):
    """Application context for database operations."""
    with app_config.app_context():
        db.create_all()
        yield
        db.drop_all()


@pytest.fixture
def sample_user(app_context):
    """Create a sample user for testing."""
    from app import Users, Departments
    
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