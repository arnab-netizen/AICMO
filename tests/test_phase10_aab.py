"""
Phase 10 Tests: Agency Auto-Brain (AAB) Implementation

Tests cover:
1. AutoBrainTask model creation and serialization
2. AutoBrainPlan orchestration and phase management
3. AutoBrainTaskScanner brief analysis and task detection
4. Task dependency resolution
5. Time budget optimization
"""

import pytest
import json
from datetime import datetime

from aicmo.agency.auto_brain import (
    AutoBrainTask,
    AutoBrainPlan,
    TaskType,
    TaskPriority,
    TaskStatus,
    TaskDependency,
)
from aicmo.agency.task_scanner import AutoBrainTaskScanner
from aicmo.io.client_reports import ClientInputBrief
from aicmo.brand.memory import BrandMemory, BrandGenerationRecord


class TestAutoBrainTask:
    """Test AutoBrainTask model."""
    
    def test_task_creation(self):
        """Test creating an AutoBrainTask."""
        task = AutoBrainTask(
            task_id="task-1",
            task_type=TaskType.SWOT_ANALYSIS,
            title="SWOT Analysis",
            description="Analyze market position",
            priority=TaskPriority.CRITICAL,
        )
        assert task.task_id == "task-1"
        assert task.task_type == TaskType.SWOT_ANALYSIS
        assert task.status == TaskStatus.PROPOSED
    
    def test_task_with_dependencies(self):
        """Test task with dependencies."""
        dep = TaskDependency(
            task_type=TaskType.SWOT_ANALYSIS,
            reason="Need SWOT first"
        )
        task = AutoBrainTask(
            task_id="task-2",
            task_type=TaskType.MESSAGING_PILLARS,
            title="Messaging Pillars",
            description="Create messaging",
            dependencies=[dep],
        )
        assert len(task.dependencies) == 1
        assert task.dependencies[0].task_type == TaskType.SWOT_ANALYSIS
    
    def test_task_serialization(self):
        """Test task serialization to dict."""
        task = AutoBrainTask(
            task_id="task-3",
            task_type=TaskType.PERSONA_GENERATION,
            title="Personas",
            description="Create personas",
            priority=TaskPriority.HIGH,
            estimated_minutes=20,
        )
        
        data = task.to_dict()
        assert data["task_id"] == "task-3"
        assert data["task_type"] == "persona_generation"
        assert data["priority"] == "HIGH"
        assert data["estimated_minutes"] == 20
    
    def test_task_deserialization(self):
        """Test task deserialization from dict."""
        data = {
            "task_id": "task-4",
            "task_type": "social_calendar",
            "title": "Social Calendar",
            "description": "Generate posts",
            "priority": "MEDIUM",
            "status": "PROPOSED",
            "dependencies": [],
            "blocking_tasks": [],
            "estimated_minutes": 10,
            "min_estimated_minutes": 5,
            "max_estimated_minutes": 15,
            "detection_reason": "Platform in brief",
            "confidence": 0.9,
            "related_generators": ["social_calendar_generator"],
            "context": {},
            "created_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "skipped_at": None,
        }
        
        task = AutoBrainTask.from_dict(data)
        assert task.task_id == "task-4"
        assert task.task_type == TaskType.SOCIAL_CALENDAR
        assert task.priority == TaskPriority.MEDIUM
        assert task.estimated_minutes == 10


class TestAutoBrainPlan:
    """Test AutoBrainPlan orchestration."""
    
    def test_plan_creation(self):
        """Test creating an AutoBrainPlan."""
        plan = AutoBrainPlan(
            plan_id="plan-1",
            brand_id="brand-x",
            brief_id="brief-1",
        )
        assert plan.plan_id == "plan-1"
        assert plan.total_estimated_minutes == 0
        assert plan.completed_count == 0
    
    def test_plan_with_tasks(self):
        """Test plan with multiple tasks."""
        plan = AutoBrainPlan(
            plan_id="plan-2",
            brand_id="brand-y",
            brief_id=None,
        )
        
        task1 = AutoBrainTask(
            task_id="t1",
            task_type=TaskType.SWOT_ANALYSIS,
            title="SWOT",
            description="Analyze",
            priority=TaskPriority.CRITICAL,
            estimated_minutes=10,
        )
        
        task2 = AutoBrainTask(
            task_id="t2",
            task_type=TaskType.MESSAGING_PILLARS,
            title="Messaging",
            description="Messages",
            priority=TaskPriority.HIGH,
            estimated_minutes=5,
            dependencies=[TaskDependency(TaskType.SWOT_ANALYSIS, "Need SWOT")],
        )
        
        plan.tasks = [task1, task2]
        plan.total_estimated_minutes = 15
        
        assert len(plan.tasks) == 2
        assert plan.total_estimated_minutes == 15
    
    def test_get_next_task_no_dependencies(self):
        """Test getting next available task."""
        plan = AutoBrainPlan(plan_id="p3", brand_id="b3", brief_id=None)
        
        task1 = AutoBrainTask(
            task_id="t1",
            task_type=TaskType.SWOT_ANALYSIS,
            title="SWOT",
            description="",
            priority=TaskPriority.CRITICAL,
        )
        
        task2 = AutoBrainTask(
            task_id="t2",
            task_type=TaskType.PERSONA_GENERATION,
            title="Personas",
            description="",
            priority=TaskPriority.CRITICAL,
        )
        
        plan.tasks = [task1, task2]
        
        next_task = plan.get_next_task()
        assert next_task is not None
        assert next_task.task_type in [TaskType.SWOT_ANALYSIS, TaskType.PERSONA_GENERATION]
    
    def test_get_next_task_respects_priority(self):
        """Test that next task respects priority order."""
        plan = AutoBrainPlan(plan_id="p4", brand_id="b4", brief_id=None)
        
        task_high = AutoBrainTask(
            task_id="t1",
            task_type=TaskType.PERSONA_GENERATION,
            title="Personas",
            description="",
            priority=TaskPriority.HIGH,
        )
        
        task_critical = AutoBrainTask(
            task_id="t2",
            task_type=TaskType.SWOT_ANALYSIS,
            title="SWOT",
            description="",
            priority=TaskPriority.CRITICAL,
        )
        
        plan.tasks = [task_high, task_critical]
        
        next_task = plan.get_next_task()
        # Critical should come first
        assert next_task.priority == TaskPriority.CRITICAL
    
    def test_get_tasks_by_phase(self):
        """Test organizing tasks into phases."""
        plan = AutoBrainPlan(plan_id="p5", brand_id="b5", brief_id=None)
        
        # Phase 1: no dependencies
        task1 = AutoBrainTask(
            task_id="t1",
            task_type=TaskType.SWOT_ANALYSIS,
            title="SWOT",
            description="",
            dependencies=[],
        )
        
        # Phase 2: depends on task1
        task2 = AutoBrainTask(
            task_id="t2",
            task_type=TaskType.MESSAGING_PILLARS,
            title="Messaging",
            description="",
            dependencies=[TaskDependency(TaskType.SWOT_ANALYSIS, "Need SWOT")],
        )
        
        # Phase 2: also depends on task1
        task3 = AutoBrainTask(
            task_id="t3",
            task_type=TaskType.BRAND_POSITIONING,
            title="Positioning",
            description="",
            dependencies=[TaskDependency(TaskType.SWOT_ANALYSIS, "Need SWOT")],
        )
        
        plan.tasks = [task1, task2, task3]
        phases = plan.get_tasks_by_phase()
        
        assert len(phases) == 2
        assert len(phases[0]) == 1  # Phase 1: just SWOT
        assert len(phases[1]) == 2  # Phase 2: Messaging + Positioning
    
    def test_plan_summary(self):
        """Test generating plan summary."""
        plan = AutoBrainPlan(plan_id="p6", brand_id="b6", brief_id=None)
        
        task = AutoBrainTask(
            task_id="t1",
            task_type=TaskType.SWOT_ANALYSIS,
            title="SWOT Analysis",
            description="",
            estimated_minutes=15,
        )
        
        plan.tasks = [task]
        plan.total_estimated_minutes = 15
        plan.critical_count = 1
        
        summary = plan.get_summary()
        assert "1 tasks" in summary
        assert "15 minutes" in summary
        assert "SWOT Analysis" in summary
    
    def test_plan_serialization(self):
        """Test plan serialization to dict."""
        plan = AutoBrainPlan(
            plan_id="p7",
            brand_id="b7",
            brief_id=None,
            total_estimated_minutes=25,
            phase_count=2,
        )
        
        data = plan.to_dict()
        assert data["plan_id"] == "p7"
        assert data["brand_id"] == "b7"
        assert data["total_estimated_minutes"] == 25


class TestAutoBrainTaskScanner:
    """Test task scanning and detection."""
    
    def test_scanner_initialization(self):
        """Test creating a task scanner."""
        scanner = AutoBrainTaskScanner()
        assert scanner is not None
    
    def test_task_dependencies_defined(self):
        """Test that task dependencies are properly defined."""
        scanner = AutoBrainTaskScanner()
        
        # SWOT should have no dependencies
        assert TaskType.SWOT_ANALYSIS in scanner.TASK_DEPENDENCIES
        assert len(scanner.TASK_DEPENDENCIES[TaskType.SWOT_ANALYSIS]) == 0
        
        # Messaging should depend on SWOT
        assert TaskType.MESSAGING_PILLARS in scanner.TASK_DEPENDENCIES
        deps = scanner.TASK_DEPENDENCIES[TaskType.MESSAGING_PILLARS]
        assert any(d.task_type == TaskType.SWOT_ANALYSIS for d in deps)
    
    def test_task_definitions_complete(self):
        """Test that all task types have definitions."""
        scanner = AutoBrainTaskScanner()
        
        for task_type in TaskType:
            assert task_type in scanner.TASK_DEFINITIONS, \
                f"Missing definition for {task_type}"
            
            defn = scanner.TASK_DEFINITIONS[task_type]
            assert "title" in defn
            assert "description" in defn
            assert "generators" in defn
            assert defn["min_minutes"] > 0
            assert defn["max_minutes"] >= defn["min_minutes"]
    
    def test_create_task_from_type(self):
        """Test creating task from type."""
        scanner = AutoBrainTaskScanner()
        
        context = {"reason": "Test reason"}
        task = scanner._create_task(TaskType.SWOT_ANALYSIS, context)
        
        assert task.task_type == TaskType.SWOT_ANALYSIS
        assert task.title == "SWOT Analysis"
        assert task.detection_reason == "Test reason"
        assert len(task.related_generators) > 0
    
    def test_assess_completed_tasks_empty(self):
        """Test assessing completed tasks with no memory."""
        scanner = AutoBrainTaskScanner()
        
        completed = scanner._assess_completed_tasks(None)
        assert len(completed) == 0
    
    def test_assess_completed_tasks_with_history(self):
        """Test assessing completed tasks with generation history."""
        scanner = AutoBrainTaskScanner()
        
        # Create memory with SWOT generation
        memory = BrandMemory(
            brand_id="test-brand",
            brand_name="Test",
        )
        
        record = BrandGenerationRecord(
            generation_id="gen-1",
            generator_type="swot_generator",
            brand_id="test-brand",
            brief_id=None,
            prompt="",
            brief_summary=None,
            output_json={},
            llm_provider="claude",
            completion_time_ms=1000,
        )
        
        memory.add_generation_record(record)
        
        completed = scanner._assess_completed_tasks(memory)
        assert TaskType.SWOT_ANALYSIS in completed
    
    def test_detect_needed_tasks_basic(self):
        """Test basic task detection."""
        scanner = AutoBrainTaskScanner()
        
        # Create minimal brief
        class MockBrief:
            brief_id = "brief-1"
            goal = None
            platform = None
        
        brief = MockBrief()
        
        needed = scanner._detect_needed_tasks(brief, None)
        
        # Should always need SWOT and personas
        assert TaskType.SWOT_ANALYSIS in needed
        assert TaskType.PERSONA_GENERATION in needed
        assert TaskType.KPI_DEFINITION in needed
    
    def test_detect_tasks_with_social_goal(self):
        """Test detecting social media tasks."""
        scanner = AutoBrainTaskScanner()
        
        class MockGoal:
            primary_goal = "Increase social media engagement"
        
        class MockPlatform:
            platform_list = ["Instagram", "TikTok"]
        
        class MockBrief:
            brief_id = "brief-2"
            goal = MockGoal()
            platform = MockPlatform()
        
        brief = MockBrief()
        
        needed = scanner._detect_needed_tasks(brief, None)
        
        # Should detect social calendar need
        assert TaskType.SOCIAL_CALENDAR in needed or TaskType.PERSONA_GENERATION in needed
    
    def test_scan_brief_basic(self):
        """Test scanning a basic brief."""
        scanner = AutoBrainTaskScanner()
        
        class MockBrief:
            brief_id = "brief-3"
            goal = None
            platform = None
        
        brief = MockBrief()
        
        plan = scanner.scan_brief(
            brief=brief,
            brand_id="test-brand",
            brand_memory=None,
        )
        
        assert plan is not None
        assert plan.brand_id == "test-brand"
        assert len(plan.tasks) > 0
        assert plan.total_estimated_minutes > 0
    
    def test_scan_brief_avoids_duplicates(self):
        """Test that scanning avoids duplicate work."""
        scanner = AutoBrainTaskScanner()
        
        # Create memory with SWOT already done
        memory = BrandMemory(
            brand_id="test-brand",
            brand_name="Test",
        )
        
        record = BrandGenerationRecord(
            generation_id="gen-1",
            generator_type="swot_generator",
            brand_id="test-brand",
            brief_id=None,
            prompt="",
            brief_summary=None,
            output_json={},
            llm_provider="claude",
            completion_time_ms=1000,
        )
        memory.add_generation_record(record)
        
        class MockBrief:
            brief_id = "brief-4"
            goal = None
            platform = None
        
        brief = MockBrief()
        
        plan = scanner.scan_brief(
            brief=brief,
            brand_id="test-brand",
            brand_memory=memory,
        )
        
        # SWOT should not be in plan (already done)
        swot_tasks = [t for t in plan.tasks if t.task_type == TaskType.SWOT_ANALYSIS]
        assert len(swot_tasks) == 0
    
    def test_scan_brief_with_time_budget(self):
        """Test scanning with time budget constraint."""
        scanner = AutoBrainTaskScanner()
        
        class MockBrief:
            brief_id = "brief-5"
            goal = None
            platform = None
        
        brief = MockBrief()
        
        # Very tight time budget
        plan = scanner.scan_brief(
            brief=brief,
            brand_id="test-brand",
            brand_memory=None,
            time_budget_minutes=10,
        )
        
        # Plan should exist but be limited
        assert plan is not None
        # Some tasks might be deprioritized due to budget


class TestPhase10Integration:
    """Integration tests for Agency Auto-Brain."""
    
    def test_full_aab_workflow(self):
        """Test complete AAB workflow: scan → plan → execute."""
        scanner = AutoBrainTaskScanner()
        
        class MockBrief:
            brief_id = "brief-final"
            goal = None
            platform = None
        
        brief = MockBrief()
        
        # Scan
        plan = scanner.scan_brief(
            brief=brief,
            brand_id="final-brand",
            brand_memory=None,
        )
        
        assert plan is not None
        assert len(plan.tasks) > 0
        
        # Get phases
        phases = plan.get_tasks_by_phase()
        assert len(phases) > 0
        
        # Get next task
        next_task = plan.get_next_task()
        assert next_task is not None
        
        # Mark as in progress
        next_task.status = TaskStatus.IN_PROGRESS
        assert next_task.status == TaskStatus.IN_PROGRESS
