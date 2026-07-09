"""
Admin routes for E-Council.

Provides an audit log view for administrators.
"""

from flask import Blueprint, abort, render_template, request
from flask_login import login_required
from sqlalchemy.orm import joinedload

from models import AuditLog
from utils.auth import is_admin

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/audit-log")
@login_required
def audit_log():
    """Render a paginated audit log for admin users."""
    from flask_login import current_user

    if not is_admin(current_user):
        abort(403)

    page = request.args.get("page", 1, type=int)
    per_page = 25
    pagination = (
        AuditLog.query.options(joinedload(AuditLog.user))
        .order_by(AuditLog.audit_log_timestamp.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    return render_template("admin/audit-log.html", pagination=pagination)
