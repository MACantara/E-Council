from flask import Blueprint, request, flash, redirect, url_for, render_template
from flask_login import login_required, current_user
from decimal import Decimal
from models import db, Events, DepartmentsEvents, TransactionHistory
from utils.helpers import safe_decimal_conversion

# Create blueprint with url_prefix='/dashboard'
dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


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
    academic_years = db.session.query(Events.events_academic_year).distinct().order_by(Events.events_academic_year.desc()).all()

    # Set default academic year to "All" if not provided
    academic_year = "All"

    # Base query for events associated with the user's department
    query = db.session.query(Events).join(DepartmentsEvents).filter(DepartmentsEvents.departments_id == users_departments_id)

    # Execute the query
    events = query.all()

    # Fetch transaction history and calculate expenses, income, and remaining budget
    event_data = []

    for event in events:
        transactions = TransactionHistory.query.filter_by(transaction_events_id=event.events_id).all()
        total_income = sum(safe_decimal_conversion(t.transaction_total) for t in transactions if t.transaction_type == 'Income')
        total_expense = sum(safe_decimal_conversion(t.transaction_total) for t in transactions if t.transaction_type == 'Expense')
        events_budget = safe_decimal_conversion(event.events_budget) if event.events_budget else Decimal('0.00')
        if isinstance(events_budget, Decimal):
            remaining_budget = total_income - total_expense + events_budget
        else:
            remaining_budget = "N/A"

        event_data.append({
            'event_id': event.events_id,
            'total_income': total_income,
            'total_expense': total_expense,
            'remaining_budget': remaining_budget,
            'events_budget': events_budget
        })

    return render_template("events/events-overview.html", events=events, academic_years=academic_years, sort_by_date=sort_by_date, event_data=event_data)


@dashboard_bp.route("/event-dashboard/<int:event_id>", methods=["GET", "POST"])
@login_required
def event_dashboard(event_id):
    # Fetch the event details based on the event_id
    event = Events.query.get_or_404(event_id)

    # Fetch the transaction history for the given event_id, sorted by most recent
    transactions = TransactionHistory.query.filter_by(transaction_events_id=event_id).order_by(TransactionHistory.transaction_date.desc()).all()

    # Query top 5 income transactions grouped by category
    top5_income = db.session.query(
        TransactionHistory.transaction_category,
        db.func.sum(TransactionHistory.transaction_total).label('transaction_total')
    ).filter_by(transaction_events_id=event_id, transaction_type='Income').group_by(TransactionHistory.transaction_category).order_by(db.func.sum(TransactionHistory.transaction_total).desc()).limit(5).all()

    # Query top 5 expense transactions grouped by category
    top5_expense = db.session.query(
        TransactionHistory.transaction_category,
        db.func.sum(TransactionHistory.transaction_total).label('transaction_total')
    ).filter_by(transaction_events_id=event_id, transaction_type='Expense').group_by(TransactionHistory.transaction_category).order_by(db.func.sum(TransactionHistory.transaction_total).desc()).limit(5).all()

    # Convert TransactionHistory objects to dictionaries
    def transaction_to_dict(transaction):
        return {
            'transaction_category': transaction.transaction_category,
            'transaction_total': float(transaction.transaction_total)
        }

    top5_income_dicts = [transaction_to_dict(transaction) for transaction in top5_income]
    top5_expense_dicts = [transaction_to_dict(transaction) for transaction in top5_expense]

    # Calculate total income and total expense
    total_income = sum(transaction['transaction_total'] for transaction in top5_income_dicts) or 0
    total_expense = sum(transaction['transaction_total'] for transaction in top5_expense_dicts) or 0

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

    return render_template("events/event-dashboard.html", event=event, transactions=transactions, top5_income=top5_income_dicts, top5_expense=top5_expense_dicts, total_income=total_income, total_expense=total_expense, remaining_budget=remaining_budget)
