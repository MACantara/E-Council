"""
Documentation and evaluation models for E-Council.
"""

from models.base import db

# Note: These models have complex relationships with other models
# Using string references to avoid circular imports


class Documentation(db.Model):
    __tablename__ = "documentation"

    documentation_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    documentation_events_id = db.Column(db.Integer, db.ForeignKey("events.events_id"), nullable=True)
    documentation_academic_year = db.Column(db.String(50), nullable=True)
    documentation_semester = db.Column(db.String(50), nullable=True)
    documentation_status = db.Column(db.String(50), nullable=True)
    documentation_departments_id = db.Column(db.Integer, db.ForeignKey("departments.departments_id"), nullable=True)
    documentation_type = db.Column(db.String(50), nullable=True)
    documentation_activity_report_forms_id = db.Column(
        db.Integer, db.ForeignKey("activity_report_forms.activity_report_forms_id"), nullable=True
    )
    documentation_prepared_by = db.Column(db.Integer, db.ForeignKey("users.users_id"), nullable=True)
    documentation_learning_journal_forms_id = db.Column(
        db.Integer, db.ForeignKey("learning_journal_forms.learning_journal_forms_id"), nullable=True
    )
    documentation_checked_by = db.Column(db.Integer, db.ForeignKey("signatories.signatory_id"), nullable=True)
    documentation_noted_by = db.Column(db.Integer, db.ForeignKey("signatories.signatory_id"), nullable=True)
    documentation_date_of_submission = db.Column(db.DateTime, nullable=True)
    documentation_rating = db.Column(db.Float, nullable=True)
    documentation_comments_suggestions = db.Column(db.Text, nullable=True)
    tally_items = db.Column(db.JSON, nullable=False, default=list)
    evaluation_images = db.Column(db.JSON, nullable=False, default=list)
    evaluation_forms = db.Column(db.JSON, nullable=False, default=list)
    attendance_images = db.Column(db.JSON, nullable=False, default=list)
    evaluation_student_names = db.Column(db.JSON, nullable=False, default=list)
    event_photo_images = db.Column(db.JSON, nullable=False, default=list)
    activity_strengths = db.Column(db.JSON, nullable=False, default=list)
    activity_weaknesses = db.Column(db.JSON, nullable=False, default=list)
    activity_recommendations = db.Column(db.JSON, nullable=False, default=list)

    # Relationships - using string references to avoid circular imports
    events = db.relationship("Events", back_populates="documentation")
    prepared_by_user = db.relationship("Users", foreign_keys=[documentation_prepared_by])
    checked_by_signatory = db.relationship("Signatories", foreign_keys=[documentation_checked_by])
    noted_by_signatory = db.relationship("Signatories", foreign_keys=[documentation_noted_by])
    department = db.relationship("Departments", foreign_keys=[documentation_departments_id])

    def __repr__(self):
        return f"<Documentation {self.documentation_id}: {self.documentation_type}>"
