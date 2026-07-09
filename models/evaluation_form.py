"""
Evaluation form model for documentation.

Replaces the JSON evaluation_forms list on Documentation.
"""

from models.base import db


class EvaluationForm(db.Model):
    __tablename__ = "evaluation_forms"

    evaluation_form_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    documentation_id = db.Column(db.Integer, db.ForeignKey("documentation.documentation_id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    rating = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f"<EvaluationForm {self.evaluation_form_id}: {self.name}>"
