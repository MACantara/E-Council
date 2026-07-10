"""Shared exception types and FastAPI exception handlers for the API."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

try:
    from werkzeug.exceptions import HTTPException as WerkzeugHTTPException
except ImportError:  # pragma: no cover
    WerkzeugHTTPException = None


class APIError(Exception):
    """Base exception for API errors with an HTTP status code."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: dict[str, str] | None = None,
    ) -> None:
        """Initialize the exception with an HTTP status code and detail."""
        self.status_code = status_code
        self.detail = detail
        self.headers = headers or {}


class BadRequestError(APIError):
    """400 Bad Request."""

    def __init__(self, detail: str = "Bad request", headers: dict[str, str] | None = None) -> None:
        super().__init__(status_code=400, detail=detail, headers=headers)


class UnauthorizedError(APIError):
    """401 Unauthorized."""

    def __init__(self, detail: str = "Unauthorized", headers: dict[str, str] | None = None) -> None:
        super().__init__(status_code=401, detail=detail, headers=headers)


class ForbiddenError(APIError):
    """403 Forbidden."""

    def __init__(self, detail: str = "Forbidden", headers: dict[str, str] | None = None) -> None:
        super().__init__(status_code=403, detail=detail, headers=headers)


class NotFoundError(APIError):
    """404 Not Found."""

    def __init__(self, detail: str = "Resource not found", headers: dict[str, str] | None = None) -> None:
        super().__init__(status_code=404, detail=detail, headers=headers)


class ConflictError(APIError):
    """409 Conflict."""

    def __init__(self, detail: str = "Conflict", headers: dict[str, str] | None = None) -> None:
        super().__init__(status_code=409, detail=detail, headers=headers)


class UnprocessableEntityError(APIError):
    """422 Unprocessable Entity."""

    def __init__(self, detail: str = "Validation error", headers: dict[str, str] | None = None) -> None:
        super().__init__(status_code=422, detail=detail, headers=headers)


def _make_json_serializable(value: Any) -> Any:
    """Recursively convert non-JSON-serializable values to strings."""
    if isinstance(value, dict):
        return {k: _make_json_serializable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_make_json_serializable(v) for v in value]
    if isinstance(value, tuple):
        return [_make_json_serializable(v) for v in value]
    try:
        # If value is not an exception, attempt standard serialization.
        if isinstance(value, BaseException):
            return str(value)
        return value
    except Exception:
        return str(value)


def _error_response(status_code: int, detail: str, errors: list[Any] | None = None) -> dict[str, Any]:
    return {
        "success": False,
        "detail": detail,
        "errors": _make_json_serializable(errors) if errors else [detail],
    }


def register_exception_handlers(app: FastAPI) -> None:
    """Register shared exception handlers on the FastAPI application."""

    @app.exception_handler(APIError)
    async def api_exception_handler(request: Request, exc: APIError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_response(exc.status_code, exc.detail),
            headers=exc.headers,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_response(exc.status_code, exc.detail),
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_error_response(422, "Validation error", exc.errors()),
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_handler(request: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_error_response(422, "Validation error", exc.errors()),
        )

    if WerkzeugHTTPException is not None:

        @app.exception_handler(WerkzeugHTTPException)
        async def werkzeug_exception_handler(request: Request, exc: WerkzeugHTTPException) -> JSONResponse:
            return JSONResponse(
                status_code=exc.code or 500,
                content=_error_response(exc.code or 500, exc.description or "Internal server error"),
            )
