"""
Learning outcome model for concept papers.

Replaces the JSON list of learning outcomes on ConceptPaperForms.
"""

from models.base import db


class LearningOutcome(db.Model):
    __tablename__ = "learning_outcomes"

    learning_outcome_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    concept_paper_forms_id = db.Column(
        db.Integer, db.ForeignKey("concept_paper_forms.concept_paper_forms_id"), nullable=False
    )
    learning_outcome_text = db.Column(db.Text, nullable=False)

    def __str__(self):
        return str(self.learning_outcome_text)

    def __repr__(self):
        return f"<LearningOutcome {self.learning_outcome_id}: {self.learning_outcome_text}>"
