"""Tests for the shared FastAPI infrastructure added in Phase 4.11."""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from api.dependencies import (
    check_ownership,
    get_pagination_params,
    get_storage,
    is_admin,
    require_admin,
    require_role,
)
from api.exceptions import NotFoundError
from api.repositories.base import APIBaseRepository
from api.schemas.auth import UserResponse
from api.schemas.common import (
    OrderEnum,
    PaginatedResponse,
    PaginationMetadata,
    PaginationParams,
    ResponseEnvelope,
    build_pagination_metadata,
)
from services.storage import MemoryStorage


class TestCommonSchemas:
    """Reusable Pydantic schemas and response wrappers."""

    def test_response_envelope(self):
        """Response envelopes wrap arbitrary data with a success flag."""
        envelope = ResponseEnvelope[UserResponse](data=None)
        assert envelope.success is True
        assert envelope.data is None

    def test_paginated_response(self):
        """Paginated responses include items and metadata."""
        metadata = build_pagination_metadata(total=50, page=2, per_page=20)
        response = PaginatedResponse[UserResponse](
            items=[],
            pagination=metadata,
        )
        assert response.pagination.total == 50
        assert response.pagination.page == 2
        assert response.pagination.pages == 3

    def test_pagination_params_defaults(self):
        """Pagination defaults are sane and page/per_page are validated."""
        params = get_pagination_params(
            page=1,
            per_page=20,
            sort=None,
            order=OrderEnum.asc,
            search=None,
        )
        assert params.page == 1
        assert params.per_page == 20
        assert params.order.value == "asc"

    def test_pagination_params_model_defaults(self):
        """PaginationParams model defaults match the expected values."""
        params = PaginationParams()
        assert params.page == 1
        assert params.per_page == 20
        assert params.order.value == "asc"

    def test_pagination_params_custom(self):
        """Pagination parameters can be overridden."""
        params = PaginationParams(page=3, per_page=10, sort="created_at", order="desc", search="hello")
        assert params.page == 3
        assert params.per_page == 10
        assert params.sort == "created_at"
        assert params.order.value == "desc"
        assert params.search == "hello"


class TestDependencies:
    """Shared FastAPI dependencies."""

    def test_get_storage(self):
        """The storage dependency resolves to the configured backend."""
        backend = get_storage()
        assert isinstance(backend, MemoryStorage)

    def test_is_admin(self):
        """is_admin checks the Admin role."""
        user = MagicMock(users_role="Admin")
        assert is_admin(user) is True
        user.users_role = "Student Council Officer"
        assert is_admin(user) is False

    def test_require_admin(self):
        """require_admin returns the user for admins and raises for others."""
        admin = MagicMock(users_role="Admin")
        assert require_admin(admin) is admin

        non_admin = MagicMock(users_role="Student Council Officer")
        with pytest.raises(HTTPException) as exc:
            require_admin(non_admin)
        assert exc.value.status_code == 403

    def test_require_role_factory(self):
        """require_role enforces one of the allowed roles."""
        staff = MagicMock(users_role="Staff")
        dep = require_role("Admin", "Staff")
        assert dep(staff) is staff

        faculty = MagicMock(users_role="Faculty")
        with pytest.raises(HTTPException) as exc:
            dep(faculty)
        assert exc.value.status_code == 403

    def test_check_ownership(self):
        """check_ownership allows owners and admins."""
        owner = MagicMock(users_id=1, users_role="Student Council Officer")
        check_ownership(owner, 1)

        admin = MagicMock(users_id=2, users_role="Admin")
        check_ownership(admin, 1)

        other = MagicMock(users_id=3, users_role="Student Council Officer")
        with pytest.raises(HTTPException) as exc:
            check_ownership(other, 1)
        assert exc.value.status_code == 403


class TestAPIBaseRepository:
    """FastAPI repository wrapper."""

    def test_get_or_404_raises_api_not_found(self):
        """APIBaseRepository.get_or_404 raises a NotFoundError on missing records."""
        repo = APIBaseRepository(model=MagicMock(__name__="Thing"))
        repo.get = MagicMock(return_value=None)
        with pytest.raises(NotFoundError) as exc:
            repo.get_or_404(999)
        assert exc.value.status_code == 404
        assert "Thing not found" in exc.value.detail

    def test_get_or_404_returns_record(self):
        """APIBaseRepository.get_or_404 returns the record when found."""
        record = MagicMock()
        repo = APIBaseRepository(model=MagicMock(__name__="Thing"))
        repo.get = MagicMock(return_value=record)
        assert repo.get_or_404(1) is record


class TestExceptionHandlers:
    """Global exception handlers."""

    def test_validation_error_response(self, fastapi_client):
        """Validation errors return the shared JSON error format."""
        response = fastapi_client.post("/api/v1/auth/login", json={})
        assert response.status_code == 422
        body = response.json()
        assert body["success"] is False
        assert "detail" in body
        assert "errors" in body


class TestAuthenticatedClient:
    """Shared authenticated test client fixture."""

    def test_authenticated_client_can_access_me(self, authenticated_client, fastapi_user):
        """The authenticated client can access protected endpoints."""
        response = authenticated_client.get("/api/v1/auth/me")
        assert response.status_code == 200
        assert response.json()["users_username"] == fastapi_user["users_username"]
