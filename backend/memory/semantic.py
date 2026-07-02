"""
FRIDAY OS - Semantic Memory Repository.

Domain-specific repository that wraps the generic ChromaProvider to handle
the indexing and semantic searching of FRIDAY OS Memory objects.
"""

from __future__ import annotations

from backend.database.models import Memory
from backend.memory.chroma import chroma_provider
from backend.utils.exceptions import DatabaseError
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class SemanticMemoryRepository:
    """Semantic index for FRIDAY OS Memories."""

    def __init__(self) -> None:
        self.provider = chroma_provider

    async def index_memory(self, memory: Memory) -> None:
        """Index a memory into the semantic store.

        Args:
            memory: The SQLAlchemy Memory instance to index.
        """
        # The document is the actual text we want to perform similarity search on.
        # For a memory, this is primarily the 'value'.
        # We can also prepend the 'key' or 'category' to give it more context.
        document_text = f"[{memory.category}] {memory.key}: {memory.value}"

        metadata = {
            "user_id": memory.user_id,
            "category": memory.category,
            "key": memory.key,
        }

        try:
            await self.provider.add_document(
                doc_id=memory.id,
                text=document_text,
                metadata=metadata,
            )
            logger.debug("memory_indexed_semantically", memory_id=memory.id)
        except Exception as exc:
            logger.error("memory_index_failed", memory_id=memory.id, error=str(exc))
            raise DatabaseError(
                message=f"Failed to semantically index memory: {exc}",
                error_code="SEMANTIC_INDEX_ERROR",
                details={"memory_id": memory.id, "error": str(exc)},
            ) from exc

    async def search_memories(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
        category: str | None = None,
    ) -> list[str]:
        """Search for memories semantically and return their IDs.

        Args:
            user_id: The ID of the user searching.
            query: The search query text.
            limit: Maximum number of results.
            category: Optional category filter.

        Returns:
            A list of matching memory IDs ordered by semantic relevance.
        """
        where = {"user_id": user_id}
        if category:
            where["category"] = category

        try:
            results = await self.provider.search_documents(
                query=query,
                n_results=limit,
                where=where,
            )

            # Extract just the IDs
            memory_ids = [res["id"] for res in results]
            logger.debug(
                "memory_semantic_search_completed",
                query=query,
                results_count=len(memory_ids),
            )
            return memory_ids
        except Exception as exc:
            logger.error("memory_semantic_search_failed", query=query, error=str(exc))
            raise DatabaseError(
                message=f"Failed to perform semantic search: {exc}",
                error_code="SEMANTIC_SEARCH_ERROR",
                details={"query": query, "error": str(exc)},
            ) from exc

    async def remove_memory(self, memory_id: str) -> None:
        """Remove a memory from the semantic index."""
        try:
            await self.provider.delete_document(doc_id=memory_id)
            logger.debug("memory_removed_semantically", memory_id=memory_id)
        except Exception as exc:
            logger.error("memory_semantic_remove_failed", memory_id=memory_id, error=str(exc))
            raise DatabaseError(
                message=f"Failed to remove memory from semantic index: {exc}",
                error_code="SEMANTIC_REMOVE_ERROR",
                details={"memory_id": memory_id, "error": str(exc)},
            ) from exc


# Global instance
semantic_memory_repo = SemanticMemoryRepository()
