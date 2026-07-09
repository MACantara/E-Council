"""Unit tests for the meetings service."""

import json

import pytest
from werkzeug.exceptions import HTTPException

from models import MinutesOfTheMeeting
from services import meetings
from tests.factories import MinutesOfTheMeetingFactory, SignatoriesFactory


class TestDeleteMinutesOfTheMeeting:
    def test_get_renders_delete_template(self, app_context, auth_service_context, sample_user):
        meeting = MinutesOfTheMeetingFactory(
            department=sample_user.department,
            prepared_by_user=sample_user,
        )
        with auth_service_context():
            response = meetings.delete_minutes_of_the_meeting(meeting.minutes_of_the_meeting_id)
        assert isinstance(response, str)

    def test_post_deletes_minutes(self, app_context, auth_service_context, sample_user):
        meeting = MinutesOfTheMeetingFactory(
            department=sample_user.department,
            prepared_by_user=sample_user,
        )
        with auth_service_context(method="POST"):
            response = meetings.delete_minutes_of_the_meeting(meeting.minutes_of_the_meeting_id)
        assert response.status_code == 302
        assert MinutesOfTheMeeting.query.get(meeting.minutes_of_the_meeting_id) is None

    def test_delete_forbidden_for_other_user(self, app_context, auth_service_context, sample_user, other_user):
        meeting = MinutesOfTheMeetingFactory(
            department=sample_user.department,
            prepared_by_user=sample_user,
        )
        with pytest.raises(HTTPException), auth_service_context(user=other_user):
            meetings.delete_minutes_of_the_meeting(meeting.minutes_of_the_meeting_id)


class TestUpdateMinutesOfTheMeetingStatus:
    def test_update_status(self, app_context, auth_service_context, sample_user):
        meeting = MinutesOfTheMeetingFactory(
            department=sample_user.department,
            prepared_by_user=sample_user,
        )
        with auth_service_context(
            method="POST",
            data=json.dumps({"status": "Done"}),
            content_type="application/json",
        ):
            response = meetings.update_minutes_of_the_meeting_status(meeting.minutes_of_the_meeting_id)
        assert response.status_code == 200
        assert response.get_json()["success"] is True
        updated = MinutesOfTheMeeting.query.get(meeting.minutes_of_the_meeting_id)
        assert updated.minutes_of_the_meeting_status == "Done"

    def test_update_status_forbidden_for_other_user(self, app_context, auth_service_context, sample_user, other_user):
        meeting = MinutesOfTheMeetingFactory(
            department=sample_user.department,
            prepared_by_user=sample_user,
        )
        with (
            pytest.raises(HTTPException),
            auth_service_context(
                method="POST",
                data=json.dumps({"status": "Done"}),
                content_type="application/json",
                user=other_user,
            ),
        ):
            meetings.update_minutes_of_the_meeting_status(meeting.minutes_of_the_meeting_id)


class TestGenerateMomPdf:
    def test_generates_pdf(self, app_context, auth_service_context, sample_user):
        meeting = MinutesOfTheMeetingFactory(
            department=sample_user.department,
            prepared_by_user=sample_user,
            approved_by_user=sample_user,
            noted_by_signatory=SignatoriesFactory(),
        )
        with auth_service_context():
            response = meetings.generate_mom_pdf(meeting.minutes_of_the_meeting_id)
        assert response.status_code == 200
        assert response.mimetype == "application/pdf"
        assert "Content-Length" in response.headers
