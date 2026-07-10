# E-Council — Integrated Student Council Management System Powered by AI

![CI](https://github.com/MACantara/E-Council/actions/workflows/ci.yml/badge.svg)

> An AI-powered central hub for student council operations — managing events, documents, finances, and reports smarter, faster, and with less administrative overhead.

E-Council is a Flask-based web application with a FastAPI backend that digitizes and centralizes the administrative work of a student council — from event planning and concept papers to post-event documentation, financial tracking, board resolutions, and meeting minutes — in a single, authenticated platform with AI-assisted drafting and one-click PDF generation.

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
- **Flask** — server-rendered web framework and UI
- **FastAPI** — REST API backend (`api/`) with automatic OpenAPI docs, JWT auth, and Pydantic validation
- **Uvicorn** — ASGI server for the FastAPI application
- **Jinja2** — templating

### Database
- **SQLite / MySQL / PostgreSQL** — any SQLAlchemy-compatible engine (configurable via `SQLALCHEMY_DATABASE_URI` or `DATABASE_URL`)
- **Flask-SQLAlchemy** — ORM
- **Flask-Migrate** — schema migrations (Alembic)
- **Repository pattern** — `repositories/` is the only layer that touches `db.session`; routes and services use `repo` and `get_repository()`

### Authentication & Security
- **Flask-Login** — session-based authentication
- **Werkzeug** — password hashing and WSGI utilities
- **Flask-WTF** — CSRF protection
- **itsdangerous** — signed tokens for email verification and password reset

### Email
- **Email abstraction layer** (`services/email/`) — provider-agnostic email delivery
  - Supports `smtp`, `console`, `memory`, `sendgrid`, `mailgun`, and `null` providers via the `EMAIL_PROVIDER` environment variable
  - `SmtpEmailBackend` — Flask-Mail/SMTP adapter
  - `ConsoleEmailBackend` / `InMemoryEmailBackend` — development and test backends
  - `SendgridEmailBackend` / `MailgunEmailBackend` — API adapters
  - `NullEmailBackend` — no-op backend

### File Storage
- **Storage abstraction layer** (`services/storage/`) — profile pictures, signatures, receipts, and photo documentation
  - Supports `cloudinary`, `local`, `memory`, and `null` providers via the `STORAGE_PROVIDER` environment variable
  - `CloudinaryStorage` — Cloudinary adapter (default)
  - `LocalFilesystemStorage` — local filesystem adapter for development and self-hosting
  - `MemoryStorage` — in-memory backend for unit tests
  - `NullStorage` — no-op backend

### AI
- **AI abstraction layer** (`services/ai/`) — provider-agnostic text generation
  - Supports `gemini`, `openai`, `anthropic`, `local`, and `mock` providers via the `AI_PROVIDER` environment variable
  - `GeminiProvider` — Google Gemini adapter
  - `OpenAIProvider` / `AnthropicProvider` — OpenAI and Anthropic API adapters
  - `LocalAIProvider` — local OpenAI-compatible endpoint (e.g. Ollama)
  - `MockAIProvider` — no-op provider for tests and offline development

### PDF & Data Processing
- **ReportLab** — PDF generation
- **pandas** / **openpyxl** — Excel import of student lists

### Frontend
- **Vite** — build tool for the React + TypeScript SPA
- **React 19** — client-side UI
- **TypeScript 6** — type safety
- **Tailwind CSS 4** — utility-first styling via the `@tailwindcss/vite` plugin and custom CSS variables in `frontend/src/index.css`
- **Lucide React** — icon set
- **React Router v7** — client-side routing
- **TanStack Query (React Query)** — server state, caching, and mutations
- **Axios** — HTTP client with JWT access/refresh token interceptors
- **React Hook Form + Zod** — form state and validation
- **Recharts** — dashboard charts
- **Jinja2 macros** — legacy reusable form and UI components (`templates/macros/`); being replaced by React components

### Testing & Tooling
- **pytest** — test runner (config in `pytest.ini`)
- **python-dotenv** — environment variable loading

## Project Structure

```
E-Council/
├── app.py                 # Flask application factory (entry point) — creates app and registers extensions/blueprints
├── api/                   # FastAPI backend and REST API
│   ├── main.py            # FastAPI application with lifespan and router registration
│   ├── database.py        # SQLAlchemy engine and FastAPI session dependency
│   ├── dependencies.py    # JWT, pagination, storage, and role dependencies
│   ├── exceptions.py      # Shared API exception handlers
│   ├── settings.py        # FastAPI-specific settings
│   ├── routers/           # FastAPI feature routers
│   ├── schemas/           # Pydantic request/response models
│   ├── services/          # FastAPI-specific service helpers
│   ├── repositories/      # FastAPI-facing repository wrappers
│   └── tests/             # FastAPI integration and feature tests
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
├── frontend/              # React + TypeScript SPA
│   ├── src/
│   │   ├── api/           # Axios instances and API functions
│   │   ├── components/    # Shared UI and layout components
│   │   ├── config/        # Feature resource definitions
│   │   ├── pages/         # Route-level pages
│   │   ├── providers/     # Auth and query providers
│   │   ├── routes/        # Route definitions
│   │   ├── types/         # Shared TypeScript interfaces
│   │   └── utils/         # Utility helpers
│   ├── package.json
│   └── vite.config.ts
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
├── repositories/          # SQLAlchemy repository abstraction layer
│   ├── __init__.py
│   ├── base.py
│   └── users.py
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
├── services/              # Business logic service layer
│   ├── __init__.py
│   ├── base.py
│   ├── board_resolutions.py
│   ├── concept_papers.py
│   ├── documentation.py
│   ├── events.py
│   ├── financial.py
│   ├── meetings.py
│   ├── ai/                  # AI generation abstraction layer
│   │   ├── __init__.py
│   │   ├── errors.py
│   │   ├── helpers.py
│   │   ├── prompts.py
│   │   ├── protocol.py
│   │   ├── providers.py
│   │   ├── service.py
│   │   └── generation.py
│   ├── email/               # Email delivery abstraction layer
│   │   ├── __init__.py
│   │   ├── backends.py
│   │   ├── errors.py
│   │   ├── protocol.py
│   │   ├── service.py
│   │   └── tasks.py
│   └── storage/             # File/object storage abstraction layer
│       ├── __init__.py
│       ├── backends.py
│       ├── errors.py
│       ├── protocol.py
│       └── service.py
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
│   ├── test_repositories.py
│   ├── test_routes.py
│   ├── test_signup.py
│   ├── test_storage.py
│   └── test_utils.py
├── uploads/               # Runtime upload folder (receipts)
├── .env                   # Environment variables (gitignored — see Setup)
├── .gitignore
└── LICENSE                # MIT
```

> **Note on architecture:** The application uses a modular Flask blueprint architecture plus a FastAPI REST API in `api/`. `app.py` contains the `create_app` factory for the server-rendered UI, and `api/main.py` contains the FastAPI application. Business logic is split into `routes/` (Flask), `api/routers/` (FastAPI), `services/`, `models/`, `repositories/`, `utils/`, and `config/`. The `repositories/` layer is the only layer that touches SQLAlchemy session internals; routes and services use `repo` and `get_repository()` for persistence. The `services/storage/`, `services/email/`, and `services/ai/` layers abstract file uploads, email delivery, and AI generation so the same backends work for both Flask and FastAPI. Legacy `static/css/` files were removed during the Tailwind CSS 4 migration.

## Prerequisites

Before setting up the project, make sure you have the following:

1. **Python 3.9 or higher** — [python.org](https://www.python.org/downloads/)
2. **pip** — bundled with Python 3.4+
3. **A database** — SQLite, MySQL, or PostgreSQL (or any SQLAlchemy-compatible engine). SQLite is used by default, so no external server is required for local development.
4. **A Cloudinary account** — only required if you set `STORAGE_PROVIDER=cloudinary` (default). For local development you can use `STORAGE_PROVIDER=local` or `STORAGE_PROVIDER=null`.
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

Copy the provided example file to a local `.env` file (this file is gitignored and should never be committed):

```bash
cp .env.example .env
```

Open `.env` and replace every placeholder with your own credentials. The example file is organized by service and describes each variable. At minimum, set the following:

| Variable | Required? | How to get it |
|----------|-----------|---------------|
| `SECRET_KEY` | Yes | Generate locally with `python -c "import secrets; print(secrets.token_hex(32))"` |
| `SQLALCHEMY_DATABASE_URI` | Yes | Flask database URI; use a local SQLite path (`sqlite:///e_council.db`) or a MySQL URI (e.g. `mysql+pymysql://user:pass@localhost/e_council`) |
| `FASTAPI_DATABASE_URI` | No | FastAPI database URI; defaults to `SQLALCHEMY_DATABASE_URI` or `sqlite:///e_council.db` |
| `MAIL_DEFAULT_SENDER` | Yes | Any email address you control; used as the sender for verification and notification emails |
| `MAIL_USERNAME` / `MAIL_PASSWORD` | Yes for real email | SMTP credentials; for Gmail, use an [App Password](https://support.google.com/accounts/answer/185833) |
| `EMAIL_PROVIDER` | No | Email backend: `smtp` (default), `console`, `memory`, `sendgrid`, `mailgun`, or `null` |
| `SENDGRID_API_KEY` / `SENDGRID_FROM_EMAIL` | No | Required when `EMAIL_PROVIDER=sendgrid` |
| `MAILGUN_API_KEY` / `MAILGUN_DOMAIN` / `MAILGUN_FROM_EMAIL` | No | Required when `EMAIL_PROVIDER=mailgun` |
| `STORAGE_PROVIDER` | No | Object storage backend: `cloudinary` (default), `local`, `memory`, or `null` |
| `STORAGE_LOCAL_PATH` | No | Local directory for `STORAGE_PROVIDER=local` (default: `uploads`) |
| `STORAGE_LOCAL_BASE_URL` | No | URL prefix for `STORAGE_PROVIDER=local` (default: `/static/uploads`) |
| `CLOUDINARY_CLOUD_NAME` / `CLOUDINARY_API_KEY` / `CLOUDINARY_API_SECRET` | Yes for Cloudinary uploads | Create a free account at [Cloudinary](https://cloudinary.com/) and copy the values from the dashboard |
| `AI_PROVIDER` | No | AI backend: `gemini` (default), `openai`, `anthropic`, `local`, or `mock` |
| `GOOGLE_GEMINI_AI_API_KEY` | Yes for `gemini` | Create a key in [Google AI Studio](https://aistudio.google.com/app/apikey) |
| `OPENAI_API_KEY` | Yes for `openai` | Create a key in [OpenAI Platform](https://platform.openai.com/) |
| `ANTHROPIC_API_KEY` | Yes for `anthropic` | Create a key in [Anthropic Console](https://console.anthropic.com/) |
| `LOCAL_AI_BASE_URL` / `LOCAL_AI_MODEL` | No | Local OpenAI-compatible endpoint (e.g. Ollama at `http://localhost:11434/v1`) |
| `API_BASE_URL` | No | Base URL for FastAPI-generated links (default: `http://localhost:8000`) |
| `FRONTEND_URL` | No | Base URL for the frontend/React app (default: `http://localhost:3000`) |
| `SENTRY_DSN` | No | Optional; create a project at [Sentry](https://sentry.io/) and paste the DSN |

> **Security:** Never commit your `.env` file. It is listed in `.gitignore`. Use App Passwords for Gmail rather than your account password, and rotate any keys if they have ever been exposed.

> **Running tests:** The CI pipeline runs with a minimal set of environment variables (`SECRET_KEY`, `SQLALCHEMY_DATABASE_URI`, `MAIL_DEFAULT_SENDER`). You can run the test suite locally with the same minimal `.env` or with a real `.env` file.

### 6. Initialize the Database Schema

With the `.env` file in place and the virtual environment active, apply the existing Flask-Migrate migrations to create the tables:

```bash
flask db upgrade
```

Migrations are versioned in the `migrations/` directory. For a fresh database, this will create the full schema. For an existing database, it will apply any pending migrations.

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

### FastAPI Backend

The FastAPI backend is in the `api/` package. Start it with Uvicorn:

```bash
uvicorn api.main:app --reload
```

The API runs on `http://127.0.0.1:8000`. Interactive documentation is available at:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

API endpoints are grouped under `/api/v1/` (e.g., `/api/v1/auth/register`, `/api/v1/concept-papers`).

### React + TypeScript Frontend

The SPA is in the `frontend/` directory. It expects the FastAPI backend to be running.

1. Copy the environment example:

```bash
cd frontend
cp .env.example .env
```

2. Install dependencies and start the dev server:

```bash
cd frontend
npm install
npm run dev
```

The frontend runs on `http://localhost:3000` by default. Build the production bundle with:

```bash
cd frontend
npm run build
```

### Production

For production, use the WSGI entry point with **gunicorn** instead of the Flask development server:

```bash
gunicorn -w 4 -b 0.0.0.0:8000 wsgi:application
```

The `wsgi.py` file creates the app with the `production` configuration. Adjust the number of workers (`-w`) and bind address (`-b`) to match your deployment environment.

For the FastAPI backend, run Uvicorn with Gunicorn in production:

```bash
gunicorn -k uvicorn.workers.UvicornWorker -w 4 -b 0.0.0.0:8000 api.main:app
```

### Background Task Queue

Long-running operations (sending emails, generating PDFs, and AI content) are offloaded to a Celery worker. The worker requires a Redis broker.

1. Set the broker URL:

```bash
export BROKER_URL="redis://localhost:6379/0"
# Or on Windows (PowerShell):
$env:BROKER_URL="redis://localhost:6379/0"
```

2. Start the Celery worker:

```bash
celery -A tasks worker -l info
```

For local development without Redis, omit `BROKER_URL`. Tasks will run synchronously as a fallback.

### Building the CSS Bundle

Styles are written with Tailwind CSS v4 and bundled with the Tailwind CLI.

1. Install Node dependencies (requires Node.js and npm):

```bash
npm install
```

2. Build the production CSS bundle:

```bash
npm run build:css
```

3. Watch for changes during development:

```bash
npm run watch:css
```

The compiled stylesheet is written to `static/css/output.css`, which is served by the Flask app. The source file is `static/css/input.css`.

## Testing

Tests are written with pytest and configured via `pytest.ini`. From the project root with the virtual environment active:

```bash
pytest
```

The suite includes both the Flask tests in `tests/` and the FastAPI tests in `api/tests/`:

- `tests/conftest.py` — shared Flask test fixtures and app setup
- `tests/test_config.py` — configuration tests
- `tests/test_repositories.py` — repository abstraction integration tests
- `tests/test_routes.py` — route tests
- `tests/test_signup.py` — signup tests
- `tests/test_storage.py` — storage abstraction layer tests (memory, local, factory)
- `tests/test_cloudinary.py` — Cloudinary backend route tests (mocked)
- `tests/test_email.py` — email abstraction layer tests (in-memory backend, factory)
- `tests/test_ai.py` — AI generation route tests (mock provider)
- `tests/services/test_ai_service.py` — AI service and provider abstraction tests
- `tests/test_utils.py` — utility and filter tests
- `api/tests/conftest.py` — FastAPI test fixtures (in-memory DB, authenticated client, admin user)
- `api/tests/test_infrastructure.py` — shared FastAPI infrastructure tests
- `api/tests/test_auth.py`, `test_account.py`, `test_admin.py` — FastAPI auth, account, and admin tests
- `api/tests/test_concept_papers.py`, `test_events.py`, `test_meetings.py`, `test_board_resolutions.py`, `test_financial.py`, `test_documentation.py`, `test_dashboard.py` — feature router tests
- `api/tests/test_integration.py` — end-to-end FastAPI integration flow

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
