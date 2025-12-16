"""
Delivery Gate

Blocks delivery if validation status ≠ PASS.
This is the final enforcement point before client-facing outputs are delivered.
"""

import os
from typing import Optional
from aicmo.validation import ValidationReport


class DeliveryGate:
    """Gates delivery based on validation status."""
    
    def __init__(self):
        """Initialize delivery gate."""
        self.enabled = os.getenv('AICMO_E2E_MODE') == '1'
    
    def check_delivery_allowed(
        self,
        validation_report: ValidationReport
    ) -> tuple[bool, Optional[str]]:
        """
        Check if delivery is allowed based on validation report.
        
        Args:
            validation_report: Validation report for the delivery
            
        Returns:
            (is_allowed, reason_if_blocked)
        """
        if not self.enabled:
            # Gate disabled - allow all deliveries
            return True, None
        
        # Check validation status
        if not validation_report.is_pass:
            failure_summary = validation_report.get_failure_summary()
            return False, f"Validation failed:\n{failure_summary}"
        
        # Check proof-run compliance
        proof_run_checks = validation_report.proof_run_checks
        if not proof_run_checks.get('no_external_sends', False):
            return False, "External sends detected in proof-run mode"
        
        if not proof_run_checks.get('no_unexpected_egress', False):
            return False, "Unexpected network egress detected"
        
        # All checks passed
        return True, None
    
    def require_delivery_allowed(
        self,
        validation_report: ValidationReport
    ) -> None:
        """
        Require delivery to be allowed, raise if not.
        
        Args:
            validation_report: Validation report
            
        Raises:
            DeliveryBlockedError: If delivery is not allowed
        """
        is_allowed, reason = self.check_delivery_allowed(validation_report)
        
        if not is_allowed:
            raise DeliveryBlockedError(reason or "Delivery blocked by gate")


class DeliveryBlockedError(Exception):
    """Raised when delivery is blocked by the gate."""
    pass


# Global gate instance
_gate: Optional[DeliveryGate] = None


def get_gate() -> DeliveryGate:
    """Get global delivery gate instance."""
    global _gate
    if _gate is None:
        _gate = DeliveryGate()
    return _gate


def check_delivery_allowed(validation_report: ValidationReport) -> bool:
    """
    Check if delivery is allowed.
    
    Usage:
        from aicmo.delivery import check_delivery_allowed
        from aicmo.validation import OutputValidator
        
        # After validation
        validator = OutputValidator('contracts.json')
        validation_report = validator.validate_manifest(manifest)
        
        if check_delivery_allowed(validation_report):
            deliver_to_client(artifacts)
        else:
            raise Exception("Delivery blocked")
    """
    gate = get_gate()
    is_allowed, _ = gate.check_delivery_allowed(validation_report)
    return is_allowed


def block_delivery(validation_report: ValidationReport) -> None:
    """
    Block delivery if validation fails.
    
    Usage:
        from aicmo.delivery import block_delivery
        
        # This will raise if validation failed
        block_delivery(validation_report)
        
        # If we get here, validation passed
        deliver_to_client(artifacts)
    """
    gate = get_gate()
    gate.require_delivery_allowed(validation_report)
