# ADR 004: Service Abstractions for AI, Email, and Storage

## Status

Accepted

## Context

The application depends on multiple external providers for AI generation, email delivery, and file storage. Hard-coding specific providers (e.g., Google Gemini, Gmail SMTP, Cloudinary) inside route handlers made the system brittle and difficult to test or swap.

## Decision

We introduced a service abstraction layer under `services/`:

- `services/ai/` — protocol, provider implementations (Gemini, OpenAI, Anthropic, local, mock), and a unified `AIService`.
- `services/email/` — protocol, backend implementations (SMTP, in-memory, null), and `EmailService`.
- `services/storage/` — protocol, backend implementations (memory, local, Cloudinary), and `StorageService`.

Each service is initialized via a factory or config and selected by environment variables (`AI_PROVIDER`, `EMAIL_PROVIDER`, `STORAGE_PROVIDER`).

## Consequences

- **Pros**: Both Flask and FastAPI can reuse the same backends; tests can use `mock`/`memory` providers; swapping providers is a config change.
- **Cons**: Slightly more indirection; new providers must implement the protocol.

## Notes

- `mock` AI and `memory` email/storage are used by default in tests.
- Local/Cloudinary storage keys are in `.env.example`.
