import os
import sys
import tempfile
import pytest

# Add the directory containing app.py to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db, Users

@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['WTF_CSRF_ENABLED'] = False

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client

    os.close(db_fd)
    os.unlink(db_path)

def test_signup_get(client):
    """Test GET request to /signup"""
    response = client.get('/signup')
    assert response.status_code == 200
    assert b'Sign Up' in response.data

def test_signup_post_valid(client):
    """Test POST request to /signup with valid data"""
    response = client.post('/signup', data={
        'users-first-name': 'John',
        'users-last-name': 'Doe',
        'users-username': 'johndoe',
        'users-email': 'johndoe@example.com',
        'users-role': 'user',
        'users-password': 'password123'
    })
    assert response.status_code == 200  # Redirect after successful signup
    assert Users.query.filter_by(users_username='johndoe').first() is not None

def test_signup_post_invalid(client):
    """Test POST request to /signup with missing data"""
    response = client.post('/signup', data={
        'users-first-name': 'John',
        'users-last-name': 'Doe',
        'users-username': '',
        'users-email': 'johndoe@example.com',
        'users-role': 'user',
        'users-password': 'password123'
    })
    assert response.status_code == 200  # Should not redirect
    assert b'All fields are required.' in response.data

def test_signup_post_missing_first_name(client):
    """Test POST request to /signup with missing first name"""
    response = client.post('/signup', data={
        'users-first-name': '',
        'users-last-name': 'Doe',
        'users-username': 'johndoe',
        'users-email': 'johndoe@example.com',
        'users-role': 'user',
        'users-password': 'password123'
    })
    assert response.status_code == 200  # Should not redirect
    assert b'All fields are required.' in response.data

def test_signup_post_missing_last_name(client):
    """Test POST request to /signup with missing last name"""
    response = client.post('/signup', data={
        'users-first-name': 'John',
        'users-last-name': '',
        'users-username': 'johndoe',
        'users-email': 'johndoe@example.com',
        'users-role': 'user',
        'users-password': 'password123'
    })
    assert response.status_code == 200  # Should not redirect
    assert b'All fields are required.' in response.data

def test_signup_post_missing_email(client):
    """Test POST request to /signup with missing email"""
    response = client.post('/signup', data={
        'users-first-name': 'John',
        'users-last-name': 'Doe',
        'users-username': 'johndoe',
        'users-email': '',
        'users-role': 'user',
        'users-password': 'password123'
    })
    assert response.status_code == 200  # Should not redirect
    assert b'All fields are required.' in response.data

def test_signup_post_missing_role(client):
    """Test POST request to /signup with missing role"""
    response = client.post('/signup', data={
        'users-first-name': 'John',
        'users-last-name': 'Doe',
        'users-username': 'johndoe',
        'users-email': 'johndoe@example.com',
        'users-role': '',
        'users-password': 'password123'
    })
    assert response.status_code == 200  # Should not redirect
    assert b'All fields are required.' in response.data

def test_signup_post_missing_password(client):
    """Test POST request to /signup with missing password"""
    response = client.post('/signup', data={
        'users-first-name': 'John',
        'users-last-name': 'Doe',
        'users-username': 'johndoe',
        'users-email': 'johndoe@example.com',
        'users-role': 'user',
        'users-password': ''
    })
    assert response.status_code == 200  # Should not redirect
    assert b'All fields are required.' in response.data

def test_signup_post_existing_username(client):
    """Test POST request to /signup with an already existing username"""
    # First, create a user
    client.post('/signup', data={
        'users-first-name': 'John',
        'users-last-name': 'Doe',
        'users-username': 'johndoe',
        'users-email': 'johndoe@example.com',
        'users-role': 'user',
        'users-password': 'password123'
    })
    # Try to create another user with the same username
    response = client.post('/signup', data={
        'users-first-name': 'Jane',
        'users-last-name': 'Doe',
        'users-username': 'johndoe',  # Same username
        'users-email': 'janedoe@example.com',
        'users-role': 'user',
        'users-password': 'password123'
    })
    assert response.status_code == 200  # Should not redirect
    assert b'Username already exists.' in response.data