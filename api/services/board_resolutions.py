"""FastAPI board resolution helper services."""

from __future__ import annotations

from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer
from sqlalchemy.orm import Session

from models import BoardResolutions, Signatories, StudentOrganizations, Users


def generate_board_resolution_pdf(
    db: Session,
    resolution: BoardResolutions,
    user: Users,
) -> BytesIO:
    """Generate a board resolution PDF using the current database session."""
    prepared_by = db.get(Users, resolution.board_resolutions_prepared_by)
    approved_by = db.get(Signatories, resolution.board_resolutions_approved_by)

    signatory_users = (
        db.query(Users, StudentOrganizations)
        .join(
            StudentOrganizations,
            Users.users_student_organization
            == StudentOrganizations.student_organizations_id,
        )
        .filter(Users.users_id.in_(resolution.student_signatory_ids or []))
        .order_by(StudentOrganizations.student_organizations_name)
        .all()
    )

    student_signatories = [(None, user, org) for user, org in signatory_users]

    buffer = BytesIO()

    def header(canvas, doc):
        canvas.saveState()

        header_perps = Image("./static/img/logos/HEADER-PERPS.png", width=325, height=75)
        perps_x = doc.leftMargin - 35
        header_perps.drawOn(canvas, perps_x, doc.height + doc.topMargin)

        header_ccs = Image("./static/img/logos/CCS-LOGO.png", width=35, height=50)
        ccs_x = doc.leftMargin + (doc.width - 35) / 2 + 125
        header_ccs.drawOn(canvas, ccs_x, doc.height + doc.topMargin + 15)

        header_iso = Image("./static/img/logos/ISO.png", width=100, height=50)
        iso_x = doc.leftMargin + doc.width - 80
        header_iso.drawOn(canvas, iso_x, doc.height + doc.topMargin + 15)

        canvas.setFont("Helvetica-Bold", 10)
        text = "College of Computer Studies"
        text_width = canvas.stringWidth(text, "Helvetica-Bold", 10)
        text_x = iso_x + (50 - text_width) / 2
        canvas.drawString(text_x, doc.height + doc.topMargin, text)

        canvas.setStrokeColorRGB(0x8C / 255, 0x04 / 255, 0x04 / 255)
        canvas.setLineWidth(2)
        line_y = doc.height + doc.topMargin - 10
        line_length = 510
        line_start_x = (doc.width - line_length) / 2 + doc.leftMargin
        line_end_x = line_start_x + line_length
        canvas.line(line_start_x - 5, line_y, line_end_x, line_y)

        if doc.page > 1:
            canvas.setFont("Helvetica", 12)
            continuation_text = "Continuation of the Board Resolution"
            canvas.drawString(doc.leftMargin, doc.height + doc.topMargin - 30, continuation_text)

        canvas.setStrokeColorRGB(0, 0, 0)
        canvas.setLineWidth(1)
        footer_y = doc.bottomMargin - 20
        canvas.line(doc.leftMargin, footer_y, doc.leftMargin + doc.width, footer_y)

        canvas.setFont("Helvetica", 12)
        canvas.drawString(doc.leftMargin, footer_y - 15, "UPHMO-CCS-GEN-912/rev0")
        right_text = "Board Resolution"
        right_text_width = canvas.stringWidth(right_text, "Helvetica", 12)
        canvas.drawString(
            doc.leftMargin + doc.width - right_text_width,
            footer_y - 15,
            right_text,
        )

        canvas.restoreState()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=110,
        bottomMargin=72,
    )

    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=12,
        alignment=1,
        spaceBefore=5,
        spaceAfter=-15,
    )
    academic_year_style = ParagraphStyle(
        "AcademicYear",
        parent=styles["Heading1"],
        fontSize=11,
        alignment=1,
        spaceAfter=20,
    )
    resolution_style = ParagraphStyle(
        "Resolution",
        parent=styles["Heading1"],
        fontSize=12,
        alignment=1,
        spaceAfter=20,
    )

    story.append(Paragraph("College of Computer Studies Council", title_style))
    story.append(
        Paragraph(f"A.Y. {resolution.board_resolutions_academic_year or ''}", academic_year_style)
    )
    story.append(Paragraph("Resolution", resolution_style))

    content_style = ParagraphStyle(
        "Content",
        parent=styles["Normal"],
        fontSize=12,
        leading=14,
        alignment=4,
        firstLineIndent=36,
    )

    story.append(Paragraph(resolution.board_resolutions_description or "", content_style))
    story.append(Spacer(1, 15))

    signature_style = ParagraphStyle(
        "Signature",
        parent=styles["Normal"],
        fontSize=12,
        alignment=0,
        spaceAfter=20,
    )

    org_signatories = {}
    for signatory, user, org in student_signatories:
        if org.student_organizations_name not in org_signatories:
            org_signatories[org.student_organizations_name] = []
        org_signatories[org.student_organizations_name].append((signatory, user))

    org_header_style = ParagraphStyle(
        "OrgHeader",
        parent=styles["Normal"],
        fontSize=12,
        alignment=0,
        fontName="Helvetica-Bold",
        spaceAfter=10,
    )

    org_acronyms = {
        "College of Computer Studies - Student Council": "CCSC",
        "Junior Philippine Computer Society": "JPCS",
    }

    for org_name, signatories in org_signatories.items():
        story.append(Paragraph(org_name, org_header_style))
        for _signatory, user in signatories:
            signature_text = f"<b>{user.users_first_name} {user.users_last_name}</b>"
            if user.users_student_organization_position:
                org_acronym = org_acronyms.get(org_name, org_name)
                signature_text += (
                    f"<br/><i>{org_acronym}, {user.users_student_organization_position}</i>"
                )
            story.append(Paragraph(signature_text, signature_style))
            story.append(Spacer(1, 5))

    if prepared_by:
        story.append(Paragraph("Prepared by:", signature_style))
        prepared_by_text = f"<b>{prepared_by.users_first_name} {prepared_by.users_last_name}</b>"
        if prepared_by.users_student_organization_position:
            org_acronym = org_acronyms.get("College of Computer Studies - Student Council", "CCSC")
            prepared_by_text += (
                f"<br/><i>{org_acronym}, {prepared_by.users_student_organization_position}</i>"
            )
        story.append(Paragraph(prepared_by_text, signature_style))
        story.append(Spacer(1, 20))

    if approved_by:
        story.append(Paragraph("Approved by:", signature_style))
        approved_by_text = (
            f"<b>{approved_by.signatory_first_name} {approved_by.signatory_last_name}</b>"
        )
        approved_by_text += "<br/><i>Adviser, College of Computer Studies - Student Council</i>"
        story.append(Paragraph(approved_by_text, signature_style))

    doc.build(story, onFirstPage=header, onLaterPages=header)
    buffer.seek(0)
    return buffer
