from flask import Blueprint
from flask_login import current_user, login_required

from routes.tasks import pdf_response
from services import financial as financial_service
from tasks import generate_pdf, run_task

financial_bp = Blueprint("financial", __name__, url_prefix="/financial")


@financial_bp.route("/financial-reports-overview")
@login_required
def financial_reports_overview():
    return financial_service.financial_reports_overview()


@financial_bp.route("/add-financial-report", methods=["GET", "POST"])
@login_required
def add_financial_report():
    return financial_service.add_financial_report()


@financial_bp.route("/update-financial-report/<int:report_id>", methods=["GET", "POST"])
@login_required
def update_financial_report(report_id):
    return financial_service.update_financial_report(report_id)


@financial_bp.route("/update-financial-report-status/<int:report_id>", methods=["POST"])
@login_required
def update_financial_report_status(report_id):
    return financial_service.update_financial_report_status(report_id)


@financial_bp.route("/delete-financial-report/<int:report_id>", methods=["GET", "POST"])
@login_required
def delete_financial_report(report_id):
    return financial_service.delete_financial_report(report_id)


@financial_bp.route("/generate-financial-report-pdf/<int:financial_report_id>")
@login_required
def generate_financial_report_pdf(financial_report_id):
    result = run_task(
        generate_pdf,
        "services.financial",
        "generate_financial_report_pdf",
        financial_report_id,
        current_user.users_id,
    )
    return pdf_response(result)
