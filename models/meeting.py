"""
Meeting and signatory models for E-Council.
"""

from models.base import db


class MinutesOfTheMeeting(db.Model):
    __tablename__ = 'minutes_of_the_meeting'

    minutes_of_the_meeting_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    minutes_of_the_meeting_date = db.Column(db.DateTime, nullable=False)
    minutes_of_the_meeting_semester = db.Column(db.String(50), nullable=False)
    minutes_of_the_meeting_academic_year = db.Column(db.String(50), nullable=False)
    minutes_of_the_meeting_status = db.Column(db.String(50), nullable=False)
    minutes_of_the_meeting_departments_id = db.Column(db.Integer, db.ForeignKey('departments.departments_id'), nullable=True)
    minutes_of_the_meeting_presiding_officer = db.Column(db.String(100), nullable=False)
    minutes_of_the_meeting_agenda = db.Column(db.Text, nullable=False)
    minutes_of_the_meeting_notes = db.Column(db.Text, nullable=True)
    minutes_of_the_meeting_adjourned = db.Column(db.DateTime, nullable=True)
    minutes_of_the_meeting_approved_by = db.Column(db.Integer, db.ForeignKey('users.users_id'), nullable=True)
    minutes_of_the_meeting_prepared_by = db.Column(db.Integer, db.ForeignKey('users.users_id'), nullable=True)
    minutes_of_the_meeting_noted_by = db.Column(db.Integer, db.ForeignKey('signatories.signatory_id'), nullable=True)

    # Relationships - using string references to avoid circular imports
    approved_by_user = db.relationship('Users', foreign_keys=[minutes_of_the_meeting_approved_by])
    prepared_by_user = db.relationship('Users', foreign_keys=[minutes_of_the_meeting_prepared_by])
    noted_by_signatory = db.relationship('Signatories', foreign_keys=[minutes_of_the_meeting_noted_by])
    department = db.relationship('Departments', foreign_keys=[minutes_of_the_meeting_departments_id])

    def __repr__(self):
        return f'<MinutesOfTheMeeting {self.minutes_of_the_meeting_id}: {self.minutes_of_the_meeting_agenda}>'


class Signatories(db.Model):
    __tablename__ = 'signatories'

    signatory_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    signatory_title = db.Column(db.String(50), nullable=False)
    signatory_first_name = db.Column(db.String(50), nullable=False)
    signatory_middle_name = db.Column(db.String(50), nullable=True)
    signatory_last_name = db.Column(db.String(50), nullable=False)
    signatory_suffix = db.Column(db.String(50), nullable=True)
    signatory_position = db.Column(db.String(100), nullable=False)
    signatory_department = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f'<Signatories {self.signatory_id}: {self.signatory_first_name} {self.signatory_last_name}>'


class MinutesOfTheMeetingPhotoDocumentation(db.Model):
    __tablename__ = 'minutes_of_the_meeting_photo_documentation'

    minutes_of_the_meeting_photo_documentation_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    minutes_of_the_meeting_id = db.Column(db.Integer, db.ForeignKey('minutes_of_the_meeting.minutes_of_the_meeting_id'), nullable=False)
    minutes_of_the_meeting_photo_documentation_cloudinary_url = db.Column(db.String(255), nullable=False)
    minutes_of_the_meeting_photo_documentation_cloudinary_public_id = db.Column(db.String(255), nullable=False)

    minutes_of_the_meeting = db.relationship('MinutesOfTheMeeting', foreign_keys=[minutes_of_the_meeting_id])

    def __repr__(self):
        return f'<MinutesOfTheMeetingPhotoDocumentation {self.minutes_of_the_meeting_photo_documentation_id}: {self.minutes_of_the_meeting_photo_documentation_url}>'


class MinutesOfTheMeetingAttendees(db.Model):
    __tablename__ = 'minutes_of_the_meeting_attendees'

    minutes_of_the_meeting_id = db.Column(db.Integer, db.ForeignKey('minutes_of_the_meeting.minutes_of_the_meeting_id'), primary_key=True, nullable=False)
    users_id = db.Column(db.Integer, db.ForeignKey('users.users_id'), primary_key=True, nullable=False)

    minutes_of_the_meeting = db.relationship('MinutesOfTheMeeting', backref='attendees')
    user = db.relationship('Users', backref='minutes_of_the_meeting_attendees')

    def __repr__(self):
        return f'<MinutesOfTheMeetingAttendees(minutes_of_the_meeting_id={self.minutes_of_the_meeting_id}, users_id={self.users_id})>'