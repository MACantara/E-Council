"""FastAPI concept paper helper services."""

from __future__ import annotations

from io import BytesIO

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
from reportlab.lib import colors
from sqlalchemy.orm import Session

from models import ConceptPaperForms, Users


def generate_concept_paper_pdf(
    db: Session,
    paper: ConceptPaperForms,
    user: Users,
) -> BytesIO:
    """Generate a simple PDF for a concept paper."""
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
    story.append(Paragraph("Concept Paper", title_style))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph(f"Subject: {paper.concept_paper_forms_subject or ''}", heading_style))
    story.append(Spacer(1, 0.1 * inch))

    def _fmt_dt(value):
        if value is None:
            return ""
        return value.strftime("%B %d, %Y %I:%M %p")

    details = [
        [Paragraph("Status:", label_style), Paragraph(str(paper.concept_paper_forms_status or ""), normal_style)],
        [Paragraph("Academic Year:", label_style), Paragraph(str(paper.concept_paper_forms_academic_year or ""), normal_style)],
        [Paragraph("Semester:", label_style), Paragraph(str(paper.concept_paper_forms_semester or ""), normal_style)],
        [Paragraph("Date of Submission:", label_style), Paragraph(_fmt_dt(paper.concept_paper_forms_date), normal_style)],
        [Paragraph("Event Start:", label_style), Paragraph(_fmt_dt(paper.concept_paper_forms_event_start_date_and_time), normal_style)],
        [Paragraph("Event End:", label_style), Paragraph(_fmt_dt(paper.concept_paper_forms_event_end_date_and_time), normal_style)],
        [Paragraph("Location:", label_style), Paragraph(str(paper.concept_paper_forms_location or ""), normal_style)],
        [Paragraph("Participants:", label_style), Paragraph(str(paper.concept_paper_forms_participants or ""), normal_style)],
        [Paragraph("Budget:", label_style), Paragraph(str(paper.concept_paper_forms_budget or ""), normal_style)],
        [Paragraph("Expected Participants:", label_style), Paragraph(str(paper.concept_paper_forms_expected_number_of_participants or ""), normal_style)],
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

    if paper.concept_paper_forms_body:
        story.append(Paragraph("Body", heading_style))
        for line in paper.concept_paper_forms_body.split("\n"):
            if line.strip():
                story.append(Paragraph(line.strip(), normal_style))
        story.append(Spacer(1, 0.2 * inch))

    if paper.concept_paper_forms_descriptions:
        story.append(Paragraph("Description", heading_style))
        story.append(Paragraph(paper.concept_paper_forms_descriptions, normal_style))
        story.append(Spacer(1, 0.2 * inch))

    if paper.objectives:
        story.append(Paragraph("Objectives", heading_style))
        for obj in paper.objectives:
            story.append(Paragraph(f"• {obj.objective_text}", normal_style))
        story.append(Spacer(1, 0.2 * inch))

    if paper.learning_outcomes:
        story.append(Paragraph("Learning Outcomes", heading_style))
        for outcome in paper.learning_outcomes:
            story.append(Paragraph(f"• {outcome.learning_outcome_text}", normal_style))

    doc.build(story)
    buffer.seek(0)
    return buffer
