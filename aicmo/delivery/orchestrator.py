"""Project orchestrator - coordinates project lifecycle.

Phase 2: Implements project creation and workflow orchestration.
"""

from typing import Optional
from aicmo.domain.intake import ClientIntake
from aicmo.domain.project import Project, ProjectState
from aicmo.domain.strategy import StrategyDoc
from aicmo.strategy.service import generate_strategy


class ProjectOrchestrator:
    """
    Orchestrates project lifecycle from intake through execution.
    
    Phase 2 Implementation:
    - Create projects from intake
    - Manage state transitions
    - Coordinate strategy generation
    """
    
    async def create_project_from_intake(
        self,
        intake: ClientIntake,
        client_email: Optional[str] = None
    ) -> Project:
        """
        Create a new project from client intake.
        
        Args:
            intake: Client intake data
            client_email: Optional client email for tracking
            
        Returns:
            New project in INTAKE_READY state
        """
        project = Project(
            name=f"{intake.brand_name} Marketing Project",
            state=ProjectState.INTAKE_READY,
            client_name=intake.brand_name,
            client_email=client_email,
            notes=f"Industry: {intake.industry or 'Not specified'}"
        )
        return project
    
    async def generate_strategy_for_project(
        self,
        project: Project,
        intake: ClientIntake
    ) -> tuple[Project, StrategyDoc]:
        """
        Generate strategy for a project and update project state.
        
        Args:
            project: Project to generate strategy for
            intake: Client intake data
            
        Returns:
            Tuple of (updated project, generated strategy)
            
        Raises:
            ValueError: If project is not in a state that allows strategy generation
        """
        # Validate project state
        if project.state not in {
            ProjectState.INTAKE_READY,
            ProjectState.STRATEGY_IN_PROGRESS,
            ProjectState.STRATEGY_DRAFT,
        }:
            raise ValueError(
                f"Cannot generate strategy for project in state {project.state.value}"
            )
        
        # Transition to in-progress
        if project.state != ProjectState.STRATEGY_IN_PROGRESS:
            project = project.transition_to(ProjectState.STRATEGY_IN_PROGRESS)
        
        # Generate strategy
        strategy = await generate_strategy(intake)
        
        # Transition to draft
        project = project.transition_to(ProjectState.STRATEGY_DRAFT)
        
        return project, strategy
    
    async def approve_strategy(
        self,
        project: Project
    ) -> Project:
        """
        Approve project strategy and move to next phase.
        
        Args:
            project: Project with strategy to approve
            
        Returns:
            Updated project in STRATEGY_APPROVED state
            
        Raises:
            ValueError: If project is not in STRATEGY_DRAFT state
        """
        if project.state != ProjectState.STRATEGY_DRAFT:
            raise ValueError(
                f"Can only approve strategy from STRATEGY_DRAFT state, got {project.state.value}"
            )
        
        return project.transition_to(ProjectState.STRATEGY_APPROVED)
    
    async def start_creative_phase(
        self,
        project: Project
    ) -> Project:
        """
        Start creative phase for approved strategy.
        
        Args:
            project: Project with approved strategy
            
        Returns:
            Updated project in CREATIVE_IN_PROGRESS state
            
        Raises:
            ValueError: If project strategy is not approved
        """
        if project.state != ProjectState.STRATEGY_APPROVED:
            raise ValueError(
                f"Creative phase requires approved strategy, got {project.state.value}"
            )
        
        return project.transition_to(ProjectState.CREATIVE_IN_PROGRESS)
