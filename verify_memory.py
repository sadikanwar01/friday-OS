import asyncio
import sys
from unittest.mock import MagicMock

# Mock chromadb globally if missing due to Windows install issues
try:
    import chromadb
except ImportError:
    mock_chromadb = MagicMock()
    mock_chromadb.PersistentClient = MagicMock()
    mock_settings = MagicMock()
    mock_chromadb.config = MagicMock()
    mock_chromadb.config.Settings = mock_settings
    sys.modules["chromadb"] = mock_chromadb
    sys.modules["chromadb.config"] = mock_chromadb.config

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.database.models import Base
from backend.memory.handlers import ConversationMemoryHandler, UserProfileHandler
from backend.memory.manager import MemoryManager


async def main():
    print("Starting Memory System Verification (Phase 2B)...")

    # 1. Setup in-memory SQLite DB
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with async_session() as session:
        manager = MemoryManager(session)

        # Test 1: Add general memory
        print("\n[Test 1] Adding general semantic memory...")
        mem1 = await manager.add_memory(
            user_id="user_123",
            category="fact",
            key="favorite_color",
            value="blue",
            importance=0.8
        )
        print(f"  -> Success: Memory stored (ID: {mem1.id}, Key: {mem1.key})")

        # Test 2: User Profile Handler
        print("\n[Test 2] Testing UserProfileHandler...")
        profile_handler = UserProfileHandler(manager)
        mem2 = await profile_handler.update_fact("user_123", "profession", "Software Engineer")
        print(f"  -> Success: Profile fact stored (Key: {mem2.key}, Importance: {mem2.importance_score})")

        # Test 3: Conversation Memory Handler
        print("\n[Test 3] Testing ConversationMemoryHandler...")
        conv_handler = ConversationMemoryHandler(manager)
        mem3 = await conv_handler.summarize_and_store("user_123", "conv_456", "User wants to build an AI.")
        print(f"  -> Success: Conversation summarized (Key: {mem3.key})")

        # Test 4: Retrieve Pinned Memories
        print("\n[Test 4] Testing pinned memories...")
        await manager.add_memory("user_123", "pinned", "system_prompt_addition", "Always be helpful.", importance=1.0)
        pinned = await manager.get_pinned_memories("user_123")
        print(f"  -> Success: Found {len(pinned)} pinned memory: '{pinned[0].value}'")

        # Test 5: Semantic Search (using the mock/real ChromaDB)
        print("\n[Test 5] Testing semantic search integration...")

        # Since Chroma is likely mocked here, search will return empty unless we mock its return.
        # But we can verify the method signature works.
        try:
            results = await manager.search("user_123", "color")
            print(f"  -> Success: Semantic search completed (Returned {len(results)} results)")
        except Exception as e:
            print(f"  -> Error: Semantic search failed: {e}")

    print("\nVerification Complete!")

if __name__ == "__main__":
    asyncio.run(main())
