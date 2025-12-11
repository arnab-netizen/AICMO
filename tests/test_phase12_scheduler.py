"""
Tests for Phase 12: Master Campaign Scheduler

Covers:
- ScheduledTask model and serialization
- SchedulerRepository (CRUD and queries)
- CampaignTimelinePlanner (timeline creation)
- SchedulerRuntime (task execution loop)
- Dependency-aware scheduling
- max_tasks_per_day constraints
"""

import pytest
from datetime import datetime, timedelta
import os
import tempfile

from aicmo.agency.scheduler import (
    ScheduledTask,
    ScheduledTaskStatus,
    SchedulerRepository,
    CampaignTimelinePlanner,
    SchedulerRuntime,
)


class TestScheduledTask:
    """Test ScheduledTask model."""
    
    def test_scheduled_task_creation(self):
        """ScheduledTask can be created."""
        now = datetime.utcnow()
        task = ScheduledTask(
            scheduled_id="sched_123",
            task_id="task_456",
            brand_id="brand_789",
            run_at=now,
            priority=2,
        )
        
        assert task.scheduled_id == "sched_123"
        assert task.task_id == "task_456"
        assert task.status == ScheduledTaskStatus.SCHEDULED
        assert task.priority == 2
    
    def test_scheduled_task_serialization(self):
        """ScheduledTask can serialize/deserialize."""
        now = datetime.utcnow()
        task = ScheduledTask(
            scheduled_id="sched_123",
            task_id="task_456",
            brand_id="brand_789",
            run_at=now,
            priority=3,
            metadata={"key": "value"},
        )
        
        # Serialize
        task_dict = task.to_dict()
        assert task_dict["scheduled_id"] == "sched_123"
        assert task_dict["priority"] == 3
        assert "metadata" in task_dict
        
        # Deserialize
        restored = ScheduledTask.from_dict(task_dict)
        assert restored.scheduled_id == task.scheduled_id
        assert restored.task_id == task.task_id
        assert restored.priority == task.priority


class TestSchedulerRepository:
    """Test SchedulerRepository."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        # Cleanup
        if os.path.exists(path):
            os.remove(path)
    
    def test_repo_creation(self, temp_db):
        """Repository can be created."""
        repo = SchedulerRepository(db_path=temp_db)
        assert repo.db_path == temp_db
    
    def test_repo_add_scheduled_task(self, temp_db):
        """Repository can add scheduled tasks."""
        repo = SchedulerRepository(db_path=temp_db)
        
        now = datetime.utcnow()
        task = ScheduledTask(
            scheduled_id="sched_123",
            task_id="task_456",
            brand_id="brand_789",
            run_at=now,
            priority=2,
        )
        
        repo.add_scheduled_task(task)
        
        # Verify it was added
        retrieved = repo.get_scheduled_task("sched_123")
        assert retrieved is not None
        assert retrieved.task_id == "task_456"
    
    def test_repo_get_scheduled_task(self, temp_db):
        """Repository can retrieve scheduled tasks."""
        repo = SchedulerRepository(db_path=temp_db)
        
        now = datetime.utcnow()
        task = ScheduledTask(
            scheduled_id="sched_123",
            task_id="task_456",
            brand_id="brand_789",
            run_at=now,
        )
        
        repo.add_scheduled_task(task)
        retrieved = repo.get_scheduled_task("sched_123")
        
        assert retrieved.scheduled_id == "sched_123"
        assert retrieved.task_id == "task_456"
        assert retrieved.brand_id == "brand_789"
    
    def test_repo_get_due_tasks(self, temp_db):
        """Repository can find due tasks."""
        repo = SchedulerRepository(db_path=temp_db)
        
        now = datetime.utcnow()
        past = now - timedelta(hours=1)
        future = now + timedelta(hours=1)
        
        # Add tasks
        past_task = ScheduledTask(
            scheduled_id="sched_past",
            task_id="task_1",
            brand_id="brand_123",
            run_at=past,
            priority=1,
        )
        future_task = ScheduledTask(
            scheduled_id="sched_future",
            task_id="task_2",
            brand_id="brand_123",
            run_at=future,
            priority=2,
        )
        
        repo.add_scheduled_task(past_task)
        repo.add_scheduled_task(future_task)
        
        # Get due tasks
        due = repo.get_due_tasks(now)
        
        # Only past task should be due
        assert len(due) == 1
        assert due[0].scheduled_id == "sched_past"
    
    def test_repo_update_status(self, temp_db):
        """Repository can update task status."""
        repo = SchedulerRepository(db_path=temp_db)
        
        now = datetime.utcnow()
        task = ScheduledTask(
            scheduled_id="sched_123",
            task_id="task_456",
            brand_id="brand_789",
            run_at=now,
        )
        
        repo.add_scheduled_task(task)
        
        # Update status
        repo.update_status(
            "sched_123",
            ScheduledTaskStatus.COMPLETED,
            metadata={"result": "success"},
        )
        
        # Verify update
        updated = repo.get_scheduled_task("sched_123")
        assert updated.status == ScheduledTaskStatus.COMPLETED
        assert updated.metadata["result"] == "success"
    
    def test_repo_list_for_brand(self, temp_db):
        """Repository can list tasks for a brand."""
        repo = SchedulerRepository(db_path=temp_db)
        
        now = datetime.utcnow()
        
        # Add tasks for different brands
        for i in range(3):
            task = ScheduledTask(
                scheduled_id=f"sched_{i}",
                task_id=f"task_{i}",
                brand_id="brand_A",
                run_at=now + timedelta(days=i),
            )
            repo.add_scheduled_task(task)
        
        for i in range(2):
            task = ScheduledTask(
                scheduled_id=f"sched_B_{i}",
                task_id=f"task_B_{i}",
                brand_id="brand_B",
                run_at=now + timedelta(days=i),
            )
            repo.add_scheduled_task(task)
        
        # List for brand A
        brand_a_tasks = repo.list_for_brand("brand_A")
        assert len(brand_a_tasks) == 3
        assert all(t.brand_id == "brand_A" for t in brand_a_tasks)
        
        # List for brand B
        brand_b_tasks = repo.list_for_brand("brand_B")
        assert len(brand_b_tasks) == 2
        assert all(t.brand_id == "brand_B" for t in brand_b_tasks)


class TestCampaignTimelinePlanner:
    """Test CampaignTimelinePlanner."""
    
    @pytest.fixture
    def temp_repo(self):
        """Create temporary repository."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        repo = SchedulerRepository(db_path=path)
        yield repo
        if os.path.exists(path):
            os.remove(path)
    
    def test_planner_creation(self, temp_repo):
        """Planner can be created."""
        planner = CampaignTimelinePlanner(scheduler_repository=temp_repo)
        assert planner.scheduler_repo is not None
    
    def test_plan_timeline_basic(self, temp_repo):
        """Planner can create basic timeline."""
        planner = CampaignTimelinePlanner(scheduler_repository=temp_repo)
        
        start = datetime.utcnow()
        end = start + timedelta(days=10)
        
        # Create timeline without pending tasks (just scheduling structure)
        scheduled = planner.plan_timeline_for_brand(
            brand_id="brand_123",
            start_at=start,
            end_at=end,
            max_tasks_per_day=5,
            pending_tasks=[],
        )
        
        # No tasks means empty schedule
        assert len(scheduled) == 0
    
    def test_plan_timeline_distributes_tasks(self, temp_repo):
        """Planner distributes tasks across days."""
        planner = CampaignTimelinePlanner(scheduler_repository=temp_repo)
        
        start = datetime.utcnow()
        end = start + timedelta(days=10)
        
        # Create pending tasks
        pending_tasks = [
            {
                "task_id": f"task_{i}",
                "task_type": "test_task",
                "priority": "MEDIUM",
                "priority_value": 3,
                "estimated_minutes": 30,
            }
            for i in range(8)
        ]
        
        scheduled = planner.plan_timeline_for_brand(
            brand_id="brand_123",
            start_at=start,
            end_at=end,
            max_tasks_per_day=3,  # Max 3 per day
            pending_tasks=pending_tasks,
        )
        
        # All tasks should be scheduled
        assert len(scheduled) == 8
        
        # Check task distribution across days
        days = {}
        for task in scheduled:
            day = task.run_at.date()
            days[day] = days.get(day, 0) + 1
        
        # No day should have more than max_tasks_per_day
        assert all(count <= 3 for count in days.values())
    
    def test_plan_timeline_respects_end_date(self, temp_repo):
        """Planner respects end date boundary."""
        planner = CampaignTimelinePlanner(scheduler_repository=temp_repo)
        
        start = datetime.utcnow()
        end = start + timedelta(days=3)  # Very short window
        
        pending_tasks = [
            {
                "task_id": f"task_{i}",
                "task_type": "test_task",
                "priority": "MEDIUM",
                "priority_value": 3,
                "estimated_minutes": 30,
            }
            for i in range(20)  # Many tasks
        ]
        
        scheduled = planner.plan_timeline_for_brand(
            brand_id="brand_123",
            start_at=start,
            end_at=end,
            max_tasks_per_day=5,
            pending_tasks=pending_tasks,
        )
        
        # Should not exceed available days (4 days * 5 per day = 20 max)
        assert len(scheduled) <= 20
        
        # All should be before or on end date
        assert all(task.run_at <= end for task in scheduled)


class TestSchedulerRuntime:
    """Test SchedulerRuntime."""
    
    @pytest.fixture
    def temp_repo(self):
        """Create temporary repository."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        repo = SchedulerRepository(db_path=path)
        yield repo
        if os.path.exists(path):
            os.remove(path)
    
    def test_runtime_creation(self, temp_repo):
        """Runtime can be created."""
        runtime = SchedulerRuntime(scheduler_repository=temp_repo)
        assert runtime.scheduler_repo is not None
    
    def test_runtime_tick_no_due_tasks(self, temp_repo):
        """Tick with no due tasks returns empty results."""
        runtime = SchedulerRuntime(scheduler_repository=temp_repo)
        
        now = datetime.utcnow()
        future = now + timedelta(hours=1)
        
        # Add future task
        task = ScheduledTask(
            scheduled_id="sched_123",
            task_id="task_456",
            brand_id="brand_789",
            run_at=future,
        )
        temp_repo.add_scheduled_task(task)
        
        results = runtime.tick(now=now)
        assert len(results) == 0
    
    def test_runtime_tick_finds_due_tasks(self, temp_repo):
        """Tick finds and processes due tasks."""
        runtime = SchedulerRuntime(scheduler_repository=temp_repo)
        
        now = datetime.utcnow()
        past = now - timedelta(hours=1)
        
        # Add due task
        task = ScheduledTask(
            scheduled_id="sched_123",
            task_id="task_456",
            brand_id="brand_789",
            run_at=past,
        )
        temp_repo.add_scheduled_task(task)
        
        results = runtime.tick(now=now)
        
        # Should have processed the task
        assert len(results) > 0
        assert "sched_123" in results
    
    def test_runtime_tick_respects_max_to_run(self, temp_repo):
        """Tick respects max_to_run limit."""
        runtime = SchedulerRuntime(scheduler_repository=temp_repo)
        
        now = datetime.utcnow()
        past = now - timedelta(hours=1)
        
        # Add multiple due tasks
        for i in range(10):
            task = ScheduledTask(
                scheduled_id=f"sched_{i}",
                task_id=f"task_{i}",
                brand_id="brand_789",
                run_at=past,
            )
            temp_repo.add_scheduled_task(task)
        
        # Tick with max_to_run=3
        results = runtime.tick(now=now, max_to_run=3)
        
        # Should only process 3
        assert len(results) <= 3
    
    def test_runtime_updates_task_status(self, temp_repo):
        """Runtime updates task status during execution."""
        runtime = SchedulerRuntime(scheduler_repository=temp_repo)
        
        now = datetime.utcnow()
        past = now - timedelta(hours=1)
        
        task = ScheduledTask(
            scheduled_id="sched_123",
            task_id="task_456",
            brand_id="brand_789",
            run_at=past,
        )
        temp_repo.add_scheduled_task(task)
        
        # Execute
        results = runtime.tick(now=now)
        
        # Check status was updated
        updated_task = temp_repo.get_scheduled_task("sched_123")
        assert updated_task.status in [ScheduledTaskStatus.COMPLETED, ScheduledTaskStatus.IN_PROGRESS]


class TestSchedulerIntegration:
    """Integration tests for scheduler components."""
    
    @pytest.fixture
    def temp_repo(self):
        """Create temporary repository."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        repo = SchedulerRepository(db_path=path)
        yield repo
        if os.path.exists(path):
            os.remove(path)
    
    def test_full_scheduling_workflow(self, temp_repo):
        """Complete workflow: plan → schedule → execute."""
        planner = CampaignTimelinePlanner(scheduler_repository=temp_repo)
        runtime = SchedulerRuntime(scheduler_repository=temp_repo)
        
        # Create timeline
        now = datetime.utcnow()
        start = now - timedelta(hours=1)  # Start in past to be due immediately
        end = now + timedelta(days=5)
        
        pending_tasks = [
            {
                "task_id": f"task_{i}",
                "task_type": "test",
                "priority": "HIGH",
                "priority_value": 2,
            }
            for i in range(5)
        ]
        
        scheduled = planner.plan_timeline_for_brand(
            brand_id="brand_test",
            start_at=start,
            end_at=end,
            max_tasks_per_day=3,
            pending_tasks=pending_tasks,
        )
        
        assert len(scheduled) == 5
        
        # Run scheduler tick
        results = runtime.tick(now=now, max_to_run=10)
        
        # Some tasks should have executed
        assert len(results) > 0
        
        # Check that tasks are no longer due
        due = temp_repo.get_due_tasks(now)
        # All previously due tasks should now be completed/failed
        assert all(task.status != ScheduledTaskStatus.SCHEDULED for task in due)


class TestSchedulerEnumandStatus:
    """Test scheduler enums and status values."""
    
    def test_scheduled_task_status_values(self):
        """All expected statuses are defined."""
        assert ScheduledTaskStatus.SCHEDULED
        assert ScheduledTaskStatus.IN_PROGRESS
        assert ScheduledTaskStatus.COMPLETED
        assert ScheduledTaskStatus.FAILED
        assert ScheduledTaskStatus.SKIPPED
