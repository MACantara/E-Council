from flask import (
    Blueprint,
)
from flask_login import login_required

from extensions import get_user_key, limiter

# Configure Gemini AI
# Create blueprint
from services import board_resolutions as board_resolutions_service

board_resolutions_bp = Blueprint("board_resolutions", __name__, url_prefix="/board-resolutions")


@board_resolutions_bp.route("/board-resolutions-overview")
@login_required
def board_resolutions_overview():
    return board_resolutions_service.board_resolutions_overview()


@board_resolutions_bp.route("/add-board-resolution", methods=["GET", "POST"])
@login_required
def add_board_resolution():
    return board_resolutions_service.add_board_resolution()


@board_resolutions_bp.route("/delete-board-resolution/<int:resolution_id>", methods=["GET", "POST"])
@login_required
def delete_board_resolution(resolution_id):
    return board_resolutions_service.delete_board_resolution(resolution_id)


@board_resolutions_bp.route("/update-board-resolution/<int:resolution_id>", methods=["GET", "POST"])
@login_required
def update_board_resolution(resolution_id):
    return board_resolutions_service.update_board_resolution(resolution_id)


@board_resolutions_bp.route("/update-board-resolution-status/<int:resolution_id>", methods=["POST"])
@login_required
def update_board_resolution_status(resolution_id):
    return board_resolutions_service.update_board_resolution_status(resolution_id)


@board_resolutions_bp.route("/generate-description", methods=["POST"])
@login_required
@limiter.limit("10 per minute", key_func=get_user_key)
def generate_description():
    return board_resolutions_service.generate_description()


@board_resolutions_bp.route("/generate-board-resolution-pdf/<int:resolution_id>")
@login_required
def generate_board_resolution_pdf(resolution_id):
    return board_resolutions_service.generate_board_resolution_pdf(resolution_id)
