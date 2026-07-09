from flask import Blueprint
from flask_login import login_required

# Create blueprint with url_prefix='/events'
from services import events as events_service

events_bp = Blueprint("events", __name__, url_prefix="/events")

# Initialize serializer (will be configured with app's SECRET_KEY when blueprint is registered)


# Attach the serializer initializer to the blueprint for app registration
events_bp.init_serializer = events_service.init_serializer


@events_bp.route("/update-event/<int:event_id>", methods=["POST", "GET"])
@login_required
def update_event(event_id):
    return events_service.update_event(event_id)


@events_bp.route("/update-event-status/<int:event_id>", methods=["POST"])
@login_required
def update_event_status(event_id):
    return events_service.update_event_status(event_id)


@events_bp.route("/add-event", methods=["GET", "POST"])
@login_required
def add_event():
    return events_service.add_event()


@events_bp.route("/delete-event/<int:event_id>", methods=["GET", "POST"])
@login_required
def delete_event(event_id):
    return events_service.delete_event(event_id)


@events_bp.route("/add-transaction/<int:event_id>", methods=["GET", "POST"])
@login_required
def add_transaction(event_id):
    return events_service.add_transaction(event_id)


@events_bp.route("/update-transaction/<int:event_id>/<int:transaction_id>", methods=["GET", "POST"])
@login_required
def update_transaction(event_id, transaction_id):
    return events_service.update_transaction(event_id, transaction_id)


@events_bp.route("/invite-user/<int:event_id>", methods=["GET", "POST"])
@login_required
def invite_user(event_id):
    return events_service.invite_user(event_id)


@events_bp.route("/accept-invite/<token>")
@login_required
def accept_invite(token):
    return events_service.accept_invite(token)


@events_bp.route("/reject-invite/<token>")
@login_required
def reject_invite(token):
    return events_service.reject_invite(token)


@events_bp.route("/event-invite-rejected")
@login_required
def event_invite_rejected():
    return events_service.event_invite_rejected()


@events_bp.route("/event-invite-accepted")
@login_required
def event_invite_accepted():
    return events_service.event_invite_accepted()
