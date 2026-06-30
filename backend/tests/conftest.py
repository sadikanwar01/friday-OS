"""FRIDAY OS — Test Configuration and Fixtures."""
import os

# Set test environment BEFORE any project imports
os.environ["FRIDAY_APP_ENV"] = "testing"
os.environ["FRIDAY_DB_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["FRIDAY_APP_LOG_LEVEL"] = "WARNING"

import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from backend.database.models import Base


@pytest.fixture(scope="session")
def anyio_backend():
    """Use asyncio as the async backend for tests."""
    return "asyncio"


@pytest.fixture(scope="session")
def test_engine():
    """Create an in-memory SQLite engine for tests."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    return engine


@pytest.fixture(scope="session", autouse=True)
async def setup_db(test_engine):
    """Create all tables in the in-memory database."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional scoped session that rolls back after each test."""
    connection = await test_engine.connect()
    transaction = await connection.begin()

    session_factory = async_sessionmaker(
        bind=connection,
        expire_on_commit=False,
        class_=AsyncSession,
    )
    session = session_factory()

    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()
