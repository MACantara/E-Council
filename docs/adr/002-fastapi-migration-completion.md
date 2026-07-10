# ADR 002: FastAPI Migration Completion

**Status**: Accepted

**Date**: 2026-07-10

## Context

E-Council began as a Flask server-rendered application. ADR 001 (2026-07-09) approved the evaluation of a FastAPI + SPA architecture and a feature-by-feature migration of Flask routes to REST endpoints. Between Phases 4.10 and 4.20, every server-rendered feature was migrated to a FastAPI router, shared infrastructure was consolidated, and the FastAPI backend was wired as the primary API.

At the end of Phase 4.20 the codebase has:

- A FastAPI application in `api/main.py` with lifespan-managed startup/shutdown.
- All feature routers registered under `/api/v1/`: auth, account, admin, concept papers, events, meetings, board resolutions, financial, documentation, and dashboard.
- Root (`/`), health (`/health`), and API discovery (`/api/v1/`) endpoints.
- OpenAPI/Swagger docs at `/docs` and ReDoc at `/redoc`.
- Shared JWT dependencies, pagination, file upload, role checks, and exception handling in `api/dependencies.py`, `api/schemas/common.py`, and `api/exceptions.py`.
- Reuse of the existing SQLAlchemy models, repository layer, and `services/storage/`, `services/email/`, and `services/ai/` abstraction layers.
- FastAPI tests in `api/tests/` and end-to-end integration coverage in `api/tests/test_integration.py`.

## Decision

Complete the FastAPI backend migration and make it the primary API for the application. The Flask server-rendered UI remains operational as the current frontend while the React + TypeScript frontend is built in Phase 4.21.

## Rationale

- **Feature parity**: Every Flask route now has a corresponding FastAPI endpoint, so the backend can serve a future SPA without duplicated business logic.
- **Automatic API documentation**: FastAPI generates OpenAPI schemas, which simplifies frontend integration and third-party API consumers.
- **Pydantic validation**: Request/response models enforce contracts and reduce validation boilerplate.
- **Shared abstractions**: The existing storage, email, and AI service layers work unchanged from FastAPI, minimizing code duplication and risk.
- **Safe transition**: Running Flask and FastAPI in parallel during the React frontend build protects the existing UI and user workflows.

## Consequences

- The `api/` package becomes a first-class backend entry point alongside `app.py`.
- CI now runs both the Flask and FastAPI smoke tests and the full `pytest` suite (Flask + FastAPI tests).
- New features should be added to `api/routers/` and `api/schemas/`; the Flask blueprints are maintained only for the current server-rendered UI.
- `README.md`, `ARCHITECTURE.md`, and `DESIGN.md` reflect the dual-backend/frontend setup.
- The next architectural step (Phase 4.21) is a React + TypeScript frontend that consumes the FastAPI backend.

## Migration Notes

- `api/settings.py` and `api/database.py` allow FastAPI to run without a Flask app context by reading environment variables and `DatabaseConfig` directly.
- `services/ai/service.py` was updated to honor runtime environment variables in the FastAPI fallback path so tests can switch AI providers without re-importing modules.
- All FastAPI tests use an in-memory SQLite database and the `mock` AI provider, making the suite deterministic and network-free.
