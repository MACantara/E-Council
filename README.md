# E-Council — Integrated Student Council Management System Powered by AI

> An AI-powered central hub for student council operations — managing events, documents, finances, and reports smarter, faster, and with less administrative overhead.

E-Council is a Flask-based web application that digitizes and centralizes the administrative work of a student council — from event planning and concept papers to post-event documentation, financial tracking, board resolutions, and meeting minutes — in a single, authenticated platform with AI-assisted drafting and one-click PDF generation.

It was designed and developed for the **Junior Philippine Computer Society (JPCS) council** and the **College of Computer Studies Student Council (CCS-SC)** at the **University of Perpetual Help System Dalta (UPHSD) — Molino Campus**.

---

## Table of Contents

- [Background of the Study](#background-of-the-study)
- [Problem Statement](#problem-statement)
- [Objectives of the Study](#objectives-of-the-study)
- [Scope and Limitations](#scope-and-limitations)
- [Significance of the Study](#significance-of-the-study)
- [System Overview](#system-overview)
- [Key Features & Modules](#key-features--modules)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup & Configuration](#setup--configuration)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [License](#license)

---

## Background of the Study

The **Junior Philippine Computer Society (JPCS)** council and the **College of Computer Studies Student Council (CCS-SC)** are the two student councils representing the students of the College of Computer Studies at the University of Perpetual Help System Dalta, Molino Campus. They are responsible for handling and organizing events for the enrichment and enjoyment of the students.

The current setup for managing such events revolves around cloud-based tools such as **Google Drive, Google Docs, Google Sheets, and Google Forms**. For communication within the student councils, **Microsoft Teams** and **Facebook Messenger** are used.

While there are strengths to utilizing these digital services — such as real-time collaboration and centralized file storage — there are notable weaknesses in the current setup:

- **No central hub** for an overview of the student council's activities, financial bank book, data analytics for event evaluation results, and other information that can aid in the council's decision-making.
- **Manual generation of documents** such as concept papers, after-documentation/activity reports, end-of-semester reports, and Society Accomplishment and Compliance (SOAC) reports. These manual processes take significant time while also being prone to human errors, leading to inefficiencies in the operations of the student councils.

To address these issues, this project proposes the development of **E-Council: an Integrated Student Council Management System Powered by AI**. The system is designed as a central hub for all of the operations of the student council. By utilizing the generative capabilities of AI, it aims to improve the operational efficiency and effectiveness of the student council while reducing the time and administrative workload for student council officers.

## Problem Statement

The manual handling of student council activities by the JPCS and CCS-SC within the College of Computer Studies at the University of Perpetual Help System Dalta, Molino Campus results in significant administrative inefficiencies and an increased potential for human errors. The current reliance on manual processes for managing events, generating reports, and maintaining records creates challenges in accuracy, timeliness, and overall effectiveness. These issues hinder the council's ability to operate efficiently and manage its responsibilities effectively.

This study aims to address these problems by developing a comprehensive, AI-powered student council management system that automates and streamlines these processes, improving efficiency and reducing administrative burdens.

## Objectives of the Study

### General Objective

To design and develop **E-Council: an Integrated Student Council Management System Powered by Artificial Intelligence** for the JPCS council and CCS-SC at the University of Perpetual Help System Dalta, Molino Campus, benefiting the student council officers, faculty, and staff.

### Specific Objectives

1. **Login Module** — secure login for student council officers, staff, and faculty.
2. **Accounts Module** — managing account details and settings for changing password and email.
3. **Password Reset Module** — secure password recovery for forgotten credentials.
4. **Council Overview Module** — a centralized dashboard providing:
   - *Event Management Overview* — a summary of ongoing, completed, and upcoming council events with their respective dates, statuses, and organizers.
   - *Financial Bank Book Tracking* — a real-time view of the council's financial transactions, including deposits, withdrawals, and current balance.
   - *Activity Completion Rate Graph* — a visual representation of completed versus planned activities for a specific period (monthly, quarterly, or annually).
   - *Event Evaluation Metrics* — a graphical summary of event evaluation results, including participant feedback, attendance, satisfaction ratings, and impact assessments.
5. **Events Management Module** — managing, creating, and updating of event details and tracking of event status.
6. **Event Management Invitation Module** — enabling users to collaborate on event management.
7. **Event Dashboard Module** — displaying key financial insights such as the top 5 expenses and income, remaining budget, transaction history, and evaluation results.
8. **Event Transaction Module** — for council officers to log event-related transactions with receipts as proof of payment.
9. **Concept Paper Module** — utilizes AI to assist in generating concept papers for council activities.
10. **Documentation Module** — enabling council officers to generate after-documentation or post-activity reports of an event.
11. **Financial Reports** — including the title of activity, date, nature of activity, time, college/department, venue, source of fund, less expense, total remaining funds, and receipts for proof of payment.
12. **Board Resolutions Module** — to generate a board resolution document with AI.

> **Note:** The implemented system also includes a **Minutes of the Meeting** module (see [Key Features & Modules](#key-features--modules)) beyond the objectives listed above.

## Scope and Limitations

### Scope

This study is confined to the development of the E-Council system powered by AI for the JPCS council and CCS-SC of the College of Computer Studies at the University of Perpetual Help System Dalta, Molino Campus. The system addresses the management needs of the student councils by automating various administrative tasks and providing tools for efficient event and document management.

### Limitations

- The study does **not** include functionalities related to **payment systems** or **merchandise management**.
- **AI capabilities are limited to text analysis and generation**, excluding images and videos.
- The system is **exclusive to the student council officers, faculty, and staff of the College of Computer Studies** at the University of Perpetual Help System Dalta, Molino Campus, and does not extend to other departments or campuses.

## Significance of the Study

- **For student council officers** — the system provides an efficient and user-friendly platform to manage their responsibilities, reducing administrative burdens and enhancing productivity.
- **For faculty and staff** — streamlined processing and improved documentation accuracy.
- **For future researchers** — the system serves as a reference and foundation for future research and development, offering a basis upon which enhancements and expansions can be built.

---

## System Overview

E-Council is a web portal built for the student councils of the College of Computer Studies at UPHSD Molino. Users sign up under a specific college department and are assigned one of four roles:

| Role | Description |
| --- | --- |
| **Student Council Officer** | Primary user — creates and manages events, documents, and reports |
| **Faculty** | Supervising/oversight role |
| **Staff** | Support role |
| **Admin** | Full administrative access |

Once authenticated, users land on the **E-Council Overview**, a dashboard that summarizes the council's activities for a selected school year, including a financial bank-book chart, an activity completion-rate chart, and an activity evaluation graph.

## Key Features & Modules

The application is organized around the modules defined in the study's specific objectives, accessible from the council overview sidebar:

### 1. Login & Authentication
- Signup with email verification (token-based, via itsdangerous)
- Login with login-attempt tracking
- Forgot-password / reset-password flows (token-based email links)

### 2. Accounts & Settings
- Account details and profile picture management (hosted on Cloudinary)
- Email-change settings with verification
- Password and security settings

### 3. Council Overview
A centralized dashboard for a selected school year, featuring:
- **Event Management Overview** — summary of ongoing, completed, and upcoming events with dates, statuses, and organizers
- **Financial Bank Book Tracking** — real-time view of the council's financial transactions (deposits, withdrawals, current balance)
- **Activity Completion Rate Graph** — completed versus planned activities
- **Event Evaluation Metrics** — graphical summary of evaluation results, feedback, attendance, and satisfaction ratings

### 4. Events Management
Full event lifecycle management:
- Create, update, and delete events with status tracking (e.g., Done, Postponed, Canceled)
- Track event status throughout its lifecycle

### 5. Event Invitations
- Email-based event invitations with accept/reject token links, enabling users to collaborate on event management

### 6. Event Dashboard
A per-event dashboard displaying key financial insights:
- Top 5 expenses and income
- Remaining budget
- Transaction history
- Evaluation results

### 7. Event Transactions
- Log event-related transactions (income/expenses) with receipts as proof of payment
- Receipts uploaded and stored via Cloudinary

### 8. Concept Papers
- Structured concept paper forms (objectives, learning outcomes, participants, consent, etc.)
- **AI-assisted generation** of the paper body, descriptions, objectives, learning outcomes, participants, and consent text via Google Gemini
- Status workflow and one-click **PDF export**

### 9. Documentation
- Post-event documentation / post-activity reports with evaluation forms and tally items
- Photo documentation (uploaded to Cloudinary)
- Excel import of student lists (via pandas/openpyxl)
- Status workflow and **PDF export**

### 10. Financial Reports
- Generate financial reports including title of activity, date, nature of activity, time, college/department, venue, source of fund, less expense, total remaining funds, and receipts for proof of payment
- Transaction history per report
- Status workflow and **PDF export**

### 11. Board Resolutions
- Structured board resolution forms with student signatories
- **AI-assisted description generation** via Google Gemini
- Status workflow and **PDF export**

### 12. Minutes of the Meeting *(beyond the stated objectives)*
- Meeting minutes with signatories and attendees
- Photo documentation (Cloudinary-hosted)
- Status workflow and **PDF export**

## Tech Stack

All dependencies are listed in [`requirements.txt`](requirements.txt). Pin or update versions there as needed.

### Backend
- **Python** — 3.9+
- **Flask** — web framework
- **Jinja2** — templating

### Database
- **MySQL** — primary datastore (database name: `e-council`)
- **Flask-SQLAlchemy** — ORM
- **Flask-Migrate** — schema migrations (Alembic)
- **PyMySQL** — MySQL driver, installed as a `MySQLdb` fallback

### Authentication & Security
- **Flask-Login** — session-based authentication
- **Werkzeug** — password hashing and WSGI utilities
- **Flask-WTF** — CSRF protection
- **itsdangerous** — signed tokens for email verification and password reset

### Email
- **Flask-Mail** — SMTP email (configured for Gmail by default)

### File Storage
- **Cloudinary** — profile pictures and photo documentation

### AI
- **google-generativeai** — Google Gemini integration (deprecated; migration to `google-genai` is tracked in `docs/ROADMAP.md`)

### PDF & Data Processing
- **ReportLab** — PDF generation
- **pandas** / **openpyxl** — Excel import of student lists

### Frontend
- **Tailwind CSS 4** — utility-first styling via CDN (`@tailwindcss/browser@4`) with custom theme in `base.html`
- **Lucide Icons** — icon set via CDN
- **Jinja2 macros** — reusable form and UI components (`templates/macros/`)
- **Chart.js** — dashboard charts
- Vanilla JavaScript (`static/js/`)

### Testing & Tooling
- **pytest** — test runner (config in `pytest.ini`)
- **python-dotenv** — environment variable loading

## Project Structure

```
E-Council/
├── app.py                 # Application factory (entry point) — creates app and registers extensions/blueprints
├── config/                # Environment-specific configuration
│   ├── __init__.py
│   └── config.py
├── docs/                  # Project documentation
│   ├── ARCHITECTURE.md
│   ├── DESIGN.md
│   ├── HAND-OVER.md
│   ├── IMPROVEMENT_ANALYSIS.md
│   ├── PROGRESS.md
│   ├── ROADMAP.md
│   └── TESTING.md
├── extensions.py          # Flask extensions (SQLAlchemy, Login, Mail, CSRF, serializer)
├── fonts/                 # Fonts used in PDF generation
├── models/                # Database models
│   ├── __init__.py
│   ├── base.py
│   ├── board_resolution.py
│   ├── concept_paper.py
│   ├── department.py
│   ├── documentation.py
│   ├── event.py
│   ├── financial.py
│   ├── meeting.py
│   └── user.py
├── pytest.ini             # pytest configuration
├── requirements.txt       # Python dependencies
├── routes/                # Flask blueprints
│   ├── __init__.py
│   ├── account.py
│   ├── auth.py
│   ├── board_resolutions.py
│   ├── concept_papers.py
│   ├── dashboard.py
│   ├── documentation.py
│   ├── events.py
│   ├── financial.py
│   └── meetings.py
├── run_tests.py           # Test runner helper
├── static/                # Static assets
│   ├── img/
│   │   ├── heroes/
│   │   └── logos/
│   ├── js/
│   │   ├── account/
│   │   ├── auth/
│   │   ├── board-resolutions/
│   │   ├── charts-theme.js
│   │   ├── concept-papers/
│   │   ├── dashboard/
│   │   ├── documentation/
│   │   ├── events/
│   │   ├── financial-reports/
│   │   ├── minutes-of-meeting/
│   │   ├── navbar.js
│   │   ├── shared/
│   │   ├── theme.js
│   │   └── utils.js
│   └── uploads/           # Local upload destination (receipts)
├── templates/             # Jinja2 HTML templates
│   ├── base.html          # Shared layout
│   ├── index.html         # Landing page
│   ├── macros/            # Reusable form and UI components
│   │   ├── email.html
│   │   ├── forms.html
│   │   ├── icons.html
│   │   └── ui.html
│   ├── account/
│   ├── auth/
│   ├── board-resolutions/
│   ├── concept-papers/
│   ├── dashboard/
│   ├── documentation/
│   ├── email/
│   ├── events/
│   ├── financial-reports/
│   └── minutes-of-meeting/
├── tests/                 # pytest tests
│   ├── conftest.py
│   ├── test_config.py
│   ├── test_routes.py
│   ├── test_signup.py
│   └── test_utils.py
├── uploads/               # Runtime upload folder (receipts)
├── .env                   # Environment variables (gitignored — see Setup)
├── .gitignore
└── LICENSE                # MIT
```

> **Note on architecture:** The application now uses a modular Flask blueprint architecture. `app.py` contains the `create_app` factory, and business logic is split into `routes/`, `models/`, `utils/`, and `config/`. Legacy `static/css/` files were removed during the Tailwind CSS 4 migration.

## Prerequisites

Before setting up the project, make sure you have the following:

1. **Python 3.9 or higher** — [python.org](https://www.python.org/downloads/)
2. **pip** — bundled with Python 3.4+
3. **MySQL server** — a running instance you can connect to (e.g., locally on `localhost`)
4. **A Cloudinary account** — for image hosting (cloud name, API key, and API secret)
5. **A Google Gemini API key** — for AI-assisted document generation
6. **An SMTP mailbox** — for email verification and notifications (the project is configured for Gmail by default; use a Gmail App Password, not your account password)

## Setup & Configuration

### 1. Clone the Repository

```bash
git clone https://github.com/MACantara/E-Council.git
cd E-Council
```

### 2. Create and Activate a Virtual Environment

```bash
python -m venv venv
```

- **Windows:**
  ```bash
  venv\Scripts\activate
  ```
- **macOS / Linux:**
  ```bash
  source venv/bin/activate
  ```

### 3. Install Dependencies

With the virtual environment activated:

```bash
pip install -r requirements.txt
```

### 4. Create the MySQL Database

Connect to your MySQL server and create the database:

```sql
CREATE DATABASE `e-council`;
```

### 5. Configure Environment Variables

Create a `.env` file in the project root (this file is gitignored) and populate it with your own credentials. The application reads the following variables:

```dotenv
# Flask
SECRET_KEY="<your-secret-key>"

# Database
SQLALCHEMY_DATABASE_URI="mysql://<user>:<password>@localhost/e-council"

# Email (SMTP — Gmail by default)
MAIL_SERVER="smtp.gmail.com"
MAIL_PORT="587"
MAIL_USE_TLS="True"
MAIL_USE_SSL="False"
MAIL_USERNAME="<your-gmail-address>"
MAIL_PASSWORD="<your-gmail-app-password>"
MAIL_DEFAULT_SENDER="<sender-email>"

# Cloudinary
CLOUDINARY_CLOUD_NAME="<your-cloud-name>"
CLOUDINARY_API_KEY="<your-api-key>"
CLOUDINARY_API_SECRET="<your-api-secret>"

# Google Gemini AI
GOOGLE_GEMINI_AI_API_KEY="<your-gemini-api-key>"
```

> **Security:** Never commit your `.env` file. It is listed in `.gitignore`. Use App Passwords for Gmail rather than your account password, and rotate any keys if they have ever been exposed.

### 6. Initialize the Database Schema

With the `.env` file in place and the virtual environment active, run the application once to create the tables:

```bash
python app.py
```

Or, if you prefer Flask-Migrate, initialize and apply migrations first:

```bash
flask db init
flask db migrate -m "Initial schema"
flask db upgrade
```

## Running the Application

Start the Flask development server:

```bash
python app.py
```

> The application entry point is the `if __name__ == "__main__":` block at the end of `app.py`. There is no separate `run.py` file.

The server runs on `http://0.0.0.0:5000` with debug mode enabled. Open your browser to:

```
http://127.0.0.1:5000/
```

## Testing

Tests are written with pytest and configured via `pytest.ini`. From the project root with the virtual environment active:

```bash
pytest
```

Test files live in the `tests/` directory:

- `tests/conftest.py` — shared fixtures and app setup
- `tests/test_config.py` — configuration tests
- `tests/test_routes.py` — route tests
- `tests/test_signup.py` — signup tests
- `tests/test_utils.py` — utility and filter tests

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
