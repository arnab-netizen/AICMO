"""Tests for Project & Resource Management Engine.

Stage PM: PM engine tests
"""

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import patch
import tempfile
import os

from aicmo.domain.intake import ClientIntake
from aicmo.pm.domain import (
    TaskStatus,
    TaskPriority,
    ResourceType,
    Task,
    Resource,
    ResourceAllocation,
    CapacityPlan,
    ProjectTimeline,
    ProjectDashboard,
)
from aicmo.pm.service import (
    create_project_task,
    allocate_resource_to_project,
    generate_capacity_plan,
    generate_project_timeline,
    generate_project_dashboard,
    update_task_status,
    assign_task,
)
from aicmo.learning.event_types import EventType


# ═══════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════


@pytest.fixture
def sample_intake():
    """Sample client intake for testing."""
    return ClientIntake(
        brand_name="PMTestCo",
        industry="Technology",
        product_service="SaaS platform",
        primary_goal="Launch product successfully",
        target_audiences=["Product teams"]
    )


@pytest.fixture
def sample_task():
    """Sample task for testing."""
    return Task(
        task_id="task-1",
        brand_name="PMTestCo",
        project_id="proj-1",
        title="Design homepage mockup",
        description="Create initial homepage design",
        status=TaskStatus.NOT_STARTED,
        priority=TaskPriority.HIGH,
        created_at=datetime.now(),
        due_date=date.today() + timedelta(days=5),
        estimated_hours=8.0
    )


@pytest.fixture
def sample_resource():
    """Sample resource for testing."""
    return Resource(
        resource_id="res-1",
        name="Jane Designer",
        email="jane@agency.com",
        resource_type=ResourceType.DESIGNER,
        role="Senior Designer",
        is_available=True,
        capacity_hours_per_week=40.0,
        skills=["UI/UX", "Figma", "Prototyping"]
    )


# ═══════════════════════════════════════════════════════════════════════
# Domain Model Tests
# ═══════════════════════════════════════════════════════════════════════


class TestTaskDomain:
    """Test Task domain model."""
    
    def test_task_creation(self, sample_task):
        """Test creating a task."""
        assert sample_task.status == TaskStatus.NOT_STARTED
        assert sample_task.priority == TaskPriority.HIGH
        assert sample_task.progress_percent == 0


class TestResourceDomain:
    """Test Resource domain model."""
    
    def test_resource_creation(self, sample_resource):
        """Test creating a resource."""
        assert sample_resource.resource_type == ResourceType.DESIGNER
        assert sample_resource.is_available
        assert len(sample_resource.skills) == 3


class TestResourceAllocationDomain:
    """Test ResourceAllocation domain model."""
    
    def test_allocation_creation(self):
        """Test creating a resource allocation."""
        allocation = ResourceAllocation(
            allocation_id="alloc-1",
            brand_name="TestBrand",
            project_id="proj-1",
            resource_id="res-1",
            resource_name="Designer",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            allocated_hours=120.0,
            is_active=True,
            created_at=datetime.now()
        )
        
        assert allocation.allocated_hours == 120.0
        assert allocation.is_active


# ═══════════════════════════════════════════════════════════════════════
# Service Function Tests
# ═══════════════════════════════════════════════════════════════════════


class TestTaskCreation:
    """Test task creation."""
    
    @pytest.fixture
    def temp_db(self):
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
    
    def test_create_task_returns_task(self, temp_db, sample_intake):
        """Test that create_project_task returns task."""
        task = create_project_task(
            sample_intake,
            project_id="proj-123",
            title="Test Task",
            description="Test description",
            priority=TaskPriority.HIGH
        )
        
        assert isinstance(task, Task)
        assert task.brand_name == sample_intake.brand_name
        assert task.status == TaskStatus.NOT_STARTED
    
    def test_task_has_due_date(self, temp_db, sample_intake):
        """Test that task includes due date."""
        task = create_project_task(
            sample_intake,
            project_id="proj-123",
            title="Task with deadline",
            description="Urgent task",
            due_days=3
        )
        
        assert task.due_date is not None
        assert task.due_date > date.today()
    
    def test_task_logs_event(self, temp_db, sample_intake):
        """Test that task creation logs learning event."""
        with patch('aicmo.pm.service.log_event') as mock_log:
            create_project_task(
                sample_intake,
                project_id="proj-123",
                title="Test",
                description="Test"
            )
            
            mock_log.assert_called()
            call_args = mock_log.call_args[0]
            assert call_args[0] == EventType.PM_TASK_SCHEDULED.value


class TestResourceAllocation:
    """Test resource allocation."""
    
    @pytest.fixture
    def temp_db(self):
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
    
    def test_allocate_returns_allocation(self, temp_db, sample_intake):
        """Test that allocate_resource_to_project returns allocation."""
        allocation = allocate_resource_to_project(
            sample_intake,
            project_id="proj-123",
            resource_id="res-1",
            resource_name="Designer",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            allocated_hours=100.0
        )
        
        assert isinstance(allocation, ResourceAllocation)
        assert allocation.allocated_hours == 100.0
        assert allocation.is_active
    
    def test_allocation_logs_event(self, temp_db, sample_intake):
        """Test that allocation logs learning event."""
        with patch('aicmo.pm.service.log_event') as mock_log:
            allocate_resource_to_project(
                sample_intake,
                project_id="proj-123",
                resource_id="res-1",
                resource_name="Designer",
                start_date=date.today(),
                end_date=date.today() + timedelta(days=30),
                allocated_hours=100.0
            )
            
            mock_log.assert_called()
            call_args = mock_log.call_args[0]
            assert call_args[0] == EventType.PM_RESOURCE_ALLOCATED.value


class TestCapacityPlanning:
    """Test capacity planning."""
    
    @pytest.fixture
    def temp_db(self):
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
    
    def test_generate_plan_returns_plan(self, temp_db):
        """Test that generate_capacity_plan returns plan."""
        start = date.today()
        end = start + timedelta(days=30)
        
        plan = generate_capacity_plan(start, end)
        
        assert isinstance(plan, CapacityPlan)
        assert plan.total_available_hours > 0
        assert 0 <= plan.total_utilization_percent <= 100
    
    def test_plan_has_capacity_breakdown(self, temp_db):
        """Test that plan includes capacity by type."""
        start = date.today()
        end = start + timedelta(days=30)
        
        plan = generate_capacity_plan(start, end)
        
        assert len(plan.capacity_by_type) > 0
        assert len(plan.hiring_needs) >= 0
    
    def test_capacity_logs_event(self, temp_db):
        """Test that capacity planning logs learning event."""
        with patch('aicmo.pm.service.log_event') as mock_log:
            start = date.today()
            end = start + timedelta(days=30)
            generate_capacity_plan(start, end)
            
            mock_log.assert_called()
            call_args = mock_log.call_args[0]
            assert call_args[0] == EventType.PM_CAPACITY_ALERT.value


class TestProjectTimeline:
    """Test project timeline generation."""
    
    @pytest.fixture
    def temp_db(self):
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
    
    def test_generate_timeline_returns_timeline(self, temp_db, sample_intake):
        """Test that generate_project_timeline returns timeline."""
        end_date = date.today() + timedelta(days=60)
        
        timeline = generate_project_timeline(
            sample_intake,
            project_id="proj-123",
            project_name="Test Project",
            target_end_date=end_date
        )
        
        assert isinstance(timeline, ProjectTimeline)
        assert timeline.brand_name == sample_intake.brand_name
        assert timeline.total_tasks > 0
    
    def test_timeline_has_milestones(self, temp_db, sample_intake):
        """Test that timeline includes milestones."""
        end_date = date.today() + timedelta(days=60)
        
        timeline = generate_project_timeline(
            sample_intake,
            project_id="proj-123",
            project_name="Test",
            target_end_date=end_date
        )
        
        assert len(timeline.milestones) > 0
        assert timeline.progress_percent >= 0
    
    def test_timeline_logs_event(self, temp_db, sample_intake):
        """Test that timeline generation logs learning event."""
        with patch('aicmo.pm.service.log_event') as mock_log:
            end_date = date.today() + timedelta(days=60)
            generate_project_timeline(
                sample_intake,
                project_id="proj-123",
                project_name="Test",
                target_end_date=end_date
            )
            
            mock_log.assert_called()
            call_args = mock_log.call_args[0]
            assert call_args[0] == EventType.PM_MILESTONE_REACHED.value


class TestProjectDashboard:
    """Test project dashboard generation."""
    
    @pytest.fixture
    def temp_db(self):
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
    
    def test_generate_dashboard_returns_dashboard(self, temp_db):
        """Test that generate_project_dashboard returns dashboard."""
        dashboard = generate_project_dashboard()
        
        assert isinstance(dashboard, ProjectDashboard)
        assert dashboard.active_projects >= 0
        assert dashboard.total_projects >= dashboard.active_projects
    
    def test_dashboard_has_metrics(self, temp_db):
        """Test that dashboard includes key metrics."""
        dashboard = generate_project_dashboard(brand_name="TestBrand")
        
        assert dashboard.total_tasks > 0
        assert dashboard.total_resources > 0
        assert dashboard.average_utilization >= 0
    
    def test_dashboard_logs_event(self, temp_db):
        """Test that dashboard generation logs learning event."""
        with patch('aicmo.pm.service.log_event') as mock_log:
            generate_project_dashboard()
            
            mock_log.assert_called()
            call_args = mock_log.call_args[0]
            assert call_args[0] == EventType.PM_CAPACITY_ALERT.value


class TestTaskHelpers:
    """Test task helper functions."""
    
    def test_update_status_to_in_progress(self, sample_task):
        """Test updating task to in progress."""
        updated = update_task_status(sample_task, TaskStatus.IN_PROGRESS)
        
        assert updated.status == TaskStatus.IN_PROGRESS
        assert updated.started_at is not None
    
    def test_update_status_to_completed(self, sample_task):
        """Test updating task to completed."""
        updated = update_task_status(sample_task, TaskStatus.COMPLETED, actual_hours=10.0)
        
        assert updated.status == TaskStatus.COMPLETED
        assert updated.completed_at is not None
        assert updated.progress_percent == 100
        assert updated.actual_hours == 10.0
    
    def test_assign_task_to_resource(self, sample_task):
        """Test assigning task to a resource."""
        assigned = assign_task(sample_task, "designer@agency.com", "pm@agency.com")
        
        assert assigned.assigned_to == "designer@agency.com"
        assert assigned.assigned_by == "pm@agency.com"


# ═══════════════════════════════════════════════════════════════════════
# Integration Tests
# ═══════════════════════════════════════════════════════════════════════


class TestPMEngineIntegration:
    """Test PM engine integration."""
    
    @pytest.fixture
    def temp_db(self):
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
    
    def test_complete_pm_workflow(self, temp_db):
        """Test complete project management workflow."""
        # Create intake
        intake = ClientIntake(
            brand_name="WorkflowTest",
            industry="Technology",
            product_service="Mobile app",
            primary_goal="Launch app on time",
            target_audiences=["Mobile users"]
        )
        
        project_id = "proj-workflow-1"
        
        # Create task
        task = create_project_task(
            intake,
            project_id=project_id,
            title="Design app screens",
            description="Create all screen designs",
            priority=TaskPriority.HIGH,
            estimated_hours=40.0
        )
        assert task.status == TaskStatus.NOT_STARTED
        
        # Assign task
        assigned_task = assign_task(task, "designer@agency.com", "pm@agency.com")
        assert assigned_task.assigned_to == "designer@agency.com"
        
        # Start task
        in_progress = update_task_status(assigned_task, TaskStatus.IN_PROGRESS)
        assert in_progress.started_at is not None
        
        # Allocate resource
        allocation = allocate_resource_to_project(
            intake,
            project_id=project_id,
            resource_id="res-1",
            resource_name="Designer",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=14),
            allocated_hours=40.0
        )
        assert allocation.is_active
        
        # Generate timeline
        timeline = generate_project_timeline(
            intake,
            project_id=project_id,
            project_name="Mobile App Launch",
            target_end_date=date.today() + timedelta(days=90)
        )
        assert len(timeline.milestones) > 0
        
        # Check capacity
        capacity = generate_capacity_plan(
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30)
        )
        assert capacity.total_utilization_percent > 0
        
        # Generate dashboard
        dashboard = generate_project_dashboard(brand_name=intake.brand_name)
        assert dashboard.active_projects > 0
