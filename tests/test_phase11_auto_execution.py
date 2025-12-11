"""
Tests for Phase 11: Auto Execution Engine

Covers:
- ExecutionContext initialization
- ExecutionStatus and TaskApprovalStatus enums
- AutoExecutionEngine.classify_executability
- AutoExecutionEngine.execute_task
- AutoExecutionEngine.execute_batch
- dry_run behavior (no real external calls)
- Executor dispatch and results
"""

import pytest
from datetime import datetime
from typing import Dict, Any

from aicmo.agency.execution_engine import (
    ExecutionContext,
    ExecutionStatus,
    TaskApprovalStatus,
    ExecutionResult,
    AutoExecutionEngine,
)


class TestExecutionContext:
    """Test ExecutionContext initialization and fields."""
    
    def test_context_creation(self):
        """ExecutionContext can be created with default values."""
        context = ExecutionContext()
        
        assert context.dry_run is False
        assert context.operator_id is None
        assert context.workspace_id is None
        assert context.execution_id is not None
    
    def test_context_with_dry_run(self):
        """ExecutionContext respects dry_run flag."""
        context = ExecutionContext(dry_run=True, operator_id="op_123")
        
        assert context.dry_run is True
        assert context.operator_id == "op_123"


class TestExecutionStatusEnum:
    """Test ExecutionStatus enum values."""
    
    def test_all_statuses_exist(self):
        """All expected statuses are defined."""
        assert ExecutionStatus.NOT_EXECUTABLE
        assert ExecutionStatus.READY_TO_RUN
        assert ExecutionStatus.RUNNING
        assert ExecutionStatus.COMPLETED
        assert ExecutionStatus.COMPLETED_PREVIEW
        assert ExecutionStatus.FAILED
        assert ExecutionStatus.SKIPPED


class TestTaskApprovalStatusEnum:
    """Test TaskApprovalStatus enum."""
    
    def test_approval_statuses(self):
        """All approval statuses are defined."""
        assert TaskApprovalStatus.PROPOSED
        assert TaskApprovalStatus.PENDING_REVIEW
        assert TaskApprovalStatus.APPROVED
        assert TaskApprovalStatus.REJECTED


class TestExecutionResult:
    """Test ExecutionResult data class."""
    
    def test_result_creation(self):
        """ExecutionResult can be created."""
        result = ExecutionResult(
            execution_id="exec_123",
            task_id="task_456",
            status=ExecutionStatus.COMPLETED,
        )
        
        assert result.execution_id == "exec_123"
        assert result.task_id == "task_456"
        assert result.status == ExecutionStatus.COMPLETED
        assert result.completed_at is None
    
    def test_result_add_log(self):
        """ExecutionResult can add log messages."""
        result = ExecutionResult(
            execution_id="exec_123",
            task_id="task_456",
            status=ExecutionStatus.RUNNING,
        )
        
        result.add_log("Test log message")
        
        assert len(result.logs) == 1
        assert "Test log message" in result.logs[0]
    
    def test_result_to_dict(self):
        """ExecutionResult can serialize to dict."""
        result = ExecutionResult(
            execution_id="exec_123",
            task_id="task_456",
            status=ExecutionStatus.COMPLETED,
            output={"key": "value"},
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["execution_id"] == "exec_123"
        assert result_dict["task_id"] == "task_456"
        assert result_dict["status"] == "completed"
        assert result_dict["output"] == {"key": "value"}


class TestAutoExecutionEngineClassification:
    """Test ExecutionEngine.classify_executability."""
    
    def test_classify_missing_required_field(self):
        """Task missing required field → NOT_EXECUTABLE."""
        context = ExecutionContext()
        engine = AutoExecutionEngine(context)
        
        task = {
            "task_id": "task_123",
            # Missing task_type
            "title": "Test Task",
            "description": "Test description",
        }
        
        status = engine.classify_executability(task)
        assert status == ExecutionStatus.NOT_EXECUTABLE
    
    def test_classify_with_all_fields(self):
        """Task with all required fields → READY_TO_RUN."""
        context = ExecutionContext()
        engine = AutoExecutionEngine(context)
        
        task = {
            "task_id": "task_123",
            "task_type": "swot_analysis",
            "title": "SWOT Analysis",
            "description": "Analyze market position",
        }
        
        status = engine.classify_executability(task)
        assert status == ExecutionStatus.READY_TO_RUN
    
    def test_classify_unknown_task_type(self):
        """Task with unknown type → NOT_EXECUTABLE."""
        context = ExecutionContext()
        engine = AutoExecutionEngine(context)
        
        task = {
            "task_id": "task_123",
            "task_type": "unknown_task_type",
            "title": "Unknown",
            "description": "Unknown task",
        }
        
        status = engine.classify_executability(task)
        assert status == ExecutionStatus.NOT_EXECUTABLE
    
    def test_classify_empty_task(self):
        """Empty task dict → NOT_EXECUTABLE."""
        context = ExecutionContext()
        engine = AutoExecutionEngine(context)
        
        status = engine.classify_executability({})
        assert status == ExecutionStatus.NOT_EXECUTABLE


class TestAutoExecutionEngineExecution:
    """Test ExecutionEngine.execute_task."""
    
    def test_execute_unapproved_task(self):
        """Task without approval → NOT_EXECUTABLE."""
        context = ExecutionContext()
        engine = AutoExecutionEngine(context)
        
        task = {
            "task_id": "task_123",
            "task_type": "swot_analysis",
            "title": "SWOT Analysis",
            "description": "Analyze market position",
            "approval_status": "proposed",  # Not approved
        }
        
        result = engine.execute_task("task_123", task)
        
        assert result.status == ExecutionStatus.NOT_EXECUTABLE
        assert "not approved" in result.logs[0].lower()
    
    def test_execute_approved_task(self):
        """Approved task with valid type → executes."""
        context = ExecutionContext(dry_run=True)
        engine = AutoExecutionEngine(context)
        
        task = {
            "task_id": "task_123",
            "task_type": "swot_analysis",
            "title": "SWOT Analysis",
            "description": "Analyze market position",
            "approval_status": "approved",
            "context": {},
        }
        
        result = engine.execute_task("task_123", task)
        
        assert result.task_id == "task_123"
        assert result.status in [ExecutionStatus.COMPLETED, ExecutionStatus.COMPLETED_PREVIEW]
        assert result.output is not None
        assert len(result.logs) > 0
    
    def test_execute_with_dry_run(self):
        """Tasks in dry_run mode mark as COMPLETED_PREVIEW."""
        context = ExecutionContext(dry_run=True)
        engine = AutoExecutionEngine(context)
        
        task = {
            "task_id": "task_123",
            "task_type": "persona_generation",
            "title": "Generate Personas",
            "description": "Create buyer personas",
            "approval_status": "approved",
            "context": {},
        }
        
        result = engine.execute_task("task_123", task)
        
        assert result.status == ExecutionStatus.COMPLETED_PREVIEW
        # Verify output contains dry_run markers
        assert "[DRY RUN]" in str(result.output)
    
    def test_execute_without_dry_run(self):
        """Tasks in live mode mark as COMPLETED."""
        context = ExecutionContext(dry_run=False)
        engine = AutoExecutionEngine(context)
        
        task = {
            "task_id": "task_123",
            "task_type": "messaging_pillars",
            "title": "Messaging Pillars",
            "description": "Generate messaging",
            "approval_status": "approved",
            "context": {},
        }
        
        result = engine.execute_task("task_123", task)
        
        assert result.status == ExecutionStatus.COMPLETED
        assert result.output is not None
    
    def test_execute_sets_timing(self):
        """Execution result includes timing info."""
        context = ExecutionContext(dry_run=True)
        engine = AutoExecutionEngine(context)
        
        task = {
            "task_id": "task_123",
            "task_type": "social_calendar",
            "title": "Social Calendar",
            "description": "Create social calendar",
            "approval_status": "approved",
            "context": {},
        }
        
        result = engine.execute_task("task_123", task)
        
        assert result.completed_at is not None
        assert result.duration_ms > 0


class TestAutoExecutionEngineBatch:
    """Test ExecutionEngine.execute_batch."""
    
    def test_execute_batch_multiple_tasks(self):
        """Batch execution runs multiple tasks."""
        context = ExecutionContext(dry_run=True)
        engine = AutoExecutionEngine(context)
        
        tasks = [
            {
                "task_id": "task_1",
                "task_type": "swot_analysis",
                "title": "SWOT",
                "description": "SWOT analysis",
                "approval_status": "approved",
                "context": {},
            },
            {
                "task_id": "task_2",
                "task_type": "persona_generation",
                "title": "Personas",
                "description": "Generate personas",
                "approval_status": "approved",
                "context": {},
            },
        ]
        
        results = engine.execute_batch(tasks)
        
        assert len(results) == 2
        assert "task_1" in results
        assert "task_2" in results
        assert results["task_1"].status in [ExecutionStatus.COMPLETED, ExecutionStatus.COMPLETED_PREVIEW]
        assert results["task_2"].status in [ExecutionStatus.COMPLETED, ExecutionStatus.COMPLETED_PREVIEW]
    
    def test_execute_batch_respects_max_tasks(self):
        """Batch execution respects max_tasks limit."""
        context = ExecutionContext(dry_run=True)
        engine = AutoExecutionEngine(context)
        
        tasks = [
            {
                "task_id": f"task_{i}",
                "task_type": "swot_analysis",
                "title": f"Task {i}",
                "description": f"Task {i}",
                "approval_status": "approved",
                "context": {},
            }
            for i in range(5)
        ]
        
        results = engine.execute_batch(tasks, max_tasks=3)
        
        assert len(results) == 3  # Only 3 executed despite 5 provided
    
    def test_execute_batch_no_max_limit(self):
        """Batch execution without max_tasks runs all."""
        context = ExecutionContext(dry_run=True)
        engine = AutoExecutionEngine(context)
        
        tasks = [
            {
                "task_id": f"task_{i}",
                "task_type": "messaging_pillars",
                "title": f"Task {i}",
                "description": f"Task {i}",
                "approval_status": "approved",
                "context": {},
            }
            for i in range(3)
        ]
        
        results = engine.execute_batch(tasks)
        
        assert len(results) == 3  # All executed


class TestExecutorMethods:
    """Test specific executor methods."""
    
    def test_social_variants_executor(self):
        """Social variants executor generates variants."""
        context = ExecutionContext(dry_run=True)
        engine = AutoExecutionEngine(context)
        
        task = {
            "task_id": "task_123",
            "task_type": "create_social_variants",
            "title": "Social Variants",
            "description": "Create social variants",
            "approval_status": "approved",
            "context": {"brand_id": "brand_123"},
        }
        
        result = engine.execute_task("task_123", task)
        
        assert result.status == ExecutionStatus.COMPLETED_PREVIEW
        assert "variants" in result.output
        assert "variant_count" in result.metadata
    
    def test_email_rewrite_executor(self):
        """Email rewrite executor generates email variants."""
        context = ExecutionContext(dry_run=True)
        engine = AutoExecutionEngine(context)
        
        task = {
            "task_id": "task_123",
            "task_type": "rewrite_email_sequence",
            "title": "Email Rewrite",
            "description": "Rewrite emails",
            "approval_status": "approved",
            "context": {"brand_id": "brand_123"},
        }
        
        result = engine.execute_task("task_123", task)
        
        assert result.status == ExecutionStatus.COMPLETED_PREVIEW
        assert "emails" in result.output
        assert "email_count" in result.metadata
    
    def test_website_copy_executor(self):
        """Website copy executor generates proposed changes."""
        context = ExecutionContext(dry_run=True)
        engine = AutoExecutionEngine(context)
        
        task = {
            "task_id": "task_123",
            "task_type": "optimize_landing_page_copy",
            "title": "Website Copy",
            "description": "Optimize website copy",
            "approval_status": "approved",
            "context": {},
        }
        
        result = engine.execute_task("task_123", task)
        
        assert result.status == ExecutionStatus.COMPLETED_PREVIEW
        assert "proposed_changes" in result.output
    
    def test_media_generation_executor(self):
        """Media generation executor creates media assets."""
        context = ExecutionContext(dry_run=True)
        engine = AutoExecutionEngine(context)
        
        task = {
            "task_id": "task_123",
            "task_type": "generate_new_creatives",
            "title": "Media Generation",
            "description": "Generate media",
            "approval_status": "approved",
            "context": {},
        }
        
        result = engine.execute_task("task_123", task)
        
        assert result.status == ExecutionStatus.COMPLETED_PREVIEW
        assert "media_assets" in result.output
        assert "asset_count" in result.metadata


class TestExecutionErrorHandling:
    """Test error handling in execution."""
    
    def test_executor_exception_caught(self):
        """Executor exceptions are caught and recorded."""
        context = ExecutionContext()
        engine = AutoExecutionEngine(context)
        
        task = {
            "task_id": "task_123",
            "task_type": "swot_analysis",
            "title": "SWOT",
            "description": "SWOT",
            "approval_status": "approved",
            "context": None,  # Context is handled gracefully
        }
        
        result = engine.execute_task("task_123", task)
        
        # Should complete despite context being None (executor handles it)
        assert result.status in [ExecutionStatus.COMPLETED, ExecutionStatus.COMPLETED_PREVIEW, ExecutionStatus.FAILED]


class TestExecutionIntegration:
    """Integration tests."""
    
    def test_full_execution_workflow(self):
        """Full workflow: classify → execute → record."""
        context = ExecutionContext(
            dry_run=True,
            operator_id="op_123",
            workspace_id="ws_456",
        )
        engine = AutoExecutionEngine(context)
        
        task = {
            "task_id": "task_123",
            "task_type": "creative_directions",
            "title": "Creative Directions",
            "description": "Generate creative directions",
            "approval_status": "approved",
            "context": {"brand_id": "brand_123"},
        }
        
        # Classify
        executability = engine.classify_executability(task)
        assert executability == ExecutionStatus.READY_TO_RUN
        
        # Execute
        result = engine.execute_task("task_123", task)
        assert result.task_id == "task_123"
        assert result.status in [ExecutionStatus.COMPLETED, ExecutionStatus.COMPLETED_PREVIEW]
        assert result.output is not None
        
        # Serialize
        result_dict = result.to_dict()
        assert "execution_id" in result_dict
        assert "status" in result_dict


class TestExecutionMetadata:
    """Test metadata tracking in execution."""
    
    def test_execution_preserves_context(self):
        """Execution preserves operator and workspace context."""
        context = ExecutionContext(
            operator_id="op_alice",
            workspace_id="ws_acme",
            dry_run=True,
        )
        engine = AutoExecutionEngine(context)
        
        task = {
            "task_id": "task_123",
            "task_type": "persona_generation",
            "title": "Personas",
            "description": "Generate personas",
            "approval_status": "approved",
            "context": {},
        }
        
        result = engine.execute_task("task_123", task)
        
        assert result.execution_id == context.execution_id
        # Metadata would be stored by caller with operator context
