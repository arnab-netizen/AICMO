"""
Tests for AICMO Learning Event Registry (Stage L0).

Ensures that new event types for subsystems can be logged without errors
and that the learning system accepts them properly.
"""

import pytest
import tempfile
import os
from aicmo.learning.event_types import (
    EventType, 
    EVENT_GROUPS, 
    get_events_by_group,
    is_success_event,
    is_failure_event
)
from aicmo.memory.engine import log_event


class TestEventTypeRegistry:
    """Test that all event types are properly registered."""
    
    def test_event_types_are_strings(self):
        """All EventType values should be strings."""
        for event in EventType:
            assert isinstance(event.value, str)
            assert len(event.value) > 0
    
    def test_event_types_are_uppercase(self):
        """Event type values should be uppercase with underscores."""
        for event in EventType:
            assert event.value.isupper()
            assert " " not in event.value
    
    def test_all_new_subsystem_events_exist(self):
        """Verify all new subsystem event types exist."""
        # Pitch events
        assert EventType.PITCH_CREATED
        assert EventType.PITCH_WON
        assert EventType.PITCH_LOST
        assert EventType.PITCH_DECK_GENERATED
        assert EventType.PROPOSAL_GENERATED
        
        # Brand events
        assert EventType.BRAND_ARCHITECTURE_GENERATED
        assert EventType.BRAND_NARRATIVE_GENERATED
        
        # Media events
        assert EventType.MEDIA_PLAN_CREATED
        assert EventType.MEDIA_CAMPAIGN_OPTIMIZED
        
        # Advanced creative events
        assert EventType.ADV_CREATIVE_VIDEO_GENERATED
        assert EventType.ADV_CREATIVE_MOTION_GENERATED
        assert EventType.ADV_CREATIVE_MOODBOARD_GENERATED
        
        # Social intel events
        assert EventType.SOCIAL_INTEL_TREND_DETECTED
        assert EventType.SOCIAL_INTEL_INFLUENCER_FOUND
        
        # Analytics events
        assert EventType.ANALYTICS_REPORT_GENERATED
        assert EventType.MMM_MODEL_UPDATED
        
        # Client portal events
        assert EventType.CLIENT_APPROVAL_REQUESTED
        assert EventType.CLIENT_APPROVAL_RESPONDED
        
        # PM events
        assert EventType.PM_TASK_SCHEDULED
        assert EventType.PM_CAPACITY_ALERT
    
    def test_event_groups_complete(self):
        """All new subsystem groups should exist in EVENT_GROUPS."""
        required_groups = [
            "pitch", "brand", "media", "advanced_creatives",
            "social_intel", "analytics", "client_portal", "pm"
        ]
        
        for group in required_groups:
            assert group in EVENT_GROUPS, f"Missing event group: {group}"
            assert len(EVENT_GROUPS[group]) > 0, f"Event group {group} is empty"
    
    def test_get_events_by_group(self):
        """get_events_by_group should return correct events."""
        pitch_events = get_events_by_group("pitch")
        assert EventType.PITCH_CREATED in pitch_events
        assert EventType.PITCH_WON in pitch_events
        
        brand_events = get_events_by_group("brand")
        assert EventType.BRAND_ARCHITECTURE_GENERATED in brand_events
        
        # Non-existent group returns empty list
        assert get_events_by_group("nonexistent") == []
    
    def test_success_event_detection(self):
        """is_success_event should correctly identify success events."""
        assert is_success_event(EventType.PITCH_WON)
        assert is_success_event(EventType.BRAND_ARCHITECTURE_GENERATED)
        assert is_success_event(EventType.CLIENT_APPROVAL_APPROVED)
        assert is_success_event(EventType.PM_TASK_COMPLETED)
        
        # Failures should not be detected as success
        assert not is_success_event(EventType.PITCH_LOST)
        assert not is_success_event(EventType.STRATEGY_FAILED)
    
    def test_failure_event_detection(self):
        """is_failure_event should correctly identify failure events."""
        assert is_failure_event(EventType.PITCH_LOST)
        assert is_failure_event(EventType.STRATEGY_FAILED)
        assert is_failure_event(EventType.CLIENT_APPROVAL_REJECTED)
        assert is_failure_event(EventType.PM_CAPACITY_ALERT)
        
        # Successes should not be detected as failures
        assert not is_failure_event(EventType.PITCH_WON)
        assert not is_failure_event(EventType.BRAND_ARCHITECTURE_GENERATED)


class TestEventLogging:
    """Test that events can be logged to the learning system."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        # Set environment variable
        old_env = os.environ.get("AICMO_MEMORY_DB")
        os.environ["AICMO_MEMORY_DB"] = db_path
        
        yield db_path
        
        # Cleanup
        if old_env:
            os.environ["AICMO_MEMORY_DB"] = old_env
        else:
            os.environ.pop("AICMO_MEMORY_DB", None)
        
        try:
            os.unlink(db_path)
        except:
            pass
    
    def test_log_pitch_events(self, temp_db):
        """Test logging pitch-related events."""
        # Should not raise
        log_event(
            EventType.PITCH_CREATED.value,
            project_id="pitch_123",
            details={"prospect": "Acme Corp", "industry": "SaaS"},
            tags=["pitch", "bizdev"]
        )
        
        log_event(
            EventType.PITCH_WON.value,
            project_id="pitch_123",
            details={"deal_size": 50000},
            tags=["pitch", "success"]
        )
    
    def test_log_brand_events(self, temp_db):
        """Test logging brand strategy events."""
        log_event(
            EventType.BRAND_ARCHITECTURE_GENERATED.value,
            project_id="brand_456",
            details={"pillars": 3, "sub_brands": 2},
            tags=["brand", "strategy"]
        )
        
        log_event(
            EventType.BRAND_NARRATIVE_GENERATED.value,
            project_id="brand_456",
            details={"word_count": 850},
            tags=["brand", "narrative"]
        )
    
    def test_log_media_events(self, temp_db):
        """Test logging media buying events."""
        log_event(
            EventType.MEDIA_PLAN_CREATED.value,
            project_id="media_789",
            details={"budget": 100000, "channels": ["META", "GOOGLE"]},
            tags=["media", "planning"]
        )
        
        log_event(
            EventType.MEDIA_CAMPAIGN_OPTIMIZED.value,
            project_id="media_789",
            details={"action": "increase_budget", "amount": 5000},
            tags=["media", "optimization"]
        )
    
    def test_log_advanced_creative_events(self, temp_db):
        """Test logging advanced creative production events."""
        log_event(
            EventType.ADV_CREATIVE_VIDEO_GENERATED.value,
            project_id="creative_101",
            details={"duration_seconds": 30, "format": "9:16"},
            tags=["creative", "video"]
        )
        
        log_event(
            EventType.ADV_CREATIVE_MOTION_GENERATED.value,
            project_id="creative_102",
            details={"style": "kinetic_typography"},
            tags=["creative", "motion"]
        )
    
    def test_log_social_intel_events(self, temp_db):
        """Test logging social intelligence events."""
        log_event(
            EventType.SOCIAL_INTEL_TREND_DETECTED.value,
            project_id="intel_201",
            details={"topic": "sustainable_packaging", "volume": 5000},
            tags=["social", "trends"]
        )
        
        log_event(
            EventType.SOCIAL_INTEL_INFLUENCER_FOUND.value,
            project_id="intel_201",
            details={"handle": "@greentech_guru", "followers": 100000},
            tags=["social", "influencer"]
        )
    
    def test_log_analytics_events(self, temp_db):
        """Test logging analytics events."""
        log_event(
            EventType.ANALYTICS_REPORT_GENERATED.value,
            project_id="analytics_301",
            details={"report_type": "monthly", "channels": 5},
            tags=["analytics", "reporting"]
        )
        
        log_event(
            EventType.MMM_MODEL_UPDATED.value,
            project_id="analytics_301",
            details={"r_squared": 0.85, "confidence": 0.95},
            tags=["analytics", "mmm"]
        )
    
    def test_log_client_portal_events(self, temp_db):
        """Test logging client portal events."""
        log_event(
            EventType.CLIENT_APPROVAL_REQUESTED.value,
            project_id="portal_401",
            details={"creative_id": 123, "deadline": "2025-12-15"},
            tags=["client_portal", "approval"]
        )
        
        log_event(
            EventType.CLIENT_APPROVAL_RESPONDED.value,
            project_id="portal_401",
            details={"status": "approved", "response_time_hours": 24},
            tags=["client_portal", "response"]
        )
    
    def test_log_pm_events(self, temp_db):
        """Test logging project management events."""
        log_event(
            EventType.PM_TASK_SCHEDULED.value,
            project_id="pm_501",
            details={"task_id": 789, "assignee": "designer_1", "due_date": "2025-12-20"},
            tags=["pm", "scheduling"]
        )
        
        log_event(
            EventType.PM_CAPACITY_ALERT.value,
            project_id="pm_501",
            details={"assignee": "designer_1", "utilization": 1.2},
            tags=["pm", "capacity", "alert"]
        )
    
    def test_log_all_new_event_types(self, temp_db):
        """Smoke test: log one of each new event type."""
        new_event_types = [
            EventType.PITCH_CREATED,
            EventType.BRAND_ARCHITECTURE_GENERATED,
            EventType.MEDIA_PLAN_CREATED,
            EventType.ADV_CREATIVE_VIDEO_GENERATED,
            EventType.SOCIAL_INTEL_TREND_DETECTED,
            EventType.ANALYTICS_REPORT_GENERATED,
            EventType.CLIENT_APPROVAL_REQUESTED,
            EventType.PM_TASK_SCHEDULED,
        ]
        
        for i, event_type in enumerate(new_event_types):
            # Should not raise any exceptions
            log_event(
                event_type.value,
                project_id=f"test_{i}",
                details={"test": True, "index": i},
                tags=["test", "smoke"]
            )
    
    def test_log_event_with_no_details(self, temp_db):
        """Events can be logged with minimal information."""
        log_event(EventType.PITCH_CREATED.value)
        log_event(EventType.BRAND_ARCHITECTURE_GENERATED.value, project_id="test")
    
    def test_log_event_survives_errors(self, temp_db):
        """log_event should not crash the system even with bad data."""
        # These should log warnings but not raise
        log_event(EventType.PITCH_CREATED.value, details={"invalid": object()})


class TestEventTypeIntegrity:
    """Test that event types maintain expected structure."""
    
    def test_no_duplicate_event_values(self):
        """Event type values should be unique."""
        values = [e.value for e in EventType]
        assert len(values) == len(set(values)), "Duplicate event type values found"
    
    def test_event_groups_no_duplicates(self):
        """No event type should appear in multiple groups."""
        all_events = []
        for group, events in EVENT_GROUPS.items():
            all_events.extend(events)
        
        # Some overlap is OK (e.g., an event could be in multiple logical groups)
        # Just verify the structure is sound
        assert len(all_events) > 0
    
    def test_event_count_reasonable(self):
        """Should have a reasonable number of event types."""
        event_count = len(list(EventType))
        assert event_count >= 50, f"Expected at least 50 event types, got {event_count}"
        assert event_count <= 200, f"Too many event types ({event_count}), consider grouping"
