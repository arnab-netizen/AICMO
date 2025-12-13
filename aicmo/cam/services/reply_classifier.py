"""
Reply classification service.

Phase 2: Classifies incoming emails as POSITIVE, NEGATIVE, OOO, BOUNCE, UNSUB, NEUTRAL.
"""

import logging
import re
from typing import Tuple
from enum import Enum


logger = logging.getLogger(__name__)


class ReplyClassification(str, Enum):
    """Classification of a reply."""
    POSITIVE = "POSITIVE"  # Interest expressed
    NEGATIVE = "NEGATIVE"  # Explicit rejection
    OOO = "OOO"  # Out of office auto-reply
    BOUNCE = "BOUNCE"  # Delivery failure
    UNSUB = "UNSUB"  # Unsubscribe request
    NEUTRAL = "NEUTRAL"  # Neither interest nor rejection


class ReplyClassifier:
    """
    Classify incoming emails using heuristic rules.
    
    Rules check:
    - Subject/body keywords for interest signals
    - Out of office patterns
    - Bounce/delivery failure patterns
    - Unsubscribe requests
    """
    
    # Positive signals
    POSITIVE_KEYWORDS = [
        r'\binterest\b',
        r'\blet\'s\b',
        r'\blooking\s+forward\b',
        r'\bgreat\b',
        r'\bwould\s+love\b',
        r'\bcan\s+we\b',
        r'\blet\'s\s+talk\b',
        r'\bwhen\s+can\s+we\b',
        r'\bscheduled?\b',
        r'\bapproach\b',
        r'\bproposal\b',
        r'\bquote\b',
        r'\bthank\s+you\b',
        r'\bappreciate\b',
        r'\bvalue\b',
        r'\boffer\b',
        r'\bopportunity\b',
        r'\bcollab',
    ]
    
    # Negative signals
    NEGATIVE_KEYWORDS = [
        r'\bnot\s+interested\b',
        r'\bno\s+thanks\b',
        r'\bnot\s+relevant\b',
        r'\bno\s+longer\b',
        r'\bremove\b',
        r'\bstop\b',
        r'\bcannot\b',
        r'\bcan\'t\b',
        r'\bnot\s+available\b',
        r'\bunavailable\b',
        r'\bwrong\s+person\b',
        r'\bnot\s+responsible\b',
        r'\bdoesn\'t\b',
        r'\bwaste\b',
        r'\bspam\b',
        r'\bstopped?\b',
        r'\bno\s+interest\b',
    ]
    
    # Out of office patterns
    OOO_KEYWORDS = [
        r'\bout\s+of\s+office\b',
        r'\bOOO\b',
        r'\bon\s+vacation\b',
        r'\breturning\b',
        r'\babsent\b',
        r'\bunfortunately.*\b(?:unavailable|away)\b',
        r'\bauto.*?reply\b',
        r'\bauto.*?responder\b',
        r'\bi\s+am\s+(?:out|away|traveling)',
    ]
    
    # Bounce/delivery failure patterns
    BOUNCE_KEYWORDS = [
        r'\bdelivery\s+failed\b',
        r'\bundeliverable\b',
        r'\bmail\s+failure\b',
        r'\bnon-delivery\b',
        r'\bBounce\b',
        r'\b550\s+(?:user|mailbox)\b',
        r'\binvalid\s+(?:address|mailbox|user)\b',
        r'\bdoes\s+not\s+(?:exist|have)\b',
        r'\bno\s+such\s+(?:user|account)\b',
        r'\brejected\b',
    ]
    
    # Unsubscribe patterns
    UNSUB_KEYWORDS = [
        r'\bunsubscribe\b',
        r'\bremove\s+(?:me|from|this)\b',
        r'\bstop\s+(?:emailing|sending)\b',
        r'\bno\s+longer\s+(?:want|wish)\b',
    ]
    
    def __init__(self):
        """Compile regex patterns."""
        self.positive_patterns = [re.compile(p, re.IGNORECASE) for p in self.POSITIVE_KEYWORDS]
        self.negative_patterns = [re.compile(p, re.IGNORECASE) for p in self.NEGATIVE_KEYWORDS]
        self.ooo_patterns = [re.compile(p, re.IGNORECASE) for p in self.OOO_KEYWORDS]
        self.bounce_patterns = [re.compile(p, re.IGNORECASE) for p in self.BOUNCE_KEYWORDS]
        self.unsub_patterns = [re.compile(p, re.IGNORECASE) for p in self.UNSUB_KEYWORDS]
    
    def classify(
        self,
        subject: str,
        body: str,
    ) -> Tuple[ReplyClassification, float, str]:
        """
        Classify an email reply.
        
        Args:
            subject: Email subject line
            body: Email body text
        
        Returns:
            Tuple of (classification, confidence 0.0-1.0, reason string)
        """
        combined_text = f"{subject}\n{body}".lower()
        
        # Check in order of priority
        # (OOO, BOUNCE, UNSUB are high-confidence; POSITIVE/NEGATIVE are lower)
        
        # Check OOO
        ooo_matches = sum(1 for p in self.ooo_patterns if p.search(combined_text))
        if ooo_matches > 0:
            confidence = min(1.0, ooo_matches / 3.0)  # Normalize
            return (ReplyClassification.OOO, confidence, "Out of office pattern detected")
        
        # Check BOUNCE
        bounce_matches = sum(1 for p in self.bounce_patterns if p.search(combined_text))
        if bounce_matches > 0:
            confidence = min(1.0, bounce_matches / 3.0)
            return (ReplyClassification.BOUNCE, confidence, "Delivery failure pattern detected")
        
        # Check UNSUB
        unsub_matches = sum(1 for p in self.unsub_patterns if p.search(combined_text))
        if unsub_matches > 0:
            confidence = min(1.0, unsub_matches / 2.0)
            return (ReplyClassification.UNSUB, confidence, "Unsubscribe request detected")
        
        # Check NEGATIVE (higher priority than positive, explicit rejection)
        negative_matches = sum(1 for p in self.negative_patterns if p.search(combined_text))
        
        # Check POSITIVE
        positive_matches = sum(1 for p in self.positive_patterns if p.search(combined_text))
        
        if negative_matches > 0 and negative_matches > positive_matches:
            confidence = min(1.0, negative_matches / 3.0)
            return (ReplyClassification.NEGATIVE, confidence, "Negative response pattern detected")
        
        if positive_matches > 0:
            confidence = min(1.0, positive_matches / 3.0)
            return (ReplyClassification.POSITIVE, confidence, "Positive response pattern detected")
        
        # Default to NEUTRAL
        return (ReplyClassification.NEUTRAL, 0.0, "No strong signals detected")
    
    def is_configured(self) -> bool:
        """ReplyClassifier is always configured (stateless, no external dependencies)."""
        return True
    
    def health(self) -> dict:
        """Return health status of classification module."""
        from aicmo.cam.contracts import ModuleHealthModel
        try:
            return ModuleHealthModel(
                module_name="ClassificationModule",
                is_healthy=True,
                status="READY",
                message="Classifier operational"
            ).dict()
        except Exception as e:
            return ModuleHealthModel(
                module_name="ClassificationModule",
                is_healthy=False,
                status="ERROR",
                message=str(e)
            ).dict()
