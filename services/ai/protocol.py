"""AI provider protocol."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AIProvider(ABC):
    """Abstract protocol for AI providers."""

    @abstractmethod
    def generate_text(self, prompt: str, *, model: str | None = None) -> str:
        """Generate text from a single prompt.

        Args:
            prompt: The user prompt.
            model: Optional model override.

        Returns:
            The generated text.
        """
        raise NotImplementedError

    @abstractmethod
    def upload_file(self, file_path: str) -> Any:
        """Upload a file to the provider and return a reference.

        Args:
            file_path: Path to the file to upload.

        Returns:
            A provider-specific file reference.
        """
        raise NotImplementedError
