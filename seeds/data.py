"""Static sample data used by the seed scripts."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

DEMO_PASSWORD = "DemoPass123!"

SAMPLE_DEPARTMENTS = [
    "College of Computer Studies",
    "Department of Information Technology",
    "Department of Computer Science",
    "Student Affairs Office",
    "Finance Office",
]

SAMPLE_ORGANIZATIONS = [
    {
        "name": "Junior Philippine Computer Society",
        "bank": Decimal("50000.00"),
    },
    {
        "name": "College of Computer Studies Student Council",
        "bank": Decimal("75000.00"),
    },
]

SAMPLE_USERS = [
    {
        "first_name": "Admin",
        "last_name": "User",
        "username": "admin",
        "email": "admin@example.com",
        "role": "Admin",
        "department": "College of Computer Studies",
    },
    {
        "first_name": "Maria",
        "last_name": "Santos",
        "username": "officer",
        "email": "officer@example.com",
        "role": "Student Council Officer",
        "department": "College of Computer Studies",
    },
    {
        "first_name": "Juan",
        "last_name": "Dela Cruz",
        "username": "faculty",
        "email": "faculty@example.com",
        "role": "Faculty",
        "department": "College of Computer Studies",
    },
    {
        "first_name": "Carlos",
        "last_name": "Reyes",
        "username": "staff",
        "email": "staff@example.com",
        "role": "Staff",
        "department": "College of Computer Studies",
    },
]

SAMPLE_SIGNATORIES = [
    {
        "title": "Dr.",
        "first_name": "Juan",
        "last_name": "Dela Cruz",
        "position": "Dean",
        "department": "College of Computer Studies",
    },
    {
        "title": "Prof.",
        "first_name": "Maria",
        "last_name": "Santos",
        "position": "Adviser",
        "department": "Department of Information Technology",
    },
    {
        "title": "Mr.",
        "first_name": "John",
        "last_name": "Doe",
        "position": "President",
        "department": "College of Computer Studies Student Council",
    },
]

SAMPLE_ACADEMIC_YEAR = "2024-2025"
SAMPLE_SEMESTER = "1st Semester"

SAMPLE_CONCEPT_PAPERS = [
    {
        "subject": "AI-Powered Campus Orientation",
        "body": "A campus-wide orientation on the responsible use of AI tools for learning.",
        "location": "University Auditorium",
        "participants": "All CCS students",
        "budget": "15000",
        "expected": "200",
        "date": date(2024, 9, 1),
        "start": datetime(2024, 9, 15, 9, 0),
        "end": datetime(2024, 9, 15, 12, 0),
        "status": "Upcoming",
        "objectives": [
            "Introduce AI tools to students",
            "Promote responsible use of generative AI",
            "Encourage participation in council activities",
        ],
        "learnings": [
            "Understand basic AI concepts",
            "Identify practical AI tools for learning",
        ],
    },
    {
        "subject": "Fundraising Workshop",
        "body": "A hands-on workshop to teach councils how to plan and execute fundraising activities.",
        "location": "IT Building Room 101",
        "participants": "Student council officers",
        "budget": "8000",
        "expected": "50",
        "date": date(2024, 9, 10),
        "start": datetime(2024, 10, 5, 13, 0),
        "end": datetime(2024, 10, 5, 17, 0),
        "status": "Upcoming",
        "objectives": [
            "Teach fundraising strategies",
            "Build team coordination",
            "Raise initial capital for events",
        ],
        "learnings": [
            "Plan a fundraising event",
            "Track income and expenses",
        ],
    },
]

SAMPLE_EVENTS = [
    {
        "name": "AI-Powered Campus Orientation",
        "status": "Upcoming",
        "venue": "University Auditorium",
        "budget": "15000",
        "description": "Orientation on AI tools for CCS students.",
        "remarks": "Tentative date; subject to final approval.",
        "start": datetime(2024, 9, 15, 9, 0),
        "end": datetime(2024, 9, 15, 12, 0),
        "concept_paper_index": 0,
    },
    {
        "name": "Fundraising Workshop",
        "status": "Done",
        "venue": "IT Building Room 101",
        "budget": "8000",
        "description": "Workshop for student council fundraising.",
        "remarks": "Completed successfully.",
        "start": datetime(2024, 10, 5, 13, 0),
        "end": datetime(2024, 10, 5, 17, 0),
        "concept_paper_index": 1,
    },
]

SAMPLE_MEETINGS = [
    {
        "agenda": "Planning for AI-Powered Campus Orientation",
        "status": "Done",
        "presiding_officer": "Dr. Juan Dela Cruz",
        "notes": "Discussed logistics, budget, and target participants.",
        "adjourned": datetime(2024, 9, 5, 11, 0),
        "date": datetime(2024, 9, 5, 9, 0),
    },
]

SAMPLE_FINANCIAL_REPORTS = [
    {
        "title": "AI-Powered Campus Orientation Budget",
        "status": "Pending",
        "amount": Decimal("15000.00"),
        "event_index": 0,
    },
]

SAMPLE_BOARD_RESOLUTIONS = [
    {
        "title": "Resolution Approving AI-Powered Campus Orientation",
        "status": "Approved",
        "amount": Decimal("15000.00"),
        "description": "The board resolves to approve the AI-Powered Campus Orientation event.",
        "event_index": 0,
    },
]

SAMPLE_DOCUMENTATION = [
    {
        "type": "Activity Report",
        "status": "Done",
        "rating": 4.8,
        "comments": "Well-attended and highly informative.",
        "event_index": 1,
    },
]
