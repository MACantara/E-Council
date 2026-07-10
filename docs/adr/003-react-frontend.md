# ADR 003: React + TypeScript SPA Frontend

## Status

Accepted

## Context

After the FastAPI backend was established as the primary API, the server-rendered Jinja2 UI became a transitional surface. The project needed a modern frontend that could consume the `/api/v1/` endpoints and support the full feature set without maintaining duplicate route logic.

## Decision

We selected **React 19 + TypeScript 6** with Vite, Tailwind CSS 4, React Router v7, TanStack Query, and Axios for the new SPA frontend in `frontend/`.

## Consequences

- **Pros**: Component-based UI, typed API clients, shared Tailwind token system, clean separation of concerns, and easier future enhancements (PWA, real-time, etc.).
- **Cons**: Two UIs coexist during the soak period; the legacy `templates/` directory still exists but is deprecated and will be removed once the React SPA is fully verified.

## Migration notes

- The Jinja2/Tailwind templates remain functional during the transition.
- New feature work targets the React SPA and FastAPI endpoints.
- The legacy UI is removed from `docs/ROADMAP.md` as a future cleanup task.
