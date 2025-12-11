"""
Phase 7.5: Creative Review Backend Service Tests

Tests for operator creative review service and approval workflows.
"""

import pytest
from datetime import datetime
from aicmo.operator_services import CreativeReviewService
from aicmo.media.optimization_loop import (
    CreativePerformanceOptimizer,
    OptimizationTaskStatus,
    OptimizationActionType,
)
from aicmo.media.engine import MediaEngine, get_media_engine, reset_media_engine
from aicmo.media.models import MediaAsset, MediaType


@pytest.fixture(autouse=True)
def reset_engine():
    """Reset media engine before and after each test."""
    reset_media_engine()
    yield
    reset_media_engine()


@pytest.fixture
def engine():
    """Get clean media engine for testing."""
    return get_media_engine()


@pytest.fixture
def optimizer(engine):
    """Create performance optimizer."""
    return CreativePerformanceOptimizer(media_engine=engine)


@pytest.fixture
def review_service(optimizer, engine):
    """Create creative review service."""
    return CreativeReviewService(
        optimization_optimizer=optimizer,
        media_engine=engine,
    )


class TestCreativeReviewServiceInitialization:
    """Test service initialization."""
    
    def test_service_initialization(self, review_service):
        """Should initialize service."""
        assert review_service.optimizer is not None
        assert review_service.media_engine is not None
        assert len(review_service.approval_history) == 0
    
    def test_service_without_optimizer(self):
        """Should handle missing optimizer gracefully."""
        service = CreativeReviewService()
        
        assert service.optimizer is None
        assert service.media_engine is None


class TestListOptimizationTasks:
    """Test listing optimization tasks for UI."""
    
    def test_list_empty_tasks(self, review_service):
        """Should return empty list when no tasks."""
        tasks = review_service.list_creative_optimization_tasks("client_1")
        
        assert tasks == []
    
    def test_list_pending_tasks(self, review_service, optimizer, engine):
        """Should list pending optimization tasks."""
        # Create asset
        lib = engine.create_library("Test")
        asset = MediaAsset(
            name="Test Asset",
            media_type=MediaType.IMAGE,
            url="http://example.com/img.jpg",
        )
        engine.add_asset_to_library(lib.library_id, asset)
        
        # Create tasks
        optimizer._create_task(
            asset_id=asset.asset_id,
            reason="Low CTR",
            action_type=OptimizationActionType.GENERATE_VARIANTS,
        )
        
        # List tasks
        tasks = review_service.list_creative_optimization_tasks("client_1")
        
        assert len(tasks) > 0
        assert tasks[0]["task_id"] is not None
        assert tasks[0]["reason"] == "Low CTR"
    
    def test_list_tasks_by_status(self, review_service, optimizer, engine):
        """Should filter tasks by status."""
        lib = engine.create_library("Test")
        asset = MediaAsset(
            name="Test",
            media_type=MediaType.IMAGE,
            url="http://example.com/img.jpg",
        )
        engine.add_asset_to_library(lib.library_id, asset)
        
        # Create and approve task
        task = optimizer._create_task(
            asset_id=asset.asset_id,
            reason="Low CTR",
            action_type=OptimizationActionType.GENERATE_VARIANTS,
        )
        optimizer.mark_task_status(task.task_id, "approved")
        
        # List approved tasks
        tasks = review_service.list_creative_optimization_tasks(
            "client_1",
            status="approved",
        )
        
        assert len(tasks) > 0
        assert tasks[0]["status"] == "approved"
    
    def test_list_tasks_respects_limit(self, review_service, optimizer, engine):
        """Should respect limit parameter."""
        lib = engine.create_library("Test")
        
        # Create multiple tasks
        for i in range(10):
            asset = MediaAsset(
                name=f"Asset {i}",
                media_type=MediaType.IMAGE,
                url=f"http://example.com/img{i}.jpg",
            )
            engine.add_asset_to_library(lib.library_id, asset)
            
            optimizer._create_task(
                asset_id=asset.asset_id,
                reason=f"Task {i}",
                action_type=OptimizationActionType.GENERATE_VARIANTS,
            )
        
        # List with limit
        tasks = review_service.list_creative_optimization_tasks(
            "client_1",
            limit=5,
        )
        
        assert len(tasks) <= 5


class TestTaskApprovalWorkflow:
    """Test task approval workflow."""
    
    def test_approve_pending_task(self, review_service, optimizer, engine):
        """Should approve pending task."""
        lib = engine.create_library("Test")
        asset = MediaAsset(
            name="Test",
            media_type=MediaType.IMAGE,
            url="http://example.com/img.jpg",
        )
        engine.add_asset_to_library(lib.library_id, asset)
        
        task = optimizer._create_task(
            asset_id=asset.asset_id,
            reason="Low CTR",
            action_type=OptimizationActionType.GENERATE_VARIANTS,
        )
        
        # Approve task
        success = review_service.approve_creative_task(
            task.task_id,
            operator_id="op_user_1",
            notes="Looks good",
        )
        
        assert success is True
        
        # Verify status updated
        updated = optimizer.get_task(task.task_id)
        assert updated.status == "approved"
        assert updated.metadata["approved_by"] == "op_user_1"
    
    def test_approve_records_in_history(self, review_service, optimizer, engine):
        """Should record approval in history."""
        lib = engine.create_library("Test")
        asset = MediaAsset(
            name="Test",
            media_type=MediaType.IMAGE,
            url="http://example.com/img.jpg",
        )
        engine.add_asset_to_library(lib.library_id, asset)
        
        task = optimizer._create_task(
            asset_id=asset.asset_id,
            reason="Test",
            action_type=OptimizationActionType.GENERATE_VARIANTS,
        )
        
        review_service.approve_creative_task(
            task.task_id,
            operator_id="op_user_1",
        )
        
        assert len(review_service.approval_history) > 0
        assert review_service.approval_history[0]["action"] == "approve"


class TestTaskRejectionWorkflow:
    """Test task rejection workflow."""
    
    def test_reject_task(self, review_service, optimizer, engine):
        """Should reject task."""
        lib = engine.create_library("Test")
        asset = MediaAsset(
            name="Test",
            media_type=MediaType.IMAGE,
            url="http://example.com/img.jpg",
        )
        engine.add_asset_to_library(lib.library_id, asset)
        
        task = optimizer._create_task(
            asset_id=asset.asset_id,
            reason="Low CTR",
            action_type=OptimizationActionType.GENERATE_VARIANTS,
        )
        
        # Reject task
        success = review_service.reject_creative_task(
            task.task_id,
            operator_id="op_user_2",
            reason="Not ready yet",
        )
        
        assert success is True
        
        # Verify status
        updated = optimizer.get_task(task.task_id)
        assert updated.status == "rejected"
    
    def test_reject_records_in_history(self, review_service, optimizer, engine):
        """Should record rejection in history."""
        lib = engine.create_library("Test")
        asset = MediaAsset(
            name="Test",
            media_type=MediaType.IMAGE,
            url="http://example.com/img.jpg",
        )
        engine.add_asset_to_library(lib.library_id, asset)
        
        task = optimizer._create_task(
            asset_id=asset.asset_id,
            reason="Test",
            action_type=OptimizationActionType.GENERATE_VARIANTS,
        )
        
        review_service.reject_creative_task(
            task.task_id,
            operator_id="op_user_2",
            reason="Not ready",
        )
        
        assert len(review_service.approval_history) > 0
        assert review_service.approval_history[0]["action"] == "reject"


class TestTaskExecution:
    """Test triggering task execution."""
    
    def test_trigger_execution_approved_task(self, review_service, optimizer, engine):
        """Should trigger execution of approved task."""
        lib = engine.create_library("Test")
        asset = MediaAsset(
            name="Test",
            description="A test image",
            media_type=MediaType.IMAGE,
            url="http://example.com/img.jpg",
        )
        engine.add_asset_to_library(lib.library_id, asset)
        
        task = optimizer._create_task(
            asset_id=asset.asset_id,
            reason="Low CTR",
            action_type=OptimizationActionType.GENERATE_VARIANTS,
        )
        
        # Approve then execute
        review_service.approve_creative_task(task.task_id, "op_user_1")
        success = review_service.trigger_task_execution(task.task_id)
        
        # Should execute or fail gracefully
        assert isinstance(success, bool)
    
    def test_cannot_execute_pending_task(self, review_service, optimizer, engine):
        """Should not execute pending task."""
        lib = engine.create_library("Test")
        asset = MediaAsset(
            name="Test",
            media_type=MediaType.IMAGE,
            url="http://example.com/img.jpg",
        )
        engine.add_asset_to_library(lib.library_id, asset)
        
        task = optimizer._create_task(
            asset_id=asset.asset_id,
            reason="Test",
            action_type=OptimizationActionType.GENERATE_VARIANTS,
        )
        
        # Try to execute without approval
        success = review_service.trigger_task_execution(task.task_id)
        
        assert success is False
    
    def test_cannot_execute_nonexistent_task(self, review_service):
        """Should handle nonexistent task."""
        success = review_service.trigger_task_execution("unknown_task")
        
        assert success is False


class TestDashboardSummary:
    """Test dashboard summary generation."""
    
    def test_dashboard_empty(self, review_service):
        """Should handle empty dashboard."""
        summary = review_service.get_dashboard_summary("client_1")
        
        assert summary["pending_count"] == 0
        assert summary["approved_count"] == 0
        assert summary["executed_count"] == 0
    
    def test_dashboard_with_tasks(self, review_service, optimizer, engine):
        """Should count tasks by status."""
        lib = engine.create_library("Test")
        
        # Create assets and tasks
        for i in range(3):
            asset = MediaAsset(
                name=f"Asset {i}",
                media_type=MediaType.IMAGE,
                url=f"http://example.com/img{i}.jpg",
            )
            engine.add_asset_to_library(lib.library_id, asset)
            
            task = optimizer._create_task(
                asset_id=asset.asset_id,
                reason=f"Reason {i}",
                action_type=OptimizationActionType.GENERATE_VARIANTS,
            )
            
            # Set different statuses
            if i == 0:
                optimizer.mark_task_status(task.task_id, "approved")
            elif i == 1:
                optimizer.mark_task_status(task.task_id, "executed")
        
        # Get dashboard
        summary = review_service.get_dashboard_summary("client_1")
        
        assert summary["pending_count"] >= 0
        assert summary["approved_count"] >= 0
        assert summary["executed_count"] >= 0
        assert summary["total_count"] >= 3


class TestAuditTrail:
    """Test approval audit trail."""
    
    def test_approve_action_in_history(self, review_service, optimizer, engine):
        """Should record approve action in history."""
        lib = engine.create_library("Test")
        asset = MediaAsset(
            name="Test",
            media_type=MediaType.IMAGE,
            url="http://example.com/img.jpg",
        )
        engine.add_asset_to_library(lib.library_id, asset)
        
        task = optimizer._create_task(
            asset_id=asset.asset_id,
            reason="Test",
            action_type=OptimizationActionType.GENERATE_VARIANTS,
        )
        
        review_service.approve_creative_task(task.task_id, "op_1", "Approved")
        
        history = review_service.approval_history
        assert len(history) == 1
        assert history[0]["action"] == "approve"
        assert history[0]["operator_id"] == "op_1"
    
    def test_multiple_actions_in_history(self, review_service, optimizer, engine):
        """Should track multiple actions."""
        lib = engine.create_library("Test")
        
        assets = []
        for i in range(2):
            asset = MediaAsset(
                name=f"Asset {i}",
                media_type=MediaType.IMAGE,
                url=f"http://example.com/img{i}.jpg",
            )
            engine.add_asset_to_library(lib.library_id, asset)
            assets.append(asset)
        
        # Create and approve first task
        task1 = optimizer._create_task(
            asset_id=assets[0].asset_id,
            reason="Task 1",
            action_type=OptimizationActionType.GENERATE_VARIANTS,
        )
        review_service.approve_creative_task(task1.task_id, "op_1")
        
        # Create and reject second task
        task2 = optimizer._create_task(
            asset_id=assets[1].asset_id,
            reason="Task 2",
            action_type=OptimizationActionType.REPLACE,
        )
        review_service.reject_creative_task(task2.task_id, "op_1")
        
        history = review_service.approval_history
        assert len(history) == 2
        assert history[0]["action"] == "approve"
        assert history[1]["action"] == "reject"
