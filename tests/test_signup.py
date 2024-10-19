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
    assert response.status_code == 302  # Redirect after successful signup
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