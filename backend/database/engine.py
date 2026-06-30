"""
FRIDAY OS — Async SQLAlchemy Engine & Session Management.

Provides singleton async engine and session factory creation, session
lifecycle management (commit/rollback), and database initialisation
(table creation) and teardown utilities.

Usage::

    from backend.database.engine import init_database, get_async_session

    await init_database()

    async for session in get_async_session():
        result = await session.execute(...)
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.config import get_settings
from backend.utils.exceptions import DatabaseError
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Module-level singletons
# ---------------------------------------------------------------------------

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

def get_engine() -> AsyncEngine:
    """Return the singleton async SQLAlchemy engine.

    On first call the engine is created using the ``db_url`` and ``db_echo``
    values from :func:`backend.config.get_settings`.  For SQLite URLs the
    parent directory of the database file is created automatically.

    Returns:
        The :class:`~sqlalchemy.ext.asyncio.AsyncEngine` singleton.

    Raises:
        DatabaseError: If the engine cannot be created.
    """
    global _engine  # noqa: PLW0603

    if _engine is not None:
        return _engine

    try:
        settings = get_settings()
        db_url: str = settings.db_url

        # Ensure the SQLite database directory exists.
        if "sqlite" in db_url:
            # Extract the file path from URLs like:
            #   sqlite+aiosqlite:///./data/friday.db
            #   sqlite+aiosqlite:////absolute/path/to/db.sqlite
            raw_path = db_url.split("///", maxsplit=1)[-1]
            if raw_path:
                db_path = Path(raw_path).resolve()
                db_path.parent.mkdir(parents=True, exist_ok=True)
                logger.info(
                    "sqlite_directory_ensured",
                    path=str(db_path.parent),
                )

        _engine = create_async_engine(
            db_url,
            echo=settings.db_echo,
            pool_pre_ping=True,
        )
        logger.info("engine_created", url=db_url, echo=settings.db_echo)
        return _engine

    except Exception as exc:
        logger.error("engine_creation_failed", error=str(exc))
        raise DatabaseError(
            message=f"Failed to create database engine: {exc}",
            error_code="DB_ENGINE_ERROR",
            details={"error": str(exc)},
        ) from exc


# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------

def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the singleton async session factory.

    Creates the factory on first call using the engine from
    :func:`get_engine` with ``expire_on_commit=False`` so that
    detached instances remain usable after commit.

    Returns:
        An :class:`~sqlalchemy.ext.asyncio.async_sessionmaker` instance.

    Raises:
        DatabaseError: If the session factory cannot be created.
    """
    global _session_factory  # noqa: PLW0603

    if _session_factory is not None:
        return _session_factory

    try:
        engine = get_engine()
        _session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        logger.info("session_factory_created")
        return _session_factory

    except DatabaseError:
        raise
    except Exception as exc:
        logger.error("session_factory_creation_failed", error=str(exc))
        raise DatabaseError(
            message=f"Failed to create session factory: {exc}",
            error_code="DB_SESSION_FACTORY_ERROR",
            details={"error": str(exc)},
        ) from exc


# ---------------------------------------------------------------------------
# Session generator (for dependency injection / context managers)
# ---------------------------------------------------------------------------

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session with automatic commit/rollback.

    Usage as an async generator::

        async for session in get_async_session():
            await session.execute(...)

    On normal exit the session is committed.  On exception the session
    is rolled back and the exception is re-raised.

    Yields:
        An :class:`~sqlalchemy.ext.asyncio.AsyncSession` instance.

    Raises:
        DatabaseError: If session creation or commit/rollback fails.
    """
    factory = get_session_factory()
    session: AsyncSession = factory()

    try:
        yield session
        await session.commit()
    except Exception as exc:
        await session.rollback()
        logger.error("session_rollback", error=str(exc))
        raise
    finally:
        await session.close()


# ---------------------------------------------------------------------------
# Database lifecycle
# ---------------------------------------------------------------------------

async def init_database() -> None:
    """Create all tables defined in the ORM models.

    Imports :class:`~backend.database.models.Base` and uses its metadata
    to issue ``CREATE TABLE IF NOT EXISTS`` statements against the
    current engine.

    Raises:
        DatabaseError: If table creation fails.
    """
    from backend.database.models import Base  # noqa: F811 — deferred import

    try:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info(
            "database_initialised",
            tables=list(Base.metadata.tables.keys()),
        )
    except Exception as exc:
        logger.error("database_init_failed", error=str(exc))
        raise DatabaseError(
            message=f"Failed to initialise database: {exc}",
            error_code="DB_INIT_ERROR",
            details={"error": str(exc)},
        ) from exc


async def close_database() -> None:
    """Dispose of the engine and reset module-level singletons.

    Safe to call even if the engine was never created.

    Raises:
        DatabaseError: If engine disposal fails.
    """
    global _engine, _session_factory  # noqa: PLW0603

    try:
        if _engine is not None:
            await _engine.dispose()
            logger.info("database_engine_disposed")
        _engine = None
        _session_factory = None
    except Exception as exc:
        logger.error("database_close_failed", error=str(exc))
        _engine = None
        _session_factory = None
        raise DatabaseError(
            message=f"Failed to close database: {exc}",
            error_code="DB_CLOSE_ERROR",
            details={"error": str(exc)},
        ) from exc


# ---------------------------------------------------------------------------
# Module-level convenience alias
# ---------------------------------------------------------------------------

def async_session_factory() -> AsyncSession:
    """Convenience callable that creates a new session from the factory.

    This provides a module-level function that can be called as
    ``async_session_factory()`` after initialisation to get a new session.

    Returns:
        A new :class:`~sqlalchemy.ext.asyncio.AsyncSession`.

    Raises:
        DatabaseError: If the session factory has not been initialised.
    """
    factory = get_session_factory()
    return factory()
