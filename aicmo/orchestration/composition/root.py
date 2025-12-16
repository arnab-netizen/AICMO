"""
Composition Root - Single wiring point for all dependencies.

This is the ONLY place where:
- Concrete adapters are instantiated
- Ports are wired to implementations
- Orchestration workflows are assembled

Phase 3: Wires in-memory adapters for all modules.
Phase 4 Lane B: Supports dual-mode (inmemory/db) via AICMO_PERSISTENCE_MODE.
"""

from aicmo.shared import settings, is_db_mode
from aicmo.orchestration.internal.event_bus import InProcessEventBus
from aicmo.orchestration.internal.saga import SagaCoordinator
from aicmo.orchestration.internal.workflows.client_to_delivery import ClientToDeliveryWorkflow

# Module adapters
from aicmo.onboarding.internal.adapters import (
    BriefNormalizeAdapter,
    IntakeCaptureAdapter,
    OnboardingQueryAdapter,
    InMemoryBriefRepo,
    DatabaseBriefRepo,
)
from aicmo.strategy.internal.adapters import (
    StrategyGenerateAdapter,
    StrategyApproveAdapter,
    StrategyQueryAdapter,
)
from aicmo.strategy.internal.repositories_mem import InMemoryStrategyRepo
from aicmo.strategy.internal.repositories_db import DatabaseStrategyRepo
from aicmo.production.internal.factory import create_production_repository
from aicmo.production.internal.adapters import (
    DraftGenerateAdapter,
    AssetAssembleAdapter,
    ProductionQueryAdapter,
)
from aicmo.qc.internal.factory import create_qc_repository
from aicmo.qc.internal.adapters import (
    QcEvaluateAdapter,
    QcQueryAdapter,
)
from aicmo.delivery.internal.factory import create_delivery_repository
from aicmo.delivery.internal.adapters import (
    DeliveryPackageAdapter,
    PublishExecuteAdapter,
    DeliveryQueryAdapter,
)
from aicmo.cam.internal.adapters import (
    CampaignCommandAdapter,
    CampaignQueryAdapter,
    InMemoryCampaignRepo,
)


class CompositionRoot:
    """
    Dependency Injection container.
    
    Assembles all adapters, orchestration primitives, and workflows.
    Supports dual-mode persistence (inmemory/db) via AICMO_PERSISTENCE_MODE.
    """
    
    def __init__(self):
        # Orchestration primitives
        self.event_bus = InProcessEventBus()
        self.saga_coordinator = SagaCoordinator()
        
        # Repos - select based on persistence mode
        if is_db_mode():
            self._brief_repo = DatabaseBriefRepo()
            self._strategy_repo = DatabaseStrategyRepo()
        else:
            self._brief_repo = InMemoryBriefRepo()
            self._strategy_repo = InMemoryStrategyRepo()
        self._production_repo = create_production_repository()
        self._qc_repo = create_qc_repository()
        self._delivery_repo = create_delivery_repository()
        self._campaign_repo = InMemoryCampaignRepo()
        
        # Onboarding adapters
        self.brief_normalize = BriefNormalizeAdapter(self._brief_repo)
        self.intake_capture = IntakeCaptureAdapter(self._brief_repo)
        self.onboarding_query = OnboardingQueryAdapter(self._brief_repo)
        
        # Strategy adapters
        self.strategy_generate = StrategyGenerateAdapter(self._strategy_repo)
        self.strategy_approve = StrategyApproveAdapter(self._strategy_repo)
        self.strategy_query = StrategyQueryAdapter(self._strategy_repo)
        
        # Production adapters
        self.draft_generate = DraftGenerateAdapter(self._production_repo)
        self.asset_assemble = AssetAssembleAdapter(self._production_repo)
        self.production_query = ProductionQueryAdapter(self._production_repo)
        
        # QC adapters
        self.qc_evaluate = QcEvaluateAdapter(self._qc_repo)
        self.qc_query = QcQueryAdapter(self._qc_repo)
        
        # Delivery adapters
        self.delivery_package = DeliveryPackageAdapter(self._delivery_repo)
        self.publish_execute = PublishExecuteAdapter(self._delivery_repo)
        self.delivery_query = DeliveryQueryAdapter(self._delivery_repo)
        
        # CAM adapters
        self.campaign_command = CampaignCommandAdapter(self._campaign_repo)
        self.campaign_query = CampaignQueryAdapter(self._campaign_repo)
        
        # Workflows
        self.client_to_delivery_workflow = ClientToDeliveryWorkflow(
            saga_coordinator=self.saga_coordinator,
            brief_normalize=self.brief_normalize,
            strategy_generate=self.strategy_generate,
            draft_generate=self.draft_generate,
            qc_evaluate=self.qc_evaluate,
            delivery_package=self.delivery_package,
        )
    
    def create_client_to_delivery_workflow(self) -> ClientToDeliveryWorkflow:
        """
        Factory method for ClientToDeliveryWorkflow.
        
        Returns a workflow wired with repos matching current persistence mode.
        This is the single source of truth for E2E test wiring.
        """
        return ClientToDeliveryWorkflow(
            saga_coordinator=self.saga_coordinator,
            brief_normalize=self.brief_normalize,
            strategy_generate=self.strategy_generate,
            draft_generate=self.draft_generate,
            qc_evaluate=self.qc_evaluate,
            delivery_package=self.delivery_package,
        )
    
    def get_workflow(self, workflow_name: str):
        """Get workflow by name."""
        workflows = {
            "client_to_delivery": self.client_to_delivery_workflow,
        }
        return workflows.get(workflow_name)


# Global instance (for convenience in Phase 3)
# Phase 4: Replace with proper DI container
_root: CompositionRoot = None


def get_composition_root() -> CompositionRoot:
    """Get or create the global composition root."""
    global _root
    if _root is None:
        _root = CompositionRoot()
    return _root


def reset_composition_root() -> None:
    """Reset the composition root (for testing)."""
    global _root
    _root = None
