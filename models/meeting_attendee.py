"""
Meeting attendee model.

Replaces the JSON attendees list on MinutesOfTheMeeting.
"""

from models.base import db


class MeetingAttendee(db.Model):
    __tablename__ = "meeting_attendees"

    meeting_attendee_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    minutes_of_the_meeting_id = db.Column(
        db.Integer, db.ForeignKey("minutes_of_the_meeting.minutes_of_the_meeting_id"), nullable=False, index=True
    )
    users_id = db.Column(db.Integer, db.ForeignKey("users.users_id"), nullable=False, index=True)
    attended = db.Column(db.Boolean, nullable=True, default=None)

    user = db.relationship("Users", backref="meeting_attendees")

    def __repr__(self):
        return f"<MeetingAttendee {self.meeting_attendee_id}: user {self.users_id}>"
