"""
Unified Gating Rules for AICMO Operator

Single source of truth for artifact dependencies.
Used by both artifact_store.py (backend) and operator_v2.py (UI).
"""

from enum import Enum
from typing import Dict, List


class ArtifactType(str, Enum):
    """Artifact types matching operator workflow"""
    INTAKE = "intake"
    STRATEGY = "strategy"
    CREATIVES = "creatives"
    EXECUTION = "execution"
    MONITORING = "monitoring"
    DELIVERY = "delivery"
    CAMPAIGN = "campaign"
    LEADGEN_REQUIREMENTS = "leadgen_requirements"


# ===================================================================
# CANONICAL GATING MAP
# ===================================================================

GATING_MAP: Dict[ArtifactType, List[ArtifactType]] = {
    ArtifactType.STRATEGY: [ArtifactType.INTAKE],
    ArtifactType.CREATIVES: [ArtifactType.STRATEGY],
    ArtifactType.EXECUTION: [ArtifactType.STRATEGY, ArtifactType.CREATIVES],
    ArtifactType.MONITORING: [ArtifactType.EXECUTION],
    ArtifactType.DELIVERY: [
        ArtifactType.INTAKE,
        ArtifactType.STRATEGY,
        ArtifactType.CREATIVES,
        ArtifactType.EXECUTION
    ],
}

# ===================================================================
# NOTES
# ===================================================================
# Rules:
# - Strategy requires Intake approved
# - Creatives requires Strategy approved
# - Execution requires Strategy + Creatives approved
# - Monitoring requires Execution approved
# - Delivery requires Intake + Strategy + Creatives + Execution approved (NOT Monitoring)
#
# Key insight: Delivery unlocks after core 4, Monitoring is optional for Delivery
