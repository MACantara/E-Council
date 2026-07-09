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
- [ ] Decide on Flask-WTF `Form` classes vs. Pydantic models. For template-rendered forms, Flask-WTF is the natural fit.
- [ ] Create `forms/auth.py` with `SignupForm`, `LoginForm`, `ForgotPasswordForm`, `ResetPasswordForm`.
- [ ] Create `forms/concept_papers.py` with `ConceptPaperForm`.
- [ ] Create `forms/documentation.py` with `DocumentationForm`.
- [ ] Create `forms/events.py` with `EventForm`, `TransactionForm`.
- [ ] Create `forms/financial.py` with `FinancialReportForm`.
- [ ] Create `forms/meetings.py` with `MinutesOfTheMeetingForm`.
- [ ] Create `forms/board_resolutions.py` with `BoardResolutionForm`.
- [ ] Refactor `routes/auth.py` to use `SignupForm` and `LoginForm` first.
- [ ] Centralize password rules in a `validators.py` helper and reuse them in the form and tests.
- [ ] Replace manual `<input type="hidden" name="csrf_token">` with `form.hidden_tag()` or CSRF token injection.
- [ ] Update templates to use `form.field()` or keep the existing markup while passing the form object.
- [ ] Run `pytest -q` and update `tests/test_signup.py` to match the form-based flow.

**Acceptance criteria**: All POST routes validate with form classes; no route manually checks `len(password) >= 8` or date formats. `pytest -q` passes.

**Effort**: Large

---

### 2.2 Implement resource-level authorization

**Why it matters**: Currently any logged-in user can view or edit any record. The system must enforce that users only access their own department's data or records they own.

**Scope**: `routes/*.py`, `models/*.py`, `utils/auth.py`

**Checklist**
- [ ] Add a helper `belongs_to_user_or_department(record, user)` in `utils/auth.py`.
- [ ] Decide authorization rules per module:
  - `ConceptPaperForms` — by `concept_paper_forms_departments_id` or `concept_paper_forms_prepared_by`
  - `Events` — by `events_departments_id` (add a column if missing) or `DepartmentsEvents`
  - `Documentation` — by `documentation_departments_id` or `documentation_prepared_by`
  - `FinancialReports` — by `financial_reports_departments_id`
  - `MinutesOfTheMeeting` — by `minutes_of_the_meeting_departments_id`
  - `BoardResolutions` — by `board_resolutions_departments_id`
- [ ] Add a decorator `@department_or_403` or an inline check at the start of each `update`/`delete` route.
- [ ] Update overview routes to filter by `current_user.users_departments_id` or admin role.
- [ ] Add an admin bypass so admins can still see all records.
- [ ] Add tests in `tests/test_authorization.py` that verify:
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
- [ ] Add `Flask-Limiter` to `requirements.txt`.
- [ ] Configure `Flask-Limiter` in `extensions.py` with a default in-memory storage for local dev and Redis/Redis extension for production.
- [ ] Add limits to auth routes:
  - `/auth/login`: 5 per minute per IP
  - `/auth/signup`: 3 per hour per IP
  - `/auth/forgot-password`: 3 per hour per IP
  - `/auth/reset-password`: 5 per minute per token
- [ ] Add limits to AI generation routes:
  - `/concept-papers/add` generate buttons: 10 per minute per user
  - `/board-resolutions/generate-description`: 10 per minute per user
- [ ] Use `LoginAttempts` data to enforce temporary account lockout after 5 failed attempts.
- [ ] Add tests for rate limiting using `flask` test client and time mocks.

**Acceptance criteria**: Excessive requests to auth and AI endpoints return `429 Too Many Requests`. `pytest` passes and does not fail due to rate limits (use test configuration).

**Effort**: Medium

---

### 2.4 Set up logging and error tracking

**Why it matters**: `print()` statements are not suitable for production. Proper logging helps diagnose issues and supports monitoring.

**Scope**: `app.py`, `utils/error_handlers.py`, `config/config.py`

**Checklist**
- [ ] Replace `print()` in `app.py` `init_database` with `app.logger.info/error`.
- [ ] Add a `logs/` directory and configure `RotatingFileHandler` in production config.
- [ ] Add `current_app.logger.error()` calls in `utils/error_handlers.py` and route `try/except` blocks.
- [ ] Add a global 500 handler in `utils/error_handlers.py` that logs the exception and returns a user-friendly message.
- [ ] (Optional) Add Sentry SDK initialization in `config/config.py` `ProductionConfig`.
- [ ] Add tests verifying logging calls are made on database failure and Cloudinary errors.

**Acceptance criteria**: No `print()` statements in `app.py`. Errors are logged with tracebacks. A 500 page does not expose stack traces.

**Effort**: Medium

---

### 2.5 Improve test coverage and fixtures

**Why it matters**: Only 62 tests cover mostly config and utilities. The route logic is largely unverified, which makes refactoring risky.

**Scope**: `tests/`, `conftest.py`, `models/`, `routes/`

**Checklist**
- [ ] Add `factory_boy` or `pytest-factoryboy` to `requirements.txt`.
- [ ] Create `tests/factories.py` with factories for `Users`, `Departments`, `StudentOrganizations`, `Events`, `ConceptPaperForms`, `Documentation`, `FinancialReports`, `MinutesOfTheMeeting`, `BoardResolutions`, `Signatories`.
- [ ] Add `tests/test_routes_crud.py` covering authenticated create, update, delete for each blueprint.
- [ ] Add `tests/test_pdf_generation.py` that checks PDF endpoints return `application/pdf` and non-empty content.
- [ ] Add `tests/test_email.py` using `mock` or `mail.record_messages()` to verify emails are sent.
- [ ] Add `tests/test_ai.py` mocking `genai.GenerativeModel` to test success/failure paths.
- [ ] Add `tests/test_cloudinary.py` mocking `cloudinary.uploader.upload`.
- [ ] Run `pytest --cov=.` and target at least 60% coverage for Phase 2.

**Acceptance criteria**: `pytest -q` passes with at least 60% coverage. Each blueprint has CRUD integration tests.

**Effort**: Large

---

### 2.6 Add linting, formatting, and type checking

**Why it matters**: Consistent code style and type hints reduce bugs and make code review faster.

**Scope**: `pyproject.toml`, `requirements.txt`, all `*.py` files

**Checklist**
- [ ] Add `ruff` and `mypy` to `requirements.txt` (or `requirements-dev.txt`).
- [ ] Create `pyproject.toml` with ruff rules and mypy configuration.
- [ ] Run `ruff check .` and `ruff format .` and fix all style issues.
- [ ] Add type hints to `utils/*.py` and `models/*.py` first.
- [ ] Add a GitHub Actions workflow `.github/workflows/ci.yml` that runs `ruff`, `mypy`, and `pytest`.
- [ ] Add a badge to `README.md`.

**Acceptance criteria**: CI passes with `ruff`, `mypy`, and `pytest` green.

**Effort**: Medium

---

## Phase 3: Architectural refactoring (6-12 weeks)

Phase 3 moves business logic out of route handlers and into services, improves the data model, and replaces deprecated libraries.

### 3.1 Introduce service layer

**Why it matters**: `routes/concept_papers.py` is over 2,000 lines and does too much. A service layer makes the code testable and lets routes focus on HTTP.

**Scope**: `routes/`, new `services/` package

**Checklist**
- [ ] Create `services/__init__.py` and `services/base.py` with a common `ServiceResult` pattern.
- [ ] Create `services/ai.py`:
  - Encapsulate `genai.configure` and `genai.GenerativeModel`
  - Provide `generate_concept_paper_body(...)`, `generate_concept_paper_descriptions(...)`, etc.
  - Handle AI failures and return a `ServiceResult` instead of raising.
- [ ] Create `services/pdf.py`:
  - Extract common ReportLab helpers (header, footer, table styles, image insertion, page numbering)
  - Provide `generate_concept_paper_pdf(...)`, `generate_documentation_pdf(...)`, etc.
- [ ] Create `services/concept_papers.py`:
  - Move create, update, delete, and PDF logic from `routes/concept_papers.py`
  - Keep route functions under 50 lines
- [ ] Create `services/documentation.py`, `services/financial.py`, `services/meetings.py`, `services/board_resolutions.py`, `services/events.py` similarly.
- [ ] Update `routes/*.py` to delegate to services and handle `ServiceResult` errors by flashing messages.
- [ ] Write unit tests for each service.

**Acceptance criteria**: No route file exceeds 250 lines. No ReportLab or AI imports in `routes/`. Services have unit tests.

**Effort**: Extra Large

---

### 3.2 Migrate AI from `google.generativeai` to `google-genai`

**Why it matters**: `google.generativeai` is deprecated and will stop receiving updates.

**Scope**: `services/ai.py`, `config/config.py`, `requirements.txt`

**Checklist**
- [ ] Replace `google-generativeai` with `google-genai` in `requirements.txt`.
- [ ] Update `AIConfig` to use `google.genai` configuration.
- [ ] Update `services/ai.py` to use the new client and model classes.
- [ ] Update safety settings to match the new SDK format.
- [ ] Test all AI generation endpoints (concept paper, board resolutions, meetings) with the new SDK.
- [ ] Update `tests/test_ai.py` mocks.

**Acceptance criteria**: No `import google.generativeai` remains. AI generation endpoints work in development and tests pass.

**Effort**: Medium

---

### 3.3 Refactor JSON columns into normalized tables where appropriate

**Why it matters**: JSON columns are fine for opaque blobs, but storing tallies, transactions, strengths, attendees, and learning objectives as JSON prevents querying, aggregation, and FK constraints.

**Scope**: `models/concept_paper.py`, `models/documentation.py`, `models/event.py`, `models/meeting.py`, `routes/*.py`

**Checklist**
- [ ] Create `models/tally_item.py` with `TallyItem` and migrate `Documentation.tally_items` to a child table.
- [ ] Create `models/evaluation_form.py` for evaluation forms.
- [ ] Create `models/activity_report_strength.py`, `activity_report_weakness.py`, `activity_report_recommendation.py` or a single `ActivityReportItem` table with a `type` column.
- [ ] Create `models/transaction.py` and migrate `Events.transactions` JSON.
- [ ] Create `models/meeting_attendee.py` for `MinutesOfTheMeeting.attendees`.
- [ ] Create `models/learning_outcome.py` and `models/objective.py` for `ConceptPaperForms` JSON lists.
- [ ] Generate Flask-Migrate migrations for each new table.
- [ ] Update route/service logic to insert/update child records instead of dumping JSON.
- [ ] Update templates to render child lists and add/remove rows via JS.

**Acceptance criteria**: No `db.JSON` is used for data that needs to be queried or aggregated. Foreign keys enforce relationships. Migrations apply cleanly.

**Effort**: Extra Large

---

### 3.4 Add pagination and indexes to overview routes

**Why it matters**: As data grows, `Model.query.all()` will slow the UI and consume memory.

**Scope**: `routes/*.py`, `templates/**/*-overview.html`, `models/*.py`

**Checklist**
- [ ] Add `index=True` to foreign keys and frequently filtered columns in `models/*.py`.
- [ ] Create Flask-Migrate migrations for the indexes.
- [ ] Add `page` and `per_page` query parameters to each overview route.
- [ ] Use `paginate()` in SQLAlchemy queries.
- [ ] Update overview templates to show page numbers and next/previous links.
- [ ] Add tests verifying pagination returns correct subsets.

**Acceptance criteria**: Overview pages with 100+ records load quickly. Pagination controls are visible. Tests verify page boundaries.

**Effort**: Medium

---

### 3.5 Replace `db.create_all()` with Flask-Migrate migrations

**Why it matters**: Production deployments should use versioned migrations, not implicit schema creation.

**Scope**: `app.py`, `migrations/` (new)

**Checklist**
- [ ] Run `flask db init` to create the `migrations/` directory.
- [ ] Run `flask db migrate -m "Initial schema"` and `flask db upgrade`.
- [ ] Remove `db.create_all()` from `app.py` `init_database` or make it test-only.
- [ ] Update `README.md` setup instructions to use `flask db upgrade`.
- [ ] Add a CI step that runs `flask db upgrade` and `flask db downgrade` to verify migrations.

**Acceptance criteria**: `flask db upgrade` creates the schema. `app.py` no longer calls `db.create_all()` in production.

**Effort**: Medium

---

## Phase 4: Production readiness and strategic work (3-6 months)

Phase 4 prepares the application for a real production environment and explores larger architectural changes.

### 4.1 Add production WSGI entry point

**Why it matters**: `app.run(debug=True)` is not safe or performant for production.

**Scope**: `wsgi.py`, `requirements.txt`, `README.md`, `Dockerfile` (optional)

**Checklist**
- [ ] Add `gunicorn` to `requirements.txt`.
- [ ] Create `wsgi.py` with `from app import create_app; application = create_app("production")`.
- [ ] Document the production command: `gunicorn -w 4 -b 0.0.0.0:8000 wsgi:application`.
- [ ] (Optional) Add `Dockerfile` and `docker-compose.yml` for local development and deployment.
- [ ] Add a CI smoke test that starts the WSGI container and hits `/`.

**Acceptance criteria**: `gunicorn wsgi:application` starts without errors and serves the app.

**Effort**: Small

---

### 4.2 Move long-running operations to a background queue

**Why it matters**: Email sending, PDF generation, and AI generation can block the request and cause timeouts.

**Scope**: `services/email.py`, `services/pdf.py`, `services/ai.py`, `extensions.py`, `requirements.txt`

**Checklist**
- [ ] Add `celery` or `rq` to `requirements.txt` and a broker (Redis).
- [ ] Create `tasks.py` with Celery/RQ tasks for `send_email`, `generate_pdf`, `generate_ai_content`.
- [ ] Update `services/email.py` to queue emails instead of sending synchronously.
- [ ] Update PDF generation to queue large exports and return a download link or send by email.
- [ ] Add a local dev fallback that runs tasks synchronously when the broker is not available.
- [ ] Document how to run the worker.

**Acceptance criteria**: AI/PDF/email endpoints no longer block the request. A worker process handles the tasks.

**Effort**: Large

---

### 4.3 Build a production-ready Tailwind CSS bundle

**Why it matters**: Loading Tailwind from a CDN is convenient for development but not ideal for production (slower, no purge, offline issues).

**Scope**: `templates/base.html`, `package.json`, `static/css/` (new), build scripts

**Checklist**
- [ ] Add `package.json` with `@tailwindcss/cli` or `tailwindcss`.
- [ ] Create `static/css/input.css` with `@import "tailwindcss"` and the theme variables.
- [ ] Configure `tailwind.config.js` (or CSS-based config) for the project.
- [ ] Add npm scripts `build:css` and `watch:css`.
- [ ] Update `templates/base.html` to load `{{ url_for('static', filename='css/main.css') }}` instead of the CDN.
- [ ] Update CI to build CSS before running tests.
- [ ] Update `README.md` with build instructions.

**Acceptance criteria**: `npm run build:css` produces a minified `static/css/main.css`. The app works without internet CSS.

**Effort**: Medium

---

### 4.4 Add audit logging and an admin dashboard

**Why it matters**: Student council data changes need to be traceable for accountability and review.

**Scope**: `models/audit.py`, `routes/`, `services/`, `templates/admin/`

**Checklist**
- [ ] Create `models/audit.py` with `AuditLog` (timestamp, user_id, action, entity_type, entity_id, changes).
- [ ] Add a `log_action` helper in `services/base.py`.
- [ ] Log every create, update, delete, status change, and PDF generation.
- [ ] Add an admin route `/admin/audit-log` restricted to users with `Admin` role.
- [ ] Create a paginated audit log template for admins.
- [ ] Add tests verifying audit records are created on key actions.

**Acceptance criteria**: Every state-changing action creates an `AuditLog` record. Admins can view the log.

**Effort**: Large

---

### 4.5 Evaluate API + SPA architecture

**Why it matters**: A REST API would enable future mobile apps, integrations, and a more interactive frontend.

**Scope**: `api/` (new), `templates/` (future), research

**Checklist**
- [ ] Document current data flows and identify REST resource boundaries.
- [ ] Prototype `api/v1/concept_papers` using Flask-RESTX or Flask-Smorest.
- [ ] Add JWT or session-based API authentication.
- [ ] Decide whether to migrate the entire UI or keep server-rendered pages for the MVP.
- [ ] Create an architecture decision record (ADR) in `docs/adr/001-api-vs-ssr.md`.

**Acceptance criteria**: A decision is documented and, if approved, a small API prototype is available.

**Effort**: Large (research/prototype), Extra Large (full migration)

---

### 4.6 Introduce a database abstraction layer

**Why it matters**: The application currently depends on SQLAlchemy directly in routes and services. A repository-style abstraction makes the system database-agnostic, easier to unit test, and smoother to migrate to FastAPI or another backend later.

**Scope**: `models/base.py`, `repositories/` (new), `services/` (new), `routes/*.py`, `config/config.py`

**Checklist**
- [ ] Define a repository protocol / interface for each entity (create, read, update, delete, list).
- [ ] Implement SQLAlchemy-backed repositories in `repositories/` (e.g., `repositories/concept_papers.py`).
- [ ] Move all direct `db.session.query`, `db.session.add`, and `db.session.commit` calls out of routes and services into repositories.
- [ ] Keep SQLAlchemy imports confined to the repository layer; business logic should operate on plain models / Pydantic DTOs.
- [ ] Add configuration to support any SQLAlchemy-compatible engine (MySQL, PostgreSQL, SQLite) without changing route/service code.
- [ ] Add integration tests that can swap the repository to an in-memory SQLite implementation.
- [ ] Update `ARCHITECTURE.md` and `README.md` with the repository pattern.

**Acceptance criteria**: The application can connect to a different SQLAlchemy-compatible database without any changes to routes or services. All existing tests pass.

**Effort**: Large

---

### 4.7 Migrate to React + TypeScript frontend and FastAPI backend

**Why it matters**: A modern React frontend with TypeScript provides type-safe UI components and a better development experience, while FastAPI offers high-performance async endpoints and automatic OpenAPI documentation. This also fully decouples the frontend from the backend.

**Scope**: New `frontend/` with React + TypeScript + Tailwind CSS, new `api/` with FastAPI, `services/`, `repositories/`, `config/`

**Checklist**
- [ ] Complete Phase 4.6 (database abstraction layer) and Phase 4.5 (API/SPA evaluation) before starting.
- [ ] Set up FastAPI project structure (`api/main.py`, `api/routers/`, `api/services/`, `api/repositories/`).
- [ ] Create Pydantic request/response models for all resources (users, events, concept papers, documents, financial reports, meetings, board resolutions).
- [ ] Reimplement authentication and authorization with FastAPI dependencies and JWT tokens.
- [ ] Reimplement all routes as REST endpoints under `/api/v1/`.
- [ ] Create a React frontend with TypeScript and Vite (or a similar build tool).
- [ ] Port templates to React components/pages, preserving the Tailwind CSS 4 design system and existing macro behavior.
- [ ] Build shared React components (Button, Card, Input, Select, etc.) to replace the Jinja2 macro system.
- [ ] Add an API client layer (e.g., TanStack Query, Axios, or `fetch` wrappers) with TypeScript types.
- [ ] Update CI/CD to build the frontend and run the FastAPI backend.
- [ ] Update `README.md`, `ARCHITECTURE.md`, and `DESIGN.md` to document the new stack.
- [ ] Add end-to-end tests for the most critical user flows.

**Acceptance criteria**: The React + FastAPI implementation has feature parity with the current Flask server-rendered application, all existing functionality is preserved, and tests pass.

**Effort**: Extra Large

---

## Appendix: Decision log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-07-09 | Use service layer for business logic | `routes/concept_papers.py` is too large and mixes concerns |
| 2026-07-09 | Use Flask-WTF for forms | Tight integration with Jinja2 and built-in CSRF |
| 2026-07-09 | Keep server-side rendering for now | Faster to secure current UI; evaluate API separately |
| 2026-07-09 | Introduce a database abstraction layer | Makes the system database-agnostic and eases migration to FastAPI |
| 2026-07-09 | Migrate frontend to React + TypeScript + Tailwind CSS and backend to FastAPI | Modern type-safe stack, decoupled API, and better scalability |

## Appendix: Definition of done

For each recommendation:
- Code is merged into the main branch.
- Tests pass (`pytest -q`).
- Relevant documentation (`README.md`, `ARCHITECTURE.md`, `HAND-OVER.md`) is updated if behavior changed.
- A brief note is added to this roadmap's changelog section.

## Changelog

- **2026-07-09**: Created initial roadmap from `docs/IMPROVEMENT_ANALYSIS.md`.
- **2026-07-09**: Added database abstraction layer and React + TypeScript + FastAPI migration to Phase 4.
