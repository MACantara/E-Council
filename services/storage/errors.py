"""Storage-layer exceptions for E-Council."""


class StorageError(Exception):
    """Raised when a storage backend operation fails."""

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        """Initialize the storage error with an optional wrapped exception."""
        super().__init__(message)
        self.message = message
        self.original_error = original_error
