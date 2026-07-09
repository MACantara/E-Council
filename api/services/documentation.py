"""FastAPI documentation helper services."""

from __future__ import annotations

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy.orm import Session

from models import Documentation, Users


def generate_documentation_pdf(
    db: Session,
    documentation: Documentation,
    user: Users,
) -> BytesIO:
    """Generate a simple PDF for a documentation record."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=18,
        alignment=1,
        spaceAfter=20,
    )
    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontSize=12,
        spaceAfter=10,
        textColor=colors.HexColor("#8c0404"),
    )
    normal_style = ParagraphStyle(
        "Normal",
        parent=styles["Normal"],
        fontSize=11,
        leading=14,
        alignment=4,
        spaceAfter=10,
    )
    label_style = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=11,
        leading=14,
        fontName="Helvetica-Bold",
    )

    story = []
    story.append(Paragraph("Documentation", title_style))
    story.append(Spacer(1, 0.2 * inch))

    def _fmt(value):
        return value.strftime("%B %d, %Y %I:%M %p") if value else ""

    details = [
        [Paragraph("Type:", label_style), Paragraph(str(documentation.documentation_type or ""), normal_style)],
        [Paragraph("Status:", label_style), Paragraph(str(documentation.documentation_status or ""), normal_style)],
        [Paragraph("Academic Year:", label_style), Paragraph(str(documentation.documentation_academic_year or ""), normal_style)],
        [Paragraph("Semester:", label_style), Paragraph(str(documentation.documentation_semester or ""), normal_style)],
        [Paragraph("Date of Submission:", label_style), Paragraph(_fmt(documentation.documentation_date_of_submission), normal_style)],
        [Paragraph("Rating:", label_style), Paragraph(str(documentation.documentation_rating or ""), normal_style)],
    ]

    table = Table(details, colWidths=[2 * inch, 4.5 * inch])
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 0.2 * inch))

    if documentation.documentation_comments_suggestions:
        story.append(Paragraph("Comments / Suggestions", heading_style))
        story.append(Paragraph(documentation.documentation_comments_suggestions, normal_style))
        story.append(Spacer(1, 0.2 * inch))

    if documentation.activity_report_items:
        story.append(Paragraph("Activity Report Items", heading_style))
        for item in documentation.activity_report_items:
            story.append(Paragraph(f"• {item.item_type}: {item.item_text}", normal_style))
        story.append(Spacer(1, 0.2 * inch))

    if documentation.tally_items:
        story.append(Paragraph("Tally Items", heading_style))
        for tally in documentation.tally_items:
            story.append(
                Paragraph(
                    f"• {tally.name}: {tally.extremely_satisfied} / {tally.satisfied} / "
                    f"{tally.neutral} / {tally.dissatisfied} / {tally.extremely_dissatisfied}",
                    normal_style,
                )
            )
        story.append(Spacer(1, 0.2 * inch))

    if documentation.evaluation_forms:
        story.append(Paragraph("Evaluation Forms", heading_style))
        for form in documentation.evaluation_forms:
            story.append(Paragraph(f"• {form.name}: {form.rating or 'N/A'}", normal_style))

    doc.build(story)
    buffer.seek(0)
    return buffer
