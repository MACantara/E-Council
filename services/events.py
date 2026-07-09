"""Service layer for the events module."""

from datetime import datetime
from types import SimpleNamespace

import cloudinary
import cloudinary.uploader
from flask import abort, current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from models import ConceptPaperForms, Departments, DepartmentsEvents, EventInvitations, Events, Transaction, Users
from repositories import repo
from utils.auth import belongs_to_user_or_department
from utils.email import send_invite_email
from utils.helpers import get_concept_papers, get_distinct_academic_years

s = None


def init_serializer(secret_key):
    """Initialize the serializer with the app's secret key"""
    global s
    s = URLSafeTimedSerializer(secret_key)


def update_event(event_id):
    # Get the event by ID and verify access
    event = Events.query.get_or_404(event_id)

    if not belongs_to_user_or_department(event, current_user):
        abort(403)

    if request.method == "GET":
        # Query distinct academic years
        academic_years = (
            repo.query(Events.events_academic_year).distinct().order_by(Events.events_academic_year.desc()).all()
        )

        # Render the template with the event and academic years
        return render_template("events/update-event.html", event=event, academic_years=academic_years)

    elif request.method == "POST":
        # Get form data
        event_name = request.form.get("events-name")
        event_semester = request.form.get("events-semester")
        event_academic_year = request.form.get("events-academic-year")
        event_start_date_and_time = request.form.get("events-start-date-and-time")
        event_end_date_and_time = request.form.get("events-end-date-and-time")
        event_venue = request.form.get("events-venue")
        event_budget = request.form.get("events-budget")
        event_status = request.form.get("events-status")
        event_description = request.form.get("events-description")
        event_remarks = request.form.get("events-remarks")

        # Update event details
        event.events_name = event_name
        event.events_semester = event_semester
        event.events_academic_year = event_academic_year
        event.events_start_date_and_time = datetime.strptime(event_start_date_and_time, "%Y-%m-%dT%H:%M")
        event.events_end_date_and_time = datetime.strptime(event_end_date_and_time, "%Y-%m-%dT%H:%M")
        event.events_venue = event_venue
        event.events_budget = event_budget
        event.events_status = event_status
        event.events_description = event_description
        event.events_remarks = event_remarks

        # Commit changes to the database
        repo.commit()

        flash("Event updated successfully.", "success")

        return redirect(url_for("dashboard.events_overview"))


def update_event_status(event_id):
    data = request.get_json()
    new_status = data.get("status")

    # Find the event by ID
    event = Events.query.get_or_404(event_id)

    if not belongs_to_user_or_department(event, current_user):
        abort(403)

    # Update the event status
    event.events_status = new_status
    repo.commit()

    return jsonify(success=True)


def add_event():
    if request.method == "POST":
        creation_method = request.form.get("creation-method")
        concept_paper_forms_id = request.form.get("concept-paper-forms-id")
        events_name = request.form.get("events-name")
        events_semester = request.form.get("events-semester")
        events_academic_year = request.form.get("events-academic-year")
        other_academic_year = request.form.get("other-academic-year")
        events_start_date_and_time = request.form.get("events-start-date-and-time")
        events_end_date_and_time = request.form.get("events-end-date-and-time")
        events_venue = request.form.get("events-venue")
        events_budget = request.form.get("events-budget")
        events_status = request.form.get("events-status")
        events_description = request.form.get("events-description")
        events_remarks = request.form.get("events-remarks")

        # Use the value from the additional input field if "Other A.Y." is selected
        if events_academic_year == "Other":
            events_academic_year = other_academic_year

        # Validation
        if creation_method == "scratch":
            if (
                not events_name
                or not events_semester
                or not events_academic_year
                or not events_start_date_and_time
                or not events_end_date_and_time
            ):
                flash("Please fill out all required fields.", "modal-error")
                return render_template(
                    "events/add-event.html",
                    academic_years=get_distinct_academic_years(),
                    concept_papers=get_concept_papers(),
                )

            # Check if event name already exists
            existing_event = Events.query.filter_by(events_name=events_name).first()
            if existing_event:
                flash("An event with this name already exists. Please choose a different name.", "modal-error")
                return render_template(
                    "events/add-event.html",
                    academic_years=get_distinct_academic_years(),
                    concept_papers=get_concept_papers(),
                )

            # Validate date format
            try:
                events_start_date_and_time = datetime.strptime(events_start_date_and_time, "%Y-%m-%dT%H:%M")
                events_end_date_and_time = datetime.strptime(events_end_date_and_time, "%Y-%m-%dT%H:%M")
            except ValueError:
                flash("Invalid date format. Please use the format YYYY-MM-DDTHH:MM.", "modal-error")
                return render_template(
                    "events/add-event.html",
                    academic_years=get_distinct_academic_years(),
                    concept_papers=get_concept_papers(),
                )

            # Validate budget format
            if events_budget:
                try:
                    events_budget = float(events_budget)
                except ValueError:
                    flash("Invalid budget format. Please enter a valid number.", "modal-error")
                    return render_template(
                        "events/add-event.html",
                        academic_years=get_distinct_academic_years(),
                        concept_papers=get_concept_papers(),
                    )

        # If creating from an existing concept paper, retrieve the concept paper details
        if creation_method == "existing" and concept_paper_forms_id:
            concept_paper = ConceptPaperForms.query.get(concept_paper_forms_id)
            if concept_paper:
                events_name = concept_paper.concept_paper_forms_subject
                events_semester = concept_paper.concept_paper_forms_semester
                events_academic_year = concept_paper.concept_paper_forms_academic_year
                events_start_date_and_time = concept_paper.concept_paper_forms_event_start_date_and_time
                events_end_date_and_time = concept_paper.concept_paper_forms_event_end_date_and_time
                events_venue = concept_paper.concept_paper_forms_location
                events_budget = concept_paper.concept_paper_forms_budget
                events_description = concept_paper.concept_paper_forms_descriptions

        # Create event
        event = Events(
            events_concept_paper_forms_id=concept_paper_forms_id,
            events_name=events_name,
            events_semester=events_semester,
            events_academic_year=events_academic_year,
            events_start_date_and_time=events_start_date_and_time,
            events_end_date_and_time=events_end_date_and_time,
            events_venue=events_venue,
            events_budget=events_budget,
            events_status=events_status,
            events_description=events_description,
            events_remarks=events_remarks,
        )

        repo.add(event)
        repo.commit()

        # Insert into departments_events table
        departments_id = current_user.users_departments_id
        departments_event = DepartmentsEvents(departments_id=departments_id, events_id=event.events_id)
        repo.add(departments_event)
        repo.commit()

        flash("Event added successfully!", "success")
        return redirect(url_for("dashboard.events_overview"))

    # Query distinct academic years and concept papers
    academic_years = get_distinct_academic_years()
    concept_papers = get_concept_papers()
    return render_template("events/add-event.html", academic_years=academic_years, concept_papers=concept_papers)


def delete_event(event_id):
    # Find the event by ID
    event = Events.query.get_or_404(event_id)

    if not belongs_to_user_or_department(event, current_user):
        abort(403)

    if request.method == "POST":
        # Delete related records in the departments_events table
        DepartmentsEvents.query.filter_by(events_id=event_id).delete()

        # Delete related records in the event_invitations table
        EventInvitations.query.filter_by(event_invitations_events_id=event_id).delete()

        # Delete transaction receipts from Cloudinary
        for transaction in event.transactions or []:
            if transaction.receipt_public_id:
                try:
                    cloudinary.uploader.destroy(transaction.receipt_public_id)
                except Exception as e:
                    current_app.logger.error(
                        "Failed to delete transaction receipt from Cloudinary: %s", e, exc_info=True
                    )

        # Delete the event
        repo.delete(event)
        repo.commit()

        flash("Event deleted successfully.", "success")
        return redirect(url_for("dashboard.events_overview"))

    return render_template("events/delete-event.html", event=event)


def add_transaction(event_id):
    # Fetch the event details based on the event_id
    event = Events.query.get_or_404(event_id)

    if not belongs_to_user_or_department(event, current_user):
        abort(403)

    if request.method == "POST":
        # Get form data
        transaction_name = request.form.get("transaction-name")
        transaction_date = request.form.get("transaction-date")
        unit_amount = request.form.get("transaction-unit-amount")
        unit_price = request.form.get("transaction-unit-price")
        transaction_total = request.form.get("transaction-total")
        transaction_category = request.form.get("transaction-category")
        other_transaction_category = request.form.get("other-transaction-category")
        transaction_type = request.form.get("transaction-type")
        transaction_receipt = request.files.get("transaction-receipt")

        # Use the value from the additional input field if "Other" is selected
        if transaction_category == "Other":
            transaction_category = other_transaction_category

        # Handle file upload to Cloudinary
        receipt_url = None
        receipt_public_id = None
        if transaction_receipt:
            upload_result = cloudinary.uploader.upload(transaction_receipt)
            receipt_url = upload_result.get("secure_url")
            receipt_public_id = upload_result.get("public_id")

        # Create a new Transaction record
        new_transaction = Transaction(
            events_id=event.events_id,
            transaction_name=transaction_name,
            transaction_date=datetime.strptime(transaction_date, "%Y-%m-%dT%H:%M"),
            unit_amount=int(unit_amount) if unit_amount else 0,
            unit_price=float(unit_price) if unit_price else 0,
            total=float(transaction_total) if transaction_total else 0,
            category=transaction_category,
            type=transaction_type,
            receipt_url=receipt_url,
            receipt_public_id=receipt_public_id,
        )
        event.transactions.append(new_transaction)
        repo.commit()

        flash("Transaction added successfully.", "success")
        return redirect(url_for("dashboard.event_dashboard", event_id=event_id))

    # Build distinct transaction categories from all Transaction records
    transaction_categories = sorted({t.category for ev in Events.query.all() for t in ev.transactions if t.category})

    return render_template("events/add-transaction.html", event=event, transaction_categories=transaction_categories)


def update_transaction(event_id, transaction_id):
    # Fetch the event details based on the event_id
    event = Events.query.get_or_404(event_id)

    if not belongs_to_user_or_department(event, current_user):
        abort(403)

    transaction = Transaction.query.filter_by(transaction_id=transaction_id, events_id=event_id).first()
    if not transaction:
        abort(404)

    if request.method == "POST":
        # Get form data
        transaction_name = request.form.get("transaction-name")
        transaction_date = request.form.get("transaction-date")
        unit_amount = request.form.get("transaction-unit-amount")
        unit_price = request.form.get("transaction-unit-price")
        transaction_total = request.form.get("transaction-total")
        transaction_category = request.form.get("transaction-category")
        other_transaction_category = request.form.get("other-transaction-category")
        transaction_type = request.form.get("transaction-type")
        transaction_receipt = request.files.get("transaction-receipt")

        # Use the value from the additional input field if "Other" is selected
        if transaction_category == "Other":
            transaction_category = other_transaction_category

        # Handle file upload to Cloudinary
        receipt_url = transaction.receipt_url
        receipt_public_id = transaction.receipt_public_id
        if transaction_receipt:
            if receipt_public_id:
                cloudinary.uploader.destroy(receipt_public_id)
            upload_result = cloudinary.uploader.upload(transaction_receipt)
            receipt_url = upload_result.get("secure_url")
            receipt_public_id = upload_result.get("public_id")

        # Update the transaction record
        transaction.transaction_name = transaction_name
        transaction.transaction_date = datetime.strptime(transaction_date, "%Y-%m-%dT%H:%M")
        transaction.unit_amount = int(unit_amount) if unit_amount else 0
        transaction.unit_price = float(unit_price) if unit_price else 0
        transaction.total = float(transaction_total) if transaction_total else 0
        transaction.category = transaction_category
        transaction.type = transaction_type
        transaction.receipt_url = receipt_url
        transaction.receipt_public_id = receipt_public_id

        # Commit the changes to the database
        repo.commit()

        flash("Transaction updated successfully.", "success")
        return redirect(url_for("dashboard.event_dashboard", event_id=event_id))

    # Build distinct transaction categories from all Transaction records
    transaction_categories = sorted({t.category for ev in Events.query.all() for t in ev.transactions if t.category})

    # Provide a template-compatible object with old TransactionHistory attribute names
    transaction_obj = SimpleNamespace(
        transaction_id=transaction.transaction_id,
        transaction_name=transaction.transaction_name,
        transaction_date=transaction.transaction_date.strftime("%Y-%m-%dT%H:%M")
        if transaction.transaction_date
        else None,
        transaction_unit_amount=transaction.unit_amount,
        transaction_unit_price=transaction.unit_price,
        transaction_total=transaction.total,
        transaction_category=transaction.category,
        transaction_type=transaction.type,
        transaction_receipt_cloudinary_url=transaction.receipt_url,
        transaction_receipt_cloudinary_public_id=transaction.receipt_public_id,
    )

    return render_template(
        "events/update-transaction.html",
        event=event,
        transaction=transaction_obj,
        transaction_categories=transaction_categories,
    )


def invite_user(event_id):
    # Get the event by ID
    event = Events.query.get_or_404(event_id)

    if not belongs_to_user_or_department(event, current_user):
        abort(403)

    if request.method == "POST":
        # Get form data
        users_email = request.form.get("users-email")
        source = request.form.get("source")

        # Find the user by email
        user = Users.query.filter_by(users_email=users_email).first_or_404()

        # Get the user's department ID
        users_department_id = user.users_departments_id

        # Check if the departments_id and events_id pair already exists
        existing_entry = (
            repo.query(DepartmentsEvents)
            .join(Departments)
            .filter(DepartmentsEvents.departments_id == users_department_id, DepartmentsEvents.events_id == event_id)
            .first()
        )

        if existing_entry:
            department_name = existing_entry.department.departments_name
            flash(
                f"The department of the user {users_email} ({department_name}) is already managing the event '{event.events_name}'.",
                "error",
            )
            return redirect(
                url_for(source, event_id=event_id)
                if source == "event_dashboard"
                else url_for("dashboard.events_overview")
            )

        # Check if there is an existing invitation
        existing_invitation = EventInvitations.query.filter_by(
            event_invitations_events_id=event_id, event_invitations_email=users_email
        ).first()
        if existing_invitation:
            flash(f"An invitation for the event '{event.events_name}' has already been sent to {users_email}.", "error")
            return redirect(
                url_for(source, event_id=event_id)
                if source == "event_dashboard"
                else url_for("dashboard.events_overview")
            )

        # Send invite email
        send_invite_email(users_email, event.events_name, event_id)

        flash(
            f"Invitation email for the event '{event.events_name}' to {users_email} has been sent successfully.",
            "success",
        )
        return redirect(
            url_for(source, event_id=event_id) if source == "event_dashboard" else url_for("dashboard.events_overview")
        )

    # Get the source from the query parameters
    source = request.args.get("source", "events_overview")
    return render_template("events/invite-user.html", event=event, source=source)


def accept_invite(token):
    try:
        # Decode the token
        users_email = s.loads(token, salt="invite-user", max_age=3600)
    except SignatureExpired:
        flash("The invitation link has expired.", "error")
        return redirect(url_for("auth.login"))
    except BadSignature:
        flash("The invitation link is invalid.", "error")
        return redirect(url_for("auth.login"))

    # Find the invitation by token
    invitation = EventInvitations.query.filter_by(event_invitations_token=token).first()
    if not invitation:
        flash("The invitation link is invalid or has expired.", "error")
        return redirect(url_for("dashboard.events_overview"))

    # Check if the invitation email matches the current user's email
    if invitation.event_invitations_email != current_user.users_email:
        flash("You are not authorized to accept this invitation.", "error")
        return redirect(url_for("dashboard.events_overview"))

    # Find the user by email
    user = Users.query.filter_by(users_email=users_email).first_or_404()

    # Get the user's department ID
    users_department_id = user.users_departments_id

    # Get the event ID from the invitation
    event_id = invitation.event_invitations_events_id

    # Link the user's department to the event in the departments_events junction table
    departments_event = DepartmentsEvents(departments_id=users_department_id, events_id=event_id)
    repo.add(departments_event)

    # Delete the invitation record from the event_invitations table
    repo.delete(invitation)

    # Commit changes to the database
    repo.commit()

    flash("You have successfully accepted the invitation to manage the event.", "success")
    return redirect(url_for("dashboard.events_overview"))


def reject_invite(token):
    try:
        # Decode the token
        s.loads(token, salt="invite-user", max_age=3600)
    except SignatureExpired:
        flash("The invitation link has expired.", "error")
        return redirect(url_for("auth.login"))
    except BadSignature:
        flash("The invitation link is invalid.", "error")
        return redirect(url_for("auth.login"))

    # Find the invitation by token
    invitation = EventInvitations.query.filter_by(event_invitations_token=token).first()
    if not invitation:
        flash("The invitation link is invalid or has expired.", "error")
        return redirect(url_for("dashboard.events_overview"))

    # Check if the invitation email matches the current user's email
    if invitation.event_invitations_email != current_user.users_email:
        flash("You are not authorized to reject this invitation.", "error")
        return redirect(url_for("dashboard.events_overview"))

    # Get the event and department details
    event = Events.query.get_or_404(invitation.event_invitations_events_id)
    department_event = DepartmentsEvents.query.filter_by(events_id=event.events_id).first()
    department = Departments.query.get_or_404(department_event.departments_id)

    # Delete the invitation record from the event_invitations table
    repo.delete(invitation)
    repo.commit()

    flash(
        f"You have successfully rejected the invitation to manage the event '{event.events_name}' from the department '{department.departments_name}'.",
        "success",
    )
    return redirect(url_for("dashboard.events_overview"))


def event_invite_rejected():
    return render_template("events/event-invite-rejected.html")


def event_invite_accepted():
    return render_template("events/event-invite-accepted.html")
