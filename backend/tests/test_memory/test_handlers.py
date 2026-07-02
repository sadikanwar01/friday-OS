from unittest.mock import AsyncMock

import pytest

from backend.memory.handlers import ConversationMemoryHandler, UserProfileHandler


@pytest.mark.asyncio
async def test_user_profile_handler():
    mock_manager = AsyncMock()
    handler = UserProfileHandler(mock_manager)

    await handler.update_fact("123", "color", "blue")

    mock_manager.add_memory.assert_called_once_with(
        user_id="123", category="profile", key="color", value="blue", importance=0.9
    )


@pytest.mark.asyncio
async def test_conversation_memory_handler():
    mock_manager = AsyncMock()
    handler = ConversationMemoryHandler(mock_manager)

    await handler.summarize_and_store("123", "conv_1", "Summary text")

    mock_manager.add_memory.assert_called_once_with(
        user_id="123",
        category="conversation",
        key="summary_conv_1",
        value="Summary text",
        metadata={"conversation_id": "conv_1"},
        importance=0.5,
    )
