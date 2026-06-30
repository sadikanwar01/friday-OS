"""
FRIDAY OS — FastAPI Dependency Injection.

Provides reusable FastAPI dependency callables for:

* **Settings** — application-wide configuration singleton.
* **Database sessions** — scoped async SQLAlchemy sessions with
  automatic commit / rollback semantics.

Usage in a FastAPI route::

    from fastapi import Depends
    from backend.dependencies import get_current_settings, get_db_session

    @router.get("/health")
    async def health(settings: Settings = Depends(get_current_settings)):
        return {"status": "ok", "version": settings.app_version}
"""

from __future__ import annotations

from typing import TYPE_CHECKING, AsyncGenerator

from backend.config import Settings, get_settings

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


# ---------------------------------------------------------------------------
# Settings dependency
# ---------------------------------------------------------------------------


async def get_current_settings() -> Settings:
    """FastAPI dependency that returns the global :class:`Settings` singleton.

    Returns:
        The application :class:`Settings` instance.
    """
    return get_settings()


# ---------------------------------------------------------------------------
# Database session dependency
# ---------------------------------------------------------------------------


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a scoped async database session.

    The session is automatically committed on successful completion of
    the request and rolled back if any unhandled exception propagates.

    .. note::
        The ``async_session_factory`` is imported lazily from
        ``backend.database.engine`` so that this module remains
        importable before the database package is fully built.

    Yields:
        An :class:`~sqlalchemy.ext.asyncio.AsyncSession` bound to the
        configured database engine.

    Raises:
        ImportError: If ``backend.database.engine`` has not been created
            yet (will surface clearly during development).
        Exception: Any exception raised during request handling is
            re-raised after the session rollback.
    """
    from backend.database.engine import async_session_factory

    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
