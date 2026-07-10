"""Seed departments and student organizations."""

from __future__ import annotations

from models import Departments, StudentOrganizations
from seeds import data
from seeds.core import get_or_create


def seed() -> dict:
    """Create sample departments and organizations.

    Returns a mapping of department name to department instance.
    """
    department_map = {}

    for name in data.SAMPLE_DEPARTMENTS:
        department, _ = get_or_create(
            Departments,
            departments_name=name,
        )
        department_map[name] = department

    for org in data.SAMPLE_ORGANIZATIONS:
        get_or_create(
            StudentOrganizations,
            student_organizations_name=org["name"],
            defaults={"student_organizations_financial_bank_book_amount": org["bank"]},
        )

    return department_map
