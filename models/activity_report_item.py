"""
Activity report item model.

Replaces the JSON strength / weakness / recommendation lists on
ActivityReportForms and Documentation.
"""

from models.base import db


class ActivityReportItem(db.Model):
    __tablename__ = "activity_report_items"

    activity_report_item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    activity_report_forms_id = db.Column(
        db.Integer,
        db.ForeignKey("activity_report_forms.activity_report_forms_id"),
        nullable=True,
        index=True,
    )
    documentation_id = db.Column(
        db.Integer,
        db.ForeignKey("documentation.documentation_id"),
        nullable=True,
        index=True,
    )
    item_type = db.Column(db.String(50), nullable=False, index=True)
    item_text = db.Column(db.Text, nullable=False)

    def __str__(self):
        return str(self.item_text)

    def __repr__(self):
        return f"<ActivityReportItem {self.activity_report_item_id}: {self.item_type}>"
