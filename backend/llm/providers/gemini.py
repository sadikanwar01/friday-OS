"""
FRIDAY OS - Gemini Provider.

Implements the BaseLLMProvider interface for the Google Gemini API.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from google import genai
from google.genai import types

from backend.config import get_settings
from backend.llm.providers.base import BaseLLMProvider
from backend.utils.exceptions import ConfigurationError, LLMError
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class GeminiProvider(BaseLLMProvider):
    """LLM Provider implementation for Google Gemini."""

    def __init__(self) -> None:
        self.settings = get_settings()
        api_key = self.settings.gemini_api_key
        if not api_key:
            raise ConfigurationError(
                message="GEMINI_API_KEY is not set in configuration.",
                error_code="GEMINI_MISSING_API_KEY",
            )
        self.client = genai.Client(
            api_key=api_key,
            http_options={'base_url': 'https://generativelanguage.googleapis.com'}
        )

    @property
    def provider_name(self) -> str:
        return "gemini"

    def _convert_messages(
        self, messages: list[dict[str, str]], system_prompt: str | None
    ) -> tuple[list[types.Content], types.GenerateContentConfig]:
        """Convert standard message format to Gemini format."""
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(
                types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])])
            )

        config_kwargs: dict[str, Any] = {}
        if system_prompt:
            config_kwargs["system_instruction"] = system_prompt

        return contents, types.GenerateContentConfig(**config_kwargs)

    async def generate(
        self,
        model: str,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> str:
        contents, config = self._convert_messages(messages, system_prompt)
        config.temperature = temperature

        if kwargs.get("format") == "json" or kwargs.get("json_mode"):
            config.response_mime_type = "application/json"

        try:
            response = await self.client.aio.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
            return response.text or ""
        except Exception as e:
            logger.error("gemini_api_error", error=str(e))
            raise LLMError(
                message=f"Gemini API error: {e}",
                error_code="GEMINI_API_ERROR",
                details={"error": str(e)},
                model=model,
            ) from e

    async def stream(
        self,
        model: str,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        contents, config = self._convert_messages(messages, system_prompt)
        config.temperature = temperature

        try:
            response = await self.client.aio.models.generate_content_stream(
                model=model,
                contents=contents,
                config=config,
            )
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error("gemini_api_stream_error", error=str(e))
            raise LLMError(
                message=f"Gemini API error during stream: {e}",
                error_code="GEMINI_API_ERROR",
                details={"error": str(e)},
                model=model,
            ) from e

    async def health_check(self) -> dict[str, Any]:
        try:
            # We fetch model list or make a tiny test request to verify API key
            model_to_test = self.settings.gemini_model
            await self.client.aio.models.get(model=model_to_test)
            return {"status": "ok", "provider": self.provider_name}
        except Exception as e:
            return {"status": "error", "provider": self.provider_name, "details": str(e)}
