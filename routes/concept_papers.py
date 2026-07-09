"""
Concept Papers Blueprint
Handles all concept paper related routes including CRUD operations and PDF generation.
"""

from flask import (
    Blueprint,
    jsonify,
    make_response,
    render_template,
    request,
)
from flask_login import current_user, login_required

from extensions import get_user_key, limiter
from models import (
    ConceptPaperForms,
)
from services import ai
from services import concept_papers as concept_paper_service
from utils.auth import is_admin
from utils.helpers import get_pagination_args

# Create blueprint
concept_papers_bp = Blueprint("concept_papers", __name__, url_prefix="/concept-papers")


@concept_papers_bp.route("/overview")
@login_required
def concept_papers_overview():
    # Determine the sorting order and pagination parameters
    sort_by_date = request.args.get("sort_by_date", "recent-to-old")
    page, per_page = get_pagination_args()

    # Admins can view all concept papers; others only see their own department's
    query = ConceptPaperForms.query.order_by(ConceptPaperForms.concept_paper_forms_date.desc())
    if not is_admin(current_user):
        from sqlalchemy import or_

        query = query.filter(
            or_(
                ConceptPaperForms.concept_paper_forms_departments_id == current_user.users_departments_id,
                ConceptPaperForms.concept_paper_forms_prepared_by == current_user.users_id,
            )
        )

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        "concept-papers/concept-papers-overview.html",
        concept_papers=pagination.items,
        pagination=pagination,
        sort_by_date=sort_by_date,
    )


@concept_papers_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_concept_paper():
    return concept_paper_service.create_concept_paper()


@concept_papers_bp.route("/update-status/<int:paper_id>", methods=["POST"])
@login_required
def update_concept_paper_status(paper_id):
    return concept_paper_service.update_concept_paper_status(paper_id)


@concept_papers_bp.route("/update/<int:paper_id>", methods=["GET", "POST"])
@login_required
def update_concept_paper(paper_id):
    return concept_paper_service.update_concept_paper(paper_id)


@concept_papers_bp.route("/delete/<int:paper_id>", methods=["GET", "POST"])
@login_required
def delete_concept_paper(paper_id):
    return concept_paper_service.delete_concept_paper(paper_id)


@concept_papers_bp.route("/generate-body", methods=["POST"])
@login_required
@limiter.limit("10 per minute", key_func=get_user_key)
def generate_concept_body():
    if not request.is_json:
        return make_response(jsonify({"error": "Content-Type must be application/json"}), 400)

    data = request.json
    result = ai.generate_concept_paper_body(
        data.get("subject"), data.get("start_date"), data.get("end_date"), data.get("location")
    )
    if not result:
        return make_response(jsonify({"error": result.error}), 400)
    return make_response(jsonify({"content": result.data}), 200)


@concept_papers_bp.route("/generate-descriptions", methods=["POST"])
@login_required
@limiter.limit("10 per minute", key_func=get_user_key)
def generate_concept_descriptions():
    if not request.is_json:
        return make_response(jsonify({"error": "Content-Type must be application/json"}), 400)

    result = ai.generate_concept_paper_descriptions(request.json.get("subject"))
    if not result:
        return make_response(jsonify({"error": result.error}), 400)
    return make_response(jsonify({"content": result.data}), 200)


@concept_papers_bp.route("/generate-objectives", methods=["POST"])
@login_required
@limiter.limit("10 per minute", key_func=get_user_key)
def generate_concept_objectives():
    if not request.is_json:
        return make_response(jsonify({"error": "Content-Type must be application/json"}), 400)

    result = ai.generate_concept_paper_objectives(request.json.get("subject"))
    if not result:
        return make_response(jsonify({"error": result.error}), 400)
    return make_response(jsonify({"content": result.data}), 200)


@concept_papers_bp.route("/generate-learning-outcomes", methods=["POST"])
@login_required
@limiter.limit("10 per minute", key_func=get_user_key)
def generate_concept_learning_outcomes():
    if not request.is_json:
        return make_response(jsonify({"error": "Content-Type must be application/json"}), 400)

    result = ai.generate_concept_paper_learning_outcomes(request.json.get("subject"))
    if not result:
        return make_response(jsonify({"error": result.error}), 400)
    return make_response(jsonify({"content": result.data}), 200)


@concept_papers_bp.route("/generate-participants", methods=["POST"])
@login_required
@limiter.limit("10 per minute", key_func=get_user_key)
def generate_concept_participants():
    if not request.is_json:
        return make_response(jsonify({"error": "Content-Type must be application/json"}), 400)

    result = ai.generate_concept_paper_participants(request.json.get("subject"))
    if not result:
        return make_response(jsonify({"error": result.error}), 400)
    return make_response(jsonify({"content": result.data}), 200)


@concept_papers_bp.route("/generate-consent", methods=["POST"])
@login_required
@limiter.limit("10 per minute", key_func=get_user_key)
def generate_concept_consent():
    if not request.is_json:
        return make_response(jsonify({"error": "Content-Type must be application/json"}), 400)

    data = request.json
    result = ai.generate_concept_paper_consent(
        data.get("subject"), data.get("start_date"), data.get("end_date"), data.get("location")
    )
    if not result:
        return make_response(jsonify({"error": result.error}), 400)
    return make_response(jsonify({"content": result.data}), 200)


@concept_papers_bp.route("/generate-pdf/<int:concept_paper_id>")
@login_required
def generate_concept_paper_pdf(concept_paper_id):
    return concept_paper_service.generate_concept_paper_pdf(concept_paper_id)


# Blueprint is ready to be imported and registered in app.py
# Add to app.py: from routes.concept_papers import concept_papers_bp
# Register: app.register_blueprint(concept_papers_bp)
