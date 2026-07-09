"""
Base service layer for E-Council.

Provides a generic ServiceResult pattern so services can return either a
successful payload or a user-friendly error message without raising HTTP
exceptions.
"""

from dataclasses import dataclass
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass
class ServiceResult(Generic[T]):
    """Result of a service operation.

    Attributes:
        success: True if the operation succeeded.
        data: Payload returned on success (may be None).
        error: Human-readable error message returned on failure.
    """

    success: bool
    data: T | None = None
    error: str | None = None

    def __bool__(self) -> bool:
        return self.success

    @classmethod
    def ok(cls, data: T | None = None) -> "ServiceResult[T]":
        """Create a successful result."""
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, message: str) -> "ServiceResult[Any]":
        """Create a failed result with an error message."""
        return cls(success=False, error=message)
