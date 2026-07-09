# ADR 001: FastAPI + SPA Architecture for E-Council

**Status**: Accepted

**Date**: 2026-07-09

## Context

E-Council is currently a Flask server-rendered application. The existing Phase 4.5 roadmap item asks the team to evaluate a REST API + Single Page Application (SPA) architecture so the platform can support mobile clients, third-party integrations, and a more interactive frontend.

During this evaluation we built a small `api/v1/auth` prototype using FastAPI. The goals of the prototype were:

- Validate FastAPI as a future backend layer.
- Confirm that the existing SQLAlchemy models and a small repository layer can be reused from FastAPI.
- Prove JWT-based authentication can be implemented with Pydantic request/response models.

## Decision

Adopt **FastAPI** for the backend API and **React + TypeScript** for the future frontend.

Keep the Flask server-rendered UI for the MVP, but treat it as a transitional frontend. The FastAPI backend will be developed incrementally alongside the Flask app, starting with the `api/v1/auth` module and expanding resource by resource.

## Rationale

- **FastAPI** provides automatic OpenAPI documentation, Pydantic-native validation, and high-performance async request handling, all of which map cleanly to the repository + Pydantic-DTO direction planned in Phase 4.6.
- **React + TypeScript** gives the project type-safe UI components, a large ecosystem, and a natural path to share the Tailwind CSS 4 design system from the current Jinja2 templates.
- **SQLAlchemy repository layer** can be shared between Flask and FastAPI during the transition, minimizing duplication.
- The current Flask SSR pages remain usable while the API is being built, so the MVP feature set is not blocked by a full migration.

## Consequences

- The prototype adds a new `api/` package and `repositories/` package. These will grow into the new backend structure.
- The Flask routes remain in place but will be gradually replaced by API calls from a React frontend.
- A future migration step will move the React frontend into `frontend/` and eventually retire the Jinja2 templates once parity is reached.
- JWT tokens require secure storage on the frontend (HttpOnly cookies are recommended once the SPA is implemented).

## MVP UI Decision

For the current MVP, the server-rendered Flask templates will continue to be the primary UI. The FastAPI API will be used as a parallel proving ground and for integrations that require JSON endpoints. The full SPA migration will be planned after the repository abstraction layer is complete.
