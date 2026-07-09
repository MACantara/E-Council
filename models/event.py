"""
Event and event-related models for E-Council.
"""

from models.base import db


class Events(db.Model):
    __tablename__ = "events"

    events_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    events_concept_paper_forms_id = db.Column(
        db.Integer, db.ForeignKey("concept_paper_forms.concept_paper_forms_id"), nullable=True
    )
    events_name = db.Column(db.String(255), nullable=True)
    events_semester = db.Column(db.String(50), nullable=False)
    events_academic_year = db.Column(db.String(50), nullable=False)
    events_start_date_and_time = db.Column(db.DateTime, nullable=True)
    events_end_date_and_time = db.Column(db.DateTime, nullable=True)
    events_venue = db.Column(db.String(255), nullable=True)
    events_budget = db.Column(db.String(255), nullable=True)
    events_status = db.Column(db.String(50), nullable=True)
    events_description = db.Column(db.Text, nullable=True)
    events_remarks = db.Column(db.String(255), nullable=True)

    # Relationships to related models
    board_resolutions = db.relationship("BoardResolutions", back_populates="events")
    documentation = db.relationship("Documentation", back_populates="events")
    financial_reports = db.relationship("FinancialReports", back_populates="events")
    transactions = db.relationship("Transaction", backref="event", cascade="all, delete-orphan")

    def __repr__(self):
        return f"Events({self.events_id}, {self.events_name}, {self.events_semester}, {self.events_academic_year}, {self.events_start_date_and_time}, {self.events_end_date_and_time}, {self.events_venue}, {self.events_budget}, {self.events_status}, {self.events_description}, {self.events_remarks}, {self.events_concept_paper_forms_id})"


class DepartmentsEvents(db.Model):
    __tablename__ = "departments_events"

    # Composite primary key: departments_id and events_id
    departments_id = db.Column(
        db.Integer, db.ForeignKey("departments.departments_id"), primary_key=True, nullable=False
    )
    events_id = db.Column(db.Integer, db.ForeignKey("events.events_id"), primary_key=True, nullable=False)

    # Relationship to Departments and Events models
    department = db.relationship("Departments", backref="departments_events")
    event = db.relationship("Events", backref="departments_events")

    def __repr__(self):
        return f"DepartmentsEvents({self.departments_id}, {self.events_id})"


class EventInvitations(db.Model):
    __tablename__ = "event_invitations"

    event_invitations_id = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    event_invitations_events_id = db.Column(db.Integer, db.ForeignKey("events.events_id"), nullable=False)
    event_invitations_email = db.Column(db.String(255), nullable=False)
    event_invitations_token = db.Column(db.String(64), nullable=False)
    event_invitations_created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)

    # Relationship to Events model
    event = db.relationship("Events", backref="event_invitations")

    def __repr__(self):
        return f"EventInvitations({self.event_invitations_id}, {self.event_invitations_events_id}, {self.event_invitations_email}, {self.event_invitations_token}, {self.event_invitations_created_at})"
