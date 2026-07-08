"""
Board resolution models for E-Council.
"""

from datetime import datetime
from models.base import db


class BoardResolutions(db.Model):
    __tablename__ = 'board_resolutions'

    board_resolutions_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    board_resolutions_date = db.Column(db.DateTime, default=datetime.utcnow)
    board_resolutions_events_id = db.Column(db.Integer, db.ForeignKey('events.events_id'), nullable=True)
    board_resolutions_departments_id = db.Column(db.Integer, db.ForeignKey('departments.departments_id'), nullable=True)
    board_resolutions_title = db.Column(db.String(255), nullable=True)
    board_resolutions_academic_year = db.Column(db.String(50), nullable=True)
    board_resolutions_semester = db.Column(db.String(50), nullable=True)
    board_resolutions_status = db.Column(db.String(50), nullable=True)
    board_resolutions_total_amount = db.Column(db.Numeric(20, 2), nullable=True)
    board_resolutions_description = db.Column(db.Text, nullable=True)
    board_resolutions_prepared_by = db.Column(db.Integer, db.ForeignKey('users.users_id'), nullable=True)
    board_resolutions_approved_by = db.Column(db.Integer, db.ForeignKey('signatories.signatory_id'), nullable=True)
    student_signatory_ids = db.Column(db.JSON, nullable=False, default=list)

    # Relationships - using string references to avoid circular imports
    events = db.relationship('Events', back_populates='board_resolutions')
    prepared_by_user = db.relationship('Users', foreign_keys=[board_resolutions_prepared_by])
    approved_by_signatory = db.relationship('Signatories', foreign_keys=[board_resolutions_approved_by])
    department = db.relationship('Departments', foreign_keys=[board_resolutions_departments_id])

    def __repr__(self):
        return f'<BoardResolution {self.board_resolutions_id}: {self.board_resolutions_description}>'
