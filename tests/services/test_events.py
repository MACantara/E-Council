"""Unit tests for the events service."""

import json

import pytest
from werkzeug.exceptions import HTTPException

from extensions import db
from models import DepartmentsEvents, EventInvitations, Events
from services import events
from tests.factories import EventsFactory


class TestDeleteEvent:
    def test_get_renders_delete_template(self, app_context, auth_service_context, sample_user, link_event_to_user):
        event = EventsFactory()
        link_event_to_user(event, sample_user)
        with auth_service_context():
            response = events.delete_event(event.events_id)
        assert isinstance(response, str)

    def test_post_deletes_event(self, app_context, auth_service_context, sample_user, link_event_to_user):
        event = EventsFactory()
        link_event_to_user(event, sample_user)
        with auth_service_context(method="POST"):
            response = events.delete_event(event.events_id)
        assert response.status_code == 302
        assert Events.query.get(event.events_id) is None

    def test_delete_forbidden_for_other_user(self, app_context, auth_service_context, sample_user, other_user):
        event = EventsFactory()
        with pytest.raises(HTTPException), auth_service_context(user=other_user):
            events.delete_event(event.events_id)


class TestUpdateEventStatus:
    def test_update_status(self, app_context, auth_service_context, sample_user, link_event_to_user):
        event = EventsFactory()
        link_event_to_user(event, sample_user)
        with auth_service_context(
            method="POST",
            data=json.dumps({"status": "Done"}),
            content_type="application/json",
        ):
            response = events.update_event_status(event.events_id)
        assert response.status_code == 200
        assert response.get_json()["success"] is True
        updated = Events.query.get(event.events_id)
        assert updated.events_status == "Done"

    def test_update_status_forbidden_for_other_user(self, app_context, auth_service_context, sample_user, other_user):
        event = EventsFactory()
        with (
            pytest.raises(HTTPException),
            auth_service_context(
                method="POST",
                data=json.dumps({"status": "Done"}),
                content_type="application/json",
                user=other_user,
            ),
        ):
            events.update_event_status(event.events_id)


class TestAddEvent:
    def test_get_renders_add_template(self, app_context, auth_service_context, sample_user):
        with auth_service_context():
            response = events.add_event()
        assert isinstance(response, str)


class TestUpdateEvent:
    def test_get_renders_update_template(self, app_context, auth_service_context, sample_user, link_event_to_user):
        event = EventsFactory()
        link_event_to_user(event, sample_user)
        with auth_service_context():
            response = events.update_event(event.events_id)
        assert isinstance(response, str)


class TestInviteUser:
    def test_get_renders_invite_template(self, app_context, auth_service_context, sample_user, link_event_to_user):
        event = EventsFactory()
        link_event_to_user(event, sample_user)
        with auth_service_context(query_string="source=dashboard.event_dashboard"):
            response = events.invite_user(event.events_id)
        assert isinstance(response, str)


class TestAcceptInvite:
    def test_accept_invite(self, app_context, auth_service_context, sample_user):
        event = EventsFactory()
        token = events.s.dumps(sample_user.users_email, salt="invite-user")
        invitation = EventInvitations(
            event_invitations_events_id=event.events_id,
            event_invitations_email=sample_user.users_email,
            event_invitations_token=token,
        )
        db.session.add(invitation)
        db.session.commit()

        with auth_service_context():
            response = events.accept_invite(token)
        assert response.status_code == 302
        assert EventInvitations.query.filter_by(event_invitations_token=token).first() is None
        assert (
            DepartmentsEvents.query.filter_by(
                departments_id=sample_user.users_departments_id, events_id=event.events_id
            ).first()
            is not None
        )


class TestRejectInvite:
    def test_reject_invite(self, app_context, auth_service_context, sample_user, link_event_to_user):
        event = EventsFactory()
        link_event_to_user(event, sample_user)
        token = events.s.dumps(sample_user.users_email, salt="invite-user")
        invitation = EventInvitations(
            event_invitations_events_id=event.events_id,
            event_invitations_email=sample_user.users_email,
            event_invitations_token=token,
        )
        db.session.add(invitation)
        db.session.commit()

        with auth_service_context():
            response = events.reject_invite(token)
        assert response.status_code == 302
        assert EventInvitations.query.filter_by(event_invitations_token=token).first() is None
