import sys
import os

# Add the directory containing app.py to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from extensions import db
from models import Users, Departments


@pytest.fixture
def department(app):
    """Create a sample department for signup tests."""
    with app.app_context():
        dept = Departments(departments_name="Test Department")
        db.session.add(dept)
        db.session.commit()
        yield dept


def test_signup_get(client):
    response = client.get('/auth/signup')
    assert response.status_code == 200

def test_signup_post_missing_fields(client):
    response = client.post('/auth/signup', data={})
    assert response.status_code == 200
    assert b"All fields are required." in response.data

def test_signup_post_existing_username(client, department):
    with client.application.app_context():
        user = Users(
            users_first_name="Test",
            users_last_name="User",
            users_username="testuser",
            users_email="test@example.com",
            users_departments_id=department.departments_id,
            users_role="Faculty",
            users_email_verified=0
        )
        user.set_password("Password123!")
        db.session.add(user)
        db.session.commit()

        # Verify user is added to the database
        assert Users.query.filter_by(users_username="testuser").first() is not None

    response = client.post('/auth/signup', data={
        "users-first-name": "Test",
        "users-last-name": "User",
        "users-username": "testuser",
        "users-email": "test2@example.com",
        "users-department": "Test Department",
        "users-role": "Faculty",
        "users-password": "Password123!",
        "users-repeat-password": "Password123!"
    })
    
    assert response.status_code == 200
    assert b"Username already exists." in response.data

def test_signup_post_password_mismatch(client):
    response = client.post('/auth/signup', data={
        "users-first-name": "Test",
        "users-last-name": "User",
        "users-username": "testuser2",
        "users-email": "test2@example.com",
        "users-department": "Test Department",
        "users-role": "Faculty",
        "users-password": "Password123!",
        "users-repeat-password": "Password1234!"
    })
    assert response.status_code == 200
    assert b"Passwords do not match." in response.data

def test_signup_post_password_requirements(client):
    response = client.post('/auth/signup', data={
        "users-first-name": "Test",
        "users-last-name": "User",
        "users-username": "testuser3",
        "users-email": "test3@example.com",
        "users-department": "Test Department",
        "users-role": "Faculty",
        "users-password": "pass",
        "users-repeat-password": "pass"
    })
    assert response.status_code == 200
    assert b"Password must be at least 8 characters." in response.data

    response = client.post('/auth/signup', data={
        "users-first-name": "Test",
        "users-last-name": "User",
        "users-username": "testuser4",
        "users-email": "test4@example.com",
        "users-department": "Test Department",
        "users-role": "Faculty",
        "users-password": "password",
        "users-repeat-password": "password"
    })
    assert response.status_code == 200
    assert b"Password must contain at least one uppercase letter." in response.data

    response = client.post('/auth/signup', data={
        "users-first-name": "Test",
        "users-last-name": "User",
        "users-username": "testuser5",
        "users-email": "test5@example.com",
        "users-department": "Test Department",
        "users-role": "Faculty",
        "users-password": "PASSWORD",
        "users-repeat-password": "PASSWORD"
    })
    assert response.status_code == 200
    assert b"Password must contain at least one lowercase letter." in response.data

    response = client.post('/auth/signup', data={
        "users-first-name": "Test",
        "users-last-name": "User",
        "users-username": "testuser6",
        "users-email": "test6@example.com",
        "users-department": "Test Department",
        "users-role": "Faculty",
        "users-password": "Password",
        "users-repeat-password": "Password"
    })
    assert response.status_code == 200
    assert b"Password must contain at least one number." in response.data

    response = client.post('/auth/signup', data={
        "users-first-name": "Test",
        "users-last-name": "User",
        "users-username": "testuser7",
        "users-email": "test7@example.com",
        "users-department": "Test Department",
        "users-role": "Faculty",
        "users-password": "Password1",
        "users-repeat-password": "Password1"
    })
    assert response.status_code == 200
    assert b"Password must contain at least one special character." in response.data

def test_signup_post_success(client, department):
    response = client.post('/auth/signup', data={
        "users-first-name": "Test",
        "users-last-name": "User",
        "users-username": "testuser8",
        "users-email": "test8@example.com",
        "users-department": "Test Department",
        "users-role": "Faculty",
        "users-password": "Password123!",
        "users-repeat-password": "Password123!"
    })
    assert response.status_code == 302