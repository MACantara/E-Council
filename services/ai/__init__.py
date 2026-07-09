"""AI abstraction layer for E-Council."""

from .errors import AIError
from .generation import (
    generate_concept_paper_body,
    generate_concept_paper_consent,
    generate_concept_paper_descriptions,
    generate_concept_paper_learning_outcomes,
    generate_concept_paper_objectives,
    generate_concept_paper_participants,
)
from .protocol import AIProvider
from .providers import (
    AnthropicProvider,
    GeminiProvider,
    LocalAIProvider,
    MockAIProvider,
    OpenAIProvider,
)
from .service import generate_content, get_ai, upload_file

__all__ = [
    "AIProvider",
    "AIError",
    "GeminiProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "LocalAIProvider",
    "MockAIProvider",
    "get_ai",
    "generate_content",
    "upload_file",
    "generate_concept_paper_body",
    "generate_concept_paper_descriptions",
    "generate_concept_paper_objectives",
    "generate_concept_paper_learning_outcomes",
    "generate_concept_paper_participants",
    "generate_concept_paper_consent",
]
