"""FastAPI event helper services."""

from __future__ import annotations

from sqlalchemy.orm import Session

from api.emails import get_serializer
from api.settings import FRONTEND_URL
from models import Departments, EventInvitations, Events, Users
from services.email import EmailBackend


def send_event_invite_email(
    db: Session,
    backend: EmailBackend,
    inviter: Users,
    invitee: Users,
    event: Events,
) -> str:
    """Send an event invitation email and return the generated token."""
    s = get_serializer()
    token = s.dumps(invitee.users_email, salt="invite-user")

    accept_link = f"{FRONTEND_URL}/events/invitations/accept?token={token}"
    reject_link = f"{FRONTEND_URL}/events/invitations/reject?token={token}"

    inviter_department = db.get(Departments, inviter.users_departments_id)
    inviter_department_name = inviter_department.departments_name if inviter_department else ""

    subject = f"Invitation to manage event: {event.events_name}"
    recipients = [invitee.users_email]
    html = (
        f"<html><body>"
        f"<p>You have been invited by {inviter.users_first_name} {inviter.users_last_name} "
        f"from {inviter_department_name} to manage the event "
        f"<strong>{event.events_name}</strong>.</p>"
        f"<p><a href='{accept_link}'>Accept</a> | <a href='{reject_link}'>Reject</a></p>"
        f"</body></html>"
    )
    body = (
        f"You have been invited by {inviter.users_first_name} {inviter.users_last_name} "
        f"from {inviter_department_name} to manage the event '{event.events_name}'.\n\n"
        f"Accept: {accept_link}\nReject: {reject_link}"
    )

    backend.send(recipients, subject, html=html, body=body)

    invitation = EventInvitations(
        event_invitations_events_id=event.events_id,
        event_invitations_email=invitee.users_email,
        event_invitations_token=token,
    )
    db.add(invitation)
    db.commit()

    return token
