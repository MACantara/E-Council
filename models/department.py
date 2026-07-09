"""
Department and Student Organization models for E-Council.
"""

from models.base import db


class Departments(db.Model):
    __tablename__ = "departments"

    departments_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    departments_name = db.Column(db.String(255), nullable=False, unique=True)

    def __repr__(self):
        return f"Departments({self.departments_id}, {self.departments_name})"


class StudentOrganizations(db.Model):
    __tablename__ = "student_organizations"

    student_organizations_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_organizations_name = db.Column(db.String(255), nullable=False)
    student_organizations_financial_bank_book_amount = db.Column(db.Numeric(20, 2), nullable=True)

    def __repr__(self):
        return f"<StudentOrganizations(id={self.student_organizations_id}, name={self.student_organizations_name})>"
