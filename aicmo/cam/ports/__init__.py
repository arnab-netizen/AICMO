"""
CAM Ports (Gateway Interfaces).

Defines abstract interfaces for external service integrations in client acquisition.
Follows ports & adapters architecture for testability and flexibility.

Phase CAM-2: Port interfaces for lead sources, enrichment, and verification.
"""

from .lead_source import LeadSourcePort
from .lead_enricher import LeadEnricherPort
from .email_verifier import EmailVerifierPort

__all__ = [
    "LeadSourcePort",
    "LeadEnricherPort",
    "EmailVerifierPort",
]
