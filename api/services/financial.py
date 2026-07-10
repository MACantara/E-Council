"""FastAPI financial helper services."""

from __future__ import annotations

from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
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

from models import Departments, DepartmentsEvents, Events, FinancialReports, Signatories, Users


def _format_currency(value: Any) -> str:
    """Format a numeric value as Philippine pesos."""
    try:
        amount = float(value or 0)
    except (TypeError, ValueError):
        amount = 0.0
    return f"₱{amount:,.2f}"


def _parse_budget(value: Any) -> float:
    """Parse a budget value to a float."""
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def generate_financial_report_pdf(
    db: Session,
    report: FinancialReports,
) -> BytesIO:
    """Generate a financial report PDF."""
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
        spaceAfter=10,
    )
    label_style = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=11,
        leading=14,
        fontName="Helvetica-Bold",
    )
    right_aligned_style = ParagraphStyle(
        "RightAligned",
        parent=styles["Normal"],
        alignment=TA_RIGHT,
    )

    story = []
    story.append(Paragraph("Financial Report", title_style))
    story.append(Spacer(1, 12))

    story.append(Paragraph("I. Report Details", heading_style))

    details = [
        [Paragraph("Title:", label_style), Paragraph(report.financial_reports_title or "", normal_style)],
        [
            Paragraph("Academic Year:", label_style),
            Paragraph(report.financial_reports_academic_year or "", normal_style),
        ],
        [Paragraph("Semester:", label_style), Paragraph(report.financial_reports_semester or "", normal_style)],
        [Paragraph("Status:", label_style), Paragraph(report.financial_reports_status or "", normal_style)],
    ]

    event = db.get(Events, report.financial_reports_events_id) if report.financial_reports_events_id else None
    if event:
        details.append([Paragraph("Event:", label_style), Paragraph(event.events_name or "", normal_style)])

        dept_event = db.query(DepartmentsEvents).filter_by(events_id=event.events_id).first()
        department = db.get(Departments, dept_event.departments_id) if dept_event else None
        if department:
            details.append(
                [Paragraph("Department:", label_style), Paragraph(department.departments_name or "", normal_style)]
            )

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
    story.append(Spacer(1, 20))

    story.append(Paragraph("II. Collection and Expenses", heading_style))

    budget = _parse_budget(event.events_budget if event else 0)
    transactions = sorted(event.transactions or [], key=lambda t: t.transaction_date or 0) if event else []
    total_expenses = sum(float(t.total or 0) for t in transactions)
    remaining = budget - total_expenses

    table_data = [
        [Paragraph("Source of Fund", label_style), Paragraph("", normal_style)],
        [Paragraph("CCS Bankbook", normal_style), Paragraph(_format_currency(budget), normal_style)],
        [
            Paragraph("<b>Total Budget:</b>", right_aligned_style),
            Paragraph(f"<b>{_format_currency(budget)}</b>", normal_style),
        ],
        [Paragraph("", normal_style), Paragraph("", normal_style)],
        [Paragraph("<b>Less Expense:</b>", label_style), Paragraph("", normal_style)],
    ]

    for transaction in transactions:
        table_data.append(
            [
                Paragraph(transaction.transaction_name or "", normal_style),
                Paragraph(_format_currency(transaction.total), normal_style),
            ]
        )

    table_data.extend(
        [
            [Paragraph("", normal_style), Paragraph("", normal_style)],
            [
                Paragraph("<b>Total Expenses:</b>", right_aligned_style),
                Paragraph(f"<b>{_format_currency(total_expenses)}</b>", normal_style),
            ],
            [Paragraph("", normal_style), Paragraph("", normal_style)],
            [
                Paragraph("<b>Total Remaining Money:</b>", label_style),
                Paragraph(f"<b>{_format_currency(remaining)}</b>", normal_style),
            ],
        ]
    )

    financial_table = Table(table_data, colWidths=[4.5 * inch, 2 * inch])
    financial_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("BOX", (0, 0), (-1, -1), 1, colors.black),
                ("LINEABOVE", (0, -4), (-1, -4), 1, colors.black),
                ("LINEABOVE", (0, -1), (-1, -1), 1, colors.black),
            ]
        )
    )
    story.append(financial_table)
    story.append(Spacer(1, 30))

    story.append(Paragraph("III. Signatories", heading_style))

    auditor = (
        db.get(Users, report.financial_reports_audited_and_prepared_by)
        if report.financial_reports_audited_and_prepared_by
        else None
    )
    treasurer = db.get(Users, report.financial_reports_noted_by) if report.financial_reports_noted_by else None
    president = (
        db.get(Users, report.financial_reports_recommending_approval_by)
        if report.financial_reports_recommending_approval_by
        else None
    )
    adviser = (
        db.get(Signatories, report.financial_reports_approved_by) if report.financial_reports_approved_by else None
    )

    def _user_name(user: Users | None) -> str:
        if user is None:
            return ""
        middle = f" {user.users_middle_name}" if user.users_middle_name else ""
        return f"{user.users_first_name}{middle} {user.users_last_name}"

    def _signatory_name(signatory: Signatories | None) -> str:
        if signatory is None:
            return ""
        middle = f" {signatory.signatory_middle_name}" if signatory.signatory_middle_name else ""
        title = f"{signatory.signatory_title} " if signatory.signatory_title else ""
        return f"{title}{signatory.signatory_first_name}{middle} {signatory.signatory_last_name}"

    signatory_lines = [
        ("Audited and Prepared By:", _user_name(auditor)),
        ("Noted By:", _user_name(treasurer)),
        ("Recommending Approval By:", _user_name(president)),
        ("Approved By:", _signatory_name(adviser)),
    ]

    for label, name in signatory_lines:
        if name:
            story.append(Paragraph(f"<b>{label}</b>", label_style))
            story.append(Paragraph(name, normal_style))
            story.append(Spacer(1, 10))

    doc.build(story)
    buffer.seek(0)
    return buffer
