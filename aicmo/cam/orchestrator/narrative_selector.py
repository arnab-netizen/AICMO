"""
Narrative selector - MVP implementation.

Chooses which message to send to a lead based on:
- Lead routing sequence
- Campaign default
- Step index (intro, followup1, followup2)
"""

from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from aicmo.cam.db_models import LeadDB, CampaignDB


@dataclass
class MessageChoice:
    """Result of narrative selection."""
    message_id: str
    step_index: int
    reason: str
    confidence: float = 0.5


class NarrativeSelector:
    """
    MVP narrative selector.
    
    Simple deterministic rules:
    1. If lead has routing_sequence, use it to determine step
    2. Otherwise use campaign default (if exists)
    3. Fallback to generic sequence: intro → followup1 → followup2
    """
    
    # Default message sequence
    DEFAULT_SEQUENCE = [
        "intro_v1",
        "followup1_v1",
        "followup2_v1",
    ]
    
    def __init__(self, session: Session):
        self.session = session
    
    def choose_message(
        self,
        campaign_id: int,
        lead: LeadDB,
        step_index: int,
    ) -> MessageChoice:
        """
        Choose message for lead at given step.
        
        Args:
            campaign_id: Campaign ID
            lead: Lead database record
            step_index: Which step in sequence (0=intro, 1=followup1, 2=followup2)
            
        Returns:
            MessageChoice with message_id and rationale
        """
        # Check if lead has specific routing sequence
        if lead.routing_sequence:
            message_id = self._get_sequence_message(lead.routing_sequence, step_index)
            if message_id:
                return MessageChoice(
                    message_id=message_id,
                    step_index=step_index,
                    reason=f"routing_sequence:{lead.routing_sequence}:step_{step_index}",
                    confidence=0.8,
                )
        
        # Check campaign default
        campaign = self.session.query(CampaignDB).filter_by(id=campaign_id).first()
        if campaign and hasattr(campaign, 'default_message_sequence'):
            # TODO: Add default_message_sequence to CampaignDB schema
            pass
        
        # Fallback to default sequence
        if step_index < len(self.DEFAULT_SEQUENCE):
            message_id = self.DEFAULT_SEQUENCE[step_index]
        else:
            # Exhausted sequence
            message_id = self.DEFAULT_SEQUENCE[-1]  # Repeat last message
        
        return MessageChoice(
            message_id=message_id,
            step_index=step_index,
            reason=f"default_sequence:step_{step_index}",
            confidence=0.5,
        )
    
    def _get_sequence_message(
        self,
        sequence_name: str,
        step_index: int,
    ) -> Optional[str]:
        """
        Get message ID for named sequence at step.
        
        Sequences:
        - aggressive_close: Fast 2-step close
        - regular_nurture: Standard 3-step
        - long_nurture: Extended 5-step
        """
        sequences = {
            "aggressive_close": [
                "aggressive_intro_v1",
                "aggressive_close_v1",
            ],
            "regular_nurture": [
                "intro_v1",
                "followup1_v1",
                "followup2_v1",
            ],
            "long_nurture": [
                "intro_v1",
                "followup1_v1",
                "value_prop_v1",
                "case_study_v1",
                "final_ask_v1",
            ],
        }
        
        sequence = sequences.get(sequence_name, self.DEFAULT_SEQUENCE)
        
        if step_index < len(sequence):
            return sequence[step_index]
        
        return None  # Exhausted sequence
