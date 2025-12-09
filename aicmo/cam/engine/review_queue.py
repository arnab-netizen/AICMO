"""
CAM Review Queue Engine — Phase 9

Human-in-the-loop control for high-value or sensitive actions.

Workflow:
1. Mark lead as requires_human_review=True when conditions met
2. Operator sees lead in review queue
3. Operator approves/rejects/edits suggested action
4. Lead proceeds or moves to different status

This adds safety layer between autonomous engine and real outreach.
"""

import logging
from datetime import datetime
from typing import List, Optional

from aicmo.cam.db_models import LeadDB, CampaignDB
from aicmo.cam.domain import LeadStatus

logger = logging.getLogger(__name__)


class ReviewTask:
    """
    Single lead requiring human review.
    
    Operator can approve, edit, reject, or skip.
    """
    
    def __init__(
        self,
        lead_id: int,
        lead_name: str,
        lead_company: Optional[str],
        lead_email: Optional[str],
        review_type: str,
        review_reason: str,
        suggested_action: Optional[str] = None,
        suggested_subject: Optional[str] = None,
        suggested_body: Optional[str] = None,
        lead_score: Optional[float] = None,
        last_reply_snippet: Optional[str] = None,
    ):
        self.lead_id = lead_id
        self.lead_name = lead_name
        self.lead_company = lead_company
        self.lead_email = lead_email
        self.review_type = review_type  # MESSAGE, PROPOSAL, PRICING, etc.
        self.review_reason = review_reason
        self.suggested_action = suggested_action
        self.suggested_subject = suggested_subject
        self.suggested_body = suggested_body
        self.lead_score = lead_score
        self.last_reply_snippet = last_reply_snippet
        self.created_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert to dict for JSON/API response."""
        return {
            "lead_id": self.lead_id,
            "lead_name": self.lead_name,
            "lead_company": self.lead_company,
            "lead_email": self.lead_email,
            "review_type": self.review_type,
            "review_reason": self.review_reason,
            "suggested_action": self.suggested_action,
            "suggested_subject": self.suggested_subject,
            "suggested_body": self.suggested_body,
            "lead_score": self.lead_score,
            "last_reply_snippet": self.last_reply_snippet,
            "created_at": self.created_at.isoformat(),
        }


def get_review_queue(
    db_session,
    campaign_id: Optional[int] = None,
) -> List[ReviewTask]:
    """
    Get all leads requiring human review.
    
    Args:
        db_session: Database session
        campaign_id: Optional filter to single campaign
        
    Returns:
        List of ReviewTask objects
    """
    try:
        query = db_session.query(LeadDB).filter(LeadDB.requires_human_review == True)
        
        if campaign_id:
            query = query.filter(LeadDB.campaign_id == campaign_id)
        
        leads = query.all()
        
        tasks = []
        for lead in leads:
            # Extract last reply snippet if available
            last_reply = None
            if lead.notes:
                lines = lead.notes.split("\n")
                for line in lines[-5:]:  # Last 5 lines
                    if "[Reply]" in line:
                        last_reply = line[:100]
                        break
            
            task = ReviewTask(
                lead_id=lead.id,
                lead_name=lead.name,
                lead_company=lead.company,
                lead_email=lead.email,
                review_type=lead.review_type or "MESSAGE",
                review_reason=lead.review_reason or "Pending human review",
                lead_score=lead.lead_score,
                last_reply_snippet=last_reply,
            )
            tasks.append(task)
        
        logger.info(f"Review queue has {len(tasks)} tasks")
        return tasks
    
    except Exception as e:
        logger.error(f"Error fetching review queue: {e}")
        return []


def approve_review_task(
    lead_id: int,
    db_session,
    action: str = "approve",
    custom_message: Optional[str] = None,
) -> bool:
    """
    Approve a review task and clear the hold.
    
    Args:
        lead_id: Lead to approve
        db_session: Database session
        action: "approve" (send CAM message), "skip" (don't follow up), etc.
        custom_message: Optional operator-provided message (overrides CAM suggestion)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        lead = db_session.query(LeadDB).filter(LeadDB.id == lead_id).first()
        
        if not lead:
            logger.warning(f"Lead {lead_id} not found")
            return False
        
        if action == "approve":
            # Clear review flag, allow outreach to proceed
            lead.requires_human_review = False
            lead.review_type = None
            lead.review_reason = None
            lead.notes = f"{lead.notes or ''}\n[REVIEW] Approved by operator at {datetime.utcnow().isoformat()}"
            
            logger.info(f"Approved review task for lead {lead_id}")
        
        elif action == "skip":
            # Don't follow up with this lead further
            lead.requires_human_review = False
            lead.review_type = None
            lead.review_reason = None
            lead.status = LeadStatus.LOST
            lead.tags = list(set(lead.tags + ["operator_skip"]))
            lead.notes = f"{lead.notes or ''}\n[REVIEW] Skipped by operator at {datetime.utcnow().isoformat()}"
            
            logger.info(f"Skipped review task for lead {lead_id}")
        
        else:
            logger.warning(f"Unknown review action: {action}")
            return False
        
        db_session.add(lead)
        db_session.commit()
        return True
    
    except Exception as e:
        logger.error(f"Error approving review task: {e}")
        return False


def reject_review_task(
    lead_id: int,
    db_session,
    reason: str = "Operator rejection",
) -> bool:
    """
    Reject a review task and mark as handled.
    
    Args:
        lead_id: Lead to reject
        db_session: Database session
        reason: Why operator rejected
        
    Returns:
        True if successful, False otherwise
    """
    try:
        lead = db_session.query(LeadDB).filter(LeadDB.id == lead_id).first()
        
        if not lead:
            logger.warning(f"Lead {lead_id} not found")
            return False
        
        # Clear review flag and mark as handled
        lead.requires_human_review = False
        lead.review_type = None
        lead.review_reason = None
        lead.status = LeadStatus.LOST
        lead.tags = list(set(lead.tags + ["operator_reject"]))
        lead.notes = f"{lead.notes or ''}\n[REVIEW REJECTED] {reason} at {datetime.utcnow().isoformat()}"
        
        db_session.add(lead)
        db_session.commit()
        
        logger.info(f"Rejected review task for lead {lead_id}: {reason}")
        return True
    
    except Exception as e:
        logger.error(f"Error rejecting review task: {e}")
        return False


def flag_lead_for_review(
    lead_id: int,
    db_session,
    review_type: str = "MESSAGE",
    reason: str = "Flagged for human review",
) -> bool:
    """
    Flag a lead for human review (pause automated actions).
    
    Args:
        lead_id: Lead to flag
        db_session: Database session
        review_type: Type of review (MESSAGE, PROPOSAL, PRICING, etc.)
        reason: Why human review is needed
        
    Returns:
        True if successful, False otherwise
    """
    try:
        lead = db_session.query(LeadDB).filter(LeadDB.id == lead_id).first()
        
        if not lead:
            logger.warning(f"Lead {lead_id} not found")
            return False
        
        lead.requires_human_review = True
        lead.review_type = review_type
        lead.review_reason = reason
        lead.notes = f"{lead.notes or ''}\n[FLAGGED FOR REVIEW] {reason} at {datetime.utcnow().isoformat()}"
        
        db_session.add(lead)
        db_session.commit()
        
        logger.info(f"Flagged lead {lead_id} for {review_type} review: {reason}")
        return True
    
    except Exception as e:
        logger.error(f"Error flagging lead for review: {e}")
        return False
