"""AI service factory and high-level API."""

from __future__ import annotations

from typing import Any

from flask import current_app

from config import AIConfig
from services.base import ServiceResult


class _AIConfigProxy:
    """A Flask-like config object for AI provider settings.

    Uses the current Flask app config when available, otherwise falls back to
    the shared ``AIConfig`` class so the AI service can be used from FastAPI or
    other non-Flask contexts.
    """

    def __init__(self):
        try:
            self.config = current_app.config
        except RuntimeError:
            self.config = {k: v for k, v in vars(AIConfig).items() if not k.startswith("_")}

    def get(self, key, default=None):
        if isinstance(self.config, dict):
            return self.config.get(key, default)
        return self.config.get(key, default)

    def __getitem__(self, key):
        if isinstance(self.config, dict):
            return self.config[key]
        return self.config[key]

    def __contains__(self, key):
        if isinstance(self.config, dict):
            return key in self.config
        return key in self.config


from .errors import AIError
from .protocol import AIProvider
from .providers import (
    AnthropicProvider,
    GeminiProvider,
    LocalAIProvider,
    MockAIProvider,
    OpenAIProvider,
)

PROVIDER_MAP: dict[str, type[AIProvider]] = {
    "gemini": GeminiProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "local": LocalAIProvider,
    "mock": MockAIProvider,
}


def get_ai(app=None):
    """Return the configured AI provider.

    Args:
        app: Optional Flask app or config-like object. Defaults to the current
            Flask app when available, otherwise ``AIConfig``.

    Returns:
        An AIProvider instance.
    """
    if app is None:
        config = _AIConfigProxy()
    else:
        config = getattr(app, "config", app)

    if "AI_BACKEND" in config:
        return config["AI_BACKEND"]

    provider = config.get("AI_PROVIDER", AIConfig.AI_PROVIDER)
    provider_class = PROVIDER_MAP.get(provider)
    if provider_class is None:
        raise AIError(f"Unknown AI provider: {provider}")

    return provider_class(**_provider_kwargs(config, provider))


def _provider_kwargs(app, provider: str) -> dict[str, Any]:
    if provider == "gemini":
        return {
            "api_key": app.get("GOOGLE_GEMINI_AI_API_KEY", AIConfig.GOOGLE_GEMINI_AI_API_KEY),
            "model": app.get("GEMINI_MODEL", AIConfig.GEMINI_MODEL),
        }
    if provider == "openai":
        return {
            "api_key": app.get("OPENAI_API_KEY", AIConfig.OPENAI_API_KEY),
            "model": app.get("OPENAI_MODEL", AIConfig.OPENAI_MODEL),
        }
    if provider == "anthropic":
        return {
            "api_key": app.get("ANTHROPIC_API_KEY", AIConfig.ANTHROPIC_API_KEY),
            "model": app.get("ANTHROPIC_MODEL", AIConfig.ANTHROPIC_MODEL),
        }
    if provider == "local":
        return {
            "base_url": app.get("LOCAL_AI_BASE_URL", AIConfig.LOCAL_AI_BASE_URL),
            "model": app.get("LOCAL_AI_MODEL", AIConfig.LOCAL_AI_MODEL),
        }
    if provider == "mock":
        return {"response": app.get("MOCK_AI_RESPONSE", AIConfig.MOCK_AI_RESPONSE)}
    return {}


def generate_content(contents: str | list[Any], *, model: str | None = None) -> ServiceResult:
    """Generate content using the configured AI provider.

    Args:
        contents: The prompt or list of content parts.
        model: Optional model override.

    Returns:
        A ServiceResult with the generated text.
    """
    try:
        provider = get_ai()
        prompt = contents if isinstance(contents, str) else str(contents)
        text = provider.generate_text(prompt, model=model)
        if text:
            return ServiceResult.ok(text.strip())
        return ServiceResult.fail("Invalid response from AI model")
    except Exception as exc:  # noqa: BLE001
        return ServiceResult.fail(str(exc))


def upload_file(file_path: str) -> ServiceResult:
    """Upload a file using the configured AI provider.

    Args:
        file_path: Path to the file.

    Returns:
        A ServiceResult with the provider file reference.
    """
    try:
        provider = get_ai()
        uploaded = provider.upload_file(file_path)
        return ServiceResult.ok(uploaded)
    except Exception as exc:  # noqa: BLE001
        return ServiceResult.fail(str(exc))
