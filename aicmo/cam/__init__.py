"""
Client Acquisition Mode (CAM) for AICMO.

Handles lead management, outreach campaign generation, and execution
for acquiring new clients through LinkedIn and email channels.

Public API:
  - Domain models: Lead, Campaign, Channel, etc.
  - Orchestration: Available in aicmo.cam.orchestrator subpackage

Usage:
  from aicmo.cam import Lead, Campaign, Channel
  from aicmo.cam.orchestrator import OrchestratorRunDB
"""

from .domain import (
    LeadSource,
    LeadStatus,
    Channel,
    Campaign,
    Lead,
    SequenceStep,
    OutreachMessage,
    AttemptStatus,
    OutreachAttempt,
)

__all__ = [
    # Domain models
    "LeadSource",
    "LeadStatus",
    "Channel",
    "Campaign",
    "Lead",
    "SequenceStep",
    "OutreachMessage",
    "AttemptStatus",
    "OutreachAttempt",
]
