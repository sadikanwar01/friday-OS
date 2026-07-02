"""
FRIDAY OS - Base LLM Provider Interface.

Defines the contract that all LLM integrations (Ollama, OpenAI, Claude, etc.)
must adhere to, allowing the Conversation Engine to remain provider-agnostic.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """The canonical name of the provider (e.g., 'ollama', 'openai')."""
        pass

    @abstractmethod
    async def generate(
        self,
        model: str,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> str:
        """Generate a complete text response from the LLM.

        Args:
            model: The model to use (e.g., 'llama3.1:8b').
            messages: List of conversation messages (role, content).
            system_prompt: Optional system prompt to guide the model.
            temperature: Sampling temperature.
            **kwargs: Provider-specific options (e.g., max_tokens).

        Returns:
            The complete response string.
        """
        pass

    @abstractmethod
    async def stream(
        self,
        model: str,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """Stream the text response from the LLM token by token.

        Args:
            model: The model to use (e.g., 'llama3.1:8b').
            messages: List of conversation messages (role, content).
            system_prompt: Optional system prompt to guide the model.
            temperature: Sampling temperature.
            **kwargs: Provider-specific options (e.g., max_tokens).

        Yields:
            Text chunks (tokens) as they are generated.
        """
        yield ""

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Check the health and availability of the provider.

        Returns:
            A dictionary containing status information (e.g., {'status': 'ok'}).
        """
        pass
