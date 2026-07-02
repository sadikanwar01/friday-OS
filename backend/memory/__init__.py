"""
FRIDAY OS - Memory Module (Phase 2B).

Provides semantic storage, structured retrieval, and domain-specific handlers
for the Long-Term Memory System.
"""

from __future__ import annotations

from backend.memory.chroma import ChromaProvider, chroma_provider
from backend.memory.handlers import (
    ConversationMemoryHandler,
    MemoryExpirationHandler,
    UserProfileHandler,
)
from backend.memory.manager import MemoryManager
from backend.memory.semantic import SemanticMemoryRepository, semantic_memory_repo

__all__ = [
    "ChromaProvider",
    "ConversationMemoryHandler",
    "MemoryExpirationHandler",
    "MemoryManager",
    "SemanticMemoryRepository",
    "UserProfileHandler",
    "chroma_provider",
    "semantic_memory_repo",
]
