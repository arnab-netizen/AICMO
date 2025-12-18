"""
QC Rules Registry

Maintains a registry of quality control rules per artifact type.
Rules are deterministic functions that validate artifact content.
"""
from typing import Callable, List, Dict, Optional
from aicmo.ui.persistence.artifact_store import ArtifactType
from aicmo.ui.quality.qc_models import QCCheck

# Type alias for rule functions
# Rule functions take artifact content dict and return list of QCCheck results
QCRuleFunc = Callable[[Dict], List[QCCheck]]

# Global registry: ArtifactType -> list of rule functions
QC_RULES: Dict[ArtifactType, List[QCRuleFunc]] = {
    ArtifactType.INTAKE: [],
    ArtifactType.STRATEGY: [],
    ArtifactType.CREATIVES: [],
    ArtifactType.EXECUTION: [],
    ArtifactType.MONITORING: [],
    ArtifactType.DELIVERY: [],
}


def register_rule(artifact_type: ArtifactType, rule_fn: QCRuleFunc) -> None:
    """
    Register a QC rule function for an artifact type.
    
    Args:
        artifact_type: The artifact type this rule applies to
        rule_fn: Function that takes artifact content and returns List[QCCheck]
    """
    if artifact_type not in QC_RULES:
        QC_RULES[artifact_type] = []
    
    QC_RULES[artifact_type].append(rule_fn)


def get_rules(artifact_type: ArtifactType) -> List[QCRuleFunc]:
    """
    Get all registered QC rules for an artifact type.
    
    Args:
        artifact_type: The artifact type to get rules for
        
    Returns:
        List of rule functions for this artifact type
    """
    return QC_RULES.get(artifact_type, [])


def clear_rules(artifact_type: Optional[ArtifactType] = None) -> None:
    """
    Clear registered rules (useful for testing).
    
    Args:
        artifact_type: If specified, clear only this type. Otherwise clear all.
    """
    if artifact_type:
        QC_RULES[artifact_type] = []
    else:
        for key in QC_RULES:
            QC_RULES[key] = []
