"""Service layer for the board_resolutions module."""

from datetime import datetime
from io import BytesIO

import google.generativeai as genai
from flask import (
    abort,
    current_app,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_login import current_user
from google.generativeai.types import HarmBlockThreshold, HarmCategory
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)
from sqlalchemy import or_

from config import AIConfig
from models import (
    BoardResolutions,
    DepartmentsEvents,
    Events,
    Signatories,
    StudentOrganizations,
    Users,
    db,
)
from utils.auth import belongs_to_user_or_department, is_admin

genai.configure(api_key=AIConfig.GOOGLE_GEMINI_AI_API_KEY)


model = genai.GenerativeModel(AIConfig.GEMINI_MODEL)


safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}


def board_resolutions_overview():
    # Determine the sorting order
    sort_by_date = request.args.get("sort_by_date", "recent-to-old")

    # Admins can view all board resolutions; others only see their own department's or ones they prepared
    if is_admin(current_user):
        board_resolutions = BoardResolutions.query.order_by(BoardResolutions.board_resolutions_date.desc()).all()
    else:
        board_resolutions = (
            BoardResolutions.query.filter(
                or_(
                    BoardResolutions.board_resolutions_departments_id == current_user.users_departments_id,
                    BoardResolutions.board_resolutions_prepared_by == current_user.users_id,
                )
            )
            .order_by(BoardResolutions.board_resolutions_date.desc())
            .all()
        )

    return render_template(
        "board-resolutions/board-resolutions-overview.html",
        board_resolutions=board_resolutions,
        sort_by_date=sort_by_date,
    )


def add_board_resolution():
    if request.method == "POST":
        events_id = request.form.get("board-resolutions-events-id")
        other_event_name = request.form.get("other-event-name")
        title = request.form.get("board-resolutions-title")
        description = request.form.get("board-resolutions-description")
        total_amount = request.form.get("board-resolutions-total-amount")
        academic_year = request.form.get("board-resolutions-academic-year")
        other_academic_year = request.form.get("other-academic-year")
        semester = request.form.get("board-resolutions-semester")
        status = request.form.get("board-resolutions-status")
        date = request.form.get("board-resolutions-date")
        prepared_by = request.form.get("board-resolutions-prepared-by")
        approved_by = request.form.get("board-resolutions-approved-by")
        student_signatories = request.form.getlist("board-resolutions-student-signatories")

        # Use the value from the "Other" input field if "Other" is selected for academic year
        if academic_year == "Other":
            academic_year = other_academic_year

        # Handle the "Other" option for event name
        if events_id == "Other":
            # Create a new event with the provided name
            new_event = Events(
                events_name=other_event_name,
                events_academic_year=academic_year,
                events_semester=semester,
                events_description=description,
            )
            db.session.add(new_event)
            db.session.commit()
            events_id = new_event.events_id

            # Link the event to the department of the current user
            departments_events = DepartmentsEvents(
                departments_id=current_user.users_departments_id, events_id=events_id
            )
            db.session.add(departments_events)
            db.session.commit()
        elif events_id == "None":
            events_id = None

        # Convert date to datetime object
        date = datetime.strptime(date, "%Y-%m-%dT%H:%M")

        # Create a new board resolution
        new_resolution = BoardResolutions(
            board_resolutions_events_id=events_id,
            board_resolutions_departments_id=current_user.users_departments_id,
            board_resolutions_title=title,
            board_resolutions_description=description,
            board_resolutions_total_amount=total_amount,
            board_resolutions_academic_year=academic_year,
            board_resolutions_semester=semester,
            board_resolutions_status=status,
            board_resolutions_date=date,
            board_resolutions_prepared_by=prepared_by,
            board_resolutions_approved_by=approved_by,
        )

        # Add student signatories as a JSON list of user IDs
        new_resolution.student_signatory_ids = student_signatories

        # Add the new resolution to the database
        db.session.add(new_resolution)
        db.session.commit()

        flash("Board resolution added successfully!", "success")
        return redirect(url_for("board_resolutions.board_resolutions_overview"))

    # Query for events that are not yet linked to any board resolutions
    events = (
        Events.query.outerjoin(BoardResolutions, Events.events_id == BoardResolutions.board_resolutions_events_id)
        .filter(BoardResolutions.board_resolutions_events_id is None)
        .all()
    )

    # Query for distinct academic years
    academic_years = db.session.query(BoardResolutions.board_resolutions_academic_year).distinct().all()
    academic_years = [year[0] for year in academic_years]

    student_organizations = StudentOrganizations.query.all()
    signatories = Signatories.query.all()

    return render_template(
        "board-resolutions/add-board-resolution.html",
        events=events,
        academic_years=academic_years,
        student_organizations=student_organizations,
        signatories=signatories,
    )


def delete_board_resolution(resolution_id):
    # Find the board resolution by ID
    resolution = BoardResolutions.query.get_or_404(resolution_id)

    if not belongs_to_user_or_department(resolution, current_user):
        abort(403)

    if request.method == "POST":
        # Delete related records in the departments_events table
        DepartmentsEvents.query.filter_by(events_id=resolution.board_resolutions_events_id).delete()

        # Delete the board resolution
        db.session.delete(resolution)
        db.session.commit()

        flash("Board resolution deleted successfully.", "success")
        return redirect(url_for("board_resolutions.board_resolutions_overview"))

    return render_template("board-resolutions/delete-board-resolution.html", resolution=resolution)


def update_board_resolution(resolution_id):
    resolution = BoardResolutions.query.get_or_404(resolution_id)

    if not belongs_to_user_or_department(resolution, current_user):
        abort(403)

    if request.method == "POST":
        events_id = request.form.get("board-resolutions-events-id")
        other_event_name = request.form.get("other-event-name")
        title = request.form.get("board-resolutions-title")
        description = request.form.get("board-resolutions-description")
        total_amount = request.form.get("board-resolutions-total-amount")
        academic_year = request.form.get("board-resolutions-academic-year")
        other_academic_year = request.form.get("other-academic-year")
        semester = request.form.get("board-resolutions-semester")
        status = request.form.get("board-resolutions-status")
        date = request.form.get("board-resolutions-date")
        prepared_by = request.form.get("board-resolutions-prepared-by")
        approved_by = request.form.get("board-resolutions-approved-by")
        student_signatories = request.form.getlist("board-resolutions-student-signatories")

        # Use the value from the "Other" input field if "Other" is selected for academic year
        if academic_year == "Other":
            academic_year = other_academic_year

        # Handle the "Other" option for event name
        if events_id == "Other":
            # Create a new event with the provided name
            new_event = Events(
                events_name=other_event_name,
                events_academic_year=academic_year,
                events_semester=semester,
                events_description=description,
            )
            db.session.add(new_event)
            db.session.commit()
            events_id = new_event.events_id

            # Link the event to the department of the current user
            departments_events = DepartmentsEvents(
                departments_id=current_user.users_departments_id, events_id=events_id
            )
            db.session.add(departments_events)
            db.session.commit()
        elif events_id == "None":
            events_id = None

        # Convert date to datetime object
        date = datetime.strptime(date, "%Y-%m-%dT%H:%M")

        # Update the board resolution
        resolution.board_resolutions_events_id = events_id
        resolution.board_resolutions_title = title
        resolution.board_resolutions_description = description
        resolution.board_resolutions_total_amount = total_amount
        resolution.board_resolutions_academic_year = academic_year
        resolution.board_resolutions_semester = semester
        resolution.board_resolutions_status = status
        resolution.board_resolutions_date = date
        resolution.board_resolutions_prepared_by = prepared_by
        resolution.board_resolutions_approved_by = approved_by

        # Update student signatories as a JSON list of user IDs
        resolution.student_signatory_ids = student_signatories

        db.session.commit()

        flash("Board resolution updated successfully!", "success")
        return redirect(url_for("board_resolutions.board_resolutions_overview"))

    # Query for events that are not yet linked to any board resolutions
    events = (
        Events.query.outerjoin(BoardResolutions, Events.events_id == BoardResolutions.board_resolutions_events_id)
        .filter(BoardResolutions.board_resolutions_events_id is None)
        .all()
    )

    # Query for distinct academic years
    academic_years = db.session.query(BoardResolutions.board_resolutions_academic_year).distinct().all()
    academic_years = [year[0] for year in academic_years]

    student_organizations = StudentOrganizations.query.all()
    signatories = Signatories.query.all()

    # Query for existing student signatories
    existing_signatories = resolution.student_signatory_ids or []

    return render_template(
        "board-resolutions/update-board-resolution.html",
        resolution=resolution,
        events=events,
        academic_years=academic_years,
        student_organizations=student_organizations,
        signatories=signatories,
        existing_signatories=existing_signatories,
    )


def update_board_resolution_status(resolution_id):
    data = request.get_json()
    new_status = data.get("status")

    # Find the board resolution by ID
    resolution = BoardResolutions.query.get_or_404(resolution_id)

    if not belongs_to_user_or_department(resolution, current_user):
        abort(403)

    # Update the board resolution status
    resolution.board_resolutions_status = new_status
    db.session.commit()

    return jsonify(success=True)


def generate_description():
    if not request.is_json:
        return make_response(jsonify({"error": "Content-Type must be application/json"}), 400)

    try:
        data = request.json
        if not data:
            return make_response(jsonify({"error": "No JSON data provided"}), 400)

        event_name = data.get("event_name")
        title = data.get("title")
        date = data.get("date")
        total_amount = data.get("total_amount")

        if not event_name or not title:
            return make_response(jsonify({"error": "Missing event_name or title"}), 400)

        current_app.logger.info(
            f"Generating description for event: {event_name}, title: {title}, date: {date}, amount: {total_amount}"
        )

        # Convert date to proper format
        try:
            if date:
                date_obj = datetime.strptime(date, "%Y-%m-%dT%H:%M")
                formatted_date = f"Signed this {date_obj.day}th of {date_obj.strftime('%B')} in the name of the Lord Jesus Christ {date_obj.year}"
            else:
                formatted_date = "Signed this 13th of May in the name of the Lord Jesus Christ 2024"  # Default date
        except ValueError as e:
            current_app.logger.error(f"Date parsing error: {str(e)}")
            formatted_date = "Signed this 13th of May in the name of the Lord Jesus Christ 2024"  # Default date

        # Format amount with commas and two decimal places if provided
        formatted_amount = f"₱{float(total_amount):,.2f}" if total_amount else "the specified amount"

        prompt = f"""Generate a formal description for a proposed board resolution with the following details:
                Event: {event_name}
                Title: {title}
                Total Amount: {formatted_amount}

                Requirements:
                1. Use clear, formal language in present tense
                2. Focus only on describing the purpose, scope, and proposed decisions
                3. Keep it concise and straightforward
                4. Do not include any signatories
                5. Do not use any text formatting
                6. Do not include the board resolution title
                7. Do not include any resolution numbers
                8. Do not use 'WHEREAS' statements
                9. Begin with 'The College of Computer Studies Student Council proposes to'
                10. Use language that indicates the resolution is pending approval (e.g., 'seeks to allocate', 'proposes to implement')
                11. Explicitly mention the total amount in the main paragraph using the phrase 'with a proposed budget of {formatted_amount}'
                12. Include a financial breakdown section with the following format:
                    Proposed Financial Breakdown:
                    [List all relevant expense categories based on the event type and purpose]
                    Proposed Total Amount: {formatted_amount}
                13. The description should be 1 paragraph only, followed by the financial breakdown
                14. End with exactly this date: '{formatted_date}'

                Note: Create a comprehensive list of expense categories appropriate for this specific event"""

        current_app.logger.info("Sending request to Gemini API")
        try:
            response = model.generate_content(prompt, safety_settings=safety_settings)
            current_app.logger.info("Received response from Gemini API")

            if response and hasattr(response, "text"):
                description = response.text.strip()
                current_app.logger.info(f"Generated description: {description[:100]}...")
                return make_response(jsonify({"description": description}), 200)
            else:
                current_app.logger.error("Invalid response format from Gemini API")
                return make_response(jsonify({"error": "Invalid response from AI model"}), 500)

        except Exception as gemini_error:
            current_app.logger.error(f"Gemini API error: {str(gemini_error)}")
            return make_response(jsonify({"error": f"AI generation error: {str(gemini_error)}"}), 500)

    except Exception as e:
        current_app.logger.error(f"Error generating description: {str(e)}")
        return make_response(jsonify({"error": str(e)}), 500)


def generate_board_resolution_pdf(resolution_id):
    # Get the resolution data
    resolution = BoardResolutions.query.get_or_404(resolution_id)

    if not belongs_to_user_or_department(resolution, current_user):
        abort(403)

    # Get prepared by and approved by users
    prepared_by = Users.query.get(resolution.board_resolutions_prepared_by)
    approved_by = Signatories.query.get(resolution.board_resolutions_approved_by)

    # Get student signatories from the JSON list of user IDs
    signatory_users = (
        db.session.query(Users, StudentOrganizations)
        .join(StudentOrganizations, Users.users_student_organization == StudentOrganizations.student_organizations_id)
        .filter(Users.users_id.in_(resolution.student_signatory_ids or []))
        .order_by(StudentOrganizations.student_organizations_name)
        .all()
    )

    # Maintain tuple structure (signatory_placeholder, user, org) for downstream code
    student_signatories = [(None, user, org) for user, org in signatory_users]

    # Create BytesIO buffer for PDF
    buffer = BytesIO()

    def header(canvas, doc):
        canvas.saveState()

        # Add header images with manual positioning
        # PERPS header - left side
        header_perps = Image("./static/img/logos/HEADER-PERPS.png", width=325, height=75)
        perps_x = doc.leftMargin - 35
        header_perps.drawOn(canvas, perps_x, doc.height + doc.topMargin)

        # CCS Logo - center
        header_ccs = Image("./static/img/logos/CCS-LOGO.png", width=35, height=50)
        ccs_x = doc.leftMargin + (doc.width - 35) / 2 + 125
        header_ccs.drawOn(canvas, ccs_x, doc.height + doc.topMargin + 15)

        # ISO Logo - right side
        header_iso = Image("./static/img/logos/ISO.png", width=100, height=50)
        iso_x = doc.leftMargin + doc.width - 80
        header_iso.drawOn(canvas, iso_x, doc.height + doc.topMargin + 15)

        # Add text below ISO logo
        canvas.setFont("Helvetica-Bold", 10)
        text = "College of Computer Studies"
        text_width = canvas.stringWidth(text, "Helvetica-Bold", 10)
        text_x = iso_x + (50 - text_width) / 2
        canvas.drawString(text_x, doc.height + doc.topMargin, text)

        # Add red line after text
        canvas.setStrokeColorRGB(0x8C / 255, 0x04 / 255, 0x04 / 255)  # #8c0404
        canvas.setLineWidth(2)
        line_y = doc.height + doc.topMargin - 10
        line_length = 510
        line_start_x = (doc.width - line_length) / 2 + doc.leftMargin
        line_end_x = line_start_x + line_length
        canvas.line(line_start_x - 5, line_y, line_end_x, line_y)

        # Add "Continuation of the Board Resolution" text if not the first page
        if doc.page > 1:  # Check if this is not the first page
            canvas.setFont("Helvetica", 12)
            continuation_text = "Continuation of the Board Resolution"
            # Use doc.leftMargin for left alignment
            text_x = doc.leftMargin
            # Increase space after the text by adjusting the y-coordinate (from -30 to -40)
            canvas.drawString(text_x, doc.height + doc.topMargin - 30, continuation_text)

        # Add footer
        canvas.setStrokeColorRGB(0, 0, 0)
        canvas.setLineWidth(1)
        footer_y = doc.bottomMargin - 20
        canvas.line(doc.leftMargin, footer_y, doc.leftMargin + doc.width, footer_y)

        # Add footer text
        canvas.setFont("Helvetica", 12)
        # Left aligned text
        canvas.drawString(doc.leftMargin, footer_y - 15, "UPHMO-CCS-GEN-912/rev0")
        # Right aligned text
        right_text = "Board Resolution"
        right_text_width = canvas.stringWidth(right_text, "Helvetica", 12)
        canvas.drawString(doc.leftMargin + doc.width - right_text_width, footer_y - 15, right_text)

        canvas.restoreState()

    # Create the PDF document
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=110, bottomMargin=72)

    # Create the story (content) for the PDF
    story = []
    styles = getSampleStyleSheet()

    # Add title
    title_style = ParagraphStyle(
        "CustomTitle", parent=styles["Heading1"], fontSize=12, alignment=1, spaceBefore=5, spaceAfter=-15
    )

    # Add the academic year subtitle
    academic_year_style = ParagraphStyle(
        "AcademicYear", parent=styles["Heading1"], fontSize=11, alignment=1, spaceAfter=20
    )

    # Add resolution title style
    resolution_style = ParagraphStyle("Resolution", parent=styles["Heading1"], fontSize=12, alignment=1, spaceAfter=20)

    story.append(Paragraph("College of Computer Studies Council", title_style))
    story.append(Paragraph(f"A.Y. {resolution.board_resolutions_academic_year}", academic_year_style))
    story.append(Paragraph("Resolution", resolution_style))

    # Create a style for the main content
    content_style = ParagraphStyle(
        "Content",
        parent=styles["Normal"],
        fontSize=12,
        leading=14,
        alignment=4,  # Justified alignment
        firstLineIndent=36,  # Add indentation for paragraph
    )

    # Add resolution details
    story.append(Paragraph(resolution.board_resolutions_description, content_style))
    story.append(Spacer(1, 15))

    # Add signatories section
    signature_style = ParagraphStyle("Signature", parent=styles["Normal"], fontSize=12, alignment=0, spaceAfter=20)

    # Student signatories
    # Group signatories by organization
    org_signatories = {}
    for signatory, user, org in student_signatories:
        if org.student_organizations_name not in org_signatories:
            org_signatories[org.student_organizations_name] = []
        org_signatories[org.student_organizations_name].append((signatory, user))

    # Create styles for organization headers and signatures
    org_header_style = ParagraphStyle(
        "OrgHeader", parent=styles["Normal"], fontSize=12, alignment=0, fontName="Helvetica-Bold", spaceAfter=10
    )

    # Organization acronyms mapping
    org_acronyms = {
        "College of Computer Studies - Student Council": "CCSC",
        "Junior Philippine Computer Society": "JPCS",
    }

    # Add grouped signatories to the story
    for org_name, signatories in org_signatories.items():
        # Add organization header
        story.append(Paragraph(org_name, org_header_style))

        # Add signatories for this organization
        for _signatory, user in signatories:
            # Make name bold using <b> tag
            signature_text = f"<b>{user.users_first_name} {user.users_last_name}</b>"
            if user.users_student_organization_position:  # Add position if available
                # Get organization acronym, default to org_name if not in mapping
                org_acronym = org_acronyms.get(org_name, org_name)
                signature_text += f"<br/><i>{org_acronym}, {user.users_student_organization_position}</i>"

            story.append(Paragraph(signature_text, signature_style))
            story.append(Spacer(1, 5))

    # Prepared by
    story.append(Paragraph("Prepared by:", signature_style))
    prepared_by_text = f"<b>{prepared_by.users_first_name} {prepared_by.users_last_name}</b>"
    if prepared_by.users_student_organization_position:
        org_acronym = org_acronyms.get("College of Computer Studies - Student Council", "CCSC")
        prepared_by_text += f"<br/><i>{org_acronym}, {prepared_by.users_student_organization_position}</i>"
    story.append(Paragraph(prepared_by_text, signature_style))
    story.append(Spacer(1, 20))

    # Approved by
    story.append(Paragraph("Approved by:", signature_style))
    approved_by_text = f"<b>{approved_by.signatory_first_name} {approved_by.signatory_last_name}</b>"
    approved_by_text += "<br/><i>Adviser, College of Computer Studies - Student Council</i>"
    story.append(Paragraph(approved_by_text, signature_style))

    # Build the PDF
    doc.build(story, onFirstPage=header, onLaterPages=header)

    # Prepare the response
    buffer.seek(0)
    return send_file(buffer, download_name=f"Board_Resolution_{resolution_id}.pdf", mimetype="application/pdf")
