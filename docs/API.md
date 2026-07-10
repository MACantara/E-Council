# E-Council API Documentation

The FastAPI backend is the primary API for the E-Council SPA. It is defined in `api/main.py` and exposes all feature groups under `/api/v1/`.

## Base URL

```
http://localhost:8000
```

All v1 endpoints are prefixed with `/api/v1/`.

## OpenAPI / Swagger

Interactive documentation is generated automatically:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Authentication

The API uses JWT access tokens and refresh tokens.

### Token flow

1. **Register**: `POST /api/v1/auth/register` returns the created user. No token is issued until the email is verified.
2. **Verify email**: `POST /api/v1/auth/verify-email` (or `GET /api/v1/auth/verify-email/{token}`) verifies the email.
3. **Login**: `POST /api/v1/auth/login` returns an `access_token` and `refresh_token`.
4. **Call protected endpoints**: Send the `access_token` in the `Authorization` header as `Bearer <token>`.
5. **Refresh**: `POST /api/v1/auth/refresh` returns a new `access_token` when the old one expires.
6. **Logout**: `POST /api/v1/auth/logout` is a client-side hook to discard tokens.

### Token lifetimes (configurable)

- `ACCESS_TOKEN_EXPIRE_MINUTES` (default: 30)
- `REFRESH_TOKEN_EXPIRE_DAYS` (default: 7)

### Password reset

- `POST /api/v1/auth/forgot-password` sends a reset link.
- `POST /api/v1/auth/reset-password/{selector}/{token}` resets the password.

### Current user

- `GET /api/v1/auth/me` returns the authenticated user profile.

## Common response shape

Successful feature endpoints return a JSON envelope:

```json
{
  "data": { ... },
  "message": "...",
  "success": true
}
```

Paginated list endpoints return:

```json
{
  "data": {
    "items": [ ... ],
    "total": 100,
    "page": 1,
    "per_page": 20,
    "pages": 5
  },
  "message": "...",
  "success": true
}
```

## Feature groups

| Group | Base path | Main operations |
| --- | --- | --- |
| Auth | `/api/v1/auth` | Register, login, refresh, logout, verify, forgot/reset password, me |
| Account | `/api/v1/account` | Profile, change password, update settings, upload profile picture |
| Admin | `/api/v1/admin` | User/department/org management, admin dashboard |
| Dashboard | `/api/v1/dashboard` | Council overview, stats, recent activity |
| Concept Papers | `/api/v1/concept-papers` | CRUD, objectives, learning outcomes, AI generate, PDF |
| Events | `/api/v1/events` | CRUD, transactions, invitations, status |
| Meetings | `/api/v1/meetings` | CRUD, agenda, minutes, attendees, status, PDF |
| Financial Reports | `/api/v1/financial` | CRUD, status, PDF |
| Board Resolutions | `/api/v1/board-resolutions` | CRUD, status, AI generate, PDF |
| Documentation | `/api/v1/documentation` | CRUD, files, related forms, activity report details, PDF |

## Standard CRUD patterns

Most feature groups follow the same pattern:

- `GET /` — list (paginated, sortable, filterable)
- `POST /` — create
- `GET /{id}` — retrieve
- `PUT /{id}` — update
- `DELETE /{id}` — delete
- `PUT /{id}/status` — update status
- `GET /{id}/pdf` — generate/download PDF

## Status codes

- `200 OK` — success
- `201 Created` — resource created
- `400 Bad Request` — validation error
- `401 Unauthorized` — missing or invalid token
- `403 Forbidden` — permission denied
- `404 Not Found` — resource does not exist
- `422 Unprocessable Entity` — request body validation failed
- `500 Internal Server Error` — unexpected server error

## CORS

The FastAPI app is configured to allow the frontend URLs from `FRONTEND_URL` plus common Vite dev ports (`3000`, `5173`, `5174`, `4173`, `4174`). Update `FRONTEND_URL` in `.env` to match the production frontend URL.

## Testing

Run the FastAPI test suite:

```bash
pytest api/tests/
```

See `docs/TESTING.md` for the full testing guide.
