"""Fixtures for service-layer unit tests."""

from contextlib import contextmanager

import pytest
from flask_login import login_user

from extensions import db
from models import DepartmentsEvents


@pytest.fixture
def auth_service_context(app, sample_user):
    """Provide a logged-in request context for calling service functions."""

    @contextmanager
    def _context(method="GET", data=None, content_type=None, user=None, **kwargs):
        with app.test_request_context(method=method, data=data, content_type=content_type, **kwargs):
            login_user(user or sample_user)
            yield

    return _context


@pytest.fixture
def link_event_to_user():
    """Associate an event with a user's department for access control tests."""

    def _link(event, user):
        db.session.add(DepartmentsEvents(departments_id=user.users_departments_id, events_id=event.events_id))
        db.session.commit()

    return _link
