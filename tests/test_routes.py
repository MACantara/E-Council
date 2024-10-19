import pytest
import sys
import os

# Add the directory containing app.py to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_index(client):
    response = client.get('/')
    assert response.status_code == 200
    
def test_signup(client):
    response = client.get('/signup')
    assert response.status_code == 200
    
def test_login(client):
    response = client.get('/login')
    assert response.status_code == 200
    
def test_logout(client):
    response = client.get('/logout')
    assert response.status_code == 302    
    
def test_reset_password(client):
    response = client.get('/reset-password')
    assert response.status_code == 200
    
def test_forgot_password(client):
    response = client.get('/forgot-password')
    assert response.status_code == 200
    
def test_reset_password(client):
    response = client.get('/reset-password')
    assert response.status_code == 200
    
def test_account(client):
    response = client.get('/account')
    assert response.status_code == 302
    
def test_account_settings(client):
    response = client.get('/account-settings')
    assert response.status_code == 302
    
def test_email_settings(client):
    response = client.get('/email-settings')
    assert response.status_code == 302

def test_password_security_settings(client):
    response = client.get('/password-security-settings')
    assert response.status_code == 302
    
def test_council_overview(client):
    response = client.get('/council-overview')
    assert response.status_code == 302
    
def test_events_overview(client):
    response = client.get('/events-overview')
    assert response.status_code == 302
    
def test_event_dashboard(client):
    response = client.get('/event-dashboard')
    assert response.status_code == 302
    
def test_add_transaction(client):
    response = client.get('/add-transaction')
    assert response.status_code == 302
    
def test_invite_user(client):
    response = client.get('/invite-user')
    assert response.status_code == 302
    
def test_event_invite_rejected(client):
    response = client.get('/event-invite-rejected')
    assert response.status_code == 302
    
def test_event_invite_accepted(client):
    response = client.get('/event-invite-accepted')
    assert response.status_code == 302
    
def test_concept_papers_overview(client):
    response = client.get('/concept-papers-overview')
    assert response.status_code == 302
    
def test_documentation_overview(client):
    response = client.get('/documentation-overview')
    assert response.status_code == 302

def test_financial_reports_overview(client):
    response = client.get('/financial-reports-overview')
    assert response.status_code == 302
    
def test_accreditation_requirements_overview(client):
    response = client.get('/accreditation-requirements-overview')
    assert response.status_code == 302
    
def test_board_resolutions_overview(client):
    response = client.get('/board-resolutions-overview')
    assert response.status_code == 302
    
def test_notable_achievement_reports_overview(client):
    response = client.get('/notable-achievement-reports-overview')
    assert response.status_code == 302
    
def test_society_accomplishment_and_compliance_reports_overview(client):
    response = client.get('/society-achievement-and-compliance-reports-overview')
    assert response.status_code == 302

def test_minutes_of_the_meeting_overview(client):
    response = client.get('/minutes-of-the-meeting-overview')
    assert response.status_code == 302
    
def test_student_enrichment_activity_reports_overview(client):
    response = client.get('/student-enrichment-activity-reports-overview')
    assert response.status_code == 302
    
def test_end_of_semester_reports_overview(client):
    response = client.get('/end-of-semester-reports-overview')
    assert response.status_code == 302

def test_calendar_of_activities_overview(client):
    response = client.get('/calendar-of-activities-overview')
    assert response.status_code == 302
    
def test_semestral_clearance_overview(client):
    response = client.get('/semestral-clearance-overview')
    assert response.status_code == 302