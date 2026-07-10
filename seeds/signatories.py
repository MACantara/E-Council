"""Seed signatory records used by concept papers, meetings, and reports."""

from __future__ import annotations

from models import Signatories

from seeds import data
from seeds.core import get_or_create


def seed() -> list:
    """Create sample signatories and return the list of instances."""
    signatories = []

    for sig in data.SAMPLE_SIGNATORIES:
        instance, _ = get_or_create(
            Signatories,
            signatory_first_name=sig["first_name"],
            signatory_last_name=sig["last_name"],
            signatory_position=sig["position"],
            signatory_department=sig["department"],
            defaults={
                "signatory_title": sig["title"],
                "signatory_suffix": "",
            },
        )
        signatories.append(instance)

    return signatories
