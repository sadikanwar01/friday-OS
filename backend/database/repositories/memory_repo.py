"""
FRIDAY OS — Memory Repository.

Async CRUD operations for :class:`~backend.database.models.Memory` with
importance scoring, access tracking, and keyword search.

Usage::

    async for session in get_async_session():
        repo = MemoryRepository(session)
        mem = await repo.store(
            user_id="...",
            category="preference",
            key="favourite_language",
            value="Python",
        )
"""

from __future__ import annotations

from datetime import datetime, timezone

import orjson
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Memory
from backend.utils.exceptions import DatabaseError
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def _utcnow() -> datetime:
    """Return the current UTC datetime.

    Returns:
        A timezone-aware UTC :class:`datetime`.
    """
    return datetime.now(timezone.utc)


class MemoryRepository:
    """Async repository for Memory CRUD operations.

    All methods operate within the provided session and do **not** commit
    or close it — that responsibility belongs to the caller or the
    session lifecycle manager.

    Args:
        session: An active :class:`~sqlalchemy.ext.asyncio.AsyncSession`.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Create / Store
    # ------------------------------------------------------------------

    async def store(
        self,
        user_id: str,
        category: str,
        key: str,
        value: str,
        metadata: dict | None = None,
        importance: float = 0.5,
    ) -> Memory:
        """Store a new memory entry, or update if the key already exists.

        If a memory with the same ``user_id`` and ``key`` already exists,
        its ``value``, ``metadata_json``, and ``importance_score`` are
        updated in-place.

        Args:
            user_id: The owning user's ID.
            category: Memory category (e.g. ``preference``, ``project``).
            key: Lookup key for the memory.
            value: The memory content.
            metadata: Optional metadata dictionary (serialised as JSON).
            importance: Importance score between 0.0 and 1.0 (default 0.5).

        Returns:
            The created or updated :class:`Memory` instance.

        Raises:
            DatabaseError: If the operation fails.
        """
        try:
            metadata_json: str | None = None
            if metadata is not None:
                metadata_json = orjson.dumps(metadata).decode("utf-8")

            # Check for existing memory with same user_id + key.
            existing = await self.get_by_key(user_id, key)
            if existing is not None:
                existing.value = value
                existing.category = category
                existing.metadata_json = metadata_json
                existing.importance_score = importance
                existing.last_accessed = _utcnow()
                await self._session.flush()
                await self._session.refresh(existing)
                logger.info(
                    "memory_updated_via_store",
                    memory_id=existing.id,
                    key=key,
                )
                return existing

            memory = Memory(
                user_id=user_id,
                category=category,
                key=key,
                value=value,
                metadata_json=metadata_json,
                importance_score=importance,
            )
            self._session.add(memory)
            await self._session.flush()
            await self._session.refresh(memory)
            logger.info(
                "memory_stored",
                memory_id=memory.id,
                user_id=user_id,
                key=key,
            )
            return memory
        except DatabaseError:
            raise
        except Exception as exc:
            logger.error("memory_store_failed", key=key, error=str(exc))
            raise DatabaseError(
                message=f"Failed to store memory: {exc}",
                error_code="DB_MEMORY_STORE",
                details={"user_id": user_id, "key": key, "error": str(exc)},
            ) from exc

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def get_by_id(self, memory_id: str) -> Memory | None:
        """Retrieve a memory by its ID.

        Args:
            memory_id: The memory's UUID.

        Returns:
            The :class:`Memory` instance, or ``None`` if not found.

        Raises:
            DatabaseError: If the query fails.
        """
        try:
            stmt = select(Memory).where(Memory.id == memory_id)
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as exc:
            logger.error(
                "memory_get_failed",
                memory_id=memory_id,
                error=str(exc),
            )
            raise DatabaseError(
                message=f"Failed to get memory: {exc}",
                error_code="DB_MEMORY_GET",
                details={"memory_id": memory_id, "error": str(exc)},
            ) from exc

    async def get_by_key(self, user_id: str, key: str) -> Memory | None:
        """Retrieve a memory by user ID and key.

        Args:
            user_id: The owning user's ID.
            key: The memory's lookup key.

        Returns:
            The :class:`Memory` instance, or ``None`` if not found.

        Raises:
            DatabaseError: If the query fails.
        """
        try:
            stmt = (
                select(Memory)
                .where(Memory.user_id == user_id, Memory.key == key)
            )
            result = await self._session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as exc:
            logger.error(
                "memory_get_by_key_failed",
                user_id=user_id,
                key=key,
                error=str(exc),
            )
            raise DatabaseError(
                message=f"Failed to get memory by key: {exc}",
                error_code="DB_MEMORY_GET_KEY",
                details={"user_id": user_id, "key": key, "error": str(exc)},
            ) from exc

    async def search_by_category(
        self,
        user_id: str,
        category: str,
        limit: int = 50,
    ) -> list[Memory]:
        """Search memories by category for a user.

        Args:
            user_id: The owning user's ID.
            category: The category to filter on.
            limit: Maximum number of results (default 50).

        Returns:
            A list of :class:`Memory` instances ordered by
            ``importance_score`` descending.

        Raises:
            DatabaseError: If the query fails.
        """
        try:
            stmt = (
                select(Memory)
                .where(
                    Memory.user_id == user_id,
                    Memory.category == category,
                )
                .order_by(Memory.importance_score.desc())
                .limit(limit)
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except Exception as exc:
            logger.error(
                "memory_search_category_failed",
                user_id=user_id,
                category=category,
                error=str(exc),
            )
            raise DatabaseError(
                message=f"Failed to search memories by category: {exc}",
                error_code="DB_MEMORY_SEARCH_CATEGORY",
                details={
                    "user_id": user_id,
                    "category": category,
                    "error": str(exc),
                },
            ) from exc

    async def search_by_keyword(
        self,
        user_id: str,
        keyword: str,
        limit: int = 50,
    ) -> list[Memory]:
        """Search memories by keyword in key or value.

        Performs a case-insensitive ``LIKE`` search against both the
        ``key`` and ``value`` columns.

        Args:
            user_id: The owning user's ID.
            keyword: The keyword to search for.
            limit: Maximum number of results (default 50).

        Returns:
            A list of matching :class:`Memory` instances ordered by
            ``importance_score`` descending.

        Raises:
            DatabaseError: If the query fails.
        """
        try:
            pattern = f"%{keyword}%"
            stmt = (
                select(Memory)
                .where(
                    Memory.user_id == user_id,
                    (Memory.key.ilike(pattern) | Memory.value.ilike(pattern)),
                )
                .order_by(Memory.importance_score.desc())
                .limit(limit)
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except Exception as exc:
            logger.error(
                "memory_search_keyword_failed",
                user_id=user_id,
                keyword=keyword,
                error=str(exc),
            )
            raise DatabaseError(
                message=f"Failed to search memories by keyword: {exc}",
                error_code="DB_MEMORY_SEARCH_KEYWORD",
                details={
                    "user_id": user_id,
                    "keyword": keyword,
                    "error": str(exc),
                },
            ) from exc

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    async def update_value(
        self,
        memory_id: str,
        value: str,
    ) -> Memory | None:
        """Update a memory's value.

        Args:
            memory_id: The memory's UUID.
            value: The new value.

        Returns:
            The updated :class:`Memory`, or ``None`` if not found.

        Raises:
            DatabaseError: If the update fails.
        """
        try:
            stmt = select(Memory).where(Memory.id == memory_id)
            result = await self._session.execute(stmt)
            memory = result.scalar_one_or_none()

            if memory is None:
                return None

            memory.value = value
            memory.last_accessed = _utcnow()
            await self._session.flush()
            await self._session.refresh(memory)
            logger.info("memory_value_updated", memory_id=memory_id)
            return memory
        except Exception as exc:
            logger.error(
                "memory_update_value_failed",
                memory_id=memory_id,
                error=str(exc),
            )
            raise DatabaseError(
                message=f"Failed to update memory value: {exc}",
                error_code="DB_MEMORY_UPDATE_VALUE",
                details={"memory_id": memory_id, "error": str(exc)},
            ) from exc

    async def update_access(self, memory_id: str) -> None:
        """Record an access event for a memory.

        Increments ``access_count`` and updates ``last_accessed``.

        Args:
            memory_id: The memory's UUID.

        Raises:
            DatabaseError: If the update fails.
        """
        try:
            stmt = select(Memory).where(Memory.id == memory_id)
            result = await self._session.execute(stmt)
            memory = result.scalar_one_or_none()

            if memory is None:
                return

            memory.access_count += 1
            memory.last_accessed = _utcnow()
            await self._session.flush()
            logger.debug(
                "memory_access_updated",
                memory_id=memory_id,
                access_count=memory.access_count,
            )
        except Exception as exc:
            logger.error(
                "memory_update_access_failed",
                memory_id=memory_id,
                error=str(exc),
            )
            raise DatabaseError(
                message=f"Failed to update memory access: {exc}",
                error_code="DB_MEMORY_UPDATE_ACCESS",
                details={"memory_id": memory_id, "error": str(exc)},
            ) from exc

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    async def delete(self, memory_id: str) -> bool:
        """Delete a memory by its ID.

        Args:
            memory_id: The memory's UUID.

        Returns:
            ``True`` if the memory was found and deleted, ``False``
            otherwise.

        Raises:
            DatabaseError: If the deletion fails.
        """
        try:
            stmt = select(Memory).where(Memory.id == memory_id)
            result = await self._session.execute(stmt)
            memory = result.scalar_one_or_none()

            if memory is None:
                return False

            await self._session.delete(memory)
            await self._session.flush()
            logger.info("memory_deleted", memory_id=memory_id)
            return True
        except Exception as exc:
            logger.error(
                "memory_delete_failed",
                memory_id=memory_id,
                error=str(exc),
            )
            raise DatabaseError(
                message=f"Failed to delete memory: {exc}",
                error_code="DB_MEMORY_DELETE",
                details={"memory_id": memory_id, "error": str(exc)},
            ) from exc

    # ------------------------------------------------------------------
    # Ranked retrieval
    # ------------------------------------------------------------------

    async def get_most_important(
        self,
        user_id: str,
        limit: int = 20,
    ) -> list[Memory]:
        """Retrieve the most important memories for a user.

        Args:
            user_id: The owning user's ID.
            limit: Maximum number of results (default 20).

        Returns:
            A list of :class:`Memory` instances ordered by
            ``importance_score`` descending.

        Raises:
            DatabaseError: If the query fails.
        """
        try:
            stmt = (
                select(Memory)
                .where(Memory.user_id == user_id)
                .order_by(Memory.importance_score.desc())
                .limit(limit)
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except Exception as exc:
            logger.error(
                "memory_most_important_failed",
                user_id=user_id,
                error=str(exc),
            )
            raise DatabaseError(
                message=f"Failed to get most important memories: {exc}",
                error_code="DB_MEMORY_MOST_IMPORTANT",
                details={"user_id": user_id, "error": str(exc)},
            ) from exc

    async def get_recently_accessed(
        self,
        user_id: str,
        limit: int = 20,
    ) -> list[Memory]:
        """Retrieve the most recently accessed memories for a user.

        Args:
            user_id: The owning user's ID.
            limit: Maximum number of results (default 20).

        Returns:
            A list of :class:`Memory` instances ordered by
            ``last_accessed`` descending.

        Raises:
            DatabaseError: If the query fails.
        """
        try:
            stmt = (
                select(Memory)
                .where(Memory.user_id == user_id)
                .order_by(Memory.last_accessed.desc())
                .limit(limit)
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except Exception as exc:
            logger.error(
                "memory_recently_accessed_failed",
                user_id=user_id,
                error=str(exc),
            )
            raise DatabaseError(
                message=f"Failed to get recently accessed memories: {exc}",
                error_code="DB_MEMORY_RECENTLY_ACCESSED",
                details={"user_id": user_id, "error": str(exc)},
            ) from exc
