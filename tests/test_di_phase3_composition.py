"""Test composition root and DI wiring."""
import pytest
from aicmo.orchestration.composition.root import CompositionRoot, get_composition_root, reset_composition_root
from aicmo.orchestration.api.dtos import WorkflowInputDTO
from aicmo.shared.ids import ClientId, BriefId

# Port interfaces
from aicmo.onboarding.api.ports import BriefNormalizePort, IntakeCapturePort, OnboardingQueryPort
from aicmo.strategy.api.ports import StrategyGeneratePort, StrategyApprovePort, StrategyQueryPort
from aicmo.production.api.ports import DraftGeneratePort, AssetAssemblePort, ProductionQueryPort
from aicmo.qc.api.ports import QcEvaluatePort, QcQueryPort
from aicmo.delivery.api.ports import DeliveryPackagePort, PublishExecutePort, DeliveryQueryPort
from aicmo.cam.api.ports import CampaignCommandPort, CampaignQueryPort


def test_composition_root_creates_all_adapters():
    """Test that composition root creates concrete implementations for all ports."""
    root = CompositionRoot()
    
    # Onboarding
    assert isinstance(root.brief_normalize, BriefNormalizePort)
    assert isinstance(root.intake_capture, IntakeCapturePort)
    assert isinstance(root.onboarding_query, OnboardingQueryPort)
    
    # Strategy
    assert isinstance(root.strategy_generate, StrategyGeneratePort)
    assert isinstance(root.strategy_approve, StrategyApprovePort)
    assert isinstance(root.strategy_query, StrategyQueryPort)
    
    # Production
    assert isinstance(root.draft_generate, DraftGeneratePort)
    assert isinstance(root.asset_assemble, AssetAssemblePort)
    assert isinstance(root.production_query, ProductionQueryPort)
    
    # QC
    assert isinstance(root.qc_evaluate, QcEvaluatePort)
    assert isinstance(root.qc_query, QcQueryPort)
    
    # Delivery
    assert isinstance(root.delivery_package, DeliveryPackagePort)
    assert isinstance(root.publish_execute, PublishExecutePort)
    assert isinstance(root.delivery_query, DeliveryQueryPort)
    
    # CAM
    assert isinstance(root.campaign_command, CampaignCommandPort)
    assert isinstance(root.campaign_query, CampaignQueryPort)


def test_composition_root_creates_orchestration_primitives():
    """Test that orchestration primitives are created."""
    root = CompositionRoot()
    
    assert root.event_bus is not None
    assert root.saga_coordinator is not None


def test_composition_root_creates_workflows():
    """Test that workflows are assembled."""
    root = CompositionRoot()
    
    assert root.client_to_delivery_workflow is not None
    
    # Workflow should be accessible by name
    workflow = root.get_workflow("client_to_delivery")
    assert workflow is not None
    assert workflow == root.client_to_delivery_workflow


def test_workflow_executes_through_composition_root():
    """Test running workflow through composition root (end-to-end DI proof)."""
    root = CompositionRoot()
    
    workflow = root.client_to_delivery_workflow
    
    # Execute workflow
    input_dto = WorkflowInputDTO(
        client_id=ClientId("client_di_test"),
        brief_id=BriefId("brief_di_test"),
        force_qc_fail=False,
    )
    
    result = workflow.execute(input_dto)
    
    # Verify success
    assert result.success is True
    assert len(result.completed_steps) == 5
    
    # Verify state
    state = workflow.get_state(result.saga_id)
    assert state.package_id is not None


def test_global_composition_root_singleton():
    """Test global composition root singleton pattern."""
    # Reset first
    reset_composition_root()
    
    # Get root twice
    root1 = get_composition_root()
    root2 = get_composition_root()
    
    # Should be same instance
    assert root1 is root2


def test_composition_root_can_be_reset():
    """Test that composition root can be reset (for testing)."""
    root1 = get_composition_root()
    
    reset_composition_root()
    
    root2 = get_composition_root()
    
    # Should be different instances
    assert root1 is not root2


def test_all_ports_are_concrete_implementations():
    """Test that no port is None (all concrete)."""
    root = CompositionRoot()
    
    # Check all adapter attributes are not None
    adapters = [
        root.brief_normalize,
        root.intake_capture,
        root.onboarding_query,
        root.strategy_generate,
        root.strategy_approve,
        root.strategy_query,
        root.draft_generate,
        root.asset_assemble,
        root.production_query,
        root.qc_evaluate,
        root.qc_query,
        root.delivery_package,
        root.publish_execute,
        root.delivery_query,
        root.campaign_command,
        root.campaign_query,
    ]
    
    for adapter in adapters:
        assert adapter is not None, f"Adapter {adapter} is None"


def test_workflow_runs_deterministically():
    """Test that workflow produces consistent results."""
    root = CompositionRoot()
    workflow = root.client_to_delivery_workflow
    
    # Run workflow twice
    input1 = WorkflowInputDTO(
        client_id=ClientId("client_det_1"),
        brief_id=BriefId("brief_det_1"),
    )
    input2 = WorkflowInputDTO(
        client_id=ClientId("client_det_2"),
        brief_id=BriefId("brief_det_2"),
    )
    
    result1 = workflow.execute(input1)
    result2 = workflow.execute(input2)
    
    # Both should succeed
    assert result1.success is True
    assert result2.success is True
    
    # Both should complete same steps
    assert result1.completed_steps == result2.completed_steps
