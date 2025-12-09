"""Tests for Kaizen Context building.

Stage K1: Test that KaizenContext aggregates learning events correctly
and provides actionable insights for decision-making.
"""

import pytest
import tempfile
import os
from datetime import datetime

from aicmo.learning.domain import KaizenContext
from aicmo.memory.engine import log_event, build_kaizen_context
from aicmo.learning.event_types import EventType


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    
    old_env = os.environ.get("AICMO_MEMORY_DB")
    os.environ["AICMO_MEMORY_DB"] = db_path
    
    yield db_path
    
    if old_env:
        os.environ["AICMO_MEMORY_DB"] = old_env
    else:
        os.environ.pop("AICMO_MEMORY_DB", None)
    
    if os.path.exists(db_path):
        os.unlink(db_path)


class TestKaizenContextBuilding:
    """Test building KaizenContext from learning events."""
    
    def test_empty_context_when_no_events(self, temp_db):
        """Test that building context with no events returns empty context."""
        context = build_kaizen_context(project_id=999, db_path=temp_db)
        
        assert isinstance(context, KaizenContext)
        assert context.project_id == 999
        assert context.total_events_analyzed == 0
        assert len(context.best_channels) == 0
        assert len(context.rejected_patterns) == 0
    
    def test_media_channel_analysis(self, temp_db):
        """Test that media events populate best/weak channels."""
        project_id = "test-media-123"
        
        # Log media events with channel performance
        log_event(
            EventType.MEDIA_PLAN_CREATED.value,
            project_id=project_id,
            details={"channels": ["meta", "google", "meta"]},
            tags=["media", "planning"]
        )
        
        log_event(
            EventType.MEDIA_CAMPAIGN_OPTIMIZED.value,
            project_id=project_id,
            details={"best_channel": "meta", "action": "increase_budget"},
            tags=["media", "optimization"]
        )
        
        log_event(
            EventType.ANALYTICS_REPORT_GENERATED.value,
            project_id=project_id,
            details={"channel": "twitter", "performance": "poor"},
            tags=["analytics", "channel"]
        )
        
        # Build context
        context = build_kaizen_context(project_id=project_id, db_path=temp_db)
        
        assert context.total_events_analyzed >= 3
        assert "meta" in context.best_channels
        assert "google" in context.best_channels or "google" in str(context.channel_performance)
    
    def test_creative_pattern_tracking(self, temp_db):
        """Test that creative rejection patterns are tracked."""
        project_id = "test-creative-456"
        
        # Log creative rejections
        log_event(
            EventType.CLIENT_COMMENT_RECEIVED.value,
            project_id=project_id,
            details={"hook": "generic startup story", "status": "rejected"},
            tags=["creative", "feedback"]
        )
        
        log_event(
            EventType.CLIENT_APPROVAL_RESPONDED.value,
            project_id=project_id,
            details={"pattern": "boring headline", "rejected": True},
            tags=["creative", "portal"]
        )
        
        log_event(
            EventType.ADV_CREATIVE_MOTION_GENERATED.value,
            project_id=project_id,
            details={"creative_hook": "emotional story", "approved": True},
            tags=["creative", "advanced"]
        )
        
        # Build context
        context = build_kaizen_context(project_id=project_id, db_path=temp_db)
        
        assert len(context.rejected_patterns) > 0
        rejected_hooks = [p["pattern"] for p in context.rejected_patterns]
        assert any("generic" in hook or "boring" in hook for hook in rejected_hooks)
        
        # Successful hooks should be tracked
        assert len(context.successful_hooks) > 0
    
    def test_pitch_win_patterns(self, temp_db):
        """Test that pitch outcomes build win patterns."""
        project_id = "test-pitch-789"
        
        # Log pitch wins
        log_event(
            EventType.PITCH_WON.value,
            project_id=project_id,
            details={"industry": "tech", "prospect_size": "startup"},
            tags=["pitch", "success"]
        )
        
        log_event(
            EventType.PITCH_WON.value,
            project_id=project_id,
            details={"industry": "tech", "deal_size": 50000},
            tags=["pitch", "success"]
        )
        
        log_event(
            EventType.PITCH_LOST.value,
            project_id=project_id,
            details={"industry": "retail"},
            tags=["pitch", "failure"]
        )
        
        # Build context
        context = build_kaizen_context(project_id=project_id, db_path=temp_db)
        
        assert len(context.pitch_win_patterns) > 0
        pattern = context.pitch_win_patterns[0]
        assert pattern["total_wins"] == 2
        assert pattern["win_rate"] > 0.5
        assert "tech" in pattern["successful_industries"]
    
    def test_pm_delay_tracking(self, temp_db):
        """Test that PM events track delays and capacity issues."""
        project_id = "test-pm-101"
        
        # Log PM issues
        log_event(
            EventType.PM_TASK_DELAYED.value,
            project_id=project_id,
            details={"reason": "resource unavailable", "days_delayed": 3},
            tags=["pm", "delay"]
        )
        
        log_event(
            EventType.PM_CAPACITY_ALERT.value,
            project_id=project_id,
            details={"reason": "designers over-allocated"},
            tags=["pm", "capacity"]
        )
        
        # Build context
        context = build_kaizen_context(project_id=project_id, db_path=temp_db)
        
        assert len(context.delay_risks) > 0
        assert len(context.capacity_issues) > 0
    
    def test_approval_pattern_tracking(self, temp_db):
        """Test that client approval patterns are tracked."""
        project_id = "test-portal-202"
        
        # Log approval events
        log_event(
            EventType.CLIENT_APPROVAL_APPROVED.value,
            project_id=project_id,
            details={"asset_type": "video", "status": "approved"},
            tags=["portal", "approval"]
        )
        
        log_event(
            EventType.CLIENT_APPROVAL_APPROVED.value,
            project_id=project_id,
            details={"status": "approved"},
            tags=["portal"]
        )
        
        log_event(
            EventType.CLIENT_APPROVAL_RESPONDED.value,
            project_id=project_id,
            details={"changes": "requested", "feedback": "needs revision"},
            tags=["portal"]
        )
        
        # Build context
        context = build_kaizen_context(project_id=project_id, db_path=temp_db)
        
        assert "approved" in context.approval_patterns
        assert context.approval_patterns["approved"] == 2
        assert context.approval_patterns["changes_requested"] >= 1
    
    def test_multi_event_integration(self, temp_db):
        """Test that context integrates insights from multiple subsystems."""
        project_id = "test-full-303"
        
        # Media
        log_event(EventType.MEDIA_PLAN_CREATED.value, project_id=project_id, 
                 details={"channels": ["meta", "google"]}, tags=["media"])
        
        # Creative
        log_event(EventType.ADV_CREATIVE_STORYBOARD_GENERATED.value, project_id=project_id,
                 details={"creative_hook": "problem-solution", "approved": True}, tags=["creative"])
        
        # Pitch
        log_event(EventType.PITCH_WON.value, project_id=project_id,
                 details={"industry": "saas"}, tags=["pitch"])
        
        # PM
        log_event(EventType.PM_TASK_SCHEDULED.value, project_id=project_id,
                 details={}, tags=["pm"])
        
        # Portal
        log_event(EventType.CLIENT_APPROVAL_APPROVED.value, project_id=project_id,
                 details={"status": "approved"}, tags=["portal"])
        
        # Build context
        context = build_kaizen_context(project_id=project_id, db_path=temp_db)
        
        # Should have insights from multiple areas
        assert context.total_events_analyzed >= 5
        assert len(context.best_channels) > 0  # From media
        assert len(context.successful_hooks) > 0  # From creative
        assert len(context.pitch_win_patterns) > 0  # From pitch
        assert context.approval_patterns["approved"] > 0  # From portal
    
    def test_context_without_project_id(self, temp_db):
        """Test building context without project filter gets all events."""
        # Log events for different projects
        log_event(EventType.MEDIA_PLAN_CREATED.value, project_id="proj-1",
                 details={"channel": "meta"}, tags=["media"])
        log_event(EventType.MEDIA_PLAN_CREATED.value, project_id="proj-2",
                 details={"channel": "google"}, tags=["media"])
        
        # Build context without project filter
        context = build_kaizen_context(db_path=temp_db)
        
        # Should analyze all events
        assert context.total_events_analyzed >= 2
        assert context.project_id is None


class TestKaizenContextModel:
    """Test KaizenContext domain model."""
    
    def test_context_creation(self):
        """Test creating a KaizenContext."""
        context = KaizenContext(
            project_id=123,
            brand_name="TestBrand",
            best_channels=["meta", "google"],
            rejected_patterns=[{"pattern": "boring", "rejection_count": 3}]
        )
        
        assert context.project_id == 123
        assert "meta" in context.best_channels
        assert len(context.rejected_patterns) == 1
    
    def test_context_defaults(self):
        """Test that KaizenContext has sensible defaults."""
        context = KaizenContext()
        
        assert context.project_id is None
        assert context.best_channels == []
        assert context.rejected_patterns == []
        assert context.pitch_win_patterns == []
        assert context.total_events_analyzed == 0
