"""Phase 2 tests: Project workflow and orchestration.

Verifies that:
1. Project state machine works correctly
2. State transitions are validated
3. ProjectOrchestrator manages lifecycle properly
4. Integration with Phase 1 strategy service works
5. No breaking changes to existing backend
"""

import pytest
from unittest.mock import AsyncMock, patch

from aicmo.domain.project import Project, ProjectState
from aicmo.domain.intake import ClientIntake
from aicmo.domain.strategy import StrategyDoc
from aicmo.core.workflow import is_valid_transition, get_valid_transitions
from aicmo.delivery.orchestrator import ProjectOrchestrator


class TestPhase2WorkflowStateMachine:
    """Phase 2: Workflow state machine tests."""

    def test_valid_transitions_from_new_lead(self):
        """NEW_LEAD can transition to INTAKE_PENDING or CANCELLED."""
        assert is_valid_transition(ProjectState.NEW_LEAD, ProjectState.INTAKE_PENDING)
        assert is_valid_transition(ProjectState.NEW_LEAD, ProjectState.CANCELLED)
        assert not is_valid_transition(ProjectState.NEW_LEAD, ProjectState.STRATEGY_DRAFT)

    def test_valid_transitions_from_strategy_draft(self):
        """STRATEGY_DRAFT can be revised, approved, or cancelled."""
        assert is_valid_transition(ProjectState.STRATEGY_DRAFT, ProjectState.STRATEGY_APPROVED)
        assert is_valid_transition(ProjectState.STRATEGY_DRAFT, ProjectState.STRATEGY_IN_PROGRESS)
        assert is_valid_transition(ProjectState.STRATEGY_DRAFT, ProjectState.CANCELLED)
        assert not is_valid_transition(ProjectState.STRATEGY_DRAFT, ProjectState.CREATIVE_DRAFT)

    def test_terminal_state_cancelled(self):
        """CANCELLED is a terminal state with no transitions out."""
        valid = get_valid_transitions(ProjectState.CANCELLED)
        assert len(valid) == 0

    def test_execution_done_limited_transitions(self):
        """EXECUTION_DONE can only go to ON_HOLD."""
        valid = get_valid_transitions(ProjectState.EXECUTION_DONE)
        assert ProjectState.ON_HOLD in valid
        assert len(valid) == 1

    def test_on_hold_resume_flexibility(self):
        """ON_HOLD can resume to various states."""
        valid = get_valid_transitions(ProjectState.ON_HOLD)
        assert ProjectState.INTAKE_PENDING in valid
        assert ProjectState.STRATEGY_IN_PROGRESS in valid
        assert ProjectState.CREATIVE_IN_PROGRESS in valid
        assert ProjectState.EXECUTION_IN_PROGRESS in valid


class TestPhase2ProjectModel:
    """Phase 2: Enhanced Project model tests."""

    def test_project_creation_with_defaults(self):
        """Project can be created with minimal fields."""
        project = Project(name="Test Project")
        assert project.name == "Test Project"
        assert project.state == ProjectState.STRATEGY_DRAFT
        assert project.id is None
        assert project.client_name is None

    def test_project_with_full_fields(self):
        """Project can be created with all fields."""
        project = Project(
            id=1,
            name="Full Project",
            state=ProjectState.STRATEGY_APPROVED,
            client_name="ACME Corp",
            client_email="contact@acme.com",
            intake_id=10,
            strategy_id=20,
            notes="Important client"
        )
        assert project.id == 1
        assert project.client_name == "ACME Corp"
        assert project.intake_id == 10

    def test_project_can_transition_to(self):
        """Project.can_transition_to() validates transitions."""
        project = Project(name="Test", state=ProjectState.STRATEGY_DRAFT)
        assert project.can_transition_to(ProjectState.STRATEGY_APPROVED)
        assert not project.can_transition_to(ProjectState.EXECUTION_DONE)

    def test_project_transition_to_success(self):
        """Project.transition_to() changes state when valid."""
        project = Project(name="Test", state=ProjectState.STRATEGY_DRAFT)
        updated = project.transition_to(ProjectState.STRATEGY_APPROVED)
        assert updated.state == ProjectState.STRATEGY_APPROVED

    def test_project_transition_to_invalid_raises(self):
        """Project.transition_to() raises ValueError for invalid transition."""
        project = Project(name="Test", state=ProjectState.STRATEGY_DRAFT)
        with pytest.raises(ValueError, match="Invalid transition"):
            project.transition_to(ProjectState.EXECUTION_DONE)


class TestPhase2ProjectOrchestrator:
    """Phase 2: ProjectOrchestrator tests."""

    @pytest.mark.asyncio
    async def test_create_project_from_intake(self):
        """Orchestrator creates project from intake."""
        orchestrator = ProjectOrchestrator()
        intake = ClientIntake(
            brand_name="Test Co",
            industry="Technology"
        )

        project = await orchestrator.create_project_from_intake(
            intake,
            client_email="test@example.com"
        )

        assert project.name == "Test Co Marketing Project"
        assert project.state == ProjectState.INTAKE_READY
        assert project.client_name == "Test Co"
        assert project.client_email == "test@example.com"
        assert "Technology" in project.notes

    @pytest.mark.asyncio
    async def test_generate_strategy_for_project(self):
        """Orchestrator generates strategy and updates project state."""
        orchestrator = ProjectOrchestrator()
        
        project = Project(
            name="Test Project",
            state=ProjectState.INTAKE_READY
        )
        
        intake = ClientIntake(
            brand_name="Strategy Co",
            industry="FinTech",
            primary_goal="Growth"
        )

        # Mock the strategy generation
        from aicmo.io.client_reports import MarketingPlanView, StrategyPillar as BackendPillar
        
        mock_plan = MarketingPlanView(
            executive_summary="Summary",
            situation_analysis="Analysis",
            strategy="Strategy",
            pillars=[BackendPillar(name="P1", description="D1", kpi_impact="K1")]
        )

        with patch("backend.generators.marketing_plan.generate_marketing_plan", new=AsyncMock(return_value=mock_plan)):
            updated_project, strategy = await orchestrator.generate_strategy_for_project(project, intake)

        # Verify project state updated
        assert updated_project.state == ProjectState.STRATEGY_DRAFT
        
        # Verify strategy generated
        assert isinstance(strategy, StrategyDoc)
        assert strategy.brand_name == "Strategy Co"

    @pytest.mark.asyncio
    async def test_generate_strategy_invalid_state_raises(self):
        """Orchestrator raises error if project in wrong state."""
        orchestrator = ProjectOrchestrator()
        
        project = Project(
            name="Test",
            state=ProjectState.EXECUTION_DONE  # Wrong state
        )
        
        intake = ClientIntake(brand_name="Test")

        with pytest.raises(ValueError, match="Cannot generate strategy"):
            await orchestrator.generate_strategy_for_project(project, intake)

    @pytest.mark.asyncio
    async def test_approve_strategy(self):
        """Orchestrator approves strategy and transitions state."""
        orchestrator = ProjectOrchestrator()
        
        project = Project(
            name="Test",
            state=ProjectState.STRATEGY_DRAFT
        )

        approved = await orchestrator.approve_strategy(project)
        assert approved.state == ProjectState.STRATEGY_APPROVED

    @pytest.mark.asyncio
    async def test_approve_strategy_wrong_state_raises(self):
        """Orchestrator raises error if approving from wrong state."""
        orchestrator = ProjectOrchestrator()
        
        project = Project(
            name="Test",
            state=ProjectState.INTAKE_READY  # Wrong state
        )

        with pytest.raises(ValueError, match="Can only approve strategy"):
            await orchestrator.approve_strategy(project)

    @pytest.mark.asyncio
    async def test_start_creative_phase(self):
        """Orchestrator starts creative phase after strategy approval."""
        orchestrator = ProjectOrchestrator()
        
        project = Project(
            name="Test",
            state=ProjectState.STRATEGY_APPROVED
        )

        creative_project = await orchestrator.start_creative_phase(project)
        assert creative_project.state == ProjectState.CREATIVE_IN_PROGRESS

    @pytest.mark.asyncio
    async def test_full_workflow_integration(self):
        """End-to-end workflow from intake to creative phase."""
        orchestrator = ProjectOrchestrator()
        
        # 1. Create project from intake
        intake = ClientIntake(
            brand_name="Full Workflow Co",
            industry="Retail",
            primary_goal="Sales"
        )
        
        project = await orchestrator.create_project_from_intake(intake)
        assert project.state == ProjectState.INTAKE_READY
        
        # 2. Generate strategy
        from aicmo.io.client_reports import MarketingPlanView, StrategyPillar as BackendPillar
        
        mock_plan = MarketingPlanView(
            executive_summary="Summary",
            situation_analysis="Analysis",
            strategy="Strategy",
            pillars=[BackendPillar(name="P1", description="D1", kpi_impact="K1")]
        )

        with patch("backend.generators.marketing_plan.generate_marketing_plan", new=AsyncMock(return_value=mock_plan)):
            project, strategy = await orchestrator.generate_strategy_for_project(project, intake)
        
        assert project.state == ProjectState.STRATEGY_DRAFT
        assert strategy.brand_name == "Full Workflow Co"
        
        # 3. Approve strategy
        project = await orchestrator.approve_strategy(project)
        assert project.state == ProjectState.STRATEGY_APPROVED
        
        # 4. Start creative phase
        project = await orchestrator.start_creative_phase(project)
        assert project.state == ProjectState.CREATIVE_IN_PROGRESS
