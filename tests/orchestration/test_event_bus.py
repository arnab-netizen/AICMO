"""Tests for InProcessEventBus."""
import pytest
from aicmo.orchestration.internal.event_bus import InProcessEventBus
from aicmo.shared.ids import EventId


def test_event_bus_publish_and_subscribe():
    """Test basic publish/subscribe functionality."""
    bus = InProcessEventBus()
    received_events = []

    def handler(event_id: EventId, event_data: dict):
        received_events.append((event_id, event_data))

    bus.subscribe("test.event", handler)
    
    event_id = EventId("evt_123")
    event_data = {"event_type": "test.event", "payload": "hello"}
    
    bus.publish(event_id, event_data)
    
    assert len(received_events) == 1
    assert received_events[0][0] == event_id
    assert received_events[0][1] == event_data


def test_event_bus_multiple_handlers():
    """Test multiple handlers for same event type."""
    bus = InProcessEventBus()
    handler1_calls = []
    handler2_calls = []

    def handler1(event_id: EventId, event_data: dict):
        handler1_calls.append(event_id)

    def handler2(event_id: EventId, event_data: dict):
        handler2_calls.append(event_id)

    bus.subscribe("multi.event", handler1)
    bus.subscribe("multi.event", handler2)
    
    event_id = EventId("evt_multi")
    bus.publish(event_id, {"event_type": "multi.event"})
    
    assert len(handler1_calls) == 1
    assert len(handler2_calls) == 1


def test_event_bus_multiple_event_types():
    """Test different handlers for different event types."""
    bus = InProcessEventBus()
    type_a_calls = []
    type_b_calls = []

    def handler_a(event_id: EventId, event_data: dict):
        type_a_calls.append(event_id)

    def handler_b(event_id: EventId, event_data: dict):
        type_b_calls.append(event_id)

    bus.subscribe("type.a", handler_a)
    bus.subscribe("type.b", handler_b)
    
    bus.publish(EventId("evt_a"), {"event_type": "type.a"})
    bus.publish(EventId("evt_b"), {"event_type": "type.b"})
    
    assert len(type_a_calls) == 1
    assert len(type_b_calls) == 1


def test_event_bus_no_handlers():
    """Test publishing to event type with no handlers."""
    bus = InProcessEventBus()
    
    # Should not raise
    bus.publish(EventId("evt_orphan"), {"event_type": "orphan.event"})
    
    events = bus.get_published_events()
    assert len(events) == 1


def test_event_bus_missing_event_type():
    """Test that event_data must contain event_type."""
    bus = InProcessEventBus()
    
    with pytest.raises(ValueError, match="event_type"):
        bus.publish(EventId("evt_bad"), {"payload": "data"})


def test_event_bus_get_published_events():
    """Test retrieving published event history."""
    bus = InProcessEventBus()
    
    bus.publish(EventId("evt_1"), {"event_type": "test", "seq": 1})
    bus.publish(EventId("evt_2"), {"event_type": "test", "seq": 2})
    
    events = bus.get_published_events()
    assert len(events) == 2
    assert events[0][0] == EventId("evt_1")
    assert events[1][0] == EventId("evt_2")


def test_event_bus_clear_events():
    """Test clearing event history."""
    bus = InProcessEventBus()
    
    bus.publish(EventId("evt_1"), {"event_type": "test"})
    assert len(bus.get_published_events()) == 1
    
    bus.clear_events()
    assert len(bus.get_published_events()) == 0


def test_event_bus_clear_handlers():
    """Test clearing all handlers."""
    bus = InProcessEventBus()
    received = []

    def handler(event_id: EventId, event_data: dict):
        received.append(event_id)

    bus.subscribe("test", handler)
    bus.publish(EventId("evt_1"), {"event_type": "test"})
    assert len(received) == 1
    
    bus.clear_handlers()
    bus.publish(EventId("evt_2"), {"event_type": "test"})
    # Handler was cleared, so no new events received
    assert len(received) == 1
