"""
FRIDAY OS - Phase 2A Manual Verification Script.

Tests the Event Bus, Provider Router, and Conversation Engine.
"""

import asyncio
from pathlib import Path

from backend.llm import (
    Event,
    conversation_engine,
    event_bus,
    provider_router,
)
from backend.utils.logger import setup_logging


async def verify():
    # Setup logger for console
    setup_logging(log_level="DEBUG", log_dir=Path("data/logs"), json_output=False)

    print("=" * 60)
    print("FRIDAY OS - Phase 2A Verification")
    print("=" * 60)

    # 1. Verify Event Bus
    print("\n[1] Verifying Event Bus...")
    events_received = []
    async def handler(event: Event):
        events_received.append(event)
        print(f"    -> [Event Received] {event.name} from {event.source}")

    event_bus.subscribe("conversation.started", handler)
    event_bus.subscribe("conversation.completed", handler)
    event_bus.subscribe("conversation.error", handler)
    print("    -> Subscribed to conversation events.")

    # 2. Verify Provider Router Health Checks
    print("\n[2] Verifying Provider Health Checks...")
    health = await provider_router.health_check_all()
    for provider, status in health.items():
        print(f"    -> {provider}: {status}")

    # 3. Verify Engine (will likely fail gracefully if Ollama is not running)
    print("\n[3] Verifying Conversation Engine...")
    try:
        response = await conversation_engine.process_message(
            user_id="test_user",
            conversation_id="test_conv",
            message="Hello, FRIDAY!",
            model_override="llama3.1:8b"
        )
        print(f"\n    -> Engine Response: {response}")
    except Exception as e:
        print(f"\n    -> Engine Error Handled Gracefully: {e.__class__.__name__}: {e}")

    # Wait for events to flush
    await asyncio.sleep(0.1)
    print(f"\n    -> Total Events Processed: {len(events_received)}")

if __name__ == "__main__":
    asyncio.run(verify())
