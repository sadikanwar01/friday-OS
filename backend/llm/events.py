"""
FRIDAY OS - Internal Event Bus.

Provides an asynchronous publish-subscribe pattern to decouple internal modules
(e.g., Memory, Automation, UI, Notifications, Skills) from the core engine.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from backend.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Event:
    """Base class for all internal events."""

    name: str
    source: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


# A subscriber is an async callable that takes an Event and returns None.
EventSubscriber = Callable[[Event], Awaitable[None]]


class EventBus:
    """Asynchronous event bus for decoupling modules."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventSubscriber]] = defaultdict(list)
        # Store tasks to prevent them from being garbage collected mid-execution
        self._background_tasks: set[asyncio.Task] = set()

    def subscribe(self, event_name: str, callback: EventSubscriber) -> None:
        """Register a callback for a specific event."""
        if callback not in self._subscribers[event_name]:
            self._subscribers[event_name].append(callback)
            logger.debug(f"Subscribed to event '{event_name}'", callback=callback.__name__)

    def unsubscribe(self, event_name: str, callback: EventSubscriber) -> None:
        """Unregister a callback for a specific event."""
        if callback in self._subscribers[event_name]:
            self._subscribers[event_name].remove(callback)

    def publish(self, event: Event) -> None:
        """Publish an event asynchronously to all registered subscribers.

        This method returns immediately (fire-and-forget).
        """
        subscribers = self._subscribers.get(event.name, [])
        if not subscribers:
            return

        logger.debug(
            "event_published",
            event_name=event.name,
            source=event.source,
            subscriber_count=len(subscribers),
        )

        for callback in subscribers:
            # Create a background task for each subscriber
            task = asyncio.create_task(self._safe_execute(callback, event))
            self._background_tasks.add(task)
            # Remove task from the set when done
            task.add_done_callback(self._background_tasks.discard)

    async def _safe_execute(self, callback: EventSubscriber, event: Event) -> None:
        """Execute a callback safely, catching any unhandled exceptions."""
        try:
            await callback(event)
        except Exception as e:
            logger.exception(
                "event_handler_failed",
                event_name=event.name,
                callback=callback.__name__,
                error=str(e),
            )


# Global singleton instance of the EventBus
event_bus = EventBus()
