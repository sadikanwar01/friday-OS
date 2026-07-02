"""
FRIDAY OS - Model Capability Registry.

Centralized registry for defining the capabilities and constraints of various
LLM models across different providers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from backend.config import get_settings


@dataclass
class ModelCapabilities:
    """Describes what a specific LLM model can do."""

    name: str
    provider: str
    context_size: int
    supports_streaming: bool = True
    supports_tools: bool = False
    supports_vision: bool = False
    supports_json_mode: bool = False
    supports_embeddings: bool = False


class ModelRegistry:
    """Registry holding capability definitions for all supported models."""

    _models: ClassVar[dict[str, ModelCapabilities]] = {}

    @classmethod
    def register(cls, model: ModelCapabilities) -> None:
        """Register a new model's capabilities."""
        cls._models[model.name] = model

    @classmethod
    def get(cls, name: str) -> ModelCapabilities | None:
        """Retrieve capabilities for a model by name."""
        return cls._models.get(name)

    @classmethod
    def all(cls) -> list[ModelCapabilities]:
        """List all registered models."""
        return list(cls._models.values())


# ---------------------------------------------------------------------------
# Default Registrations (Phase 2A)
# ---------------------------------------------------------------------------

ModelRegistry.register(
    ModelCapabilities(
        name="llama3.1:8b",
        provider="ollama",
        context_size=8192,
        supports_streaming=True,
        supports_tools=True,
        supports_json_mode=True,
    )
)

ModelRegistry.register(
    ModelCapabilities(
        name="gpt-4o",
        provider="openai",
        context_size=128000,
        supports_streaming=True,
        supports_tools=True,
        supports_vision=True,
        supports_json_mode=True,
    )
)

ModelRegistry.register(
    ModelCapabilities(
        name="gemini-1.5-pro",
        provider="google",
        context_size=2000000,
        supports_streaming=True,
        supports_tools=True,
        supports_vision=True,
        supports_json_mode=True,
    )
)

# Register the default Gemini model from configuration
settings = get_settings()
ModelRegistry.register(
    ModelCapabilities(
        name=settings.gemini_model,
        provider="gemini",
        context_size=2000000,
        supports_streaming=True,
        supports_tools=True,
        supports_vision=True,
        supports_json_mode=True,
    )
)
