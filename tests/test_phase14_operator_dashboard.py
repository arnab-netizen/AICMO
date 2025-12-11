"""
Tests for Phase 14: Operator Command Center

Covers:
- OperatorView models (BrandStatusView, TaskQueueView, etc.)
- OperatorDashboardView aggregation
- AutomationSettings storage and retrieval
- OperatorDashboardService logic
- Automation modes (manual, review_first, full_auto)
- Safety rules (dry_run, approval enforcement)
- Operator service wrapper functions
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from aicmo.operator.dashboard_models import (
    BrandStatusView,
    TaskQueueView,
    ScheduleView,
    FeedbackView,
    AutomationModeView,
    OperatorDashboardView,
)
from aicmo.operator.automation_settings import (
    AutomationSettings,
    AutomationSettingsRepository,
)
from aicmo.operator.dashboard_service import OperatorDashboardService


# ============================================================================
# Tests for Dashboard Models
# ============================================================================

class TestBrandStatusView:
    """Test BrandStatusView model."""
    
    def test_brand_status_creation(self):
        """BrandStatusView can be created."""
        view = BrandStatusView(
            brand_id="brand_123",
            brand_name="Acme Inc",
            key_persona="CEO",
            primary_tone="professional",
            top_channels=["LinkedIn", "Twitter"],
        )
        
        assert view.brand_id == "brand_123"
        assert view.brand_name == "Acme Inc"
        assert view.top_channels == ["LinkedIn", "Twitter"]
    
    def test_brand_status_with_risk_flags(self):
        """BrandStatusView tracks risk flags."""
        view = BrandStatusView(
            brand_id="brand_123",
            risk_flags=["email_underperforming", "low_engagement"],
        )
        
        assert len(view.risk_flags) == 2
        assert "email_underperforming" in view.risk_flags
    
    def test_brand_status_defaults(self):
        """BrandStatusView has sensible defaults."""
        view = BrandStatusView(brand_id="brand_123")
        
        assert view.brand_name is None
        assert view.top_channels == []
        assert view.risk_flags == []


class TestTaskQueueView:
    """Test TaskQueueView model."""
    
    def test_task_queue_creation(self):
        """TaskQueueView can be created."""
        view = TaskQueueView(
            brand_id="brand_123",
            pending=5,
            approved=3,
            running=1,
            completed=10,
            failed=2,
        )
        
        assert view.pending == 5
        assert view.approved == 3
        assert view.running == 1
    
    def test_task_queue_with_recent_tasks(self):
        """TaskQueueView tracks recent tasks."""
        recent = [
            {
                "id": "task_1",
                "type": "social_variants",
                "status": "completed",
                "reason": "Create social variants",
                "created_at": datetime.utcnow(),
            }
        ]
        
        view = TaskQueueView(
            brand_id="brand_123",
            recent_tasks=recent,
        )
        
        assert len(view.recent_tasks) == 1
        assert view.recent_tasks[0]["type"] == "social_variants"


class TestScheduleView:
    """Test ScheduleView model."""
    
    def test_schedule_view_creation(self):
        """ScheduleView can be created."""
        now = datetime.utcnow()
        upcoming = [
            {
                "scheduled_id": "sched_1",
                "task_id": "task_1",
                "task_type": "email_rewrite",
                "run_at": now + timedelta(hours=1),
                "status": "scheduled",
            }
        ]
        
        view = ScheduleView(
            brand_id="brand_123",
            upcoming=upcoming,
        )
        
        assert len(view.upcoming) == 1
        assert view.upcoming[0]["task_type"] == "email_rewrite"
    
    def test_schedule_view_with_overdue(self):
        """ScheduleView tracks overdue tasks."""
        now = datetime.utcnow()
        overdue = [
            {
                "scheduled_id": "sched_2",
                "task_id": "task_2",
                "run_at": now - timedelta(hours=1),
                "status": "scheduled",
            }
        ]
        
        view = ScheduleView(
            brand_id="brand_123",
            overdue=overdue,
        )
        
        assert len(view.overdue) == 1


class TestFeedbackView:
    """Test FeedbackView model."""
    
    def test_feedback_view_creation(self):
        """FeedbackView can be created."""
        view = FeedbackView(
            brand_id="brand_123",
            last_snapshot_at=datetime.utcnow(),
            last_anomalies=["email_open_rate_dropped"],
        )
        
        assert view.brand_id == "brand_123"
        assert len(view.last_anomalies) == 1


class TestAutomationModeView:
    """Test AutomationModeView model."""
    
    def test_automation_mode_manual(self):
        """AutomationModeView supports manual mode."""
        view = AutomationModeView(
            brand_id="brand_123",
            mode="manual",
            dry_run=True,
        )
        
        assert view.mode == "manual"
        assert view.dry_run is True
    
    def test_automation_mode_review_first(self):
        """AutomationModeView supports review_first mode."""
        view = AutomationModeView(
            brand_id="brand_123",
            mode="review_first",
            dry_run=False,
        )
        
        assert view.mode == "review_first"
        assert view.dry_run is False
    
    def test_automation_mode_full_auto(self):
        """AutomationModeView supports full_auto mode."""
        view = AutomationModeView(
            brand_id="brand_123",
            mode="full_auto",
            dry_run=False,
        )
        
        assert view.mode == "full_auto"


class TestOperatorDashboardView:
    """Test OperatorDashboardView model."""
    
    def test_dashboard_view_creation(self):
        """OperatorDashboardView aggregates all sections."""
        brand_status = BrandStatusView(brand_id="brand_123")
        task_queue = TaskQueueView(brand_id="brand_123")
        schedule = ScheduleView(brand_id="brand_123")
        feedback = FeedbackView(brand_id="brand_123")
        automation = AutomationModeView(brand_id="brand_123")
        
        view = OperatorDashboardView(
            brand_id="brand_123",
            brand_status=brand_status,
            task_queue=task_queue,
            schedule=schedule,
            feedback=feedback,
            automation=automation,
        )
        
        assert view.brand_id == "brand_123"
        assert view.brand_status == brand_status
        assert view.snapshot_at is not None
    
    def test_dashboard_view_to_dict(self):
        """OperatorDashboardView can be serialized to dict."""
        brand_status = BrandStatusView(brand_id="brand_123", brand_name="Acme")
        task_queue = TaskQueueView(brand_id="brand_123", pending=5)
        schedule = ScheduleView(brand_id="brand_123")
        feedback = FeedbackView(brand_id="brand_123")
        automation = AutomationModeView(brand_id="brand_123", mode="review_first")
        
        view = OperatorDashboardView(
            brand_id="brand_123",
            brand_status=brand_status,
            task_queue=task_queue,
            schedule=schedule,
            feedback=feedback,
            automation=automation,
        )
        
        data = view.to_dict()
        
        assert data["brand_id"] == "brand_123"
        assert data["brand_status"]["brand_name"] == "Acme"
        assert data["task_queue"]["pending"] == 5
        assert data["automation"]["mode"] == "review_first"
        assert "snapshot_at" in data


# ============================================================================
# Tests for Automation Settings
# ============================================================================

class TestAutomationSettings:
    """Test AutomationSettings dataclass."""
    
    def test_automation_settings_creation(self):
        """AutomationSettings can be created."""
        settings = AutomationSettings(
            brand_id="brand_123",
            mode="review_first",
            dry_run=True,
        )
        
        assert settings.brand_id == "brand_123"
        assert settings.mode == "review_first"
        assert settings.dry_run is True
        assert settings.created_at is not None
        assert settings.updated_at is not None
    
    def test_automation_settings_to_dict(self):
        """AutomationSettings can be serialized."""
        settings = AutomationSettings(
            brand_id="brand_123",
            mode="full_auto",
            dry_run=False,
        )
        
        data = settings.to_dict()
        
        assert data["brand_id"] == "brand_123"
        assert data["mode"] == "full_auto"
        assert data["dry_run"] is False
    
    def test_automation_settings_from_dict(self):
        """AutomationSettings can be deserialized."""
        data = {
            "brand_id": "brand_123",
            "mode": "manual",
            "dry_run": True,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        settings = AutomationSettings.from_dict(data)
        
        assert settings.brand_id == "brand_123"
        assert settings.mode == "manual"
        assert settings.dry_run is True


class TestAutomationSettingsRepository:
    """Test AutomationSettingsRepository."""
    
    def test_repository_creation(self, tmp_path):
        """Repository can be created."""
        repo = AutomationSettingsRepository(data_dir=str(tmp_path / "settings"))
        assert repo is not None
    
    def test_get_default_settings(self, tmp_path):
        """Repository returns default settings when not found."""
        repo = AutomationSettingsRepository(data_dir=str(tmp_path / "settings"))
        
        settings = repo.get_settings("brand_unknown")
        
        assert settings.brand_id == "brand_unknown"
        assert settings.mode == "review_first"
        assert settings.dry_run is True
    
    def test_save_and_retrieve_settings(self, tmp_path):
        """Repository can save and retrieve settings."""
        repo = AutomationSettingsRepository(data_dir=str(tmp_path / "settings"))
        
        # Save
        original = AutomationSettings(
            brand_id="brand_123",
            mode="full_auto",
            dry_run=False,
        )
        repo.save_settings(original)
        
        # Retrieve
        retrieved = repo.get_settings("brand_123")
        
        assert retrieved.brand_id == "brand_123"
        assert retrieved.mode == "full_auto"
        assert retrieved.dry_run is False
    
    def test_list_all_settings(self, tmp_path):
        """Repository can list all settings."""
        repo = AutomationSettingsRepository(data_dir=str(tmp_path / "settings"))
        
        # Save multiple
        for i in range(3):
            settings = AutomationSettings(
                brand_id=f"brand_{i}",
                mode="manual" if i % 2 == 0 else "full_auto",
            )
            repo.save_settings(settings)
        
        # List all
        all_settings = repo.list_all()
        
        assert len(all_settings) == 3


# ============================================================================
# Tests for Dashboard Service
# ============================================================================

class TestOperatorDashboardService:
    """Test OperatorDashboardService."""
    
    def test_service_creation(self):
        """OperatorDashboardService can be created."""
        service = OperatorDashboardService()
        assert service is not None
    
    def test_get_dashboard_view_without_repos(self, tmp_path):
        """Service returns valid view even without repos."""
        from aicmo.operator.automation_settings import AutomationSettingsRepository
        
        # Use temp dir to avoid persisted settings from previous tests
        repo = AutomationSettingsRepository(data_dir=str(tmp_path / "settings"))
        service = OperatorDashboardService(automation_settings_repo=repo)
        
        view = service.get_dashboard_view("brand_unknown_temp")
        
        assert view.brand_id == "brand_unknown_temp"
        assert view.brand_status.brand_id == "brand_unknown_temp"
        assert view.task_queue.brand_id == "brand_unknown_temp"
        assert view.automation.mode == "review_first"
        assert view.automation.dry_run is True
    
    def test_set_automation_mode_manual(self, tmp_path):
        """Service can set manual automation mode."""
        repo = AutomationSettingsRepository(data_dir=str(tmp_path / "settings"))
        service = OperatorDashboardService(
            automation_settings_repo=repo,
        )
        
        result = service.set_automation_mode(
            brand_id="brand_123",
            mode="manual",
            dry_run=True,
        )
        
        assert result["status"] == "success"
        assert result["automation"]["mode"] == "manual"
    
    def test_set_automation_mode_review_first(self, tmp_path):
        """Service can set review_first automation mode."""
        repo = AutomationSettingsRepository(data_dir=str(tmp_path / "settings"))
        service = OperatorDashboardService(
            automation_settings_repo=repo,
        )
        
        result = service.set_automation_mode(
            brand_id="brand_123",
            mode="review_first",
            dry_run=False,
        )
        
        assert result["status"] == "success"
        assert result["automation"]["mode"] == "review_first"
        assert result["automation"]["dry_run"] is False
    
    def test_set_automation_mode_full_auto(self, tmp_path):
        """Service can set full_auto automation mode."""
        repo = AutomationSettingsRepository(data_dir=str(tmp_path / "settings"))
        service = OperatorDashboardService(
            automation_settings_repo=repo,
        )
        
        result = service.set_automation_mode(
            brand_id="brand_123",
            mode="full_auto",
            dry_run=False,
        )
        
        assert result["status"] == "success"
        assert result["automation"]["mode"] == "full_auto"
    
    def test_set_automation_mode_invalid(self, tmp_path):
        """Service rejects invalid automation modes."""
        repo = AutomationSettingsRepository(data_dir=str(tmp_path / "settings"))
        service = OperatorDashboardService(
            automation_settings_repo=repo,
        )
        
        result = service.set_automation_mode(
            brand_id="brand_123",
            mode="invalid_mode",
            dry_run=True,
        )
        
        assert result["status"] == "error"
        assert "Invalid mode" in result["message"]


# ============================================================================
# Tests for Safety Rules
# ============================================================================

class TestSafetyRules:
    """Test automation mode safety rules."""
    
    def test_manual_mode_blocks_execution(self, tmp_path):
        """Manual mode prevents execution cycle."""
        repo = AutomationSettingsRepository(data_dir=str(tmp_path / "settings"))
        service = OperatorDashboardService(
            automation_settings_repo=repo,
        )
        
        # Set manual mode
        service.set_automation_mode("brand_123", "manual", True)
        
        # Try to execute
        result = service.run_execution_cycle_for_brand("brand_123")
        
        assert result["status"] == "skipped"
        assert "manual" in result["reason"].lower()
    
    def test_review_first_mode_explained(self, tmp_path):
        """Review_first mode is explained in results."""
        repo = AutomationSettingsRepository(data_dir=str(tmp_path / "settings"))
        service = OperatorDashboardService(
            automation_settings_repo=repo,
        )
        
        # Set review_first mode
        service.set_automation_mode("brand_123", "review_first", True)
        
        # Execute (should work but respect approved-only logic)
        result = service.run_execution_cycle_for_brand("brand_123")
        
        assert result["status"] in ["success", "error"]
        assert "dry_run" in result
    
    def test_dry_run_flag_preserved(self, tmp_path):
        """dry_run flag is preserved in execution."""
        repo = AutomationSettingsRepository(data_dir=str(tmp_path / "settings"))
        service = OperatorDashboardService(
            automation_settings_repo=repo,
        )
        
        # Set with dry_run=True
        service.set_automation_mode("brand_123", "full_auto", dry_run=True)
        
        # Execute
        result = service.run_execution_cycle_for_brand("brand_123")
        
        assert result["dry_run"] is True
    
    def test_dry_run_disabled_allowed(self, tmp_path):
        """dry_run can be disabled for real execution."""
        repo = AutomationSettingsRepository(data_dir=str(tmp_path / "settings"))
        service = OperatorDashboardService(
            automation_settings_repo=repo,
        )
        
        # Set with dry_run=False (dangerous, but allowed)
        service.set_automation_mode("brand_123", "review_first", dry_run=False)
        
        # Check it was saved
        settings = repo.get_settings("brand_123")
        
        assert settings.dry_run is False


# ============================================================================
# Tests for Workflow Triggers
# ============================================================================

class TestWorkflowTriggers:
    """Test workflow trigger methods."""
    
    def test_run_auto_brain_returns_summary(self):
        """run_auto_brain_for_brand returns execution summary."""
        service = OperatorDashboardService()
        
        result = service.run_auto_brain_for_brand("brand_123")
        
        assert "status" in result
        assert "message" in result
        assert "tasks_created" in result or "error" in result["status"]
    
    def test_run_execution_cycle_returns_summary(self):
        """run_execution_cycle_for_brand returns execution summary."""
        service = OperatorDashboardService()
        
        result = service.run_execution_cycle_for_brand("brand_123", max_tasks=5)
        
        assert "status" in result
        assert "message" in result
    
    def test_run_scheduler_tick_returns_summary(self):
        """run_scheduler_tick_for_brand returns execution summary."""
        service = OperatorDashboardService()
        
        result = service.run_scheduler_tick_for_brand("brand_123", max_to_run=10)
        
        assert "status" in result
        assert "message" in result
    
    def test_run_feedback_cycle_returns_summary(self):
        """run_feedback_cycle_for_brand returns feedback summary."""
        service = OperatorDashboardService()
        
        result = service.run_feedback_cycle_for_brand("brand_123")
        
        assert "status" in result
        assert "message" in result


# ============================================================================
# Tests for Operator Service Wrapper Functions
# ============================================================================

class TestOperatorServiceWrappers:
    """Test operator_services.py wrapper functions."""
    
    def test_get_operator_dashboard_service_factory(self):
        """Factory function creates service."""
        from aicmo.operator_services import get_operator_dashboard_service
        
        service = get_operator_dashboard_service()
        
        assert service is not None
        assert hasattr(service, "get_dashboard_view")
    
    def test_get_brand_dashboard_wrapper(self):
        """Wrapper returns JSON-serializable dashboard."""
        from aicmo.operator_services import get_brand_dashboard
        
        result = get_brand_dashboard("brand_123")
        
        assert "brand_id" in result
        assert "brand_status" in result
        assert "task_queue" in result
        assert "automation" in result
    
    def test_update_automation_settings_wrapper(self, tmp_path):
        """Wrapper updates automation settings."""
        from aicmo.operator_services import (
            get_operator_dashboard_service,
            update_automation_settings,
        )
        
        dashboard_service = get_operator_dashboard_service()
        
        result = update_automation_settings(
            brand_id="brand_123",
            mode="full_auto",
            dry_run=False,
            dashboard_service=dashboard_service,
        )
        
        assert result["status"] == "success"
    
    def test_trigger_auto_brain_wrapper(self):
        """Wrapper triggers AAB."""
        from aicmo.operator_services import trigger_auto_brain
        
        result = trigger_auto_brain("brand_123")
        
        assert "status" in result
        assert "message" in result
    
    def test_trigger_execution_cycle_wrapper(self):
        """Wrapper triggers execution cycle."""
        from aicmo.operator_services import trigger_execution_cycle
        
        result = trigger_execution_cycle("brand_123", max_tasks=5)
        
        assert "status" in result
        assert "message" in result
    
    def test_trigger_scheduler_tick_wrapper(self):
        """Wrapper triggers scheduler tick."""
        from aicmo.operator_services import trigger_scheduler_tick
        
        result = trigger_scheduler_tick("brand_123", max_to_run=10)
        
        assert "status" in result
        assert "message" in result
    
    def test_trigger_feedback_cycle_wrapper(self):
        """Wrapper triggers feedback cycle."""
        from aicmo.operator_services import trigger_feedback_cycle
        
        result = trigger_feedback_cycle("brand_123")
        
        assert "status" in result
        assert "message" in result
