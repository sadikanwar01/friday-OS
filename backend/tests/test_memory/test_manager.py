from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.database.models import Memory
from backend.memory.manager import MemoryManager


@pytest.mark.asyncio
async def test_memory_manager_add():
    mock_session = MagicMock()

    manager = MemoryManager(session=mock_session)

    # Mock repositories
    manager.sql_repo = AsyncMock()
    manager.semantic_repo = AsyncMock()

    fake_memory = Memory(id="mem_1", user_id="123", key="test", value="test value")
    manager.sql_repo.store.return_value = fake_memory

    result = await manager.add_memory(
        user_id="123", category="general", key="test", value="test value"
    )

    assert result == fake_memory
    manager.sql_repo.store.assert_called_once()
    manager.semantic_repo.index_memory.assert_called_once_with(fake_memory)


@pytest.mark.asyncio
async def test_memory_manager_search():
    mock_session = MagicMock()

    manager = MemoryManager(session=mock_session)
    manager.sql_repo = AsyncMock()
    manager.semantic_repo = AsyncMock()

    # Semantic returns IDs
    manager.semantic_repo.search_memories.return_value = ["mem_2", "mem_1"]

    fake_mem_1 = Memory(id="mem_1")
    fake_mem_2 = Memory(id="mem_2")

    # SQL returns full objects
    manager.sql_repo.get_by_id.side_effect = lambda x: fake_mem_2 if x == "mem_2" else fake_mem_1

    results = await manager.search(user_id="123", query="test")

    assert len(results) == 2
    assert results[0].id == "mem_2"
    assert results[1].id == "mem_1"

    assert manager.sql_repo.update_access.call_count == 2
