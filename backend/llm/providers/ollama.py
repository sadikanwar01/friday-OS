"""
FRIDAY OS - Ollama Provider.

Implements the BaseLLMProvider interface for the local Ollama service.
Supports the OpenAI-compatible `/api/chat` endpoint logic, parsing streaming JSON lines.
"""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from typing import Any

import httpx

from backend.config import get_settings
from backend.llm.providers.base import BaseLLMProvider
from backend.utils.exceptions import LLMError
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class OllamaProvider(BaseLLMProvider):
    """LLM Provider implementation for Ollama."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_url = self.settings.ollama_base_url.rstrip("/")
        self.timeout = self.settings.ollama_timeout
        self.client = httpx.AsyncClient(timeout=self.timeout)

    @property
    def provider_name(self) -> str:
        return "ollama"

    def _prepare_payload(
        self,
        model: str,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        stream: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Format the payload for the Ollama /api/chat endpoint."""
        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        formatted_messages.extend(messages)

        payload = {
            "model": model,
            "messages": formatted_messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
            },
        }

        # Merge any additional options like JSON mode
        if kwargs.get("json_mode"):
            payload["format"] = "json"

        return payload

    async def generate(
        self,
        model: str,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> str:
        payload = self._prepare_payload(
            model=model,
            messages=messages,
            system_prompt=system_prompt,
            temperature=temperature,
            stream=False,
            **kwargs,
        )

        url = f"{self.base_url}/api/chat"
        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]
        except httpx.HTTPStatusError as e:
            logger.error(
                "ollama_http_error", status_code=e.response.status_code, error=e.response.text
            )
            raise LLMError(
                message=f"Ollama returned HTTP error: {e.response.status_code}",
                error_code="OLLAMA_HTTP_ERROR",
                details={"status": e.response.status_code, "text": e.response.text},
                model=model,
            ) from e
        except httpx.RequestError as e:
            logger.error("ollama_connection_error", error=str(e))
            raise LLMError(
                message=f"Could not connect to Ollama: {e}",
                error_code="OLLAMA_CONNECTION_ERROR",
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
        payload = self._prepare_payload(
            model=model,
            messages=messages,
            system_prompt=system_prompt,
            temperature=temperature,
            stream=True,
            **kwargs,
        )

        url = f"{self.base_url}/api/chat"
        try:
            async with self.client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]
                        if data.get("done"):
                            break
                    except json.JSONDecodeError:
                        logger.warning("ollama_stream_decode_error", line=line)

        except httpx.HTTPStatusError as e:
            # We have to read the body synchronously or asynchronously depending on state,
            # but in stream mode we just raise.
            raise LLMError(
                message=f"Ollama returned HTTP error: {e.response.status_code}",
                error_code="OLLAMA_HTTP_ERROR",
                details={"status": e.response.status_code},
                model=model,
            ) from e
        except httpx.RequestError as e:
            raise LLMError(
                message=f"Could not connect to Ollama: {e}",
                error_code="OLLAMA_CONNECTION_ERROR",
                details={"error": str(e)},
                model=model,
            ) from e

    async def health_check(self) -> dict[str, Any]:
        url = f"{self.base_url}/api/tags"
        try:
            response = await self.client.get(url, timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                models = [m.get("name") for m in data.get("models", [])]
                return {"status": "ok", "provider": self.provider_name, "models_available": models}
            return {"status": "error", "provider": self.provider_name, "details": response.text}
        except httpx.RequestError as e:
            return {"status": "error", "provider": self.provider_name, "details": str(e)}
