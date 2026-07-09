"""AI provider implementations."""

from __future__ import annotations

from typing import Any

from flask import current_app

from .protocol import AIProvider


class GeminiProvider(AIProvider):
    """Google Gemini provider adapter."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key
        self.model = model

    def _client(self):
        from google import genai

        api_key = self.api_key or (current_app.config.get("GOOGLE_GEMINI_AI_API_KEY") if current_app else None)
        return genai.Client(api_key=api_key)

    def _safety_settings(self):
        from google.genai import types

        return [
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
        ]

    def _generate_config(self):
        from google.genai import types

        return types.GenerateContentConfig(safety_settings=self._safety_settings())

    def generate_text(self, prompt: str, *, model: str | None = None) -> str:
        """Generate text using Google Gemini."""
        response = self._client().models.generate_content(
            model=model or self.model or (current_app.config.get("GEMINI_MODEL") if current_app else None),
            contents=prompt,
            config=self._generate_config(),
        )
        if response and response.text:
            return response.text.strip()
        return ""

    def upload_file(self, file_path: str) -> Any:
        """Upload a file to Google Gemini."""
        return self._client().files.upload(file=file_path)


class OpenAIProvider(AIProvider):
    """OpenAI provider adapter."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key
        self.model = model

    def _client(self):
        import openai

        api_key = self.api_key or (current_app.config.get("OPENAI_API_KEY") if current_app else None)
        return openai.OpenAI(api_key=api_key)

    def generate_text(self, prompt: str, *, model: str | None = None) -> str:
        """Generate text using OpenAI."""
        response = self._client().chat.completions.create(
            model=model or self.model or (current_app.config.get("OPENAI_MODEL") if current_app else None),
            messages=[{"role": "user", "content": prompt}],
        )
        if response and response.choices:
            content = response.choices[0].message.content
            return content.strip() if content else ""
        return ""

    def upload_file(self, file_path: str) -> Any:
        """OpenAI file upload is not implemented."""
        raise NotImplementedError("upload_file is not supported for the OpenAI provider")


class AnthropicProvider(AIProvider):
    """Anthropic provider adapter."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key
        self.model = model

    def _client(self):
        import anthropic

        api_key = self.api_key or (current_app.config.get("ANTHROPIC_API_KEY") if current_app else None)
        return anthropic.Anthropic(api_key=api_key)

    def generate_text(self, prompt: str, *, model: str | None = None) -> str:
        """Generate text using Anthropic."""
        response = self._client().messages.create(
            model=model or self.model or (current_app.config.get("ANTHROPIC_MODEL") if current_app else None),
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        if response and response.content:
            return response.content[0].text.strip()
        return ""

    def upload_file(self, file_path: str) -> Any:
        """Anthropic file upload is not implemented."""
        raise NotImplementedError("upload_file is not supported for the Anthropic provider")


class MockAIProvider(AIProvider):
    """No-op AI provider for tests and offline development."""

    def __init__(self, response: str = "Generated AI content") -> None:
        self.response = response

    def generate_text(self, prompt: str, *, model: str | None = None) -> str:
        """Return the configured response."""
        return self.response

    def upload_file(self, file_path: str) -> Any:
        """Return a simple dict reference."""
        return {"file_path": file_path, "mime_type": None}


class LocalAIProvider(AIProvider):
    """Local/Ollama provider adapter for development and self-hosting."""

    def __init__(self, base_url: str | None = None, model: str | None = None) -> None:
        self.base_url = base_url
        self.model = model

    def _client(self):
        import openai

        base_url = self.base_url or (current_app.config.get("LOCAL_AI_BASE_URL") if current_app else None)
        return openai.OpenAI(base_url=base_url, api_key="no-key")

    def generate_text(self, prompt: str, *, model: str | None = None) -> str:
        """Generate text from a local OpenAI-compatible endpoint."""
        response = self._client().chat.completions.create(
            model=model or self.model or (current_app.config.get("LOCAL_AI_MODEL") if current_app else None),
            messages=[{"role": "user", "content": prompt}],
        )
        if response and response.choices:
            content = response.choices[0].message.content
            return content.strip() if content else ""
        return ""

    def upload_file(self, file_path: str) -> Any:
        """Local file upload is not implemented."""
        raise NotImplementedError("upload_file is not supported for the local AI provider")
