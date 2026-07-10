# ADR 005: Idempotent Seeding for Development and Demo Data

## Status

Accepted

## Context

The application needed realistic sample data for development, manual QA, and demo deployments. Creating records manually was slow and error-prone, and the existing test fixtures could not be reused by seed scripts.

## Decision

We created a `seeds/` package with idempotent seed scripts and a `seed.py` CLI entry point:

- `tests/factories.py` provides `factory_boy` factories shared by tests and seeds.
- `seeds/core.py` provides `get_session()` and `get_or_create()` helpers.
- `seeds/<domain>.py` create departments, users, signatories, concept papers, events, meetings, financial reports, board resolutions, and documentation.
- `seed.py` runs all seeds, enforces `--force` for production environments, and prints demo credentials.

## Consequences

- **Pros**: Consistent sample data, reusable factories, safe to re-run (`get_or_create` prevents duplicates), and easy demo setup.
- **Cons**: Seed scripts must be updated when model relationships change.

## Notes

- Demo credentials are printed after seeding; the default admin password is `DemoPass123!`.
- Seed tests in `tests/test_seeds.py` verify idempotency and summary counts.
