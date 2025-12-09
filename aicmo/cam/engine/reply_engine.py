"""
CAM Reply Engine — Phase 8

Inbox integration: fetch replies, classify them, map back to leads, and update status.

Workflow:
1. Fetch new replies since last check (via ReplyFetcher port)
2. Classify each reply (keyword-based: positive/negative/auto-reply/etc)
3. Map reply to Lead + OutreachEvent (using thread_id, in_reply_to, etc.)
4. Update lead status and reschedule follow-ups
5. Emit events (Make.com webhook, Kaizen learning events)

All adapters and external services are optional - graceful degradation when missing.
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Optional, Tuple, List
from dataclasses import dataclass

from aicmo.cam.ports.reply_fetcher import EmailReply
from aicmo.cam.domain import Lead, LeadStatus
from aicmo.cam.db_models import LeadDB, OutreachAttemptDB, CampaignDB

logger = logging.getLogger(__name__)


class ReplyCategory(str, Enum):
    """Classification of email reply sentiment/intent."""
    
    POSITIVE = "POSITIVE"
    """Interested, wants to talk, engaged"""
    
    NEUTRAL = "NEUTRAL"
    """Acknowledged but non-committal"""
    
    NEGATIVE = "NEGATIVE"
    """Not interested, unsubscribe, spam complaint"""
    
    AUTO_REPLY = "AUTO_REPLY"
    """Automatic response (out of office, auto-generated, etc.)"""
    
    OOO = "OOO"
    """Out of office explicitly"""
    
    UNKNOWN = "UNKNOWN"
    """Couldn't classify"""


@dataclass
class ReplyAnalysis:
    """Result of classifying an email reply."""
    
    category: ReplyCategory
    """Determined category"""
    
    reason: str
    """Explanation of classification"""
    
    raw_reply: EmailReply
    """Original email data"""
    
    confidence: float = 0.5
    """Confidence in classification (0.0-1.0)"""


# ═══════════════════════════════════════════════════════════════════════
# CLASSIFICATION: Keyword-based reply categorization
# ═══════════════════════════════════════════════════════════════════════


def classify_reply(reply: EmailReply) -> ReplyAnalysis:
    """
    Classify email reply using keyword matching.
    
    Args:
        reply: Raw email reply to classify
        
    Returns:
        ReplyAnalysis with category and reason
    """
    text_lower = (reply.subject + " " + reply.body_text).lower()
    
    # Check for auto-reply patterns first (highest priority)
    auto_reply_patterns = [
        "auto-reply", "autoreply", "automated response",
        "i am currently out of the office",
        "i will return",
        "automatic response",
        "do not reply to this message",
    ]
    if any(pattern in text_lower for pattern in auto_reply_patterns):
        return ReplyAnalysis(
            category=ReplyCategory.AUTO_REPLY,
            reason="Detected auto-reply pattern",
            raw_reply=reply,
            confidence=0.9,
        )
    
    # Check for out of office
    ooo_patterns = [
        "out of office", "out of the office", "ooo",
        "on vacation", "on holiday", "away",
        "unavailable", "not available",
    ]
    if any(pattern in text_lower for pattern in ooo_patterns):
        return ReplyAnalysis(
            category=ReplyCategory.OOO,
            reason="Detected out of office",
            raw_reply=reply,
            confidence=0.85,
        )
    
    # Check for negative signals
    negative_patterns = [
        "not interested", "no thanks", "no thank you",
        "remove me", "unsubscribe", "stop emailing",
        "don't contact", "not relevant", "spam",
        "please remove", "decline", "declining",
        "sorry, not", "unfortunately", "can't help",
    ]
    if any(pattern in text_lower for pattern in negative_patterns):
        return ReplyAnalysis(
            category=ReplyCategory.NEGATIVE,
            reason="Detected negative signal",
            raw_reply=reply,
            confidence=0.85,
        )
    
    # Check for positive signals
    positive_patterns = [
        "interested", "let's talk", "call me",
        "let me know", "sounds good", "great",
        "yes", "absolutely", "definitely",
        "would love", "excited", "let's discuss",
        "reply received", "got it", "thanks",
        "looking forward", "perfect", "exactly",
        "meeting", "call", "schedule",
    ]
    if any(pattern in text_lower for pattern in positive_patterns):
        return ReplyAnalysis(
            category=ReplyCategory.POSITIVE,
            reason="Detected positive signal",
            raw_reply=reply,
            confidence=0.75,
        )
    
    # If we got a reply but can't classify, assume neutral engagement
    if len(reply.body_text.strip()) > 10:
        return ReplyAnalysis(
            category=ReplyCategory.NEUTRAL,
            reason="Reply received but no clear positive/negative signal",
            raw_reply=reply,
            confidence=0.5,
        )
    
    # Very short replies are usually neutral/unknown
    return ReplyAnalysis(
        category=ReplyCategory.UNKNOWN,
        reason="Could not classify (empty or very short reply)",
        raw_reply=reply,
        confidence=0.3,
    )


# ═══════════════════════════════════════════════════════════════════════
# MAPPING: Map reply back to Lead + OutreachEvent
# ═══════════════════════════════════════════════════════════════════════


def map_reply_to_lead_and_event(
    reply: EmailReply,
    db_session,
) -> Tuple[Optional[LeadDB], Optional[OutreachAttemptDB]]:
    """
    Find the Lead and OutreachEvent that this reply corresponds to.
    
    Strategy:
    1. Try to find OutreachAttemptDB by thread_id (if reply is from known contact)
    2. Fall back to matching by email address across recent attempts
    3. If found, get the associated LeadDB
    
    Args:
        reply: Email reply to map
        db_session: Database session
        
    Returns:
        Tuple of (LeadDB or None, OutreachAttemptDB or None)
    """
    try:
        # Import here to avoid circular imports
        from sqlalchemy.orm import Session
        from sqlalchemy import and_
        
        session: Session = db_session
        
        # Try matching by thread_id first (Gmail-style)
        if reply.thread_id:
            # This is simplistic - in real scenario, would need to store thread IDs
            # For now, just log the attempt
            logger.debug(f"Would search by thread_id: {reply.thread_id}")
        
        # Try matching by from_email (the sender of the reply should be a lead's email)
        # Look for recent OutreachAttemptDB where the lead's email matches reply.from_email
        recent_attempts = session.query(OutreachAttemptDB).filter(
            OutreachAttemptDB.lead_id == LeadDB.id
        ).all()
        
        for attempt in recent_attempts[-100:]:  # Check last 100 attempts
            lead = session.query(LeadDB).filter(LeadDB.id == attempt.lead_id).first()
            if lead and lead.email and lead.email.lower() == reply.from_email.lower():
                logger.info(f"Mapped reply from {reply.from_email} to lead {lead.id}")
                return lead, attempt
        
        # No match found
        logger.debug(f"Could not map reply from {reply.from_email} to any known lead")
        return None, None
    
    except Exception as e:
        logger.error(f"Error mapping reply to lead: {e}")
        return None, None


# ═══════════════════════════════════════════════════════════════════════
# PROCESSING: Main reply processing pipeline
# ═══════════════════════════════════════════════════════════════════════


def process_new_replies(
    db_session,
    now: Optional[datetime] = None,
    reply_fetcher=None,
) -> dict:
    """
    Main entry point for reply processing.
    
    Fetches new replies, classifies them, maps to leads, updates status and timing.
    
    Args:
        db_session: Database session
        now: Current datetime (for testing), defaults to utcnow()
        reply_fetcher: Reply fetcher adapter (injected for testing)
        
    Returns:
        Summary dict with counts of replies processed
    """
    if now is None:
        now = datetime.utcnow()
    
    if reply_fetcher is None:
        # Import here to avoid circular imports at module level
        from aicmo.gateways.factory import get_reply_fetcher
        reply_fetcher = get_reply_fetcher()
    
    stats = {
        "processed_count": 0,
        "positive_count": 0,
        "negative_count": 0,
        "neutral_count": 0,
        "ooo_count": 0,
        "auto_reply_count": 0,
        "total_fetched": 0,
        "classified": 0,
        "mapped_to_lead": 0,
        "status_updated": 0,
        "errors": [],
    }
    
    try:
        # Get the time of last reply check (or use 24 hours ago as default)
        from datetime import timedelta
        since = now - timedelta(hours=24)
        
        logger.info(f"Fetching replies since {since}")
        
        # Fetch new replies
        replies = reply_fetcher.fetch_new_replies(since)
        stats["total_fetched"] = len(replies)
        logger.info(f"Fetched {len(replies)} new replies")
        
        # Process each reply
        for reply in replies:
            try:
                # Step 1: Classify
                analysis = classify_reply(reply)
                stats["classified"] += 1
                logger.debug(
                    f"Classified reply from {reply.from_email}: "
                    f"{analysis.category} ({analysis.confidence:.2f})"
                )
                
                # Step 2: Map to lead
                lead, attempt = map_reply_to_lead_and_event(reply, db_session)
                if not lead:
                    logger.debug(f"Reply from {reply.from_email} could not be mapped to lead")
                    continue
                
                stats["mapped_to_lead"] += 1
                
                # Step 3: Update lead based on reply category
                old_status = lead.status
                
                if analysis.category == ReplyCategory.POSITIVE:
                    lead.status = LeadStatus.REPLIED
                    lead.tags = list(set(lead.tags + ["warm", "replied_positive"]))
                    lead.notes = f"{lead.notes or ''}\n[Reply] {reply.subject} ({now.isoformat()})"
                    stats["positive_count"] += 1
                
                elif analysis.category == ReplyCategory.NEGATIVE:
                    lead.status = LeadStatus.LOST
                    lead.tags = list(set(lead.tags + ["lost", "replied_negative"]))
                    lead.notes = f"{lead.notes or ''}\n[Reply] {reply.subject} - NOT INTERESTED ({now.isoformat()})"
                    stats["negative_count"] += 1
                
                elif analysis.category == ReplyCategory.AUTO_REPLY:
                    # Don't change status, but mark that we got an auto-reply
                    lead.tags = list(set(lead.tags + ["auto_reply"]))
                    # Reschedule for later
                    lead.next_action_at = now + timedelta(days=3)
                    stats["auto_reply_count"] += 1
                
                elif analysis.category == ReplyCategory.OOO:
                    # Out of office - reschedule for later
                    lead.tags = list(set(lead.tags + ["ooo"]))
                    lead.next_action_at = now + timedelta(days=7)
                    stats["ooo_count"] += 1
                
                else:  # NEUTRAL, UNKNOWN
                    # Treat as engagement but don't mark as warm yet
                    lead.tags = list(set(lead.tags + ["replied"]))
                    stats["neutral_count"] += 1
                
                lead.last_reply_at = reply.received_at
                lead.last_contacted_at = now
                
                db_session.add(lead)
                db_session.commit()
                
                stats["status_updated"] += 1
                stats["processed_count"] += 1
                logger.info(
                    f"Updated lead {lead.id} status from {old_status} to {lead.status} "
                    f"based on reply category {analysis.category}"
                )
                
                # Step 4: Emit event (Make webhook, Kaizen logging, etc.)
                # For now, just log - can extend with actual event emission
                logger.debug(
                    f"Would emit event: LeadReplied(lead_id={lead.id}, category={analysis.category})"
                )
            
            except Exception as e:
                logger.error(f"Error processing reply from {reply.from_email}: {e}")
                stats["errors"].append(str(e))
        
        logger.info(f"Reply processing complete: {stats}")
        return stats
    
    except Exception as e:
        logger.error(f"Reply processing pipeline failed: {e}")
        stats["errors"].append(str(e))
        return stats
