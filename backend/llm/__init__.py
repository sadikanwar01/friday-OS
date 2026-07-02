"""
FRIDAY OS - LLM Module (Phase 2A).

Provides the core intelligence layer including provider routing,
layered prompt compilation, context management, and execution orchestration.
"""

from __future__ import annotations

from backend.llm.context import ContextManager, context_manager
from backend.llm.engine import ConversationEngine, conversation_engine
from backend.llm.events import Event, EventBus, event_bus
from backend.llm.models import ModelCapabilities, ModelRegistry
from backend.llm.prompts import PromptLayers, PromptManager, prompt_manager
from backend.llm.router import ProviderRouter, provider_router
from backend.llm.tools import BaseTool

__all__ = [
    "ContextManager",
    "ConversationEngine",
    "Event",
    "EventBus",
    "ModelCapabilities",
    "ModelRegistry",
    "PromptLayers",
    "PromptManager",
    "ProviderRouter",
    "BaseTool",
    "context_manager",
    "conversation_engine",
    "event_bus",
    "prompt_manager",
    "provider_router",
]
