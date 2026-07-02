import asyncio

import pytest

from backend.llm.events import Event, EventBus


@pytest.mark.asyncio
async def test_event_bus_pub_sub():
    bus = EventBus()
    received = []

    async def handler(event: Event):
        received.append(event)

    bus.subscribe("test.event", handler)
    bus.publish(Event(name="test.event", source="test", payload={"key": "value"}))

    # Yield control to allow background tasks to process
    await asyncio.sleep(0.01)

    assert len(received) == 1
    assert received[0].source == "test"
    assert received[0].payload["key"] == "value"


@pytest.mark.asyncio
async def test_event_bus_unsubscribe():
    bus = EventBus()
    received = []

    async def handler(event: Event):
        received.append(event)

    bus.subscribe("test.event", handler)
    bus.unsubscribe("test.event", handler)
    bus.publish(Event(name="test.event", source="test"))

    await asyncio.sleep(0.01)
    assert len(received) == 0
