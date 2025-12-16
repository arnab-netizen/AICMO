"""
Proof-Run Ledger

Records all attempted external sends for audit.
In proof-run mode, no actual sends should occur.
"""

import os
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path


@dataclass
class SendAttempt:
    """Record of an attempted send."""
    timestamp: str
    send_type: str  # email, sms, api_call, etc.
    destination: str
    payload_summary: str
    proof_run: bool
    actually_sent: bool
    blocked_reason: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


class ProofRunLedger:
    """Tracks all send attempts for audit."""
    
    def __init__(self, ledger_path: Optional[str] = None):
        """
        Initialize ledger.
        
        Args:
            ledger_path: Path to ledger file. If None, uses default from env.
        """
        if ledger_path is None:
            artifact_dir = os.getenv('AICMO_E2E_ARTIFACT_DIR', 'artifacts/e2e')
            run_id = os.getenv('AICMO_RUN_ID', 'default')
            ledger_path = os.path.join(artifact_dir, run_id, 'proof_run_ledger.json')
        
        self.ledger_path = ledger_path
        self.attempts: List[SendAttempt] = []
        
        # Load existing ledger if it exists
        if os.path.exists(ledger_path):
            self.load()
    
    def record_attempt(
        self,
        send_type: str,
        destination: str,
        payload_summary: str,
        actually_sent: bool = False,
        blocked_reason: Optional[str] = None
    ) -> None:
        """
        Record a send attempt.
        
        Args:
            send_type: Type of send (email, sms, etc.)
            destination: Destination address/identifier
            payload_summary: Brief summary of payload
            actually_sent: Whether send actually occurred
            blocked_reason: If blocked, why
        """
        proof_run = os.getenv('AICMO_PROOF_RUN') == '1'
        
        attempt = SendAttempt(
            timestamp=datetime.utcnow().isoformat(),
            send_type=send_type,
            destination=destination,
            payload_summary=payload_summary,
            proof_run=proof_run,
            actually_sent=actually_sent,
            blocked_reason=blocked_reason
        )
        
        self.attempts.append(attempt)
        self.save()
    
    def save(self) -> None:
        """Save ledger to disk."""
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.ledger_path), exist_ok=True)
        
        data = {
            'ledger_version': '1.0.0',
            'last_updated': datetime.utcnow().isoformat(),
            'proof_run_mode': os.getenv('AICMO_PROOF_RUN') == '1',
            'total_attempts': len(self.attempts),
            'external_sends': [a.to_dict() for a in self.attempts if a.actually_sent],
            'blocked_sends': [a.to_dict() for a in self.attempts if not a.actually_sent],
            'all_attempts': [a.to_dict() for a in self.attempts]
        }
        
        with open(self.ledger_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load(self) -> None:
        """Load ledger from disk."""
        with open(self.ledger_path, 'r') as f:
            data = json.load(f)
        
        self.attempts = [
            SendAttempt(**attempt)
            for attempt in data.get('all_attempts', [])
        ]
    
    def get_external_sends(self) -> List[SendAttempt]:
        """Get all attempts that actually resulted in external sends."""
        return [a for a in self.attempts if a.actually_sent]
    
    def verify_no_external_sends(self) -> tuple[bool, List[str]]:
        """
        Verify no external sends occurred in proof-run mode.
        
        Returns:
            (is_valid, list_of_violations)
        """
        external_sends = self.get_external_sends()
        
        if not external_sends:
            return True, []
        
        violations = [
            f"{a.send_type} to {a.destination} at {a.timestamp}"
            for a in external_sends
        ]
        
        return False, violations
    
    def to_report_dict(self) -> Dict:
        """Generate dict suitable for validation report."""
        external_sends = self.get_external_sends()
        no_external_sends = len(external_sends) == 0
        
        return {
            'no_external_sends': no_external_sends,
            'total_attempts': len(self.attempts),
            'external_send_count': len(external_sends),
            'external_send_details': [a.to_dict() for a in external_sends] if external_sends else []
        }


# Global ledger instance
_ledger: Optional[ProofRunLedger] = None


def get_ledger() -> ProofRunLedger:
    """Get global ledger instance."""
    global _ledger
    if _ledger is None:
        _ledger = ProofRunLedger()
    return _ledger


def record_send_attempt(
    send_type: str,
    destination: str,
    payload_summary: str,
    actually_sent: bool = False,
    blocked_reason: Optional[str] = None
) -> None:
    """
    Convenience function to record a send attempt.
    
    Usage:
        from aicmo.safety import record_send_attempt
        
        # Before attempting to send
        if AICMO_PROOF_RUN:
            record_send_attempt('email', recipient, 'Campaign X', False, 'Proof-run mode')
        else:
            send_email(recipient, body)
            record_send_attempt('email', recipient, 'Campaign X', True)
    """
    ledger = get_ledger()
    ledger.record_attempt(send_type, destination, payload_summary, actually_sent, blocked_reason)
