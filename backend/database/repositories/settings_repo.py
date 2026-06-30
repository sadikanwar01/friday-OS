"""
FRIDAY OS — Settings Repository.

Async CRUD operations for :class:`~backend.database.models.Setting`,
including bulk upsert and category-based retrieval.

Usage::

    async for session in get_async_session():
        repo = SettingsRepository(session)
        await repo.set("theme", "dark", category="ui")
        value = await repo.get("theme")
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Setting
from backend.utils.exceptions import DatabaseError
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class SettingsRepository:
    """Async repository for Setting CRUD operations.

    All methods operate within the provided session and do **not** commit
    or close it — that responsibility belongs to the caller or the
    session lifecycle manager.

    Args:
        session: An active :class:`~sqlalchemy.ext.asyncio.AsyncSession`.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    async def get(self, key: str) -> str | None:
        """Retrieve the value of a setting by its key.

        Args:
            key: The unique setting key.

        Returns:
            The setting value string, or ``None`` if the key does not
            exist.

        Raises:
            DatabaseError: If the query fails.
        """
        try:
            stmt = select(Setting).where(Setting.key == key)
            result = await self._session.execute(stmt)
            setting = result.scalar_one_or_none()
            return setting.value if setting is not None else None
        except Exception as exc:
            logger.error("setting_get_failed", key=key, error=str(exc))
            raise DatabaseError(
                message=f"Failed to get setting: {exc}",
                error_code="DB_SETTING_GET",
                details={"key": key, "error": str(exc)},
            ) from exc

    async def get_by_category(self, category: str) -> list[Setting]:
        """Retrieve all settings within a category.

        Args:
            category: The category to filter on.

        Returns:
            A list of :class:`Setting` instances.

        Raises:
            DatabaseError: If the query fails.
        """
        try:
            stmt = (
                select(Setting)
                .where(Setting.category == category)
                .order_by(Setting.key.asc())
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except Exception as exc:
            logger.error(
                "settings_get_by_category_failed",
                category=category,
                error=str(exc),
            )
            raise DatabaseError(
                message=f"Failed to get settings by category: {exc}",
                error_code="DB_SETTING_GET_CATEGORY",
                details={"category": category, "error": str(exc)},
            ) from exc

    async def get_all(self) -> list[Setting]:
        """Retrieve all settings.

        Returns:
            A list of all :class:`Setting` instances, ordered by
            category then key.

        Raises:
            DatabaseError: If the query fails.
        """
        try:
            stmt = select(Setting).order_by(
                Setting.category.asc(),
                Setting.key.asc(),
            )
            result = await self._session.execute(stmt)
            return list(result.scalars().all())
        except Exception as exc:
            logger.error("settings_get_all_failed", error=str(exc))
            raise DatabaseError(
                message=f"Failed to get all settings: {exc}",
                error_code="DB_SETTING_GET_ALL",
                details={"error": str(exc)},
            ) from exc

    # ------------------------------------------------------------------
    # Create / Update
    # ------------------------------------------------------------------

    async def set(
        self,
        key: str,
        value: str,
        category: str = "general",
    ) -> Setting:
        """Create or update a setting.

        If a setting with the given ``key`` already exists, its ``value``
        and ``category`` are updated.  Otherwise a new setting is created.

        Args:
            key: The unique setting key.
            value: The setting value.
            category: Setting category (default ``general``).

        Returns:
            The created or updated :class:`Setting` instance.

        Raises:
            DatabaseError: If the operation fails.
        """
        try:
            stmt = select(Setting).where(Setting.key == key)
            result = await self._session.execute(stmt)
            setting = result.scalar_one_or_none()

            if setting is not None:
                setting.value = value
                setting.category = category
                await self._session.flush()
                await self._session.refresh(setting)
                logger.info("setting_updated", key=key, category=category)
                return setting

            setting = Setting(
                key=key,
                value=value,
                category=category,
            )
            self._session.add(setting)
            await self._session.flush()
            await self._session.refresh(setting)
            logger.info("setting_created", key=key, category=category)
            return setting
        except Exception as exc:
            logger.error("setting_set_failed", key=key, error=str(exc))
            raise DatabaseError(
                message=f"Failed to set setting: {exc}",
                error_code="DB_SETTING_SET",
                details={"key": key, "error": str(exc)},
            ) from exc

    async def set_bulk(
        self,
        settings: dict[str, str],
        category: str = "general",
    ) -> list[Setting]:
        """Create or update multiple settings in a single operation.

        Each key in *settings* is treated as a setting key, and the
        corresponding value is the setting value.

        Args:
            settings: Dictionary of ``{key: value}`` pairs.
            category: Category for all settings (default ``general``).

        Returns:
            A list of created or updated :class:`Setting` instances.

        Raises:
            DatabaseError: If the operation fails.
        """
        try:
            results: list[Setting] = []
            for key, value in settings.items():
                setting = await self.set(key, value, category)
                results.append(setting)
            logger.info(
                "settings_bulk_set",
                count=len(results),
                category=category,
            )
            return results
        except DatabaseError:
            raise
        except Exception as exc:
            logger.error("settings_bulk_set_failed", error=str(exc))
            raise DatabaseError(
                message=f"Failed to bulk set settings: {exc}",
                error_code="DB_SETTING_BULK_SET",
                details={"count": len(settings), "error": str(exc)},
            ) from exc

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    async def delete(self, key: str) -> bool:
        """Delete a setting by its key.

        Args:
            key: The unique setting key.

        Returns:
            ``True`` if the setting was found and deleted, ``False``
            otherwise.

        Raises:
            DatabaseError: If the deletion fails.
        """
        try:
            stmt = select(Setting).where(Setting.key == key)
            result = await self._session.execute(stmt)
            setting = result.scalar_one_or_none()

            if setting is None:
                return False

            await self._session.delete(setting)
            await self._session.flush()
            logger.info("setting_deleted", key=key)
            return True
        except Exception as exc:
            logger.error("setting_delete_failed", key=key, error=str(exc))
            raise DatabaseError(
                message=f"Failed to delete setting: {exc}",
                error_code="DB_SETTING_DELETE",
                details={"key": key, "error": str(exc)},
            ) from exc
