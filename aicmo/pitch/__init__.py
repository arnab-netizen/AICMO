"""
Pitch & Proposal Engine.

Business development AI for prospect qualification, pitch generation, and proposals.
"""

from aicmo.pitch.domain import (
    Prospect,
    PitchDeck,
    PitchSection,
    Proposal,
    ProposalScope,
    ProposalPricing,
    PitchOutcome,
)

from aicmo.pitch.service import (
    generate_pitch_deck,
    generate_proposal,
    record_pitch_outcome,
)

__all__ = [
    # Domain models
    "Prospect",
    "PitchDeck",
    "PitchSection",
    "Proposal",
    "ProposalScope",
    "ProposalPricing",
    "PitchOutcome",
    # Service functions
    "generate_pitch_deck",
    "generate_proposal",
    "record_pitch_outcome",
]
