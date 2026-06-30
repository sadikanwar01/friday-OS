import pytest
from backend.database.models import User, Conversation, Message, Memory
from backend.database.repositories.conversation_repo import ConversationRepository
from backend.database.repositories.memory_repo import MemoryRepository

pytestmark = pytest.mark.asyncio

async def test_create_and_get_conversation(db_session):
    # First create a user manually for foreign key constraint
    user = User(name="Test User", security_mode="safe")
    db_session.add(user)
    await db_session.commit()
    
    repo = ConversationRepository(db_session)
    conv = await repo.create(user_id=user.id, title="Test Conv")
    
    assert conv.id is not None
    assert conv.title == "Test Conv"
    assert conv.user_id == user.id
    
    fetched = await repo.get_by_id(conv.id)
    assert fetched is not None
    assert fetched.title == "Test Conv"

async def test_add_message(db_session):
    user = User(name="Test User 2")
    db_session.add(user)
    await db_session.commit()
    
    repo = ConversationRepository(db_session)
    conv = await repo.create(user_id=user.id)
    
    msg = await repo.add_message(
        conversation_id=conv.id,
        role="user",
        content="Hello Friday!"
    )
    
    assert msg.id is not None
    assert msg.role == "user"
    assert msg.content == "Hello Friday!"
    
    messages = await repo.get_messages(conv.id)
    assert len(messages) == 1
    assert messages[0].content == "Hello Friday!"

async def test_memory_repository(db_session):
    user = User(name="Test User 3")
    db_session.add(user)
    await db_session.commit()
    
    repo = MemoryRepository(db_session)
    mem = await repo.store(
        user_id=user.id,
        category="preference",
        key="theme",
        value="dark"
    )
    
    assert mem.id is not None
    
    fetched = await repo.get_by_key(user_id=user.id, key="theme")
    assert fetched is not None
    assert fetched.value == "dark"
    
    memories = await repo.search_by_category(user_id=user.id, category="preference")
    assert len(memories) == 1
