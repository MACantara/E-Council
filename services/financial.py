"""Service layer for the financial module."""

import os
from datetime import datetime
from io import BytesIO

from flask import abort, flash, jsonify, redirect, render_template, request, send_file, url_for
from flask_login import current_user
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Flowable, Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import or_

from models import (
    ActivityReportForms,
    Departments,
    DepartmentsEvents,
    Events,
    FinancialReports,
    Signatories,
    StudentOrganizations,
    Users,
    db,
)
from utils.auth import belongs_to_user_or_department, is_admin
from utils.helpers import get_pagination_args


class CustomUnderline(Flowable):
    def __init__(self, width, thickness, y_offset=0, gap=2):
        Flowable.__init__(self)
        self.width = width
        self.thickness = thickness
        self.y_offset = y_offset
        self.gap = gap

    def draw(self):
        shortened_width = self.width * 0.3
        start_x = (self.width - shortened_width) / 2
        self.canv.setLineWidth(self.thickness)
        self.canv.line(start_x, self.y_offset, start_x + shortened_width, self.y_offset)


def financial_reports_overview():
    # Determine the sorting order and pagination parameters
    sort_by_date = request.args.get("sort_by_date", "recent-to-old")
    page, per_page = get_pagination_args()

    # Admins can view all financial reports; others only see their own department's or ones they prepared
    query = FinancialReports.query.order_by(FinancialReports.financial_reports_date.desc())
    if not is_admin(current_user):
        query = query.filter(
            or_(
                FinancialReports.financial_reports_departments_id == current_user.users_departments_id,
                FinancialReports.financial_reports_audited_and_prepared_by == current_user.users_id,
            )
        )

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        "financial-reports/financial-reports-overview.html",
        financial_reports=pagination.items,
        pagination=pagination,
        sort_by_date=sort_by_date,
    )


def add_financial_report():
    if request.method == "POST":
        financial_reports_date = request.form.get("financial-reports-date")
        financial_reports_academic_year = request.form.get("financial-reports-academic-year")
        financial_reports_semester = request.form.get("financial-reports-semester")
        financial_reports_events_id = request.form.get("financial-reports-events-id")
        financial_reports_title = request.form.get("financial-reports-title")
        financial_reports_status = request.form.get("financial-reports-status")
        financial_reports_audited_and_prepared_by = request.form.get("financial-reports-audited-and-prepared-by")
        financial_reports_noted_by = request.form.get("financial-reports-noted-by")
        financial_reports_recommending_approval_by = request.form.get("financial-reports-recommending-approval-by")
        financial_reports_approved_by = request.form.get("financial-reports-approved-by")

        # Create a new financial report
        new_financial_report = FinancialReports(
            financial_reports_date=datetime.strptime(financial_reports_date, "%Y-%m-%dT%H:%M"),
            financial_reports_academic_year=financial_reports_academic_year,
            financial_reports_semester=financial_reports_semester,
            financial_reports_events_id=financial_reports_events_id,
            financial_reports_departments_id=current_user.users_departments_id,
            financial_reports_title=financial_reports_title,
            financial_reports_status=financial_reports_status,
            financial_reports_audited_and_prepared_by=financial_reports_audited_and_prepared_by,
            financial_reports_noted_by=financial_reports_noted_by,
            financial_reports_recommending_approval_by=financial_reports_recommending_approval_by,
            financial_reports_approved_by=financial_reports_approved_by,
        )

        # Add the new financial report to the database
        db.session.add(new_financial_report)
        db.session.commit()

        flash("Financial report added successfully!", "success")
        return redirect(url_for("financial.financial_reports_overview"))

    # Query for events that do not have a financial report
    events = (
        Events.query.outerjoin(FinancialReports, Events.events_id == FinancialReports.financial_reports_events_id)
        .filter(FinancialReports.financial_reports_events_id is None)
        .all()
    )

    # Query for users grouped by student organization
    student_organizations = StudentOrganizations.query.all()

    # Query for signatories
    signatories = Signatories.query.all()

    # Query for distinct academic years
    academic_years = db.session.query(FinancialReports.financial_reports_academic_year).distinct().all()
    academic_years = [year[0] for year in academic_years]

    return render_template(
        "financial-reports/add-financial-report.html",
        events=events,
        student_organizations=student_organizations,
        signatories=signatories,
        academic_years=academic_years,
    )


def update_financial_report(report_id):
    report = FinancialReports.query.get_or_404(report_id)

    if not belongs_to_user_or_department(report, current_user):
        abort(403)

    if request.method == "POST":
        financial_reports_date = request.form.get("financial-reports-date")
        financial_reports_academic_year = request.form.get("financial-reports-academic-year")
        financial_reports_semester = request.form.get("financial-reports-semester")
        financial_reports_events_id = request.form.get("financial-reports-events-id")
        financial_reports_title = request.form.get("financial-reports-title")
        financial_reports_status = request.form.get("financial-reports-status")
        financial_reports_audited_and_prepared_by = request.form.get("financial-reports-audited-and-prepared-by")
        financial_reports_noted_by = request.form.get("financial-reports-noted-by")
        financial_reports_recommending_approval_by = request.form.get("financial-reports-recommending-approval-by")
        financial_reports_approved_by = request.form.get("financial-reports-approved-by")

        # Update the financial report
        report.financial_reports_date = datetime.strptime(financial_reports_date, "%Y-%m-%dT%H:%M")
        report.financial_reports_academic_year = financial_reports_academic_year
        report.financial_reports_semester = financial_reports_semester
        report.financial_reports_events_id = financial_reports_events_id
        report.financial_reports_title = financial_reports_title
        report.financial_reports_status = financial_reports_status
        report.financial_reports_audited_and_prepared_by = financial_reports_audited_and_prepared_by
        report.financial_reports_noted_by = financial_reports_noted_by
        report.financial_reports_recommending_approval_by = financial_reports_recommending_approval_by
        report.financial_reports_approved_by = financial_reports_approved_by

        db.session.commit()

        flash("Financial report updated successfully!", "success")
        return redirect(url_for("financial.financial_reports_overview"))

    # Query for events
    events = Events.query.all()

    # Query for users grouped by student organization
    student_organizations = StudentOrganizations.query.all()

    # Query for signatories
    signatories = Signatories.query.all()

    # Query for distinct academic years
    academic_years = db.session.query(FinancialReports.financial_reports_academic_year).distinct().all()
    academic_years = [year[0] for year in academic_years]

    return render_template(
        "financial-reports/update-financial-report.html",
        report=report,
        events=events,
        student_organizations=student_organizations,
        signatories=signatories,
        academic_years=academic_years,
    )


def update_financial_report_status(report_id):
    data = request.get_json()
    new_status = data.get("status")

    # Find the financial report by ID
    report = FinancialReports.query.get_or_404(report_id)

    if not belongs_to_user_or_department(report, current_user):
        abort(403)

    # Update the financial report status
    report.financial_reports_status = new_status
    db.session.commit()

    return jsonify(success=True)


def delete_financial_report(report_id):
    report = FinancialReports.query.get_or_404(report_id)

    if not belongs_to_user_or_department(report, current_user):
        abort(403)

    if request.method == "POST":
        # Delete the financial report
        db.session.delete(report)
        db.session.commit()

        flash("Financial report deleted successfully!", "success")
        return redirect(url_for("financial.financial_reports_overview"))

    return render_template("financial-reports/delete-financial-report.html", report=report)


def generate_financial_report_pdf(financial_report_id):
    # Get financial report with event details
    report = (
        db.session.query(FinancialReports, Events)
        .outerjoin(Events, FinancialReports.financial_reports_events_id == Events.events_id)
        .filter(FinancialReports.financial_reports_id == financial_report_id)
        .first_or_404()
    )

    if not belongs_to_user_or_department(report[0], current_user):
        abort(403)

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

        # Add footer
        canvas.setStrokeColorRGB(0, 0, 0)
        canvas.setLineWidth(1)
        footer_y = doc.bottomMargin - 20
        canvas.line(doc.leftMargin, footer_y, doc.leftMargin + doc.width, footer_y)

        # Add footer text
        canvas.setFont("Helvetica", 12)
        canvas.drawString(doc.leftMargin, footer_y - 15, "UPHMO-CCS-GEN-912/rev0")
        right_text = "Financial Report"
        right_text_width = canvas.stringWidth(right_text, "Helvetica", 12)
        canvas.drawString(doc.leftMargin + doc.width - right_text_width, footer_y - 15, right_text)

        canvas.restoreState()

    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=100, bottomMargin=72)

    # Create the story (content) for the PDF
    story = []
    styles = getSampleStyleSheet()

    # Add title
    title_style = ParagraphStyle("CustomTitle", parent=styles["Heading1"], fontSize=16, alignment=1)

    story.append(Paragraph("Financial Report Form (FPF)", title_style))
    story.append(Spacer(1, 12))

    # Add Activity Details header
    section_header_style = ParagraphStyle(
        "SectionHeader", parent=styles["Normal"], fontSize=12, fontName="Helvetica-Bold", spaceAfter=10
    )
    story.append(Paragraph("I. Activity Details", section_header_style))
    story.append(Spacer(1, 10))

    # Get event details
    event = Events.query.get(report[0].financial_reports_events_id)

    # Get department through DepartmentsEvents
    dept_event = DepartmentsEvents.query.filter_by(events_id=event.events_id).first()
    department = Departments.query.get(dept_event.departments_id) if dept_event else None

    # Get activity report form
    activity_report = ActivityReportForms.query.filter_by(
        activity_report_forms_concept_paper_forms_id=event.events_concept_paper_forms_id
    ).first()

    # Format dates and times
    start_datetime = event.events_start_date_and_time
    end_datetime = event.events_end_date_and_time

    date_str = f"{start_datetime.strftime('%B %d, %Y')}"
    if start_datetime.date() != end_datetime.date():
        date_str += f" - {end_datetime.strftime('%B %d, %Y')}"

    # Remove leading zeros by converting to int
    start_hour = int(start_datetime.strftime("%I"))
    end_hour = int(end_datetime.strftime("%I"))
    time_str = f"{start_hour}:{start_datetime.strftime('%M %p')} - {end_hour}:{end_datetime.strftime('%M %p')}"

    # Create table data with two columns, combining title and content
    table_data = [
        [
            Paragraph("<b>Title of the Activity:</b><br/>" + event.events_name, styles["Normal"]),
            Paragraph("<b>Date:</b><br/>" + date_str, styles["Normal"]),
        ],
        [
            Paragraph(
                "<b>Nature of the Activity:</b><br/>"
                + (activity_report.activity_report_forms_nature_of_the_activity if activity_report else ""),
                styles["Normal"],
            ),
            Paragraph("<b>Time:</b><br/>" + time_str, styles["Normal"]),
        ],
        [
            Paragraph(
                "<b>College/Department:</b><br/>" + (department.departments_name if department else ""),
                styles["Normal"],
            ),
            Paragraph("<b>Venue:</b><br/>" + event.events_venue, styles["Normal"]),
        ],
    ]

    # Create table style
    table_style = TableStyle(
        [
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ]
    )

    # Create and add table with two equal columns
    col_widths = [230, 230]
    table = Table(table_data, colWidths=col_widths)
    table.setStyle(table_style)
    story.append(table)
    story.append(Spacer(1, 20))

    # Add Collection and Expenses header
    story.append(Spacer(1, 20))
    story.append(Paragraph("II. Collection and Expenses", section_header_style))
    story.append(Spacer(1, 10))

    # Get transactions for this event from the related Transaction records
    transactions = sorted(event.transactions or [], key=lambda t: t.transaction_date or 0)
    total_expenses = sum(float(t.total or 0) for t in transactions)
    budget = float(event.events_budget)
    remaining_money = budget - total_expenses

    # Create a right-aligned style for totals
    right_aligned_style = ParagraphStyle("RightAligned", parent=styles["Normal"], alignment=TA_RIGHT)

    # Register DejaVu Sans font with the correct path
    font_path = os.path.join(os.path.dirname(__file__), "..", "fonts", "DejaVuSans.ttf")
    pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))

    # Create a style that uses the Unicode-compatible font
    amount_style = ParagraphStyle("Amount", parent=styles["Normal"], fontName="DejaVuSans")

    # Create combined data for a single table
    table_data = [
        # Source of Fund section
        [Paragraph("<b>Source of Fund:</b>", styles["Normal"]), Paragraph("", styles["Normal"])],
        [Paragraph("CCS Bankbook", styles["Normal"]), Paragraph(f"₱{budget:,.2f}", amount_style)],
        [Paragraph("<b>Total Budget:</b>", right_aligned_style), Paragraph(f"<b>₱{budget:,.2f}</b>", amount_style)],
        ["", [CustomUnderline(180, 0.5, y_offset=8), CustomUnderline(180, 0.5, y_offset=6)]],
        # Less Expense section
        [Paragraph("<b>Less Expense:</b>", styles["Normal"]), Paragraph("", styles["Normal"])],
    ]

    # Add expenses
    for transaction in transactions:
        transaction_total = float(transaction.total or 0)
        table_data.append(
            [
                Paragraph(transaction.transaction_name or "", styles["Normal"]),
                Paragraph(f"₱{transaction_total:,.2f}", amount_style),
            ]
        )

    # Add empty row before totals
    table_data.append([Paragraph("", styles["Normal"]), Paragraph("", styles["Normal"])])

    table_data.extend(
        [
            [
                Paragraph("<b>Total Expenses:</b>", right_aligned_style),
                Paragraph(f"<b>₱{total_expenses:,.2f}</b>", amount_style),
            ],
            ["", [CustomUnderline(180, 0.5, y_offset=8), CustomUnderline(180, 0.5, y_offset=6)]],
            [Paragraph("", styles["Normal"]), Paragraph("", styles["Normal"])],
            [
                Paragraph("<b>Total Remaining Money:</b>", styles["Normal"]),
                Paragraph(f"<b>₱{remaining_money:,.2f}</b>", amount_style),
            ],
        ]
    )

    # Create table style with selective borders
    table_style = TableStyle(
        [
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LINEABOVE", (0, -4), (-1, -4), 1, colors.black),
            ("TOPPADDING", (0, 4), (-1, 4), 8),
            ("BOX", (0, 0), (-1, -1), 1, colors.black),
            ("LINEABOVE", (0, 2), (-1, 2), 1, colors.black),
            ("LINEABOVE", (0, -1), (-1, -1), 1, colors.black),
        ]
    )

    # Create and add table
    financial_table = Table(table_data, colWidths=[340, 125])
    financial_table.setStyle(table_style)
    story.append(financial_table)

    # Add signature section after the financial table
    story.append(Spacer(1, 30))

    # Create styles for signature sections
    signature_style = ParagraphStyle("Signature", parent=styles["Normal"], fontSize=12, spaceAfter=30)

    name_style = ParagraphStyle("SignatureName", parent=styles["Normal"], fontSize=12, fontName="Helvetica-Bold")

    position_style = ParagraphStyle("Position", parent=styles["Normal"], fontSize=12)

    # Get user data for each position from Users table
    auditor = Users.query.get(report[0].financial_reports_audited_and_prepared_by)
    treasurer = Users.query.get(report[0].financial_reports_noted_by)
    president = Users.query.get(report[0].financial_reports_recommending_approval_by)

    # Get adviser data from Signatories table
    adviser = Signatories.query.get(report[0].financial_reports_approved_by)

    # Get organization data from the first user's student organization
    organization = auditor.student_organization

    # Add signature blocks with dynamic data
    # Auditor section
    story.append(Paragraph("AUDITED AND PREPARED BY:", signature_style))
    story.append(
        Paragraph(
            f"{auditor.users_first_name} {auditor.users_middle_name if auditor.users_middle_name else ''} {auditor.users_last_name}",
            name_style,
        )
    )
    story.append(
        Paragraph(
            f"{auditor.users_student_organization_position}, {organization.student_organizations_name}", position_style
        )
    )
    story.append(Spacer(1, 30))

    # Treasurer section
    story.append(Paragraph("NOTED BY:", signature_style))
    story.append(
        Paragraph(
            f"{treasurer.users_first_name} {treasurer.users_middle_name if treasurer.users_middle_name else ''} {treasurer.users_last_name}",
            name_style,
        )
    )
    story.append(
        Paragraph(
            f"{treasurer.users_student_organization_position}, {organization.student_organizations_name}",
            position_style,
        )
    )
    story.append(Spacer(1, 30))

    # President section
    story.append(Paragraph("RECOMMENDING APPROVAL BY:", signature_style))
    story.append(
        Paragraph(
            f"{president.users_first_name} {president.users_middle_name if president.users_middle_name else ''} {president.users_last_name}",
            name_style,
        )
    )
    story.append(
        Paragraph(
            f"{president.users_student_organization_position}, {organization.student_organizations_name}",
            position_style,
        )
    )
    story.append(Spacer(1, 30))

    # Adviser section
    story.append(Paragraph("APPROVED BY:", signature_style))
    story.append(
        Paragraph(
            f"{adviser.signatory_title} {adviser.signatory_first_name} {adviser.signatory_middle_name if adviser.signatory_middle_name else ''} {adviser.signatory_last_name}",
            name_style,
        )
    )
    story.append(Paragraph(f"Adviser, {organization.student_organizations_name}", position_style))

    # Add a page break before the receipt
    story.append(PageBreak())

    # Add the receipt image if it exists
    if transactions:
        # Add each receipt image
        for idx, transaction in enumerate(transactions, 1):
            if transaction.receipt_url:
                # Add receipt number if there are multiple receipts
                if len(transactions) > 1:
                    story.append(
                        Paragraph(
                            f"Receipt {idx}",
                            ParagraphStyle(
                                "ReceiptNumber", parent=styles["Normal"], fontSize=12, alignment=1, spaceAfter=10
                            ),
                        )
                    )

                # Get the image from Cloudinary URL
                receipt_image = Image(transaction.receipt_url)

                # Calculate available space (leaving margins)
                available_width = letter[0] - 2 * inch
                available_height = letter[1] - 4 * inch

                # Calculate scaling ratios for both width and height
                width_ratio = available_width / receipt_image.imageWidth
                height_ratio = available_height / receipt_image.imageHeight

                # Use the smaller ratio to ensure image fits both dimensions
                scale_ratio = min(width_ratio, height_ratio)

                # Apply the scaling
                receipt_image.drawWidth = receipt_image.imageWidth * scale_ratio
                receipt_image.drawHeight = receipt_image.imageHeight * scale_ratio

                story.append(receipt_image)

                # Add space between receipts
                if idx < len(transactions):
                    story.append(Spacer(1, 30))
    else:
        # Add a message if no receipts are available
        no_receipt_style = ParagraphStyle("NoReceipt", parent=styles["Normal"], fontSize=12, alignment=1)
        story.append(Paragraph("No transaction receipts available", no_receipt_style))

    doc.build(story, onFirstPage=header, onLaterPages=header)

    buffer.seek(0)
    return send_file(buffer, download_name=f"Financial_Report_{financial_report_id}.pdf", mimetype="application/pdf")
