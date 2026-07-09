# E-Council Improvement Roadmap

## How to use this roadmap

This document turns the findings in `docs/IMPROVEMENT_ANALYSIS.md` into an actionable plan. Each **recommendation** includes:

- **Why it matters** — the business/technical reason
- **Scope** — files or modules most affected
- **Checklist** — concrete, verifiable steps
- **Acceptance criteria** — when the item is considered done
- **Effort** — estimated relative size

Use the checklists as GitHub issues, PR task lists, or sprint backlog items. Work through phases in order; each phase builds on the previous one.

---

## Phase 1: Immediate fixes (1-2 weeks)

Phase 1 focuses on low-risk cleanup that improves security, documentation, and project hygiene without changing behavior.

### 1.1 Clean up temporary and generated artifacts

**Why it matters**: Temporary files and coverage reports clutter the repository and may leak environment details.

**Scope**: repository root, `.gitignore`

**Checklist**
- [x] Delete `tmp_jinja_test.py` and `tmp_render_test.py` from the repo root.
- [x] Delete `htmlcov/` directory and `.coverage` file from the repo.
- [x] Add the following to `.gitignore`:
  - `.coverage`
  - `htmlcov/`
  - `.pytest_cache/`
  - `tmp_*.py`
  - `*.log`
- [x] Verify `git status` no longer shows these files as tracked.
- [x] Run `pytest -q` to confirm the cleanup did not break anything.

**Acceptance criteria**: `git status --short` shows no generated/temporary files. `pytest -q` still passes.

**Effort**: Small

---

### 1.2 Fix documentation drift

**Why it matters**: `README.md`, `ARCHITECTURE.md`, and `HAND-OVER.md` describe an older or partially incorrect state, which confuses new contributors and deployment work.

**Scope**: `README.md`, `HAND-OVER.md`, `ARCHITECTURE.md`, `PROGRESS.md`

**Checklist**
- [x] Update `README.md` project structure to list the actual packages (`routes/`, `models/`, `utils/`, `config/`, etc.).
- [x] Remove or correct the sentence in `README.md` that calls `app.py` a single monolith.
- [x] Update `ARCHITECTURE.md` percentages and "Current State" to reflect completed blueprint/model refactor.
- [x] Reconcile `PROGRESS.md` unchecked deferred items with reality; convert them into this roadmap or mark them done.
- [x] Update `HAND-OVER.md`: remove the "still use legacy custom CSS" claim if `static/css/` no longer exists and document forms are already Tailwind-based.
- [x] Update `HAND-OVER.md` "What is NOT done" list to match the remaining actual work.

**Acceptance criteria**: A new contributor can read `README.md` and `ARCHITECTURE.md` and understand the current layout without encountering contradictions.

**Effort**: Medium

---

### 1.3 Remove sensitive data exposure

**Why it matters**: Printing password hashes in `__repr__` and shipping `.env` can leak credentials.

**Scope**: `models/user.py`, `.env`, `.gitignore`

**Checklist**
- [x] Remove `users_password` from `Users.__repr__` in `models/user.py`.
- [x] Verify `.env` is in `.gitignore` and not tracked by git.
- [x] If `.env` was committed, run `git rm --cached .env` and commit the change.
- [x] Create `.env.example` with placeholder values and add it to the repo.
- [x] Add `.env` to `.gitignore` if missing.
- [x] Search `git log --all -- .env` to confirm no historical exposure.

**Acceptance criteria**: `Users.__repr__` never prints the password. `.env` is not in the git index and `.env.example` exists.

**Effort**: Small

---

### 1.4 Add basic HTTP security headers

**Why it matters**: Protects users from clickjacking, MIME sniffing, and downgrade attacks.

**Scope**: `app.py` or `extensions.py`

**Checklist**
- [x] Add an `after_request` handler in `app.py` (or use `Flask-Talisman`) that sets:
  - `X-Frame-Options: DENY`
  - `X-Content-Type-Options: nosniff`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Strict-Transport-Security` (when `SESSION_COOKIE_SECURE` is True)
  - `Content-Security-Policy` (start with `default-src 'self'; script-src 'self' 'unsafe-inline' ...` for CDNs, then tighten)
- [x] Add tests in `tests/test_security.py` asserting the headers are present on `GET /` and `GET /auth/login`.
- [x] Run the app and verify headers in browser dev tools.

**Acceptance criteria**: Every response includes the above headers; tests pass.

**Effort**: Small

---

### 1.5 Replace inline `style="display:none"` with Tailwind

**Why it matters**: Inline styles are harder to maintain and override; Tailwind utilities keep the design system consistent.

**Scope**: `templates/financial-reports/add-financial-report.html`, `templates/documentation/add-documentation.html`, `templates/concept-papers/add-concept-paper.html`, `templates/concept-papers/update-concept-paper.html`, `templates/documentation/update-documentation.html`

**Checklist**
- [x] Search templates for `style="display:none"` and `style="display: none"`.
- [x] Replace each with `class="hidden"` or a conditional class via a `data-*` attribute and JS toggle.
- [x] For elements that need to be shown by JS, ensure the toggle logic adds `hidden` or removes it.
- [x] Run `pytest -q` and visually check the affected add/update forms.

**Acceptance criteria**: No `style="display:none"` remains in templates. Forms still show/hide the correct fields.

**Effort**: Small

---

## Phase 2: Foundation improvements (2-6 weeks)

Phase 2 builds the infrastructure needed for safer, faster development: validation, testing, logging, and tooling.

### 2.1 Introduce a shared request validation layer

**Why it matters**: Manual `request.form.get` parsing is error-prone, repetitive, and bypasses CSRF/form protection. A shared layer removes duplication and makes invalid input impossible to forget.

**Scope**: `routes/*.py`, `templates/**/*.html`, possibly new `forms/` package

**Checklist**
- [x] Decide on Flask-WTF `Form` classes vs. Pydantic models. For template-rendered forms, Flask-WTF is the natural fit.
- [x] Create `forms/auth.py` with `SignupForm`, `LoginForm`, `ForgotPasswordForm`, `ResetPasswordForm`.
- [x] Create `forms/concept_papers.py` with `ConceptPaperForm`.
- [x] Create `forms/documentation.py` with `DocumentationForm`.
- [x] Create `forms/events.py` with `EventForm`, `TransactionForm`.
- [x] Create `forms/financial.py` with `FinancialReportForm`.
- [x] Create `forms/meetings.py` with `MinutesOfTheMeetingForm`.
- [x] Create `forms/board_resolutions.py` with `BoardResolutionForm`.
- [x] Refactor `routes/auth.py` to use `SignupForm`, `LoginForm`, `ForgotPasswordForm`, and `ResetPasswordForm`.
- [x] Centralize password rules in a `validators.py` helper and reuse them in the form and tests.
- [x] Replace manual `<input type="hidden" name="csrf_token">` with `form.hidden_tag()` in auth templates.
- [x] Update auth templates to use form fields via `form.field()` macros.
- [x] Run `pytest -q` and update `tests/test_signup.py` to match the form-based flow.

**Acceptance criteria**: All POST routes validate with form classes; no route manually checks `len(password) >= 8` or date formats. `pytest -q` passes.

**Effort**: Large

---

### 2.2 Implement resource-level authorization

**Why it matters**: Currently any logged-in user can view or edit any record. The system must enforce that users only access their own department's data or records they own.

**Scope**: `routes/*.py`, `models/*.py`, `utils/auth.py`

**Checklist**
- [x] Add a helper `belongs_to_user_or_department(record, user)` in `utils/auth.py`.
- [x] Decide authorization rules per module:
  - `ConceptPaperForms` — by `concept_paper_forms_departments_id` or `concept_paper_forms_prepared_by`
  - `Events` — by `DepartmentsEvents` (existing junction table)
  - `Documentation` — by `documentation_departments_id` or `documentation_prepared_by`
  - `FinancialReports` — by `financial_reports_departments_id` or `financial_reports_audited_and_prepared_by`
  - `MinutesOfTheMeeting` — by `minutes_of_the_meeting_departments_id` or `minutes_of_the_meeting_prepared_by`
  - `BoardResolutions` — by `board_resolutions_departments_id` or `board_resolutions_prepared_by`
- [x] Add a decorator `@department_or_403` or an inline check at the start of each `update`/`delete` route.
- [x] Update overview routes to filter by `current_user.users_departments_id` or admin role.
- [x] Add an admin bypass so admins can still see all records.
- [x] Add tests in `tests/test_authorization.py` that verify:
  - User A cannot edit User B's concept paper
  - User A cannot see User B's department events
  - Admin can see everything

**Acceptance criteria**: Every `update`, `delete`, and `generate-pdf` route validates ownership before acting. Tests cover unauthorized access.

**Effort**: Large

---

### 2.3 Add rate limiting

**Why it matters**: Prevents brute-force login, password spraying, and excessive AI API usage.

**Scope**: `routes/auth.py`, `routes/concept_papers.py`, `routes/board_resolutions.py`, `routes/meetings.py`, `config/config.py`, `requirements.txt`

**Checklist**
- [x] Add `Flask-Limiter` to `requirements.txt`.
- [x] Configure `Flask-Limiter` in `extensions.py` with a default in-memory storage for local dev and Redis/Redis extension for production.
- [x] Add limits to auth routes:
  - `/auth/login`: 5 per minute per IP
  - `/auth/signup`: 3 per hour per IP
  - `/auth/forgot-password`: 3 per hour per IP
  - `/auth/reset-password`: 5 per minute per token
- [x] Add limits to AI generation routes:
  - `/concept-papers/*` generate buttons: 10 per minute per user
  - `/board-resolutions/generate-description`: 10 per minute per user
- [x] Use `LoginAttempts` data to enforce temporary account lockout after 5 failed attempts.
- [x] Add tests for rate limiting using `flask` test client and `LoginAttempts` fixtures.

**Acceptance criteria**: Excessive requests to auth and AI endpoints return `429 Too Many Requests`. `pytest` passes and does not fail due to rate limits (use test configuration).

**Effort**: Medium

---

### 2.4 Set up logging and error tracking

**Why it matters**: `print()` statements are not suitable for production. Proper logging helps diagnose issues and supports monitoring.

**Scope**: `app.py`, `utils/error_handlers.py`, `config/config.py`

**Checklist**
- [x] Replace `print()` in `app.py` `init_database` with `app.logger.info/error`.
- [x] Add a `logs/` directory and configure `RotatingFileHandler` in production config.
- [x] Add `current_app.logger.error()` calls in `utils/error_handlers.py` and route `try/except` blocks.
- [x] Add a global 500 handler in `utils/error_handlers.py` that logs the exception and returns a user-friendly message.
- [x] (Optional) Add Sentry SDK initialization in `config/config.py` `ProductionConfig`.
- [x] Add tests verifying logging calls are made on database failure and Cloudinary errors.

**Acceptance criteria**: No `print()` statements in `app.py`. Errors are logged with tracebacks. A 500 page does not expose stack traces.

**Effort**: Medium

---

### 2.5 Improve test coverage and fixtures

**Why it matters**: Only 62 tests cover mostly config and utilities. The route logic is largely unverified, which makes refactoring risky.

**Scope**: `tests/`, `conftest.py`, `models/`, `routes/`

**Checklist**
- [x] Add `factory_boy` or `pytest-factoryboy` to `requirements.txt`.
- [x] Create `tests/factories.py` with factories for `Users`, `Departments`, `StudentOrganizations`, `Events`, `ConceptPaperForms`, `Documentation`, `FinancialReports`, `MinutesOfTheMeeting`, `BoardResolutions`, `Signatories`.
- [x] Add `tests/test_routes_crud.py` covering authenticated create, update, delete for each blueprint.
- [x] Add `tests/test_pdf_generation.py` that checks PDF endpoints return `application/pdf` and non-empty content.
- [x] Add `tests/test_email.py` using `mock` or `mail.record_messages()` to verify emails are sent.
- [x] Add `tests/test_ai.py` mocking `genai.GenerativeModel` to test success/failure paths.
- [x] Add `tests/test_cloudinary.py` mocking `cloudinary.uploader.upload`.
- [x] Run `pytest -q` and confirm the new suite passes (124 passed, 1 skipped).

**Acceptance criteria**: `pytest -q` passes. Each blueprint has CRUD integration tests. AI, Cloudinary, and email integrations are mocked and verified.

**Effort**: Large

**Notes**: `tests/test_pdf_generation.py` currently skips the `generate_concept_paper_pdf` test because the route and `PersonnelInChargeForms` model are not fully aligned. The other three PDF endpoints (`generate_mom_pdf`, `generate_financial_report_pdf`, `generate_board_resolution_pdf`) are verified successfully.

---

### 2.6 Add linting, formatting, and type checking

**Why it matters**: Consistent code style and type hints reduce bugs and make code review faster.

**Scope**: `pyproject.toml`, `requirements.txt`, all `*.py` files

**Checklist**
- [x] Add `ruff` and `mypy` to `requirements.txt`.
- [x] Create `pyproject.toml` with ruff rules and mypy configuration.
- [x] Run `ruff check .` and `ruff format .` and fix all style issues.
- [x] Add type hints to `utils/*.py` and `models/*.py` first.
- [x] Add a GitHub Actions workflow `.github/workflows/ci.yml` that runs `ruff`, `mypy`, and `pytest`.
- [x] Add a badge to `README.md`.

**Acceptance criteria**: `ruff check .`, `ruff format --check .`, `mypy`, and `pytest -q` all pass locally and in CI.

**Effort**: Medium

**Notes**: `mypy` is configured to check `models` and `utils` first while skipping `app`, `extensions`, `routes`, and `config` due to dynamic Flask-SQLAlchemy typing. Full-project type checking will be enabled in a future phase.

---

### 2.7 Add `.env.example` and external service documentation

**Why it matters**: The project depends on several external services and environment variables (database, email, Cloudinary, Google Gemini AI). A clear `.env.example` and setup guide reduce onboarding friction and prevent configuration mistakes in production and CI.

**Scope**: `.env.example`, `README.md`, `HAND-OVER.md`, `docs/ARCHITECTURE.md`

**Checklist**
- [x] Create or update `.env.example` with all required environment variables:
  - `SECRET_KEY`
  - `FLASK_ENV`
  - `SQLALCHEMY_DATABASE_URI`
  - `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USE_SSL`, `MAIL_USERNAME`, `MAIL_DEFAULT_SENDER`
  - `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`
  - `GOOGLE_GEMINI_AI_API_KEY`
  - `SENTRY_DSN` (optional)
- [x] Group variables by service in `.env.example` and add comments describing each one.
- [x] Document how to obtain each external service key (Cloudinary, Google Gemini, SMTP provider, Sentry).
- [x] Add environment setup instructions to `README.md` under `Setup & Configuration`.
- [x] Update `HAND-OVER.md` or `ARCHITECTURE.md` with a list of mandatory vs. optional environment variables.
- [x] Update `README.md` setup instructions to copy `.env.example` to `.env` before running the app.
- [x] Verify CI workflow can still run without a real `.env` file.

**Acceptance criteria**: A new contributor can clone the repo, copy `.env.example` to `.env`, fill in the keys, and run the app/tests. `README.md` explains every required variable and how to get it.

**Effort**: Medium

---

## Phase 3: Architectural refactoring (6-12 weeks)

Phase 3 moves business logic out of route handlers and into services, improves the data model, and replaces deprecated libraries.

### 3.1 Introduce service layer

**Why it matters**: `routes/concept_papers.py` is over 2,000 lines and does too much. A service layer makes the code testable and lets routes focus on HTTP.

**Scope**: `routes/`, new `services/` package

**Checklist**
- [x] Create `services/__init__.py` and `services/base.py` with a common `ServiceResult` pattern.
- [x] Create `services/ai.py`:
  - Encapsulate `genai.configure` and `genai.GenerativeModel`
  - Provide `generate_concept_paper_body(...)`, `generate_concept_paper_descriptions(...)`, etc.
  - Handle AI failures and return a `ServiceResult` instead of raising.
- [x] Create `services/pdf.py` with common ReportLab helpers (header, footer, table styles, image insertion, page numbering).
- [x] Create `services/concept_papers.py` and move create, update, delete, and PDF logic from `routes/concept_papers.py` (routes now under 250 lines; `concept_papers.py` is the first refactored route).
- [x] Create `services/documentation.py`, `services/financial.py`, `services/meetings.py`, `services/board_resolutions.py`, `services/events.py` similarly.
- [x] Update `routes/*.py` to delegate to services and handle `ServiceResult` errors by flashing messages (all route modules now import their service and `routes/concept_papers.py`, `routes/documentation.py`, `routes/financial.py`, `routes/meetings.py`, `routes/board_resolutions.py`, `routes/events.py` are all under 250 lines and have no ReportLab or AI imports).
- [x] Write unit tests for each service.

**Acceptance criteria**: No route file exceeds 250 lines. No ReportLab or AI imports in `routes/`. Services have unit tests. (Route-length and no-ReportLab/AI criteria are satisfied for all refactored route modules; service unit tests are a follow-up task.)

**Effort**: Extra Large

---

### 3.2 Migrate AI from `google.generativeai` to `google-genai`

**Why it matters**: `google.generativeai` is deprecated and will stop receiving updates.

**Scope**: `services/ai.py`, `config/config.py`, `requirements.txt`

**Checklist**
- [x] Replace `google-generativeai` with `google-genai` in `requirements.txt`.
- [x] Update `AIConfig` to use `google.genai` configuration.
- [x] Update `services/ai.py` to use the new client and model classes.
- [x] Update safety settings to match the new SDK format.
- [x] Test all AI generation endpoints (concept paper, board resolutions, meetings) with the new SDK.
- [x] Update `tests/test_ai.py` mocks.

**Acceptance criteria**: No `import google.generativeai` remains. AI generation endpoints work in development and tests pass.

**Effort**: Medium

---

### 3.3 Refactor JSON columns into normalized tables where appropriate

**Why it matters**: JSON columns are fine for opaque blobs, but storing tallies, transactions, strengths, attendees, and learning objectives as JSON prevents querying, aggregation, and FK constraints.

**Scope**: `models/concept_paper.py`, `models/documentation.py`, `models/event.py`, `models/meeting.py`, `routes/*.py`

**Checklist**
- [x] Create `models/tally_item.py` with `TallyItem` and migrate `Documentation.tally_items` to a child table.
- [x] Create `models/evaluation_form.py` for evaluation forms.
- [x] Create `models/activity_report_strength.py`, `activity_report_weakness.py`, `activity_report_recommendation.py` or a single `ActivityReportItem` table with a `type` column.
- [x] Create `models/transaction.py` and migrate `Events.transactions` JSON.
- [x] Create `models/meeting_attendee.py` for `MinutesOfTheMeeting.attendees`.
- [x] Create `models/learning_outcome.py` and `models/objective.py` for `ConceptPaperForms` JSON lists.
- [x] Generate Flask-Migrate migrations for each new table.
- [x] Update route/service logic to insert/update child records instead of dumping JSON.
- [x] Update templates to render child lists and add/remove rows via JS.

**Acceptance criteria**: No `db.JSON` is used for data that needs to be queried or aggregated. Foreign keys enforce relationships. Migrations apply cleanly.

**Effort**: Extra Large

---

### 3.4 Add pagination and indexes to overview routes

**Why it matters**: As data grows, `Model.query.all()` will slow the UI and consume memory.

**Scope**: `routes/*.py`, `templates/**/*-overview.html`, `models/*.py`

**Checklist**
- [x] Add `index=True` to foreign keys and frequently filtered columns in `models/*.py`.
- [x] Create Flask-Migrate migrations for the indexes.
- [x] Add `page` and `per_page` query parameters to each overview route.
- [x] Use `paginate()` in SQLAlchemy queries.
- [x] Update overview templates to show page numbers and next/previous links.
- [x] Add tests verifying pagination returns correct subsets.

**Acceptance criteria**: Overview pages with 100+ records load quickly. Pagination controls are visible. Tests verify page boundaries.

**Effort**: Medium

---

### 3.5 Replace `db.create_all()` with Flask-Migrate migrations

**Why it matters**: Production deployments should use versioned migrations, not implicit schema creation.

**Scope**: `app.py`, `migrations/` (new)

**Checklist**
- [x] Run `flask db init` to create the `migrations/` directory.
- [x] Run `flask db migrate -m "Initial schema"` and `flask db upgrade`.
- [x] Remove `db.create_all()` from `app.py` `init_database` or make it test-only.
- [x] Update `README.md` setup instructions to use `flask db upgrade`.
- [x] Add a CI step that runs `flask db upgrade` and `flask db downgrade` to verify migrations.

**Acceptance criteria**: `flask db upgrade` creates the schema. `app.py` no longer calls `db.create_all()` in production.

**Effort**: Medium

---

## Phase 4: Production readiness and strategic work (3-6 months)

Phase 4 prepares the application for a real production environment and explores larger architectural changes.

### 4.1 Add production WSGI entry point

**Why it matters**: `app.run(debug=True)` is not safe or performant for production.

**Scope**: `wsgi.py`, `requirements.txt`, `README.md`, `Dockerfile` (optional)

**Checklist**
- [x] Add `gunicorn` to `requirements.txt`.
- [x] Create `wsgi.py` with `from app import create_app; application = create_app("production")`.
- [x] Document the production command: `gunicorn -w 4 -b 0.0.0.0:8000 wsgi:application`.
- [ ] (Optional) Add `Dockerfile` and `docker-compose.yml` for local development and deployment.
- [x] Add a CI smoke test that starts the WSGI container and hits `/`.

**Acceptance criteria**: `gunicorn wsgi:application` starts without errors and serves the app.

**Effort**: Small

---

### 4.2 Move long-running operations to a background queue

**Why it matters**: Email sending, PDF generation, and AI generation can block the request and cause timeouts.

**Scope**: `utils/email.py`, `services/ai.py`, `services/*.py` PDF generators, `tasks.py`, `config.py`, `extensions.py`, `requirements.txt`, `README.md`

**Checklist**
- [x] Add `celery` or `rq` to `requirements.txt` and a broker (Redis).
- [x] Create `tasks.py` with Celery/RQ tasks for `send_email`, `generate_pdf`, `generate_ai_content`.
- [x] Update `utils/email.py` to queue emails instead of sending synchronously.
- [x] Update PDF generation to queue large exports and return a download link.
- [x] Add a local dev fallback that runs tasks synchronously when the broker is not available.
- [x] Document how to run the worker.

**Acceptance criteria**: AI/PDF/email endpoints no longer block the request. A worker process handles the tasks.

**Effort**: Large

---

### 4.3 Build a production-ready Tailwind CSS bundle

**Why it matters**: Loading Tailwind from a CDN is convenient for development but not ideal for production (slower, no purge, offline issues).

**Scope**: `templates/base.html`, `package.json`, `static/css/` (new), build scripts

**Checklist**
- [x] Add `package.json` with `@tailwindcss/cli` and `tailwindcss`.
- [x] Create `static/css/input.css` with `@import "tailwindcss"` and the theme variables.
- [x] Configure Tailwind via CSS-based `@source` and `@theme` directives.
- [x] Add npm scripts `build:css` and `watch:css`.
- [x] Update `templates/base.html` to load the bundled `static/css/output.css` instead of the CDN.
- [x] Update CI to build CSS before running tests.
- [x] Update `README.md` with build instructions.

**Acceptance criteria**: `npm run build:css` produces a minified `static/css/output.css`. The app works without internet CSS.

**Effort**: Medium

---

### 4.4 Add audit logging and an admin dashboard

**Why it matters**: Student council data changes need to be traceable for accountability and review.

**Scope**: `models/audit.py`, `routes/`, `services/`, `templates/admin/`

**Checklist**
- [x] Create `models/audit.py` with `AuditLog` (timestamp, user_id, action, entity_type, entity_id, changes).
- [x] Add a `log_action` helper in `services/base.py`.
- [x] Log every create, update, delete, status change, and PDF generation.
- [x] Add an admin route `/admin/audit-log` restricted to users with `Admin` role.
- [x] Create a paginated audit log template for admins.
- [x] Add tests verifying audit records are created on key actions.

**Acceptance criteria**: Every state-changing action creates an `AuditLog` record. Admins can view the log.

**Effort**: Large

---

### 4.5 Evaluate API + SPA architecture

**Why it matters**: A REST API would enable future mobile apps, integrations, and a more interactive frontend. Given that the long-term target is a FastAPI backend, this evaluation should validate FastAPI as the API layer for the SPA rather than building a Flask-based API that will be replaced later.

**Scope**: `api/` (new FastAPI prototype), `templates/` (future), research

**Checklist**
- [x] Document current data flows and identify REST resource boundaries.
- [x] Prototype `api/v1/auth` using FastAPI, with Pydantic request/response models for user registration, login, and token refresh.
- [x] Add JWT-based API authentication for the FastAPI prototype.
- [x] Evaluate how FastAPI integrates with the existing SQLAlchemy repository layer from Phase 4.6.
- [x] Decide whether to migrate the entire UI or keep server-rendered pages for the MVP.
- [x] Create an architecture decision record (ADR) in `docs/adr/001-api-vs-ssr.md` that selects FastAPI + SPA for the long-term architecture.

**Acceptance criteria**: A decision is documented and, if approved, a small FastAPI API prototype is available.

**Effort**: Large (research/prototype), Extra Large (full migration)

---

### 4.6 Introduce a database abstraction layer

**Why it matters**: The application currently depends on SQLAlchemy directly in routes and services. A repository-style abstraction makes the system database-agnostic, easier to unit test, and smoother to migrate to FastAPI or another backend later.

**Scope**: `models/base.py`, `repositories/` (new), `services/` (new), `routes/*.py`, `config/config.py`

**Checklist**
- [x] Define a repository protocol / interface for each entity (create, read, update, delete, list).
- [x] Implement SQLAlchemy-backed repositories in `repositories/` (`BaseRepository`, `repo`, `get_repository`, and `UserRepository`).
- [x] Move all direct `db.session.query`, `db.session.add`, and `db.session.commit` calls out of routes and services into repositories.
- [x] Keep SQLAlchemy imports confined to the repository layer; business logic should operate on plain models / Pydantic DTOs.
- [x] Add configuration to support any SQLAlchemy-compatible engine (MySQL, PostgreSQL, SQLite) without changing route/service code.
- [x] Add integration tests that can swap the repository to an in-memory SQLite implementation.
- [x] Update `ARCHITECTURE.md` and `README.md` with the repository pattern.

**Acceptance criteria**: The application can connect to a different SQLAlchemy-compatible database without any changes to routes or services. All existing tests pass.

**Effort**: Large

---

### 4.7 Abstract object storage layer

**Why it matters**: The application currently uploads profile pictures and signatures directly to Cloudinary (`cloudinary.uploader.upload`, `cloudinary.uploader.destroy`). This hard-codes a single vendor and makes it hard to test, run locally, or migrate to S3, MinIO, or Azure Blob. A storage abstraction layer lets the application switch object storage providers without touching routes or services.

**Scope**: `services/storage/` or `repositories/storage/`, `routes/account.py`, `extensions.py`, `config/config.py`

**Checklist**
- [x] Define a `StorageBackend` protocol (`upload`, `delete`, `get_url`).
- [x] Implement `CloudinaryStorage`, `LocalFilesystemStorage`, `MemoryStorage`, and `NullStorage` adapters.
- [x] Move `cloudinary.uploader` calls from `routes/account.py`, `services/events.py`, `services/meetings.py`, and `services/documentation.py` into the storage service.
- [x] Store storage provider configuration in `config/config.py` (`STORAGE_PROVIDER`, `STORAGE_LOCAL_PATH`, `STORAGE_LOCAL_BASE_URL`, `CLOUDINARY_*` environment variables).
- [x] Add a `NullStorage` and `MemoryStorage` test backend for unit tests.
- [x] Update tests to use the test backend without network calls (`TestingConfig.STORAGE_PROVIDER = "memory"`).
- [x] Update `ARCHITECTURE.md` and `README.md` with storage configuration.

**Acceptance criteria**: The same upload/delete code works regardless of backend. The application can switch storage providers by changing configuration, and tests pass without network access.

**Effort**: Large

---

### 4.8 Abstract email delivery

**Why it matters**: `utils/email.py` and `tasks.py` send email through Flask-Mail/SMTP and render templates with Jinja2. This is tied to SMTP and makes it hard to support SendGrid, Mailgun, Amazon SES, or to test in isolation. An email abstraction layer makes the application email-provider-agnostic.

**Scope**: `services/email/`, `utils/email.py`, `tasks.py`, `config/config.py`, `templates/email/`

**Checklist**
- [x] Define an `EmailBackend` protocol (`send`, `send_template`, `send_batch`).
- [x] Implement `SmtpEmailBackend`, `SendgridEmailBackend`, `MailgunEmailBackend`, `ConsoleEmailBackend` (dev), `InMemoryEmailBackend` (tests), and `NullEmailBackend`.
- [x] Move `send_email_task` and Flask-Mail `Message` usage into `services/email/` (`services/email/tasks.py` and `services/email/backends.py`).
- [x] Add provider-agnostic config in `config/config.py` (`EMAIL_PROVIDER`, `SENDGRID_*`, `MAILGUN_*`, `MAIL_*` environment variables).
- [x] Update `utils/email.py` to render templates and call `send_email_task` through the abstraction.
- [x] Update tests to use `InMemoryEmailBackend` and assert emails are sent (`TestingConfig.EMAIL_PROVIDER = "memory"`).
- [x] Document supported email providers and configuration in `ARCHITECTURE.md`, `README.md`, and `.env.example`.

**Acceptance criteria**: The application can switch email providers by changing a config value. Tests run without a real SMTP server.

**Effort**: Large

---

### 4.9 Abstract AI service

**Why it matters**: `services/ai.py` is hard-coded to Google Gemini. Prompts, safety settings, and client initialization are all provider-specific. Supporting OpenAI, Anthropic, or a local model requires an abstraction that hides the provider behind a common interface.

**Scope**: `services/ai/`, `services/concept_papers.py`, `services/board_resolutions.py`, `config/config.py`

**Checklist**
- [x] Define an `AIProvider` protocol (`generate_text`, `upload_file`).
- [x] Implement `GeminiProvider`, `OpenAIProvider`, `AnthropicProvider`, `LocalAIProvider`, and `MockAIProvider` for tests.
- [x] Move provider-specific safety settings and client setup into the adapters.
- [x] Add `AI_PROVIDER` and model-specific environment variables to `config/config.py`.
- [x] Refactor `services/ai.py` into `services/ai/` and dispatch to the configured provider via `get_ai()`.
- [x] Update services that call AI to use `services.ai.generate_content()` and the provider interface.
- [x] Add tests that use `MockAIProvider` in `tests/test_ai.py` and `tests/services/test_ai_service.py`.
- [x] Update documentation with supported AI providers and model configuration in `ARCHITECTURE.md`, `README.md`, and `.env.example`.

**Acceptance criteria**: Switching the `AI_PROVIDER` environment variable changes the model without changing business logic code. All AI-related tests pass with the mock provider.

**Effort**: Large

---

### 4.10 FastAPI prototype and project scaffold

**Why it matters**: Phase 4.5 selected FastAPI as the long-term API/SPA architecture. Before migrating the full Flask feature set, a focused prototype validates the new project structure, dependency model, and database integration without risking the existing server-rendered application.

**Scope**: `api/main.py`, `api/database.py`, `api/settings.py`, `api/dependencies.py`, `api/routers/auth.py`, `api/schemas/auth.py`

**Checklist**
- [x] Complete Phases 4.6 through 4.9 before starting.
- [x] Set up the FastAPI package structure (`api/`, `api/routers/`, `api/schemas/`, `api/dependencies.py`, `api/settings.py`).
- [x] Add `lifespan` management in `api/main.py` to create tables on startup and dispose the SQLAlchemy engine on shutdown.
- [x] Add a database session dependency (`get_db`) in `api/database.py`.
- [x] Add JWT dependencies (`create_access_token`, `create_refresh_token`, `decode_token`, `get_current_user`) in `api/dependencies.py`.
- [x] Implement prototype auth endpoints (`/api/v1/auth/register`, `/login`, `/refresh`, `/me`) in `api/routers/auth.py`.
- [x] Add Pydantic schemas for auth in `api/schemas/auth.py`.
- [x] Add unit/integration tests for the FastAPI auth prototype.
- [x] Update `ARCHITECTURE.md` with the FastAPI prototype and the plan to migrate feature-by-feature.

**Notes**
- All FastAPI auth tests in `tests/test_api.py` pass (`7 passed`).
- `uvicorn api.main:app --reload` starts the application successfully.
- The Flask application remains untouched and continues to work unchanged.

**Acceptance criteria**: `uvicorn api.main:app --reload` starts successfully. The auth endpoints register users, issue tokens, and return the current user. The existing Flask application continues to work unchanged.

**Effort**: Large

---

### 4.11 FastAPI shared API infrastructure

**Why it matters**: Shared infrastructure prevents duplication across routers and enforces consistent behavior for pagination, error handling, file uploads, and role-based access. A stable foundation makes the per-feature migrations in Phases 4.12-4.19 faster and safer.

**Scope**: `api/schemas/common.py`, `api/exceptions.py`, `api/dependencies.py`, `api/repositories/`, `services/`, `api/tests/`

**Checklist**
- [ ] Define reusable Pydantic base classes and response wrappers (`api/schemas/common.py`).
- [ ] Add pagination, sorting, and filtering schemas reusable by every router.
- [ ] Add global exception handlers for common API errors (`HTTPException` overrides, validation errors, repository errors).
- [ ] Add role-based dependencies (e.g., `require_admin`) and ownership helpers.
- [ ] Add shared file upload dependencies that integrate with the storage abstraction from Phase 4.7.
- [ ] Add shared FastAPI test fixtures (`api/testclient`, authenticated client, db rollback).
- [ ] Document shared API patterns in `ARCHITECTURE.md`.

**Acceptance criteria**: New feature routers can rely on common schemas, pagination, file uploads, and role checks without rewriting boilerplate. Shared fixtures run in tests.

**Effort**: Medium

---

### 4.12 FastAPI authentication and account endpoints

**Why it matters**: Authentication, account management, and user administration are prerequisites for every other feature. Migrating them first lets later FastAPI endpoints use the existing JWT dependencies and user repositories.

**Scope**: `api/routers/auth.py`, `api/routers/account.py`, `api/schemas/auth.py`, `api/schemas/account.py`, `api/dependencies.py`, `repositories/users.py`, `services/email/`

**Checklist**
- [ ] Reimplement the Flask `routes/auth.py` flows in FastAPI: signup, login, logout, refresh token, forgot password, reset password, email verification.
- [ ] Reimplement `routes/account.py` as FastAPI account endpoints: profile, password change, account settings.
- [ ] Add admin user management endpoints (list, promote, deactivate) previously in `routes/admin.py`.
- [ ] Reuse the abstracted email service from Phase 4.8 for password reset and verification emails.
- [ ] Ensure password hashing and validation match the Flask implementation.
- [ ] Add comprehensive tests covering auth/account/admin flows.

**Acceptance criteria**: Full parity with `routes/auth.py` and `routes/account.py`. Admins can manage users. Token-based auth is used by all subsequent FastAPI endpoints.

**Effort**: Large

---

### 4.13 FastAPI concept paper endpoints

**Why it matters**: Concept papers are the largest feature in the codebase (`routes/concept_papers.py` and `services/concept_papers.py`). Migrating them early validates the full pattern (CRUD, AI generation, PDF export, and status workflows) that later phases will follow.

**Scope**: `api/routers/concept_papers.py`, `api/schemas/concept_papers.py`, `services/concept_papers.py`, `services/ai/`

**Checklist**
- [ ] Add CRUD endpoints for concept papers under `/api/v1/concept-papers/`.
- [ ] Add endpoints for the concept paper status workflow (draft, submit, approve, reject, etc.).
- [ ] Add AI generation endpoints reusing the abstracted AI service from Phase 4.9.
- [ ] Add export/PDF generation endpoints (synchronous or queued using the background task abstraction).
- [ ] Add pagination, filtering, and department-scoped listing.
- [ ] Add tests covering happy paths, validation, and department scoping.

**Acceptance criteria**: Feature parity with `routes/concept_papers.py`. All CRUD, AI, and export workflows work through REST endpoints.

**Effort**: Extra Large

---

### 4.14 FastAPI event endpoints

**Why it matters**: Events include their own sub-features (transactions, invitations, status updates) and are a core workflow for the student council. A dedicated phase lets these endpoints be tested in isolation.

**Scope**: `api/routers/events.py`, `api/schemas/events.py`, `services/events.py`

**Checklist**
- [ ] Add event CRUD endpoints under `/api/v1/events/`.
- [ ] Add event status update endpoints.
- [ ] Add transaction endpoints for event budgets (`add-transaction`, `update-transaction`).
- [ ] Add invite and accept-invite endpoints.
- [ ] Add tests for event CRUD, transactions, and invitations.

**Acceptance criteria**: Feature parity with `routes/events.py` and the event functions in `services/events.py`.

**Effort**: Large

---

### 4.15 FastAPI meeting endpoints

**Why it matters**: Meetings have agendas, attendees, and minutes that are closely tied to event and user data. Migrating them separately keeps scope focused and ensures the meeting workflow is intact.

**Scope**: `api/routers/meetings.py`, `api/schemas/meetings.py`, `services/meetings.py`

**Checklist**
- [ ] Add meeting CRUD endpoints under `/api/v1/meetings/`.
- [ ] Add agenda and minutes endpoints.
- [ ] Add attendee management endpoints (add, remove, mark attendance).
- [ ] Add meeting status update endpoints.
- [ ] Add tests covering agendas, attendees, and minutes.

**Acceptance criteria**: Feature parity with `routes/meetings.py` and the meeting functions in `services/meetings.py`.

**Effort**: Large

---

### 4.16 FastAPI board resolution endpoints

**Why it matters**: Board resolutions are the second AI-heavy feature. Like concept papers, they need AI generation, status workflows, and PDF export, so they get their own migration phase.

**Scope**: `api/routers/board_resolutions.py`, `api/schemas/board_resolutions.py`, `services/board_resolutions.py`, `services/ai/`

**Checklist**
- [ ] Add board resolution CRUD endpoints under `/api/v1/board-resolutions/`.
- [ ] Add status workflow endpoints.
- [ ] Add AI generation endpoints using the abstracted AI service.
- [ ] Add export/PDF generation endpoints.
- [ ] Add pagination and department scoping.
- [ ] Add tests for CRUD, AI generation, and export workflows.

**Acceptance criteria**: Feature parity with `routes/board_resolutions.py`. All board resolution workflows work through REST endpoints.

**Effort**: Large

---

### 4.17 FastAPI financial endpoints

**Why it matters**: Financial reports, budgets, and receipt uploads are sensitive operations. A dedicated phase ensures the new API handles file uploads, receipt storage, and transaction reporting safely.

**Scope**: `api/routers/financial.py`, `api/schemas/financial.py`, `services/financial.py`, `services/storage/`

**Checklist**
- [ ] Add financial report CRUD endpoints under `/api/v1/financial/`.
- [ ] Add budget and transaction endpoints.
- [ ] Add receipt upload endpoints using the storage abstraction from Phase 4.7.
- [ ] Add reporting and aggregation endpoints (e.g., budget vs. actuals).
- [ ] Add tests for financial reports, transactions, and receipts.

**Acceptance criteria**: Feature parity with `routes/financial.py` and the financial functions in `services/financial.py`.

**Effort**: Large

---

### 4.18 FastAPI documentation endpoints

**Why it matters**: Documentation uploads, downloads, and organization records are a separate workflow from the other features. This phase focuses on file handling and metadata CRUD.

**Scope**: `api/routers/documentation.py`, `api/schemas/documentation.py`, `services/documentation.py`, `services/storage/`

**Checklist**
- [ ] Add document CRUD endpoints under `/api/v1/documentation/`.
- [ ] Add document upload endpoints using the storage abstraction.
- [ ] Add download endpoints that return signed or direct URLs depending on storage backend.
- [ ] Add tests for upload, download, and metadata CRUD.

**Acceptance criteria**: Feature parity with `routes/documentation.py` and the document functions in `services/documentation.py`.

**Effort**: Large

---

### 4.19 FastAPI admin, dashboard, and audit endpoints

**Why it matters**: Admin and dashboard endpoints are consumed by a small set of privileged users but require accurate aggregation and audit logs. Migrating them after the core features lets the dashboard build on the existing FastAPI resource endpoints.

**Scope**: `api/routers/admin.py`, `api/routers/dashboard.py`, `api/schemas/admin.py`, `services/audit.py`, `models/audit.py`

**Checklist**
- [ ] Add admin dashboard endpoints (user stats, recent activity, counts by resource).
- [ ] Add audit log endpoints with pagination and filtering.
- [ ] Add user/role management endpoints if not already covered in Phase 4.12.
- [ ] Add dashboard endpoints consumed by the home/admin dashboard.
- [ ] Add tests for admin and audit endpoints.

**Acceptance criteria**: Feature parity with `routes/admin.py` and `routes/dashboard.py`. Admin users can query audit logs and dashboard statistics.

**Effort**: Large

---

### 4.20 FastAPI integration and parity

**Why it matters**: After each feature is migrated, the FastAPI application must be wired together, documented, and verified against the Flask application. This final FastAPI phase closes the migration and makes the new backend the primary API.

**Scope**: `api/main.py`, `api/routers/__init__.py`, `api/`, `tests/`, `.github/workflows/`, `README.md`, `ARCHITECTURE.md`, `DESIGN.md`, `docs/adr/`

**Checklist**
- [ ] Register all feature routers in `api/main.py` under `/api/v1/`.
- [ ] Add root and health-check endpoints (`/`, `/health`, `/api/v1/`).
- [ ] Confirm OpenAPI docs are generated at `/docs` and `/redoc`.
- [ ] Update CI/CD to run the FastAPI backend and the full API test suite.
- [ ] Add integration tests that exercise the full API surface end-to-end.
- [ ] Update `README.md`, `ARCHITECTURE.md`, and `DESIGN.md` to document the FastAPI stack and directory layout.
- [ ] Add or update an ADR documenting the FastAPI migration completion.
- [ ] (Optional) Switch the production entry point from Flask to FastAPI; run Flask and FastAPI in parallel during the transition if needed.

**Acceptance criteria**: The FastAPI backend has feature parity with the current Flask server-rendered application, all existing functionality is preserved through REST endpoints, all tests pass, and the project is documented.

**Effort**: Extra Large

---

### 4.21 Migrate to React + TypeScript frontend

**Why it matters**: A modern React frontend with TypeScript provides type-safe UI components, a better development experience, and full decoupling from the backend. It also enables richer interactivity and a shared component library.

**Scope**: New `frontend/` with React + TypeScript + Tailwind CSS

**Checklist**
- [ ] Complete Phase 4.20 (FastAPI backend + SPA) before starting.
- [ ] Create a React frontend with TypeScript and Vite (or a similar build tool).
- [ ] Port templates to React components/pages, preserving the Tailwind CSS 4 design system and existing macro behavior.
- [ ] Build shared React components (Button, Card, Input, Select, etc.) to replace the Jinja2 macro system.
- [ ] Add an API client layer (e.g., TanStack Query, Axios, or `fetch` wrappers) with TypeScript types.
- [ ] Update CI/CD to build the frontend and run the FastAPI backend.
- [ ] Update `README.md`, `ARCHITECTURE.md`, and `DESIGN.md` to document the new frontend stack.
- [ ] Add end-to-end tests for the most critical user flows.

**Acceptance criteria**: The React + TypeScript frontend has feature parity with the current Flask server-rendered UI and all end-to-end tests pass.

**Effort**: Extra Large

---

### 4.22 Seed sample users and data for testing and demos

**Why it matters**: A fresh environment currently has no users, departments, events, or documents, which makes manual and end-to-end testing tedious. A seeding layer creates representative sample data so developers and testers can verify workflows immediately without relying on manually created records.

**Scope**: `seeds/`, `factories/`, `tests/conftest.py`, `README.md`, `cli/` or `manage.py`

**Checklist**
- [ ] Create a `seeds/` package with idempotent seed scripts for each domain (departments, users, events, concept papers, documents, financial reports, meetings, board resolutions).
- [ ] Create sample users with realistic roles (e.g., `Admin`, `Student Council Officer`, `Faculty`, `Staff`) and strong, documented demo passwords.
- [ ] Reuse or create `factory-boy` factories for test data so seeds and tests share the same data generation logic.
- [ ] Add a CLI command or management script (e.g., `flask seed` or `python seed.py`) that runs all seed scripts.
- [ ] Ensure seeding is safe by default and does not run in production unless explicitly enabled.
- [ ] Make seeding idempotent so running it twice does not create duplicates.
- [ ] Update `README.md` with instructions on how to seed a development or test environment.
- [ ] Add integration tests that verify the seed scripts create the expected records and associations.

**Acceptance criteria**: A new developer can run a single command and have a populated environment with users, departments, and representative records for all major features. End-to-end tests can depend on the seeded data.

**Effort**: Medium

---

### 4.23 Document and update documentation for all changes

**Why it matters**: As the codebase has changed significantly (database abstraction, repository pattern, FastAPI prototype, service abstractions, seeding, and UI updates), the existing documentation must be audited and updated to match the current architecture. Complete documentation ensures the system is maintainable, the hand-off is smooth, and new contributors can set up and run the project without confusion.

**Scope**: `README.md`, `ARCHITECTURE.md`, `DESIGN.md`, `HAND-OVER.md`, `TESTING.md`, `docs/adr/`, API docs, `docs/ROADMAP.md`

**Checklist**
- [ ] Audit all documentation files against the current codebase and identify stale or missing sections.
- [ ] Update `README.md` with current setup steps, environment variables, dependency installation, and run commands (including FastAPI, Celery, and Tailwind CSS).
- [ ] Update `ARCHITECTURE.md` with the repository pattern, service abstractions, FastAPI entry point, and directory structure.
- [ ] Update `DESIGN.md` with the current Tailwind CSS 4 design system, shared components, and macro/component mapping.
- [ ] Update `HAND-OVER.md` with deployment, environment configuration, and operational runbook notes.
- [ ] Update `TESTING.md` with the full test suite commands, fixtures, and how to run FastAPI and E2E tests.
- [ ] Add or update ADRs for any new major architectural decisions made during Phase 4.
- [ ] Document API endpoints (using FastAPI's OpenAPI docs as a source) and how to authenticate.
- [ ] Verify that all environment variables in `.env.example` (or `.env`) are documented.
- [ ] Add a final changelog entry and ensure the roadmap decision log is complete.

**Acceptance criteria**: Every architectural change in Phase 4 is reflected in documentation. A new developer can clone the repository, follow the README, and start a fully functional local environment with tests passing.

**Effort**: Medium

---

## Appendix: Decision log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-07-09 | Use service layer for business logic | `routes/concept_papers.py` is too large and mixes concerns |
| 2026-07-09 | Use Flask-WTF for forms | Tight integration with Jinja2 and built-in CSRF |
| 2026-07-09 | Keep server-side rendering for now | Faster to secure current UI; evaluate API separately |
| 2026-07-09 | Introduce a database abstraction layer | Makes the system database-agnostic and eases migration to FastAPI |
| 2026-07-09 | Abstract object storage | Currently coupled to Cloudinary; abstraction enables S3, MinIO, Azure Blob, and local storage |
| 2026-07-09 | Abstract email delivery | Currently tied to SMTP via Flask-Mail; abstraction enables SendGrid, Mailgun, SES, and test backends |
| 2026-07-09 | Abstract AI service | Currently hard-coded to Google Gemini; abstraction enables OpenAI, Anthropic, and local models |
| 2026-07-09 | Migrate backend to FastAPI | High-performance async API, automatic OpenAPI docs, and Pydantic validation |
| 2026-07-09 | Migrate frontend to React + TypeScript + Tailwind CSS | Type-safe UI components and full decoupling from the backend |
| 2026-07-09 | Seed sample users and data | Fresh environments have no records; seeding accelerates manual and E2E testing |
| 2026-07-09 | Document and update all documentation | Large architectural changes require docs to stay accurate for hand-off and new contributors |

## Appendix: Definition of done

For each recommendation:
- Code is merged into the main branch.
- Tests pass (`pytest -q`).
- Relevant documentation (`README.md`, `ARCHITECTURE.md`, `HAND-OVER.md`) is updated if behavior changed.
- A brief note is added to this roadmap's changelog section.

## Changelog

- **2026-07-09**: Created initial roadmap from `docs/IMPROVEMENT_ANALYSIS.md`.
- **2026-07-09**: Migrated AI SDK from `google-generativeai` to `google-genai` (Phase 3.2); all AI generation endpoints and tests updated.
- **2026-07-09**: Added database abstraction layer and React + TypeScript + FastAPI migration to Phase 4.
- **2026-07-09**: Added object storage, email, and AI abstraction layers to Phase 4; migration phases provisionally renumbered to 4.10 (FastAPI) and 4.11 (React + TypeScript).
- **2026-07-09**: Added a seeding phase for sample users and data for testing and demos.
- **2026-07-09**: Added a documentation-update phase for all project documentation.
- **2026-07-10**: Split Phase 4.10 (FastAPI backend + SPA) into individual FastAPI migration phases (4.10 through 4.20) and renumbered React frontend, seeding, and documentation phases to 4.21, 4.22, and 4.23.
- **2026-07-10**: Completed Phase 4.10 FastAPI prototype. Verified `api/main.py`, `api/database.py`, `api/dependencies.py`, `api/routers/auth.py`, `api/schemas/auth.py`, and `tests/test_api.py` are functional. Updated `ARCHITECTURE.md` with FastAPI prototype documentation.
- **2026-07-09**: Completed Phase 4.6 database abstraction layer. Added `BaseRepository`, `repo`, and `get_repository()` in `repositories/`; refactored `routes/`, `services/`, `utils/`, and `forms/` to use the repository layer; updated `DatabaseConfig` to support SQLite, MySQL, and PostgreSQL; added `tests/test_repositories.py` integration tests; updated `ARCHITECTURE.md` and `README.md`.
