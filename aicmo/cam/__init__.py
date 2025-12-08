"""
Client Acquisition Mode (CAM) for AICMO.

Handles lead management, outreach campaign generation, and execution
for acquiring new clients through LinkedIn and email channels.
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
