"""
Documentation routes blueprint for E-Council.
Contains all routes related to documentation management.
"""

from flask import Blueprint
from flask_login import current_user, login_required

# Import helper function from utils
# Create blueprint
from routes.tasks import pdf_response
from services import documentation as documentation_service
from tasks import generate_pdf, run_task

documentation_bp = Blueprint("documentation", __name__, url_prefix="/documentation")


@documentation_bp.route("/documentation-overview")
@login_required
def documentation_overview():
    return documentation_service.documentation_overview()


@documentation_bp.route("/add-documentation", methods=["GET", "POST"])
@login_required
def add_documentation():
    return documentation_service.add_documentation()


@documentation_bp.route("/update-documentation-status/<int:documentation_id>", methods=["POST"])
@login_required
def update_documentation_status(documentation_id):
    return documentation_service.update_documentation_status(documentation_id)


@documentation_bp.route("/update-documentation/<int:documentation_id>", methods=["GET", "POST"])
@login_required
def update_documentation(documentation_id):
    return documentation_service.update_documentation(documentation_id)


@documentation_bp.route("/delete-documentation/<int:documentation_id>", methods=["GET", "POST"])
@login_required
def delete_documentation(documentation_id):
    return documentation_service.delete_documentation(documentation_id)


@documentation_bp.route("/get-related-forms/<int:event_id>", methods=["GET"])
@login_required
def get_related_forms(event_id):
    return documentation_service.get_related_forms(event_id)


@documentation_bp.route("/get-activity-report-details/<int:activity_report_id>", methods=["GET"])
@login_required
def get_activity_report_details(activity_report_id):
    return documentation_service.get_activity_report_details(activity_report_id)


@documentation_bp.route("/process-student-excel", methods=["POST"])
@login_required
def process_student_excel():
    return documentation_service.process_student_excel()


@documentation_bp.route("/generate-documentation-pdf/<int:documentation_id>")
@login_required
def generate_documentation_pdf(documentation_id):
    result = run_task(
        generate_pdf,
        "services.documentation",
        "generate_documentation_pdf",
        documentation_id,
        current_user.users_id,
    )
    return pdf_response(result)
