"""
Lead Grading Service — Phase A

Assigns letter grades (A/B/C/D) to leads based on company fit, budget, timeline, engagement.

Grading Criteria:
- A: Hot lead (fit_score >= 0.8, budget + timeline clear)
- B: Warm lead (fit_score >= 0.6, some buying signals)
- C: Cool lead (fit_score >= 0.4, potential, needs nurturing)
- D: Cold lead (fit_score < 0.4, low priority)
"""

from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from aicmo.cam.domain import Lead, LeadGrade
from aicmo.cam.db_models import LeadDB

import logging

logger = logging.getLogger(__name__)


class LeadGradeService:
    """
    Assigns letter grades to leads based on multi-factor scoring.
    
    Grading Criteria:
    - A: Hot lead (fit_score >= 0.8, budget + timeline clear)
    - B: Warm lead (fit_score >= 0.6, some buying signals)
    - C: Cool lead (fit_score >= 0.4, potential, needs nurturing)
    - D: Cold lead (fit_score < 0.4, low priority)
    """
    
    GRADE_THRESHOLDS = {
        LeadGrade.A: {'fit_score': 0.8, 'conversion_prob': 0.7},
        LeadGrade.B: {'fit_score': 0.6, 'conversion_prob': 0.4},
        LeadGrade.C: {'fit_score': 0.4, 'conversion_prob': 0.2},
        LeadGrade.D: {'fit_score': 0.0, 'conversion_prob': 0.0},
    }
    
    @staticmethod
    def assign_grade(lead: Lead) -> Tuple[str, float, str]:
        """
        Assign a letter grade to a lead.
        
        Scoring logic:
        1. Start with lead_score (0.0-1.0)
        2. Add bonus points for buying signals:
           - Budget specified: +0.2
           - Timeline specified: +0.1
           - Pain points identified: +0.1
        3. Cap at 1.0
        4. Determine grade based on fit_score + budget/timeline
        5. Calculate conversion probability
        
        Args:
            lead: Lead domain model with scores and signals
            
        Returns:
            tuple: (grade: A/B/C/D, conversion_probability: 0.0-1.0, reason: explanation)
        """
        # Base score from lead_score
        base_score = lead.lead_score or 0.0
        
        # Bonus points for buying signals
        budget_bonus = 0.2 if lead.budget_estimate_range else 0.0
        timeline_bonus = 0.1 if lead.timeline_months else 0.0
        pain_points_bonus = 0.1 if lead.pain_points and len(lead.pain_points) > 0 else 0.0
        
        # Fit score: 0.0-1.0
        fit_score = min(1.0, base_score + budget_bonus + timeline_bonus + pain_points_bonus)
        
        # Determine conversion probability based on engagement + fit
        # Use tags as engagement indicator (each tag adds 0.05)
        engagement_factor = min(1.0, len(lead.tags or []) * 0.05) if lead.tags else 0.0
        conversion_prob = fit_score * 0.7 + engagement_factor * 0.3
        
        # Assign grade based on thresholds
        if fit_score >= LeadGradeService.GRADE_THRESHOLDS[LeadGrade.A]['fit_score']:
            # A-grade requires high fit AND clear budget/timeline
            if lead.budget_estimate_range and lead.timeline_months:
                grade = LeadGrade.A
                reason = "High fit + clear budget and timeline"
            else:
                # Fall back to B if missing critical signals
                grade = LeadGrade.B
                reason = "High fit but missing budget/timeline clarity"
        elif fit_score >= LeadGradeService.GRADE_THRESHOLDS[LeadGrade.B]['fit_score']:
            grade = LeadGrade.B
            reason = "Good fit with some buying signals"
        elif fit_score >= LeadGradeService.GRADE_THRESHOLDS[LeadGrade.C]['fit_score']:
            grade = LeadGrade.C
            reason = "Moderate fit, potential with nurturing"
        else:
            grade = LeadGrade.D
            reason = "Low fit, cold lead"
        
        return grade, conversion_prob, reason
    
    @staticmethod
    def update_lead_grade(
        db: Session,
        lead_id: int,
        lead: Lead,
    ) -> Optional[LeadDB]:
        """
        Update a lead's grade in the database.
        
        Args:
            db: Database session
            lead_id: Lead ID
            lead: Lead domain model with updated fields
            
        Returns:
            Updated LeadDB instance, or None if not found
        """
        lead_db = db.query(LeadDB).filter(LeadDB.id == lead_id).first()
        if not lead_db:
            logger.warning(f"Lead {lead_id} not found for grading")
            return None
        
        # Assign new grade
        grade, conversion_prob, reason = LeadGradeService.assign_grade(lead)
        
        # Update database
        lead_db.lead_grade = grade
        lead_db.conversion_probability = conversion_prob
        lead_db.fit_score_for_service = lead.lead_score or 0.0
        lead_db.grade_reason = reason
        lead_db.graded_at = datetime.utcnow()
        
        db.commit()
        db.refresh(lead_db)
        
        logger.info(f"Lead {lead_id} graded as {grade}: {reason}")
        
        return lead_db
