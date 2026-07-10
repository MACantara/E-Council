"""Seed sample financial reports."""

from __future__ import annotations

from models import FinancialReports
from seeds import data
from seeds.core import get_or_create
from seeds.factories import FinancialReportsFactory


def seed(department_map: dict, user_map: dict, signatories: list, events: list) -> list:
    """Create sample financial reports and return the list of instances."""
    department = department_map["College of Computer Studies"]
    officer = user_map["officer"]
    noted_by = signatories[0]
    recommending = signatories[1]
    approved_by = signatories[0]

    reports = []

    for report in data.SAMPLE_FINANCIAL_REPORTS:
        event = events[report["event_index"]]

        instance, _ = get_or_create(
            FinancialReports,
            financial_reports_title=report["title"],
            financial_reports_academic_year=data.SAMPLE_ACADEMIC_YEAR,
            financial_reports_semester=data.SAMPLE_SEMESTER,
            defaults={
                "financial_reports_date": event.events_start_date_and_time,
                "financial_reports_status": report["status"],
                "events": event,
                "department": department,
                "prepared_by_user": officer,
                "noted_by_signatory": noted_by,
                "recommending_signatory": recommending,
                "approved_by_signatory": approved_by,
            },
            factory=FinancialReportsFactory,
        )
        reports.append(instance)

    return reports
