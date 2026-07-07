# E-Council — AI-Powered Student Council Management

> Experience the future of student council leadership with AI-driven insights that make managing events, resources, and student engagement smarter, faster, and better.

E-Council is a Flask-based web application that digitizes and centralizes the administrative work of a student council — from event planning and concept papers to post-event documentation, financial tracking, board resolutions, and meeting minutes — in a single, authenticated platform with AI-assisted drafting and one-click PDF generation.

---

## Table of Contents

- [Overview](#overview)
- [The Problem It Solves](#the-problem-it-solves)
- [Key Features & Modules](#key-features--modules)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup & Configuration](#setup--configuration)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [License](#license)

---

## Overview

E-Council is a web portal built for the student councils of a multi-college institution. It supports the colleges commonly found in the partner school — College of Computer Studies, Engineering, Architecture, Criminology, Nursing, Arts/Sciences/Education, Business Administration & Accountancy, Physical & Occupational Therapy, and International Tourism & Hospitality Management.

Users sign up under a specific college department and are assigned one of four roles:

| Role | Description |
| --- | --- |
| **Student Council Officer** | Primary user — creates and manages events, documents, and reports |
| **Faculty** | Supervising/oversight role |
| **Staff** | Support role |
| **Admin** | Full administrative access |

Once authenticated, users land on the **E-Council Overview**, a dashboard that summarizes the council's activities for a selected school year, including a financial bank-book chart, an activity completion-rate chart, and an activity evaluation graph.

## The Problem It Solves

Student council operations are traditionally paper-based and fragmented across disconnected tools — word processors for concept papers, spreadsheets for finances, separate files for meeting minutes, and manual photo documentation. This creates several pain points:

- **Scattered records** — events, papers, and reports live in different places, making it hard to track what is pending, approved, or completed.
- **Repetitive paperwork** — concept papers, board resolutions, and post-event documentation require drafting large amounts of formal text from scratch each time.
- **Manual financial tracking** — income and expenses are tracked by hand with no consolidated ledger per event.
- **No audit trail** — document status (draft, pending, approved, rejected) and signatories are difficult to verify.
- **Slow PDF generation** — formal documents must be manually formatted and exported for submission.

E-Council addresses these by providing a single platform where every council document type has a structured form, a status workflow, AI-assisted text generation for the most writing-heavy documents, and built-in PDF export.

## Key Features & Modules

The application is organized around seven core modules, accessible from the council overview sidebar:

### 1. E-Council Overview
A dashboard summarizing the council's activities for a selected school year, with charts for the financial bank book, activity completion rate, and activity evaluation.

### 2. Events
Full event lifecycle management:
- Create, update, and delete events with status tracking (e.g., Done, Postponed, Canceled)
- Per-event transaction history (income/expense tracking)
- Email-based event invitations with accept/reject token links
- Event dashboard aggregating an event's related documents

### 3. Concept Papers
- Structured concept paper forms (objectives, learning outcomes, participants, consent, etc.)
- **AI-assisted generation** of the paper body, descriptions, objectives, learning outcomes, participants, and consent text via Google Gemini
- Status workflow and one-click **PDF export**

### 4. Documentation
- Post-event documentation with evaluation forms and tally items
- Photo documentation (uploaded to Cloudinary)
- Excel import of student lists (via pandas/openpyxl)
- Status workflow and **PDF export**

### 5. Financial Reports
- Create, update, and delete financial reports linked to events
- Transaction history per report
- Status workflow and **PDF export**

### 6. Board Resolutions
- Structured board resolution forms with student signatories
- **AI-assisted description generation** via Google Gemini
- Status workflow and **PDF export**

### 7. Minutes of the Meeting
- Meeting minutes with signatories and attendees
- Photo documentation (Cloudinary-hosted)
- Status workflow and **PDF export**

### Accounts & Authentication
- Signup with email verification (token-based, via itsdangerous)
- Login with login-attempt tracking
- Forgot-password / reset-password flows (token-based email links)
- Account settings, email-change settings, and password/security settings
- Profile picture upload (hosted on Cloudinary)

## Tech Stack

All versions are pinned in [`requirements.txt`](requirements.txt).

### Backend
- **Python** (3.9+ recommended)
- **Flask** 3.0.3 — web framework
- **Jinja2** 3.1.4 — templating

### Database
- **MySQL** — primary datastore (database name: `e-council`)
- **Flask-SQLAlchemy** 3.1.1 — ORM
- **Flask-Migrate** 4.0.7 / **Alembic** 1.13.2 — schema migrations
- **mysqlclient** 2.2.4 / **PyMySQL** 1.1.1 — MySQL drivers

### Authentication & Security
- **Flask-Login** 0.6.3 — session-based auth
- **Flask-Bcrypt** 1.0.1 / **bcrypt** 4.2.0 — password hashing
- **Flask-WTF** 1.2.2 — CSRF protection
- **Werkzeug** 3.0.4 — password hashing utilities
- **itsdangerous** — signed tokens for email verification & password reset

### Email
- **Flask-Mail** 0.10.0 — SMTP email (configured for Gmail by default)

### File Storage
- **Cloudinary** 1.41.0 — profile pictures and photo documentation

### AI
- **google-generativeai** 0.8.3 — Google Gemini 1.5 Flash, used for AI-assisted drafting of concept paper sections and board resolution descriptions

### PDF & Data Processing
- **ReportLab** 4.2.5 — primary PDF generation engine
- **WeasyPrint** 60.2 / **pdfkit** 1.0.0 — supplementary PDF tooling
- **pandas** 2.2.3 / **openpyxl** 3.1.5 — Excel import of student lists

### Frontend
- Custom CSS (`static/css/styles.css`)
- **Bootstrap Icons** 1.8.1
- **Chart.js** — dashboard charts
- Vanilla JavaScript (`static/js/`)

### Testing & Tooling
- **pytest** 8.3.3 — test runner (config in `pytest.ini`)
- **python-dotenv** 1.0.1 — environment variable loading

## Project Structure

```
E-Council/
├── app.py                 # Flask application (monolith): ~40 SQLAlchemy models, ~80 routes
├── requirements.txt       # Pinned Python dependencies
├── pytest.ini             # pytest configuration
├── .env                   # Environment variables (gitignored — see Setup)
├── .gitignore
├── LICENSE                # MIT
├── templates/             # Jinja2 HTML templates
│   ├── base.html          # Shared layout (header, nav, CSRF meta)
│   ├── index.html         # Landing page
│   ├── signup.html, login.html, forgot-password.html, reset-password.html
│   ├── account.html, account-settings.html, email-settings.html, password-security-settings.html
│   ├── council-overview.html, council-overview-sidebar.html
│   ├── events-overview.html, add-event.html, update-event.html, event-dashboard.html
│   ├── concept-papers-overview.html, add-concept-paper.html, update-concept-paper.html
│   ├── documentation-overview.html, add-documentation.html, update-documentation.html
│   ├── financial-reports-overview.html, add-financial-report.html, update-financial-report.html
│   ├── board-resolutions-overview.html, add-board-resolution.html, update-board-resolution.html
│   ├── minutes-of-the-meeting-overview.html, add-minutes-of-the-meeting.html, update-minutes-of-the-meeting.html
│   └── ... (delete-*.html confirmation templates)
├── static/
│   ├── css/styles.css     # Application styles
│   ├── js/                # Per-page vanilla JS (account, add-concept-paper, add-documentation, etc.)
│   ├── img/               # Logos and hero images
│   └── uploads/           # Local upload destination (receipts)
├── tests/
│   ├── test_routes.py     # Route tests
│   └── test_signup.py     # Signup tests
├── uploads/               # Runtime upload folder (receipts)
└── fonts/                 # Fonts used in PDF generation
```

> **Note on architecture:** The Flask application currently lives in a single `app.py` file (~8,700 lines) containing all models, routes, email helpers, AI-generation endpoints, and PDF-generation logic. Templates and static assets are split out into their respective directories.

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

With the `.env` file in place and the virtual environment active, apply the database migrations:

```bash
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

- `tests/test_routes.py` — route tests
- `tests/test_signup.py` — signup tests

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
