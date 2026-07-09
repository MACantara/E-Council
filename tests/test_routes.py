import os
import sys

# Add the directory containing app.py to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_index(client):
    response = client.get("/")
    assert response.status_code == 200


def test_signup(client):
    response = client.get("/auth/signup")
    assert response.status_code == 200


def test_login(client):
    response = client.get("/auth/login")
    assert response.status_code == 200


def test_logout(client):
    response = client.get("/auth/logout")
    assert response.status_code == 302


def test_forgot_password(client):
    response = client.get("/auth/forgot-password")
    assert response.status_code == 200


def test_account(client):
    response = client.get("/account/")
    assert response.status_code == 302


def test_account_settings(client):
    response = client.get("/account/account-settings")
    assert response.status_code == 302


def test_email_settings(client):
    response = client.get("/account/email-settings")
    assert response.status_code == 302


def test_password_security_settings(client):
    response = client.get("/account/password-security-settings")
    assert response.status_code == 302


def test_council_overview(client):
    response = client.get("/dashboard/council-overview")
    assert response.status_code == 302


def test_events_overview(client):
    response = client.get("/dashboard/events-overview")
    assert response.status_code == 302


def test_event_dashboard(client):
    response = client.get("/dashboard/event-dashboard/1")
    assert response.status_code == 302


def test_add_transaction(client):
    response = client.get("/events/add-transaction/1")
    assert response.status_code == 302


def test_invite_user(client):
    response = client.get("/events/invite-user/1")
    assert response.status_code == 302


def test_event_invite_rejected(client):
    response = client.get("/events/event-invite-rejected")
    assert response.status_code == 302


def test_event_invite_accepted(client):
    response = client.get("/events/event-invite-accepted")
    assert response.status_code == 302


def test_concept_papers_overview(client):
    response = client.get("/concept-papers/overview")
    assert response.status_code == 302


def test_documentation_overview(client):
    response = client.get("/documentation/documentation-overview")
    assert response.status_code == 302


def test_financial_reports_overview(client):
    response = client.get("/financial/financial-reports-overview")
    assert response.status_code == 302


def test_board_resolutions_overview(client):
    response = client.get("/board-resolutions/board-resolutions-overview")
    assert response.status_code == 302


def test_minutes_of_the_meeting_overview(client):
    response = client.get("/meetings/minutes-of-the-meeting-overview")
    assert response.status_code == 302
