"""
Transaction model for events.

Replaces the JSON transactions list on Events.
"""

from models.base import db


class Transaction(db.Model):
    __tablename__ = "transactions"

    transaction_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    events_id = db.Column(db.Integer, db.ForeignKey("events.events_id"), nullable=False)
    transaction_name = db.Column(db.String(255), nullable=True)
    transaction_date = db.Column(db.DateTime, nullable=True)
    unit_amount = db.Column(db.Integer, nullable=True, default=0)
    unit_price = db.Column(db.Numeric(10, 2), nullable=True, default=0)
    total = db.Column(db.Numeric(10, 2), nullable=True, default=0)
    category = db.Column(db.String(255), nullable=True)
    type = db.Column(db.String(50), nullable=True)
    receipt_url = db.Column(db.String(255), nullable=True)
    receipt_public_id = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<Transaction {self.transaction_id}: {self.transaction_name}>"
