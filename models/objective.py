"""
Objective model for concept papers.

Replaces the JSON list of objectives on ConceptPaperForms.
"""

from models.base import db


class Objective(db.Model):
    __tablename__ = "objectives"

    objective_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    concept_paper_forms_id = db.Column(
        db.Integer, db.ForeignKey("concept_paper_forms.concept_paper_forms_id"), nullable=False
    )
    objective_text = db.Column(db.Text, nullable=False)

    def __str__(self):
        return str(self.objective_text)

    def __repr__(self):
        return f"<Objective {self.objective_id}: {self.objective_text}>"
