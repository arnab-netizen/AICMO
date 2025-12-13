"""
Onboarding - Port Interfaces.

Handles client intake, discovery, and brief normalization.
"""

from abc import ABC, abstractmethod
from typing import Optional
from aicmo.onboarding.api.dtos import (
    IntakeFormDTO,
    DiscoveryNotesDTO,
    NormalizedBriefDTO,
    OnboardingStatusDTO,
)
from aicmo.shared.ids import ClientId, BriefId, ProjectId


# === Command Ports ===

class IntakeCapturePort(ABC):
    """Capture intake form responses."""
    
    @abstractmethod
    def capture_intake(self, client_id: ClientId, form_data: IntakeFormDTO) -> BriefId:
        """
        Store intake answers.
        
        Returns: BriefId for tracking
        """
        pass


class BriefNormalizePort(ABC):
    """Normalize intake into validated brief."""
    
    @abstractmethod
    def normalize_brief(self, brief_id: BriefId, discovery_notes: DiscoveryNotesDTO) -> NormalizedBriefDTO:
        """
        Convert raw intake + discovery into normalized brief.
        
        Returns: Validated, normalized brief ready for strategy
        Emits: BriefValidated event
        """
        pass


# === Query Ports ===

class OnboardingQueryPort(ABC):
    """Read onboarding status."""
    
    @abstractmethod
    def get_onboarding_status(self, client_id: ClientId) -> Optional[OnboardingStatusDTO]:
        """Get current onboarding progress."""
        pass


__all__ = [
    "IntakeCapturePort",
    "BriefNormalizePort",
    "OnboardingQueryPort",
]
