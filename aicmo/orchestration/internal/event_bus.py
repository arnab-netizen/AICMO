"""In-process event bus implementation."""
from typing import Callable, Dict, List
from aicmo.orchestration.api.ports import EventBusPort
from aicmo.shared.ids import EventId


class InProcessEventBus(EventBusPort):
    """
    Simple in-memory event bus for Phase 3.
    Supports synchronous publish/subscribe within a single process.
    """

    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._published_events: List[tuple[EventId, dict]] = []

    def publish(self, event_id: EventId, event_data: dict) -> None:
        """
        Publish an event to all subscribed handlers.
        
        Args:
            event_id: Unique identifier for this event instance
            event_data: Event payload (must contain 'event_type' key)
        """
        event_type = event_data.get("event_type")
        if not event_type:
            raise ValueError("event_data must contain 'event_type' key")
        
        # Store for replay/debugging
        self._published_events.append((event_id, event_data))
        
        # Invoke all handlers for this event type
        handlers = self._handlers.get(event_type, [])
        for handler in handlers:
            handler(event_id, event_data)

    def subscribe(self, event_type: str, handler_fn: Callable) -> None:
        """
        Subscribe a handler to an event type.
        
        Args:
            event_type: The type of event to listen for
            handler_fn: Callable with signature (event_id: EventId, event_data: dict) -> None
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler_fn)

    def get_published_events(self) -> List[tuple[EventId, dict]]:
        """Get all published events (for testing/debugging)."""
        return self._published_events.copy()

    def clear_events(self) -> None:
        """Clear event history (for testing)."""
        self._published_events.clear()

    def clear_handlers(self) -> None:
        """Clear all handlers (for testing)."""
        self._handlers.clear()
