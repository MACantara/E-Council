"""
Financial reports model for E-Council.
"""

from models.base import db


class FinancialReports(db.Model):
    __tablename__ = "financial_reports"

    financial_reports_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    financial_reports_date = db.Column(db.DateTime, nullable=False, index=True)
    financial_reports_academic_year = db.Column(db.String(50), nullable=False, index=True)
    financial_reports_semester = db.Column(db.String(50), nullable=False, index=True)
    financial_reports_status = db.Column(db.String(50), nullable=False, index=True)
    financial_reports_events_id = db.Column(db.Integer, db.ForeignKey("events.events_id"), nullable=True, index=True)
    financial_reports_departments_id = db.Column(
        db.Integer, db.ForeignKey("departments.departments_id"), nullable=True, index=True
    )
    financial_reports_title = db.Column(db.String(255), nullable=False)
    financial_reports_audited_and_prepared_by = db.Column(
        db.Integer, db.ForeignKey("users.users_id"), nullable=True, index=True
    )
    financial_reports_noted_by = db.Column(
        db.Integer, db.ForeignKey("signatories.signatory_id"), nullable=True, index=True
    )
    financial_reports_recommending_approval_by = db.Column(
        db.Integer, db.ForeignKey("signatories.signatory_id"), nullable=True, index=True
    )
    financial_reports_approved_by = db.Column(
        db.Integer, db.ForeignKey("signatories.signatory_id"), nullable=True, index=True
    )

    # Relationships - using string references to avoid circular imports
    events = db.relationship("Events", back_populates="financial_reports")
    prepared_by_user = db.relationship("Users", foreign_keys=[financial_reports_audited_and_prepared_by])
    noted_by_signatory = db.relationship("Signatories", foreign_keys=[financial_reports_noted_by])
    recommending_signatory = db.relationship("Signatories", foreign_keys=[financial_reports_recommending_approval_by])
    approved_by_signatory = db.relationship("Signatories", foreign_keys=[financial_reports_approved_by])
    department = db.relationship("Departments", foreign_keys=[financial_reports_departments_id])

    def __repr__(self):
        return f"<FinancialReports {self.financial_reports_id}: {self.financial_reports_title}>"
