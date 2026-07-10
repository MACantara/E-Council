"""Seed sample concept papers with objectives and learning outcomes."""

from __future__ import annotations

from models import ConceptPaperForms, LearningOutcome, Objective
from seeds import data
from seeds.core import get_or_create
from seeds.factories import ConceptPaperFormsFactory


def seed(department_map: dict, user_map: dict) -> list:
    """Create sample concept papers and return the list of instances."""
    department = department_map["College of Computer Studies"]
    officer = user_map["officer"]

    concept_papers = []

    for paper in data.SAMPLE_CONCEPT_PAPERS:
        concept_paper, created = get_or_create(
            ConceptPaperForms,
            concept_paper_forms_subject=paper["subject"],
            concept_paper_forms_academic_year=data.SAMPLE_ACADEMIC_YEAR,
            concept_paper_forms_semester=data.SAMPLE_SEMESTER,
            department=department,
            prepared_by_user=officer,
            defaults={
                "concept_paper_forms_body": paper["body"],
                "concept_paper_forms_location": paper["location"],
                "concept_paper_forms_participants": paper["participants"],
                "concept_paper_forms_budget": paper["budget"],
                "concept_paper_forms_expected_number_of_participants": paper["expected"],
                "concept_paper_forms_date": paper["date"],
                "concept_paper_forms_event_start_date_and_time": paper["start"],
                "concept_paper_forms_event_end_date_and_time": paper["end"],
                "concept_paper_forms_status": paper["status"],
            },
            factory=ConceptPaperFormsFactory,
        )

        if created:
            for objective_text in paper["objectives"]:
                get_or_create(
                    Objective,
                    concept_paper_forms_id=concept_paper.concept_paper_forms_id,
                    objective_text=objective_text,
                )
            for learning_text in paper["learnings"]:
                get_or_create(
                    LearningOutcome,
                    concept_paper_forms_id=concept_paper.concept_paper_forms_id,
                    learning_outcome_text=learning_text,
                )

        concept_papers.append(concept_paper)

    return concept_papers
