"""
QC Rules Engine for AICMO

Deterministic quality control rules and enforcement.
"""
from .qc_registry import register_rule, get_rules, QC_RULES
from .qc_runner import run_qc_for_artifact, has_blocking_failures, get_blocking_checks
from .qc_persistence import save_qc_result, load_latest_qc, get_qc_for_artifact, get_all_qc_for_engagement

# Register all rules on import
from .ruleset_v1 import register_all_rules
register_all_rules()

__all__ = [
    "register_rule",
    "get_rules",
    "QC_RULES",
    "run_qc_for_artifact",
    "has_blocking_failures",
    "get_blocking_checks",
    "save_qc_result",
    "load_latest_qc",
    "get_qc_for_artifact",
    "get_all_qc_for_engagement"
]
