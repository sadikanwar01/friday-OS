"""
FRIDAY OS - LLM Provider Router.

Acts as a factory and registry for LLM providers. Routes requests to the correct
provider based on the model requested or configuration.
"""

from __future__ import annotations

from typing import Any

from backend.llm.models import ModelRegistry
from backend.llm.providers.base import BaseLLMProvider
from backend.llm.providers.gemini import GeminiProvider
from backend.llm.providers.ollama import OllamaProvider
from backend.utils.exceptions import ConfigurationError
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ProviderRouter:
    """Routes LLM requests to the appropriate provider."""

    def __init__(self) -> None:
        self._providers: dict[str, BaseLLMProvider] = {}
        self._initialized: set[str] = set()

    def _ensure_provider_initialized(self, provider_name: str) -> BaseLLMProvider:
        """Lazily initialize and return a provider by name."""
        if provider_name in self._providers:
            return self._providers[provider_name]

        if provider_name == "ollama":
            provider_ollama: BaseLLMProvider = OllamaProvider()
            self._providers[provider_name] = provider_ollama
            return provider_ollama

        if provider_name == "gemini":
            provider_gemini: BaseLLMProvider = GeminiProvider()
            self._providers[provider_name] = provider_gemini
            return provider_gemini

        raise ConfigurationError(
            message=f"Unknown provider '{provider_name}'",
            error_code="UNKNOWN_PROVIDER",
        )

    def register_provider(self, provider: BaseLLMProvider) -> None:
        """Register a new LLM provider."""
        self._providers[provider.provider_name] = provider
        logger.debug("llm_provider_registered", provider=provider.provider_name)

    def get_provider_for_model(self, model_name: str) -> BaseLLMProvider:
        """Get the correct provider instance for a given model.

        Args:
            model_name: The name of the model (e.g., 'llama3.1:8b').

        Returns:
            An instance of BaseLLMProvider.

        Raises:
            ConfigurationError: If the model is unregistered or the provider is missing.
        """
        model_caps = ModelRegistry.get(model_name)
        if not model_caps:
            raise ConfigurationError(
                message=f"Model '{model_name}' is not registered in the ModelRegistry.",
                error_code="UNREGISTERED_MODEL",
            )

        # Lazily initialize provider
        provider = self._ensure_provider_initialized(model_caps.provider)
        return provider

    async def health_check_all(self) -> dict[str, Any]:
        """Run health checks on all registered providers.

        Returns:
            A dictionary mapping provider names to their health status.
        """
        # Force initialize known default providers to test health
        try:
            self._ensure_provider_initialized("ollama")
        except Exception:
            pass
        try:
            self._ensure_provider_initialized("gemini")
        except Exception:
            pass

        results = {}
        for name, provider in self._providers.items():
            results[name] = await provider.health_check()
        return results


# Global singleton instance of the ProviderRouter
provider_router = ProviderRouter()
