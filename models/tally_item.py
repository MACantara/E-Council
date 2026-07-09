"""
Tally item model for documentation.

Replaces the JSON tally_items list on Documentation.
"""

from models.base import db


class TallyItem(db.Model):
    __tablename__ = "tally_items"

    tally_item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    documentation_id = db.Column(db.Integer, db.ForeignKey("documentation.documentation_id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    extremely_satisfied = db.Column(db.Integer, nullable=False, default=0)
    satisfied = db.Column(db.Integer, nullable=False, default=0)
    neutral = db.Column(db.Integer, nullable=False, default=0)
    dissatisfied = db.Column(db.Integer, nullable=False, default=0)
    extremely_dissatisfied = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f"<TallyItem {self.tally_item_id}: {self.name}>"
