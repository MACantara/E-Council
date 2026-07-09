import os
import re
import requests
import tempfile
import time

from flask import Blueprint, request, flash, redirect, url_for, render_template, jsonify, send_file, abort, current_app
from flask_login import login_required, current_user
from utils.auth import belongs_to_user_or_department, is_admin
from sqlalchemy import or_
from io import BytesIO
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
from reportlab.pdfgen import canvas

import cloudinary
import cloudinary.uploader

import google.generativeai as genai

from models import (
    db,
    MinutesOfTheMeeting,
    Departments,
    Users,
    Signatories,
    StudentOrganizations
)
from werkzeug.utils import secure_filename


# Create blueprint
meetings_bp = Blueprint('meetings', __name__, url_prefix='/meetings')


@meetings_bp.route("/minutes-of-the-meeting-overview")
@login_required
def minutes_of_the_meeting_overview():
    # Determine the sorting order
    sort_by_date = request.args.get('sort_by_date', 'recent-to-old')

    # Base query for minutes of the meeting sorted by date (most recent first)
    query = db.session.query(
        MinutesOfTheMeeting,
        Users.users_first_name,
        Users.users_last_name
    ).join(
        Users, MinutesOfTheMeeting.minutes_of_the_meeting_presiding_officer == Users.users_id
    ).order_by(
        MinutesOfTheMeeting.minutes_of_the_meeting_date.desc()
    )

    # Admins can view all minutes; others only see their own department's or ones they prepared
    if not is_admin(current_user):
        query = query.filter(
            or_(
                MinutesOfTheMeeting.minutes_of_the_meeting_departments_id == current_user.users_departments_id,
                MinutesOfTheMeeting.minutes_of_the_meeting_prepared_by == current_user.users_id
            )
        )

    minutes_of_the_meeting = query.all()

    # Extract only the MinutesOfTheMeeting objects for filtering
    meetings_only = [meeting for meeting, _, _ in minutes_of_the_meeting]

    return render_template("minutes-of-meeting/minutes-of-the-meeting-overview.html", minutes_of_the_meeting=minutes_of_the_meeting, sort_by_date=sort_by_date, meetings_only=meetings_only)


@meetings_bp.route('/generate-mom-pdf/<int:minutes_of_the_meeting_id>')
@login_required
def generate_mom_pdf(minutes_of_the_meeting_id):
    # Get the meeting data with presiding officer
    meeting = db.session.query(MinutesOfTheMeeting, Users.users_first_name, Users.users_last_name)\
        .join(Users, MinutesOfTheMeeting.minutes_of_the_meeting_presiding_officer == Users.users_id)\
        .filter(MinutesOfTheMeeting.minutes_of_the_meeting_id == minutes_of_the_meeting_id)\
        .first_or_404()

    if not belongs_to_user_or_department(meeting[0], current_user):
        abort(403)
    
    # Get attendees from the JSON list of user IDs
    attendees = [Users.query.get(user_id) for user_id in meeting[0].attendees or []]
    attendees = [a for a in attendees if a]
    
    # Get photo documentation from the JSON list
    photos = meeting[0].photo_documentation or []
    
    # Get prepared by, approved by, and noted by users
    prepared_by = Users.query.get(meeting[0].minutes_of_the_meeting_prepared_by)
    approved_by = Users.query.get(meeting[0].minutes_of_the_meeting_approved_by)
    noted_by = Signatories.query.get(meeting[0].minutes_of_the_meeting_noted_by)
    
    # Create BytesIO buffer to receive PDF data
    buffer = BytesIO()

    # Create the PDF object
    class NumberedCanvas(canvas.Canvas):
        def __init__(self, *args, **kwargs):
            canvas.Canvas.__init__(self, *args, **kwargs)
            self._saved_page_states = []
            self._page_count = 0

        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._page_count += 1
            canvas.Canvas.showPage(self)

        def save(self):
            """Add page info to each page (page x of y)"""
            num_pages = self._page_count
            for state in self._saved_page_states:
                self.__dict__.update(state)
                self.draw_page_number(num_pages)
                canvas.Canvas.showPage(self)
            canvas.Canvas.save(self)

        def draw_page_number(self, page_count):
            self._doc.page_count = page_count

    # Create the PDF object using ReportLab
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=100,
        bottomMargin=72
    )
    doc.page_count = 3  # Initialize page count

    def header(canvas, doc):
        canvas.saveState()
        
        # Add header images with manual positioning
        # PERPS header - left side
        header_perps = Image('./static/img/logos/HEADER-PERPS.png', width=325, height=75)
        perps_x = doc.leftMargin - 35
        header_perps.drawOn(canvas, perps_x, doc.height + doc.topMargin)
        
        # CCS Logo - center
        header_ccs = Image('./static/img/logos/CCS-LOGO.png', width=35, height=50)
        # Calculate center position: leftMargin + (pageWidth - imageWidth)/2
        ccs_x = doc.leftMargin + (doc.width - 35)/2 + 125
        header_ccs.drawOn(canvas, ccs_x, doc.height + doc.topMargin + 15)
        
        # ISO Logo - right side
        header_iso = Image('./static/img/logos/ISO.png', width=100, height=50)
        # Calculate right position: leftMargin + pageWidth - imageWidth
        iso_x = doc.leftMargin + doc.width - 80
        header_iso.drawOn(canvas, iso_x, doc.height + doc.topMargin + 15)
        
        # Add text below ISO logo
        canvas.setFont("Helvetica-Bold", 10)
        text = "College of Computer Studies"
        text_width = canvas.stringWidth(text, "Helvetica-Bold", 10)
        # Center the text below the ISO logo
        text_x = iso_x + (50 - text_width)/2
        canvas.drawString(text_x, doc.height + doc.topMargin, text)
        
        # Add red line after text
        canvas.setStrokeColorRGB(0x8c/255, 0x04/255, 0x04/255)  # #8c0404
        canvas.setLineWidth(2)
        line_y = doc.height + doc.topMargin - 10
        line_length = 510  # Adjust this value to control line length
        # Calculate start and end points to center the line
        line_start_x = (doc.width - line_length) / 2 + doc.leftMargin
        line_end_x = line_start_x + line_length
        canvas.line(line_start_x - 5, line_y, line_end_x, line_y)
        
        # Add footer
        # Draw black line
        canvas.setStrokeColorRGB(0, 0, 0)  # Black color
        canvas.setLineWidth(1)
        footer_y = doc.bottomMargin - 20  # Position the line above the footer text
        canvas.line(doc.leftMargin, footer_y, doc.leftMargin + doc.width, footer_y)
        
        # Add footer text
        canvas.setFont("Helvetica", 12)
        
        # Left aligned text
        canvas.drawString(doc.leftMargin, footer_y - 15, "UPHMO-CCS-GEN-912/rev0")
        
        # Right aligned text with page numbers
        page_text = f"Council Meeting | Page {canvas.getPageNumber()} of {doc.page_count}"
        text_width = canvas.stringWidth(page_text, "Helvetica", 12)
        canvas.drawString(doc.leftMargin + doc.width - text_width, footer_y - 15, page_text)
        
        canvas.restoreState()
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Get styles
    styles = getSampleStyleSheet()
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        alignment=1  # 1 is for center alignment
    )
    
    # Custom style for centered sections
    centered_section_style = ParagraphStyle(
        'CenteredSection',
        parent=styles['Normal'],
        spaceAfter=6,
        fontSize=12,
        textColor=colors.black,
        alignment=1  # 1 is for center alignment
    )

    # Custom style for sections
    section_style = ParagraphStyle(
        'SectionStyle',
        parent=styles['Normal'],
        spaceAfter=6,
        leftIndent=0,
        fontSize=12,
        textColor=colors.black,
    )
    
    # Add meeting details
    meeting_data = meeting[0]

    # Add title
    elements.append(Paragraph(f'Council Meeting SY {meeting_data.minutes_of_the_meeting_academic_year}', title_style))
    
    elements.append(Paragraph(
        f'Date & Time: {meeting_data.minutes_of_the_meeting_date.strftime("%B %d, %Y, %I:%M %p")}' + 
        (f' - {meeting_data.minutes_of_the_meeting_adjourned.strftime("%I:%M %p")}' if meeting_data.minutes_of_the_meeting_adjourned else ''),
        centered_section_style
    ))
    elements.append(Spacer(1, 12))

    # Presiding Officer
    elements.append(Paragraph(
        f'Presiding Officer: {meeting[1]} {meeting[2]}',
        section_style
    ))

    # Add Attendees section
    elements.append(Paragraph('Attendees', heading_style))
    for attendee in attendees:
        elements.append(Paragraph(
            f'• {attendee.users_first_name} {attendee.users_last_name} - {attendee.users_student_organization_position}',
            section_style
        ))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(f'Agenda:', heading_style))
    elements.append(Paragraph(meeting_data.minutes_of_the_meeting_agenda, section_style))
    elements.append(Spacer(1, 12))
    elements.append(HRFlowable(
        width="100%",
        thickness=1,
        color=colors.black,
        spaceBefore=6,
        spaceAfter=6
    ))
    
    # Split notes into sections
    notes = meeting_data.minutes_of_the_meeting_notes
    
    # Helper function to extract section content
    def extract_section(text, section_name):
        pattern = f"{section_name}:(.*?)(?=(?:Summary:|Key Discussion Points:|Action Items:|Next Steps:|$))"
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else ""
    
    # Helper function to split numbered points
    def format_numbered_points(text):
        # Split text into lines and process each line
        lines = text.split('\n')
        formatted_lines = []
        
        current_point = ""
        for line in lines:
            line = line.strip()
            if line:
                # Check for numbered format (e.g., "2.1", "3.2", etc.)
                if re.match(r'^\d+\.\d+\s', line):
                    # If we have a previous point, add it
                    if current_point:
                        formatted_lines.append(Paragraph(current_point, section_style))
                    current_point = line
                else:
                    # If it's a continuation of the current point
                    if current_point:
                        current_point += " " + line
                    else:
                        current_point = line
        
        # Add the last point if exists
        if current_point:
            formatted_lines.append(Paragraph(current_point, section_style))
            formatted_lines.append(Spacer(1, 6))
        
        return formatted_lines
    
    # Extract each section
    summary = extract_section(notes, "Summary")
    key_points = extract_section(notes, "Key Discussion Points")
    action_items = extract_section(notes, "Action Items")
    next_steps = extract_section(notes, "Next Steps")
    
    # Add Summary
    if summary:
        elements.append(Paragraph("Summary", heading_style))
        elements.extend(format_numbered_points(summary))
        elements.append(Spacer(1, 12))
    
    # Add Key Discussion Points
    if key_points:
        elements.append(Paragraph("Key Discussion Points", heading_style))
        elements.extend(format_numbered_points(key_points))
        elements.append(Spacer(1, 12))
    
    # Add Action Items
    if action_items:
        elements.append(Paragraph("Action Items", heading_style))
        elements.extend(format_numbered_points(action_items))
        elements.append(Spacer(1, 12))
    
    # Add Next Steps
    if next_steps:
        elements.append(Paragraph("Next Steps", heading_style))
        elements.extend(format_numbered_points(next_steps))
        elements.append(Spacer(1, 12))
    
    if meeting_data.minutes_of_the_meeting_adjourned:
        elements.append(Paragraph(f'Meeting Adjourned: {meeting_data.minutes_of_the_meeting_adjourned.strftime("%I:%M %p")}', section_style))
    elements.append(Spacer(1, 12))

    # Get the student organizations for prepared_by and approved_by
    prepared_by_org = None
    approved_by_org = None
    
    if prepared_by:
        prepared_by_org = StudentOrganizations.query.get(prepared_by.users_student_organization)
    if approved_by:
        approved_by_org = StudentOrganizations.query.get(approved_by.users_student_organization)

    # Create data for the signatures table
    signature_data = []
    
    # Prepare the signature blocks
    if prepared_by:
        prepared_block = [
            Paragraph('Prepared By:', heading_style),
            Spacer(1, 20),
            Paragraph(f'{prepared_by.users_first_name} {prepared_by.users_last_name}', section_style),
            Paragraph(f'{prepared_by.users_student_organization_position}, {prepared_by_org.student_organizations_name if prepared_by_org else ""}', section_style)
        ]
    else:
        prepared_block = []

    if approved_by:
        approved_block = [
            Paragraph('Approved By:', heading_style),
            Spacer(1, 20),
            Paragraph(f'{approved_by.users_first_name} {approved_by.users_last_name}', section_style),
            Paragraph(f'{approved_by.users_student_organization_position}, {approved_by_org.student_organizations_name if approved_by_org else ""}', section_style)
        ]
    else:
        approved_block = []

    # Create table with signatures side by side
    if prepared_by or approved_by:
        signature_table = Table(
            [[prepared_block, approved_block]],
            colWidths=[doc.width/2]*2,  # Equal width columns without padding
            spaceAfter=30
        )
        
        # Add table style
        signature_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0)
        ]))
        
        elements.append(signature_table)
    
    # Noted By
    if noted_by:
        noted_block = [
            Paragraph('Noted By:', heading_style),
            Spacer(1, 20),
            Paragraph(f'{noted_by.signatory_first_name} {noted_by.signatory_last_name}', section_style),
            Paragraph(f'{noted_by.signatory_position}, {noted_by.signatory_department}', section_style)
        ]
        
        noted_table = Table(
            [[noted_block]],
            colWidths=[doc.width/2],  # Use half width for consistent sizing
            spaceAfter=30
        )
        
        # Add table style for centering
        noted_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0)
        ]))
        
        elements.append(noted_table)
    
    # Add Photo Documentation section if there are photos
    if photos:
        elements.append(Paragraph('Photo Documentation', heading_style))
        elements.append(Spacer(1, 12))
        
        for photo in photos:
            try:
                # Download image from Cloudinary URL
                response = requests.get(photo['url'])
                if response.status_code == 200:
                    # Use BytesIO instead of temporary file
                    image_data = BytesIO(response.content)
                    img = Image(image_data, width=400, height=300, kind='proportional')
                    elements.append(img)
                    elements.append(Spacer(1, 12))
                    
            except Exception as e:
                current_app.logger.error(
                    "Failed to load photo for PDF generation: %s", e, exc_info=True
                )
                # If image fails to load, fall back to URL
                elements.append(Paragraph(
                    f'• {photo["url"]}',
                    section_style
                ))
        elements.append(Spacer(1, 12))

    # Build PDF with header on all pages
    doc.build(elements, onFirstPage=header, onLaterPages=header)
    
    # Reset buffer position
    buffer.seek(0)
    
    # Return the PDF as a download
    return send_file(
        buffer,
        download_name=f'minutes-of-meeting-{meeting_data.minutes_of_the_meeting_id}.pdf',
        mimetype='application/pdf'
    )


@meetings_bp.route('/add-minutes-of-the-meeting', methods=['GET', 'POST'])
@login_required
def add_minutes_of_the_meeting():
    if request.method == 'POST':
        date = request.form.get('minutes-of-the-meeting-date')
        semester = request.form.get('minutes-of-the-meeting-semester')
        academic_year = request.form.get('minutes-of-the-meeting-academic-year')
        other_academic_year = request.form.get('other-academic-year')
        status = request.form.get('minutes-of-the-meeting-status')
        presiding_officer = request.form.get('minutes-of-the-meeting-presiding-officer')
        agenda = request.form.get('minutes-of-the-meeting-agenda')
        adjourned = request.form.get('minutes-of-the-meeting-adjourned')
        approved_by = request.form.get('minutes-of-the-meeting-approved-by')
        prepared_by = request.form.get('minutes-of-the-meeting-prepared-by')
        noted_by = request.form.get('minutes-of-the-meeting-noted-by')
        attendees = request.form.getlist('minutes-of-the-meeting-attendees')
        photo_documentations = request.files.getlist('photo-documentation')

        # Use the value from the additional input field if "Other A.Y." is selected
        if academic_year == "Other":
            academic_year = other_academic_year

        # Convert date to datetime object
        date = datetime.strptime(date, '%Y-%m-%dT%H:%M')
        adjourned = datetime.strptime(adjourned, '%Y-%m-%dT%H:%M') if adjourned else None

        # Process meeting recording with Gemini Pro if provided
        meeting_recording = request.files.get('meeting-recording')
        if meeting_recording:
            filename = meeting_recording.filename.lower()
            if not (filename.endswith(('.mp4', '.avi', '.mov', '.mp3', '.wav', '.m4a'))):
                flash('Invalid file format. Please upload a video or audio file.', 'error')
                return redirect(request.url)

            try:
                notes = ''
                # Save file temporarily
                temp_path = os.path.join(tempfile.gettempdir(), secure_filename(filename))
                meeting_recording.save(temp_path)

                # Use Gemini's File API to upload
                uploaded_file = genai.upload_file(temp_path)

                # Wait for file to be ready (add a small delay)
                time.sleep(10)  # Wait 10 seconds for file processing

                # Create prompt for Gemini
                prompt = f"""Please analyze this meeting transcript and provide a response with only:
                1. Summary:
                   Use a single paragraph for the summary
                2. Key Discussion Points:
                   Use sub-numbering (2.1, 2.2, etc.) for each distinct point
                3. Action Items:
                   Use sub-numbering (3.1, 3.2, etc.) for each action item
                4. Next Steps:
                   Use sub-numbering (4.1, 4.2, etc.) for each step

                No text formatting, markdown, or other formatting. No additional analysis or comments."""

                # Process with Gemini Flash
                from config import AIConfig
                model_gemini_flash = genai.GenerativeModel(AIConfig.GEMINI_MODEL)
                response = model_gemini_flash.generate_content([
                    uploaded_file,
                    prompt
                ])
                
                # Combine AI-generated notes with user input
                ai_generated_notes = response.text
                notes = f"{notes}\n\nAI-Generated Summary:\n{ai_generated_notes}" if notes else ai_generated_notes

            except Exception as e:
                current_app.logger.error(
                    "Error processing recording with AI: %s", e, exc_info=True
                )
                flash(f'Error processing recording with AI: {str(e)}', 'error')
                return redirect(request.url)

        # Create a new minutes of the meeting
        new_meeting = MinutesOfTheMeeting(
            minutes_of_the_meeting_date=date,
            minutes_of_the_meeting_semester=semester,
            minutes_of_the_meeting_academic_year=academic_year,
            minutes_of_the_meeting_status=status,
            minutes_of_the_meeting_departments_id=current_user.users_departments_id,
            minutes_of_the_meeting_presiding_officer=presiding_officer,
            minutes_of_the_meeting_agenda=agenda,
            minutes_of_the_meeting_notes=notes,
            minutes_of_the_meeting_adjourned=adjourned,
            minutes_of_the_meeting_approved_by=approved_by,
            minutes_of_the_meeting_prepared_by=prepared_by,
            minutes_of_the_meeting_noted_by=noted_by
        )

        # Set JSON fields for attendees and photo documentation
        new_meeting.attendees = attendees
        photo_documentation_list = []
        for photo_documentation in photo_documentations:
            if photo_documentation:
                upload_result = cloudinary.uploader.upload(photo_documentation)
                photo_documentation_list.append({
                    'url': upload_result.get('secure_url'),
                    'public_id': upload_result.get('public_id')
                })
        new_meeting.photo_documentation = photo_documentation_list

        # Add the new meeting to the database
        db.session.add(new_meeting)
        db.session.commit()

        flash('Minutes of the meeting added successfully!', 'success')
        return redirect(url_for('meetings.minutes_of_the_meeting_overview'))

    # Query for distinct academic years
    academic_years = db.session.query(MinutesOfTheMeeting.minutes_of_the_meeting_academic_year).distinct().all()
    academic_years = [year[0] for year in academic_years]

    # Query for users to populate the approved by and prepared by fields
    users = Users.query.all()

    # Query for signatories to populate the presiding officer and noted by fields
    signatories = Signatories.query.all()

    # Query for student organizations and their members
    student_organizations = StudentOrganizations.query.all()

    student_org = StudentOrganizations.query.get(current_user.users_student_organization)
    student_org_name = student_org.student_organizations_name if student_org else "Unknown Organization"
    org_dict = {org.student_organizations_id: org.student_organizations_name for org in student_organizations}

    return render_template('minutes-of-meeting/add-minutes-of-the-meeting.html', academic_years=academic_years, users=users, signatories=signatories, student_organizations=student_organizations, student_org_name=student_org_name, current_user=current_user, org_dict=org_dict)


@meetings_bp.route('/update-minutes-of-the-meeting/<int:meeting_id>', methods=['GET', 'POST'])
@login_required
def update_minutes_of_the_meeting(meeting_id):
    meeting = MinutesOfTheMeeting.query.get_or_404(meeting_id)

    if not belongs_to_user_or_department(meeting, current_user):
        abort(403)

    if request.method == 'POST':
        date = request.form.get('minutes-of-the-meeting-date')
        semester = request.form.get('minutes-of-the-meeting-semester')
        academic_year = request.form.get('minutes-of-the-meeting-academic-year')
        other_academic_year = request.form.get('other-academic-year')
        status = request.form.get('minutes-of-the-meeting-status')
        presiding_officer = request.form.get('minutes-of-the-meeting-presiding-officer')
        agenda = request.form.get('minutes-of-the-meeting-agenda')
        notes = request.form.get('minutes-of-the-meeting-notes')
        adjourned = request.form.get('minutes-of-the-meeting-adjourned')
        approved_by = request.form.get('minutes-of-the-meeting-approved-by')
        prepared_by = request.form.get('minutes-of-the-meeting-prepared-by')
        noted_by = request.form.get('minutes-of-the-meeting-noted-by')
        attendees = request.form.getlist('minutes-of-the-meeting-attendees')
        photo_documentations = request.files.getlist('photo-documentation')

        # Use the value from the additional input field if "Other A.Y." is selected
        if academic_year == "Other":
            academic_year = other_academic_year

        # Convert date to datetime object
        date = datetime.strptime(date, '%Y-%m-%dT%H:%M')
        adjourned = datetime.strptime(adjourned, '%Y-%m-%dT%H:%M') if adjourned else None

        # Update the minutes of the meeting
        meeting.minutes_of_the_meeting_date = date
        meeting.minutes_of_the_meeting_semester = semester
        meeting.minutes_of_the_meeting_academic_year = academic_year
        meeting.minutes_of_the_meeting_status = status
        meeting.minutes_of_the_meeting_presiding_officer = presiding_officer
        meeting.minutes_of_the_meeting_agenda = agenda
        meeting.minutes_of_the_meeting_notes = notes
        meeting.minutes_of_the_meeting_adjourned = adjourned
        meeting.minutes_of_the_meeting_approved_by = approved_by
        meeting.minutes_of_the_meeting_prepared_by = prepared_by
        meeting.minutes_of_the_meeting_noted_by = noted_by

        # Update attendees as a JSON list of user IDs
        meeting.attendees = attendees

        # Handle multiple file uploads to Cloudinary
        if photo_documentations:
            # Delete existing photos from Cloudinary
            existing_photos = meeting.photo_documentation or []
            for photo in existing_photos:
                try:
                    cloudinary.uploader.destroy(photo['public_id'])
                except Exception as e:
                    current_app.logger.error(
                        "Error deleting existing photo from Cloudinary: %s", e, exc_info=True
                    )
                    flash('Error deleting existing photo from Cloudinary', 'error')

            # Upload new photos and store as JSON
            new_photo_documentation = []
            for photo_documentation in photo_documentations:
                if photo_documentation:
                    upload_result = cloudinary.uploader.upload(photo_documentation)
                    new_photo_documentation.append({
                        'url': upload_result.get('secure_url'),
                        'public_id': upload_result.get('public_id')
                    })
            meeting.photo_documentation = new_photo_documentation

        db.session.commit()
        flash('Minutes of the meeting updated successfully!', 'success')
        return redirect(url_for('meetings.minutes_of_the_meeting_overview'))

    # Query for distinct academic years
    academic_years = db.session.query(MinutesOfTheMeeting.minutes_of_the_meeting_academic_year).distinct().all()
    academic_years = [year[0] for year in academic_years]

    # Query for existing photo documentations and attendees from JSON fields
    photo_documentations = meeting.photo_documentation or []

    # Query for users to populate the approved by and prepared by fields
    users = Users.query.all()

    # Query for signatories to populate the presiding officer and noted by fields
    signatories = Signatories.query.all()

    # Existing attendees is the JSON list
    meeting_attendees = meeting.attendees or []

    # Query for student organizations and their members
    student_organizations = StudentOrganizations.query.all()

    return render_template('minutes-of-meeting/update-minutes-of-the-meeting.html', meeting=meeting, academic_years=academic_years, photo_documentations=photo_documentations, users=users, signatories=signatories, meeting_attendees=meeting_attendees, student_organizations=student_organizations)


@meetings_bp.route("/update-minutes-of-the-meeting-status/<int:meeting_id>", methods=["POST"])
@login_required
def update_minutes_of_the_meeting_status(meeting_id):
    data = request.get_json()
    new_status = data.get('status')

    # Find the minutes of the meeting by ID
    meeting = MinutesOfTheMeeting.query.get_or_404(meeting_id)

    if not belongs_to_user_or_department(meeting, current_user):
        abort(403)

    # Update the minutes of the meeting status
    meeting.minutes_of_the_meeting_status = new_status
    db.session.commit()

    return jsonify(success=True)


@meetings_bp.route('/delete-minutes-of-the-meeting/<int:meeting_id>', methods=['GET', 'POST'])
@login_required
def delete_minutes_of_the_meeting(meeting_id):
    meeting = MinutesOfTheMeeting.query.get_or_404(meeting_id)

    if not belongs_to_user_or_department(meeting, current_user):
        abort(403)

    if request.method == 'POST':
        # Delete related photo documentation from Cloudinary
        for photo in meeting.photo_documentation or []:
            try:
                cloudinary.uploader.destroy(photo['public_id'])
            except Exception as e:
                current_app.logger.error(
                    "Error deleting photo from Cloudinary: %s", e, exc_info=True
                )
                flash('Error deleting photo from Cloudinary', 'error')

        # Finally, delete the meeting (attendees are JSON and removed automatically)
        db.session.delete(meeting)
        db.session.commit()

        flash('Minutes of the meeting deleted successfully!', 'success')
        return redirect(url_for('meetings.minutes_of_the_meeting_overview'))

    return render_template('minutes-of-meeting/delete-minutes-of-the-meeting.html', meeting=meeting)
