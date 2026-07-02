"""
FRIDAY OS - Specialized Memory Handlers.

Provides high-level interfaces for specific memory domains:
- UserProfileHandler: Manages static/evolving facts about the user.
- ConversationMemoryHandler: Bridges short-term context with long-term storage.
- MemoryExpirationHandler: Manages archiving and expiration of decayed memories.
"""

from __future__ import annotations

from backend.database.models import Memory
from backend.memory.manager import MemoryManager
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class UserProfileHandler:
    """Manages static and evolving user facts."""

    def __init__(self, memory_manager: MemoryManager) -> None:
        self.manager = memory_manager
        self.category = "profile"

    async def update_fact(self, user_id: str, key: str, value: str) -> Memory:
        """Update a user profile fact.

        Profile facts have a fixed high importance (0.9) since they define
        the core identity and preferences of the user.
        """
        return await self.manager.add_memory(
            user_id=user_id,
            category=self.category,
            key=key,
            value=value,
            importance=0.9,
        )

    async def get_profile_context(self, user_id: str) -> str:
        """Retrieve the user profile as a formatted string for the system prompt."""
        # Using a broad semantic search to get all profile entries,
        # or we can rely on the DB keyword search if needed.
        # Since profile facts are usually small in number, a semantic query for "user profile facts" works.
        memories = await self.manager.search(
            user_id=user_id,
            query="user identity preferences facts",
            limit=20,
            category=self.category,
        )

        if not memories:
            return "No profile facts known yet."

        facts = [f"- {m.key}: {m.value}" for m in memories]
        return "\n".join(facts)


class ConversationMemoryHandler:
    """Bridges short-term conversation context to long-term semantic storage."""

    def __init__(self, memory_manager: MemoryManager) -> None:
        self.manager = memory_manager
        self.category = "conversation"

    async def summarize_and_store(
        self,
        user_id: str,
        conversation_id: str,
        summary_text: str,
        importance: float = 0.5,
    ) -> Memory:
        """Store a conversation summary as a semantic memory.

        In Phase 2A, the ContextManager hooks into summarization.
        This handler actually persists that summary.
        """
        return await self.manager.add_memory(
            user_id=user_id,
            category=self.category,
            key=f"summary_{conversation_id}",
            value=summary_text,
            metadata={"conversation_id": conversation_id},
            importance=importance,
        )


class MemoryExpirationHandler:
    """Handles decay, archiving, and expiration of long-term memories."""

    def __init__(self, memory_manager: MemoryManager) -> None:
        self.manager = memory_manager

    async def prune_decayed_memories(self, user_id: str, threshold: float = 0.1) -> int:
        """Find memories with importance below the threshold and delete them.

        In a full implementation, this might calculate a dynamic decay score
        based on `created_at`, `last_accessed`, and `importance_score`.
        For Phase 2B, we rely on the static importance score.
        """
        # Fetch lowest importance memories
        # We can directly query the SQLite repo since semantic repo doesn't index importance natively
        sql_repo = self.manager.sql_repo

        try:
            # We access the underlying session to do a custom query,
            # or we could add a `get_least_important` to the repo.
            # For simplicity, we just fetch all and filter in Python for now.
            # (Production tip: use a direct SQL query).
            from sqlalchemy import select

            stmt = select(Memory).where(
                Memory.user_id == user_id,
                Memory.importance_score < threshold,
                Memory.category != "pinned",  # Pinned memories never decay
            )
            result = await sql_repo._session.execute(stmt)
            decayed = list(result.scalars().all())

            deleted_count = 0
            for mem in decayed:
                success = await self.manager.delete_memory(mem.id)
                if success:
                    deleted_count += 1

            logger.info("memories_pruned", user_id=user_id, count=deleted_count)
            return deleted_count

        except Exception as exc:
            logger.error("memory_pruning_failed", user_id=user_id, error=str(exc))
            return 0
