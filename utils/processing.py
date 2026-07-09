"""
Data processing functions for E-Council.
"""

from typing import Any


def process_tally_items(
    documentation_id: int,
    tally_names: list[str],
    extremely_satisfied: list[str],
    satisfied: list[str],
    neutral: list[str],
    dissatisfied: list[str],
    extremely_dissatisfied: list[str],
) -> None:
    """
    Process and save tally items for documentation.

    Args:
        documentation_id: ID of the documentation
        tally_names: List of tally item names
        extremely_satisfied: List of extremely satisfied counts
        satisfied: List of satisfied counts
        neutral: List of neutral counts
        dissatisfied: List of dissatisfied counts
        extremely_dissatisfied: List of extremely dissatisfied counts
    """
    from app import TallyItems, db

    # First, delete all existing tally items
    TallyItems.query.filter_by(tally_items_documentation_id=documentation_id).delete()

    # Add new tally items
    for i in range(len(tally_names)):
        new_tally = TallyItems(
            tally_items_documentation_id=documentation_id,
            tally_items_name=tally_names[i],
            tally_items_extremely_satisfied=extremely_satisfied[i],
            tally_items_satisfied=satisfied[i],
            tally_items_neutral=neutral[i],
            tally_items_dissatisfied=dissatisfied[i],
            tally_items_extremely_dissatisfied=extremely_dissatisfied[i],
        )
        db.session.add(new_tally)

    db.session.commit()


def process_evaluation_forms(documentation_id: int, tally_names: list[str], request: Any) -> None:
    """
    Process and save evaluation forms for documentation.

    Args:
        documentation_id: ID of the documentation
        tally_names: List of tally item names
        request: Flask request object containing form data
    """
    from app import EvaluationForm, db

    # First, delete all existing evaluation forms
    EvaluationForm.query.filter_by(evaluation_form_documentation_id=documentation_id).delete()

    # Process each tally item's evaluation forms
    for i, tally_name in enumerate(tally_names):
        # Get the number of evaluation forms for this tally item
        num_forms = int(request.form.get(f"num-forms-{i}", 0))

        # Process each evaluation form
        for j in range(num_forms):
            student_name = request.form.get(f"student-name-{i}-{j}", "")
            student_program = request.form.get(f"student-program-{i}-{j}", "")
            student_year = request.form.get(f"student-year-{i}-{j}", "")
            comments = request.form.get(f"comments-{i}-{j}", "")

            new_evaluation = EvaluationForm(
                evaluation_form_documentation_id=documentation_id,
                evaluation_form_tally_item_name=tally_name,
                evaluation_form_student_name=student_name,
                evaluation_form_student_program=student_program,
                evaluation_form_student_year=student_year,
                evaluation_form_comments=comments,
            )
            db.session.add(new_evaluation)

    db.session.commit()
