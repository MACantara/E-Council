import pytest
import sys
import os

# Add the directory containing app.py to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db, Users

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()

def test_signup_get(client):
    response = client.get('/signup')
    assert response.status_code == 200

def test_signup_post_missing_fields(client):
    response = client.post('/signup', data={})
    assert response.status_code == 200
    assert b"All fields are required." in response.data

def test_signup_post_existing_username(client):
    with app.app_context():
        user = Users(
            users_first_name="Test",
            users_last_name="User",
            users_username="testuser",
            users_email="test@example.com",
            users_department="Test Department",
            users_role="Test Role",
            users_email_verified=0
        )
        user.set_password("Password123!")
        db.session.add(user)
        db.session.commit()

        # Verify user is added to the database
        assert Users.query.filter_by(users_username="testuser").first() is not None

    response = client.post('/signup', data={
        "users-first-name": "Test",
        "users-last-name": "User",
        "users-username": "testuser",
        "users-email": "test2@example.com",
        "users-department": "Test Department",
        "users-role": "Test Role",
        "users-password": "Password123!",
        "users-repeat-password": "Password123!"
    })
    
    assert response.status_code == 200
    assert b"Username already exists." in response.data

def test_signup_post_password_mismatch(client):
    response = client.post('/signup', data={
        "users-first-name": "Test",
        "users-last-name": "User",
        "users-username": "testuser2",
        "users-email": "test2@example.com",
        "users-department": "Test Department",
        "users-role": "Test Role",
        "users-password": "Password123!",
        "users-repeat-password": "Password1234!"
    })
    assert response.status_code == 200
    assert b"Passwords do not match." in response.data

def test_signup_post_password_requirements(client):
    response = client.post('/signup', data={
        "users-first-name": "Test",
        "users-last-name": "User",
        "users-username": "testuser3",
        "users-email": "test3@example.com",
        "users-department": "Test Department",
        "users-role": "Test Role",
        "users-password": "pass",
        "users-repeat-password": "pass"
    })
    assert response.status_code == 200
    assert b"Password must be at least 8 characters." in response.data

    response = client.post('/signup', data={
        "users-first-name": "Test",
        "users-last-name": "User",
        "users-username": "testuser4",
        "users-email": "test4@example.com",
        "users-department": "Test Department",
        "users-role": "Test Role",
        "users-password": "password",
        "users-repeat-password": "password"
    })
    assert response.status_code == 200
    assert b"Password must contain at least one uppercase letter." in response.data

    response = client.post('/signup', data={
        "users-first-name": "Test",
        "users-last-name": "User",
        "users-username": "testuser5",
        "users-email": "test5@example.com",
        "users-department": "Test Department",
        "users-role": "Test Role",
        "users-password": "PASSWORD",
        "users-repeat-password": "PASSWORD"
    })
    assert response.status_code == 200
    assert b"Password must contain at least one lowercase letter." in response.data

    response = client.post('/signup', data={
        "users-first-name": "Test",
        "users-last-name": "User",
        "users-username": "testuser6",
        "users-email": "test6@example.com",
        "users-department": "Test Department",
        "users-role": "Test Role",
        "users-password": "Password",
        "users-repeat-password": "Password"
    })
    assert response.status_code == 200
    assert b"Password must contain at least one number." in response.data

    response = client.post('/signup', data={
        "users-first-name": "Test",
        "users-last-name": "User",
        "users-username": "testuser7",
        "users-email": "test7@example.com",
        "users-department": "Test Department",
        "users-role": "Test Role",
        "users-password": "Password1",
        "users-repeat-password": "Password1"
    })
    assert response.status_code == 200
    assert b"Password must contain at least one special character." in response.data

def test_signup_post_success(client):
    response = client.post('/signup', data={
        "users-first-name": "Test",
        "users-last-name": "User",
        "users-username": "testuser8",
        "users-email": "test8@example.com",
        "users-department": "Test Department",
        "users-role": "Test Role",
        "users-password": "Password123!",
        "users-repeat-password": "Password123!"
    })
    assert response.status_code == 200