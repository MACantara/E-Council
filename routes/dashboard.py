from collections import defaultdict
from decimal import Decimal

from flask import Blueprint, abort, render_template
from flask_login import current_user, login_required

from models import DepartmentsEvents, Events, db
from utils.auth import belongs_to_user_or_department
from utils.helpers import safe_decimal_conversion

# Create blueprint with url_prefix='/dashboard'
dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/council-overview")
@login_required
def council_overview():
    return render_template("dashboard/council-overview.html")


@dashboard_bp.route("/events-overview", methods=["GET", "POST"])
@login_required
def events_overview():
    # Get the current user's department ID
    users_departments_id = current_user.users_departments_id

    # Set default sorting to recent-to-old if not provided
    sort_by_date = "recent-to-old"

    # Query distinct academic years
    academic_years = (
        db.session.query(Events.events_academic_year).distinct().order_by(Events.events_academic_year.desc()).all()
    )

    # Set default academic year to "All" if not provided

    # Base query for events associated with the user's department
    query = (
        db.session.query(Events)
        .join(DepartmentsEvents)
        .filter(DepartmentsEvents.departments_id == users_departments_id)
    )

    # Execute the query
    events = query.all()

    # Fetch transactions and calculate expenses, income, and remaining budget from JSON lists
    event_data = []

    for event in events:
        transactions = event.transactions or []
        total_income = sum(
            safe_decimal_conversion(t.total or 0) for t in transactions if t.type == "Income"
        )
        total_expense = sum(
            safe_decimal_conversion(t.total or 0) for t in transactions if t.type == "Expense"
        )
        events_budget = safe_decimal_conversion(event.events_budget) if event.events_budget else Decimal("0.00")
        remaining_budget = total_income - total_expense + events_budget if isinstance(events_budget, Decimal) else "N/A"

        event_data.append(
            {
                "event_id": event.events_id,
                "total_income": total_income,
                "total_expense": total_expense,
                "remaining_budget": remaining_budget,
                "events_budget": events_budget,
            }
        )

    return render_template(
        "events/events-overview.html",
        events=events,
        academic_years=academic_years,
        sort_by_date=sort_by_date,
        event_data=event_data,
    )


@dashboard_bp.route("/event-dashboard/<int:event_id>", methods=["GET", "POST"])
@login_required
def event_dashboard(event_id):
    # Fetch the event details based on the event_id
    event = Events.query.get_or_404(event_id)

    if not belongs_to_user_or_department(event, current_user):
        abort(403)

    # Fetch the transactions for the given event from related Transaction records, sorted by most recent
    transactions = sorted((event.transactions or []), key=lambda t: t.transaction_date or 0, reverse=True)

    # Aggregate top 5 income transactions grouped by category
    income_by_category = defaultdict(float)
    expense_by_category = defaultdict(float)
    for t in event.transactions or []:
        try:
            total = float(t.total or 0)
        except (TypeError, ValueError):
            total = 0.0
        if t.type == "Income":
            income_by_category[t.category] += total
        elif t.type == "Expense":
            expense_by_category[t.category] += total

    top5_income = sorted(income_by_category.items(), key=lambda x: x[1], reverse=True)[:5]
    top5_expense = sorted(expense_by_category.items(), key=lambda x: x[1], reverse=True)[:5]

    top5_income_dicts = [{"category": category, "total": float(total)} for category, total in top5_income]
    top5_expense_dicts = [{"category": category, "total": float(total)} for category, total in top5_expense]

    # Calculate total income and total expense (from top 5 for consistency with previous logic)
    total_income = sum(transaction["total"] for transaction in top5_income_dicts) or 0
    total_expense = sum(transaction["total"] for transaction in top5_expense_dicts) or 0

    # Safely convert the event budget to a float if possible
    try:
        events_budget = float(event.events_budget or 0)
    except (ValueError, TypeError):
        events_budget = event.events_budget  # Keep it as a string or handle it as needed

    # Calculate remaining budget
    if isinstance(events_budget, float):
        remaining_budget = total_income - total_expense + events_budget
    else:
        remaining_budget = f"Budget: {events_budget}"  # Return as string if not a float

    return render_template(
        "events/event-dashboard.html",
        event=event,
        transactions=transactions,
        top5_income=top5_income_dicts,
        top5_expense=top5_expense_dicts,
        total_income=total_income,
        total_expense=total_expense,
        remaining_budget=remaining_budget,
    )
