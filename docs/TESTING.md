# E-Council Testing Documentation

## Testing Infrastructure Overview

This document describes the testing infrastructure for the E-Council application. The suite covers both the Flask server-rendered UI and the FastAPI REST API, plus the service, repository, and seeding layers.

## Test Structure

### Flask tests (`tests/`)

```
tests/
├── __init__.py
├── conftest.py                  # Shared Flask test fixtures and app setup
├── factories.py                 # Shared factory-boy factories
├── services/
│   └── test_ai_service.py       # AI service and provider abstraction tests
├── test_ai.py                   # AI generation route tests (mock provider)
├── test_api.py                  # API/client tests
├── test_audit.py                # Audit logging tests
├── test_authorization.py        # Authorization and role tests
├── test_cloudinary.py           # Cloudinary backend tests (mocked)
├── test_config.py               # Configuration tests
├── test_email.py                # Email abstraction tests
├── test_logging.py              # Logging tests
├── test_pagination.py           # Pagination helpers and schemas
├── test_pdf_generation.py       # PDF generation tests
├── test_rate_limiting.py        # Rate limiting tests
├── test_repositories.py         # Repository abstraction integration tests
├── test_routes.py               # Basic route tests
├── test_routes_crud.py          # CRUD route tests
├── test_seeds.py                # Idempotent seed script integration tests
├── test_security.py             # Security header / CSRF tests
├── test_signup.py               # Signup tests
├── test_storage.py              # Storage backend tests
└── test_utils.py                # Utility and filter tests
```

### FastAPI tests (`api/tests/`)

```
api/tests/
├── __init__.py
├── conftest.py                  # FastAPI fixtures (client, DB, auth, admin)
├── test_account.py              # Account endpoints
├── test_admin.py                # Admin endpoints
├── test_auth.py                 # Auth endpoints
├── test_board_resolutions.py    # Board resolutions endpoints
├── test_concept_papers.py       # Concept papers endpoints
├── test_dashboard.py            # Dashboard endpoints
├── test_documentation.py        # Documentation endpoints
├── test_events.py               # Events endpoints
├── test_financial.py            # Financial report endpoints
├── test_infrastructure.py       # Shared infrastructure tests
├── test_integration.py          # End-to-end API flow
└── test_meetings.py             # Meeting minutes endpoints
```

## Test Coverage

The current suite covers:

- **Configuration**: Base, development, production, testing, database, email, storage, AI, and login config classes.
- **Repositories**: `BaseRepository`, `repo`, `get_repository()`, and `UserRepository` with an in-memory SQLite database.
- **Services**: AI generation, storage backends (memory/local/Cloudinary), email backends, and service-layer PDF helpers.
- **Routes**: Flask route accessibility, CRUD, authentication, authorization, security, and CSRF.
- **FastAPI**: Auth, account, admin, and all feature routers plus end-to-end integration.
- **Seeds**: Idempotent `seeds/` package and `seed.py` CLI with `--force` protection.
- **Utilities**: Jinja2 filters, helper functions, pagination, and audit logging.

> **Current status**: `pytest -q` passes approximately **397 tests** with 1 skipped.

## Test Fixtures

### Flask (`tests/conftest.py`)

- `app_config` — Configures the Flask app for testing with an in-memory SQLite database and `WTF_CSRF_ENABLED = False`.
- `client` — Flask test client for route testing.
- `app_context` — Application and database context for model operations.
- `sample_user` — Creates a sample user with an associated department and password.
- `factories.py` — `factory_boy` factories for `Users`, `Departments`, `Events`, `ConceptPaperForms`, `Signatories`, etc. shared by tests and seed scripts.

### FastAPI (`api/tests/conftest.py`)

- `fastapi_client` — `TestClient` for the FastAPI app.
- `fastapi_db` — In-memory SQLite database, created/dropped per test.
- `authenticated_client` — Logged-in user client with valid JWT access token.
- `admin_user` — Admin-role user for elevated-permission tests.

## Running Tests

### Prerequisites

```bash
pip install -r requirements.txt
```

### Run the full suite

```bash
pytest
```

`pytest.ini` discovers both `tests/` and `api/tests/`.

### Run with a short summary

```bash
pytest -q
```

### Run Flask tests only

```bash
pytest tests/
```

### Run FastAPI tests only

```bash
pytest api/tests/
```

### Run a specific test file

```bash
pytest tests/test_seeds.py -v
pytest api/tests/test_auth.py -v
```

### Run a specific test

```bash
pytest tests/test_utils.py::test_safe_decimal_conversion_valid -v
pytest api/tests/test_auth.py::test_login -v
```

### Run with coverage

```bash
pytest tests/ api/tests/ --cov=. --cov-report=html
```

## Test Dependencies

### Core
- `pytest`
- `pytest-cov`
- `pytest-flask`
- `factory_boy`

### Application
- `Flask`, `Flask-SQLAlchemy`, `Flask-Migrate`, `Flask-Login`, `Flask-Mail`, `Flask-WTF`
- `FastAPI`, `uvicorn`, `httpx`, `pydantic`
- `SQLAlchemy`, `pymysql`
- `Werkzeug`, `itsdangerous`, `markupsafe`, `python-dotenv`
- `google-genai`, `openai`, `anthropic` (optional AI providers)
- `cloudinary` (optional storage provider)
- `reportlab`, `pandas` (PDF / data helpers)

## Test Categories

### Unit Tests
- Utility functions and Jinja2 filters
- Configuration classes and environment variable loading
- Repository helpers and factory definitions

### Integration Tests
- Flask routes and CRUD flows
- FastAPI endpoints and dependencies
- Database operations via the repository layer
- Email, storage, and AI backend factories

### End-to-End Tests
- FastAPI `test_integration.py` exercises a full user/feature workflow
- Seed scripts populate a realistic demo dataset

## CI Setup

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest -q
      - name: Upload coverage
        uses: codecov/codecov-action@v4
```

## Troubleshooting

### Import errors
Run `pip install -r requirements.txt` and ensure the virtual environment is active.

### Database errors
Tests use in-memory SQLite by default; verify `SQLALCHEMY_DATABASE_URI` is not set to a production database.

### Missing fixtures
Ensure `conftest.py` exists in `tests/` and `api/tests/` and that `pytest.ini` includes `testpaths = tests api/tests`.

### Missing env vars
The test config provides defaults for most values. Set `SECRET_KEY`, `SQLALCHEMY_DATABASE_URI`, and `MAIL_DEFAULT_SENDER` in `.env` if needed.

### AI tests fail offline
Set `AI_PROVIDER=mock` in `.env` or in the test environment to run without external API keys.

### Cloudinary tests fail
Tests mock Cloudinary by default; verify `STORAGE_PROVIDER=memory` or `null` for unit tests.

## Conclusion

The test suite now covers Flask, FastAPI, service abstractions, repository layer, seeding, and utility modules. It is the primary safety net for the Phase 4 migration and should be run before every commit.

### Next Steps
1. Run `pytest -q` before each commit.
2. Add FastAPI tests for any new router or schema.
3. Add Flask tests for any new legacy UI route.
4. Keep `factories.py` in sync with new models.
5. Integrate coverage reporting with CI/CD.