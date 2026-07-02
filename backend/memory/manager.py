"""
FRIDAY OS - Memory Manager.

The core orchestrator for the Long-Term Memory System.
Ensures that the SQLite MemoryRepository (Source of Truth) is always in sync
with the SemanticMemoryRepository (Vector Index).
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Memory
from backend.database.repositories.memory_repo import MemoryRepository
from backend.memory.semantic import SemanticMemoryRepository, semantic_memory_repo
from backend.utils.exceptions import DatabaseError
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class MemoryManager:
    """Orchestrates structured and semantic memory storage."""

    def __init__(
        self,
        session: AsyncSession,
        semantic_repo: SemanticMemoryRepository | None = None,
    ) -> None:
        self.sql_repo = MemoryRepository(session)
        self.semantic_repo = semantic_repo or semantic_memory_repo

    async def add_memory(
        self,
        user_id: str,
        category: str,
        key: str,
        value: str,
        metadata: dict | None = None,
        importance: float = 0.5,
    ) -> Memory:
        """Add a memory to both SQLite and the semantic index."""
        # 1. Source of Truth: SQLite
        memory = await self.sql_repo.store(
            user_id=user_id,
            category=category,
            key=key,
            value=value,
            metadata=metadata,
            importance=importance,
        )

        # 2. Semantic Index: ChromaDB
        await self.semantic_repo.index_memory(memory)
        return memory

    async def update_memory(
        self,
        memory_id: str,
        value: str,
    ) -> Memory | None:
        """Update a memory's value in both SQLite and the semantic index."""
        # 1. Source of Truth: SQLite
        memory = await self.sql_repo.update_value(memory_id, value)
        if not memory:
            return None

        # 2. Semantic Index: ChromaDB
        await self.semantic_repo.index_memory(memory)
        return memory

    async def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory from both SQLite and the semantic index."""
        # 1. Source of Truth: SQLite
        success = await self.sql_repo.delete(memory_id)
        if not success:
            return False

        # 2. Semantic Index: ChromaDB
        try:
            await self.semantic_repo.remove_memory(memory_id)
        except DatabaseError as exc:
            # If it's already missing from Chroma, we don't care during a delete.
            logger.warning(
                "semantic_remove_failed_during_delete",
                memory_id=memory_id,
                error=str(exc),
            )

        return True

    async def search(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
        category: str | None = None,
    ) -> list[Memory]:
        """Perform a semantic search and return full SQLite Memory objects."""
        # 1. Get ordered memory IDs from the semantic index
        memory_ids = await self.semantic_repo.search_memories(
            user_id=user_id,
            query=query,
            limit=limit,
            category=category,
        )

        if not memory_ids:
            return []

        # 2. Fetch the actual full objects from SQLite
        # We need to maintain the relevance ordering returned by semantic search
        memories = []
        for mid in memory_ids:
            mem = await self.sql_repo.get_by_id(mid)
            if mem:
                # Update access count implicitly when fetched for context
                await self.sql_repo.update_access(mid)
                memories.append(mem)

        logger.info(
            "memory_search_completed",
            user_id=user_id,
            query_length=len(query),
            results_found=len(memories),
        )
        return memories

    async def get_pinned_memories(self, user_id: str) -> list[Memory]:
        """Retrieve memories pinned to the system prompt.

        Pinned memories bypass regular semantic retrieval and are always injected.
        Here we define 'pinned' as category='pinned'.
        """
        return await self.sql_repo.search_by_category(
            user_id=user_id,
            category="pinned",
            limit=10,
        )

    async def get_recent_context(self, user_id: str, limit: int = 5) -> list[Memory]:
        """Retrieve recently accessed memories for context continuity."""
        return await self.sql_repo.get_recently_accessed(user_id=user_id, limit=limit)
