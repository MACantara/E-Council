from flask import Blueprint
from flask_login import current_user, login_required

from routes.tasks import pdf_response
from services import meetings as meetings_service
from tasks import generate_pdf, run_task

meetings_bp = Blueprint("meetings", __name__, url_prefix="/meetings")


@meetings_bp.route("/minutes-of-the-meeting-overview")
@login_required
def minutes_of_the_meeting_overview():
    return meetings_service.minutes_of_the_meeting_overview()


@meetings_bp.route("/generate-mom-pdf/<int:minutes_of_the_meeting_id>")
@login_required
def generate_mom_pdf(minutes_of_the_meeting_id):
    result = run_task(
        generate_pdf,
        "services.meetings",
        "generate_mom_pdf",
        minutes_of_the_meeting_id,
        current_user.users_id,
    )
    return pdf_response(result)


@meetings_bp.route("/add-minutes-of-the-meeting", methods=["GET", "POST"])
@login_required
def add_minutes_of_the_meeting():
    return meetings_service.add_minutes_of_the_meeting()


@meetings_bp.route("/update-minutes-of-the-meeting/<int:meeting_id>", methods=["GET", "POST"])
@login_required
def update_minutes_of_the_meeting(meeting_id):
    return meetings_service.update_minutes_of_the_meeting(meeting_id)


@meetings_bp.route("/update-minutes-of-the-meeting-status/<int:meeting_id>", methods=["POST"])
@login_required
def update_minutes_of_the_meeting_status(meeting_id):
    return meetings_service.update_minutes_of_the_meeting_status(meeting_id)


@meetings_bp.route("/delete-minutes-of-the-meeting/<int:meeting_id>", methods=["GET", "POST"])
@login_required
def delete_minutes_of_the_meeting(meeting_id):
    return meetings_service.delete_minutes_of_the_meeting(meeting_id)
