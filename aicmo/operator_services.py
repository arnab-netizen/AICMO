"""
Operator Command Center service layer.

Provides data and operations for the Command Center UI, integrating
with CAM, Project, and Execution domains.

All functions accept a database session and return typed data structures.
Stubs are marked with TODO comments where backend implementation is pending.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

# Domain models
from aicmo.domain.project import Project, ProjectState
from aicmo.domain.execution import ContentItem, PublishStatus, ExecutionStatus
from aicmo.cam.db_models import (
    CampaignDB,  # TODO Phase 4: Replace with CAM query ports
    LeadDB,  # TODO Phase 4: Replace with CAM query ports
    OutreachAttemptDB,  # TODO Phase 4: Replace with CAM query ports
    ContactEventDB,  # TODO Phase 4: Replace with CAM query ports
    DiscoveryJobDB,  # TODO Phase 4: Replace with CAM query ports
    SafetySettingsDB,  # TODO Phase 4: Replace with CAM query ports
)

# W2.1: Import unified orchestrator and services
from aicmo.domain.intake import ClientIntake
from aicmo.delivery.kaizen_orchestrator import KaizenOrchestrator
from aicmo.pm.service import generate_project_dashboard
from aicmo.analytics.service import generate_performance_dashboard


# ============================================================================
# ATTENTION METRICS
# ============================================================================

def get_attention_metrics(db: Session) -> Dict[str, int]:
    """
    Compute Command Center attention metrics.
    
    Returns metrics for:
    - Total leads
    - High-intent leads (job changes, engaged status)
    - Approvals pending (strategy + creative drafts)
    - Execution success rate (last 7 days)
    - Failed posts (last 24h)
    
    Args:
        db: Database session
        
    Returns:
        Dict with metric keys and integer values
    """
    # Total leads
    total_leads = db.query(LeadDB).count()
    
    # High-intent leads (using status or stage as proxy)
    high_intent_leads = db.query(LeadDB).filter(
        LeadDB.status.in_(["CONTACTED", "ENGAGED"])
    ).count()
    
    # Approvals pending - count projects in DRAFT states
    # TODO: Wire to Project table when available in DB
    # For now, estimate from Lead stages as proxy
    approvals_pending = db.query(LeadDB).filter(
        LeadDB.stage.in_(["STRATEGY_DRAFT", "CREATIVE_DRAFT"])
    ).count()
    
    # Execution success rate (last 7 days)
    seven_days_ago = datetime.now() - timedelta(days=7)
    total_attempts = db.query(OutreachAttemptDB).filter(
        OutreachAttemptDB.attempted_at >= seven_days_ago
    ).count()
    
    successful_attempts = db.query(OutreachAttemptDB).filter(
        OutreachAttemptDB.attempted_at >= seven_days_ago,
        OutreachAttemptDB.status == "SENT"
    ).count()
    
    execution_success = int((successful_attempts / total_attempts * 100) if total_attempts > 0 else 0)
    
    # Failed posts last 24h
    twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
    failed_last_24h = db.query(OutreachAttemptDB).filter(
        OutreachAttemptDB.attempted_at >= twenty_four_hours_ago,
        OutreachAttemptDB.status == "FAILED"
    ).count()
    
    return {
        "leads": total_leads,
        "high_intent": high_intent_leads,
        "approvals_pending": approvals_pending,
        "execution_success": execution_success,
        "failed_last_24h": failed_last_24h,
    }


# ============================================================================
# ACTIVITY FEED
# ============================================================================

def get_activity_feed(db: Session, limit: int = 25) -> List[Dict[str, str]]:
    """
    Fetch recent activity events for the Command Center feed.
    
    Aggregates events from:
    - Outreach attempts (sent, failed)
    - Contact events (inbound/outbound)
    - Discovery jobs (completed)
    
    Args:
        db: Database session
        limit: Maximum number of events to return
        
    Returns:
        List of event dicts with keys: time, event, detail
    """
    events = []
    
    # Recent outreach attempts
    recent_attempts = db.query(OutreachAttemptDB).order_by(
        desc(OutreachAttemptDB.attempted_at)
    ).limit(limit).all()
    
    for attempt in recent_attempts:
        lead = db.query(LeadDB).filter(LeadDB.id == attempt.lead_id).first()
        lead_name = lead.name if lead else f"Lead #{attempt.lead_id}"
        
        if attempt.status == "SENT":
            events.append({
                "time": attempt.attempted_at.strftime("%H:%M") if attempt.attempted_at else "--:--",
                "event": f"Message sent to {lead_name}",
                "detail": f"Channel: {attempt.channel}, Step: {attempt.step_number}"
            })
        elif attempt.status == "FAILED":
            events.append({
                "time": attempt.attempted_at.strftime("%H:%M") if attempt.attempted_at else "--:--",
                "event": f"Message failed for {lead_name}",
                "detail": f"Error: {attempt.last_error or 'Unknown'}"
            })
    
    # Recent contact events
    recent_contacts = db.query(ContactEventDB).order_by(
        desc(ContactEventDB.event_at)
    ).limit(limit // 2).all()
    
    for contact in recent_contacts:
        lead = db.query(LeadDB).filter(LeadDB.id == contact.lead_id).first()
        lead_name = lead.name if lead else f"Lead #{contact.lead_id}"
        
        events.append({
            "time": contact.event_at.strftime("%H:%M") if contact.event_at else "--:--",
            "event": f"{contact.event_type} from {lead_name}",
            "detail": f"Channel: {contact.channel}"
        })
    
    # Sort by time (most recent first) and limit
    events.sort(key=lambda x: x.get("time", ""), reverse=True)
    return events[:limit]


# ============================================================================
# PROJECTS PIPELINE
# ============================================================================

def get_projects_pipeline(db: Session) -> List[Dict[str, Any]]:
    """
    Fetch all projects for the Kanban board.
    
    W2.1: Now uses real campaign data + strategy status to determine stage.
    
    Args:
        db: Database session
        
    Returns:
        List of project dicts with keys: id, name, stage, clarity
    """
    campaigns = db.query(CampaignDB).filter(CampaignDB.active == True).all()
    
    projects = []
    for campaign in campaigns:
        # Count leads and outreach for clarity metric
        lead_count = db.query(LeadDB).filter(LeadDB.campaign_id == campaign.id).count()
        outreach_count = db.query(OutreachAttemptDB).filter(
            OutreachAttemptDB.campaign_id == campaign.id
        ).count()
        
        # Clarity based on data completeness
        clarity = min(100, (lead_count * 5) + (outreach_count * 2))
        
        # Stage from strategy_status and activity
        if outreach_count > 0:
            stage = "EXECUTION"
        elif campaign.strategy_status == "APPROVED":
            stage = "CREATIVE"
        elif campaign.strategy_status in ["DRAFT", "REJECTED"]:
            stage = "STRATEGY"
        else:
            stage = "INTAKE"
        
        projects.append({
            "id": campaign.id,
            "name": campaign.name,
            "stage": stage,
            "clarity": clarity,
            "strategy_status": campaign.strategy_status or "DRAFT",
            "lead_count": lead_count,
            "outreach_count": outreach_count,
        })
    
    return projects


# ============================================================================
# WAR ROOM
# ============================================================================

def get_project_context(db: Session, project_id: int) -> Dict[str, Any]:
    """
    Load intake context for a project in the War Room.
    
    Phase 9.1: Now uses real CampaignDB intake fields + metrics.
    
    Args:
        db: Database session
        project_id: Project/Campaign ID
        
    Returns:
        Dict with keys: goal, constraints, audience, budget, etc.
    """
    campaign = db.query(CampaignDB).filter(CampaignDB.id == project_id).first()
    
    if not campaign:
        return {"error": "Project not found"}
    
    # Get real metrics
    lead_count = db.query(LeadDB).filter(LeadDB.campaign_id == project_id).count()
    outreach_count = db.query(OutreachAttemptDB).filter(OutreachAttemptDB.campaign_id == project_id).count()
    
    return {
        "project_name": campaign.name,
        "goal": campaign.intake_goal or campaign.description or f"Outreach campaign for {campaign.target_niche or 'target audience'}",
        "constraints": campaign.intake_constraints or "No constraints specified",
        "audience": campaign.intake_audience or campaign.target_niche or "General audience",
        "budget": campaign.intake_budget or "Not specified",
        "timeline": "Ongoing",
        "strategy_status": campaign.strategy_status or "DRAFT",
        "lead_count": lead_count,
        "outreach_count": outreach_count,
        "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
    }


def get_project_strategy_doc(db: Session, project_id: int) -> str:
    """
    Load AI strategy document for a project.
    
    Phase 9.1: Now loads real strategy_text from CampaignDB.
    
    Args:
        db: Database session
        project_id: Project/Campaign ID
        
    Returns:
        Strategy document as markdown/text string
    """
    campaign = db.query(CampaignDB).filter(CampaignDB.id == project_id).first()
    
    if not campaign:
        return "# Error\n\nProject not found."
    
    # Return stored strategy or generate placeholder
    if campaign.strategy_text:
        return campaign.strategy_text
    
    # Generate initial placeholder if none exists
    placeholder = f"""# Strategy Document: {campaign.name}

## Campaign Overview
Target: {campaign.target_niche or 'General audience'}

## Messaging Pillars
1. Value proposition
2. Social proof
3. Call to action

## Channel Strategy
- LinkedIn: Professional outreach
- Email: Follow-up sequences
- Twitter: Engagement and awareness

## Success Metrics
- Response rate: Target 15%
- Meeting bookings: Target 5%
- Pipeline generated: Track opportunities

**Status**: {campaign.strategy_status or 'DRAFT'} - Awaiting approval

---
*Auto-generated placeholder. Update strategy_text field to customize.*
"""
    return placeholder


def approve_strategy(db: Session, project_id: int, reason: Optional[str] = None) -> None:
    """
    Approve a project's strategy and transition to CREATIVE stage.
    
    Phase 9.1: Now updates strategy_status in CampaignDB.
    
    Args:
        db: Database session
        project_id: Project/Campaign ID
        reason: Optional approval reason/notes
    """
    campaign = db.query(CampaignDB).filter(CampaignDB.id == project_id).first()
    
    if campaign:
        campaign.strategy_status = "APPROVED"
        campaign.strategy_rejection_reason = None  # Clear any previous rejection
        approval_note = f"Approved: {datetime.now().isoformat()}"
        if reason:
            approval_note += f" - {reason}"
        
        # Append approval to description for audit trail
        campaign.description = (campaign.description or "") + f"\n[{approval_note}]"
        db.commit()


def reject_strategy(db: Session, project_id: int, reason: str) -> None:
    """
    Reject a project's strategy and send back to draft.
    
    Phase 9.1: Now updates strategy_status and rejection_reason in CampaignDB.
    
    Args:
        db: Database session
        project_id: Project/Campaign ID
        reason: Rejection reason (required)
    """
    campaign = db.query(CampaignDB).filter(CampaignDB.id == project_id).first()
    
    if campaign:
        campaign.strategy_status = "REJECTED"
        campaign.strategy_rejection_reason = reason
        
        # Append rejection to description for audit trail
        rejection_note = f"Rejected: {reason} - {datetime.now().isoformat()}"
        campaign.description = (campaign.description or "") + f"\n[{rejection_note}]"
        db.commit()


# ============================================================================
# GALLERY
# ============================================================================

def get_creatives_for_project(db: Session, project_id: int) -> List[Dict[str, Any]]:
    """
    Load creative assets for a project.
    
    W2.1: Returns creatives from unified flow if available, otherwise synthetic placeholders.
    
    Args:
        db: Database session
        project_id: Project/Campaign ID
        
    Returns:
        List of creative dicts with keys: id, platform, caption, status, etc.
    """
    # Get campaign for context
    campaign = db.query(CampaignDB).filter(CampaignDB.id == project_id).first()
    if not campaign:
        return []
    
    creatives = []
    
    # If strategy is approved, try to generate real creatives from unified flow
    if campaign.strategy_status == "APPROVED" and campaign.intake_goal:
        try:
            # Build minimal intake from campaign data
            intake = ClientIntake(
                brand_name=campaign.name,
                industry=campaign.target_niche or "General",
                primary_goal=campaign.intake_goal,
                target_audiences=[campaign.intake_audience or "Target audience"],
            )
            
            # Call unified orchestrator (skip Kaizen for operator view)
            orchestrator = KaizenOrchestrator()
            result = orchestrator.run_full_campaign_flow(
                intake=intake,
                total_budget=float(campaign.intake_budget) if campaign.intake_budget and campaign.intake_budget.replace('.','',1).isdigit() else 10000.0,
                skip_kaizen=True  # Fast path for operator view
            )
            
            # Extract creative variants from result
            if "creatives" in result and hasattr(result["creatives"], "variants"):
                for idx, variant in enumerate(result["creatives"].variants, start=1):
                    creatives.append({
                        "id": f"{project_id}_real_{idx}",
                        "platform": variant.platform,
                        "caption": variant.caption or variant.hook,
                        "status": "APPROVED",
                        "asset_type": variant.format,
                        "project_id": project_id,
                        "hook": variant.hook,
                        "cta": variant.cta,
                    })
        except Exception:
            # Fall through to synthetic if flow fails
            pass
    
    # Fallback: Generate synthetic creatives
    if not creatives:
        platform_templates = [
            ("LinkedIn", "Professional post about {niche}"),
            ("Twitter", "Thread on {niche} best practices"),
            ("Email", "Weekly newsletter for {niche} audience"),
        ]
        
        for idx, (platform, template) in enumerate(platform_templates, start=1):
            niche = campaign.target_niche or "target audience"
            creatives.append({
                "id": f"{project_id}_{idx}",
                "platform": platform,
                "caption": template.format(niche=niche),
                "status": "DRAFT",
                "asset_type": "post",
                "project_id": project_id,
            })
    
    return creatives


def update_creative(db: Session, project_id: int, creative_id: int, changes: Dict[str, Any]) -> None:
    """
    Update a creative asset.
    
    Phase 9.1: Stub implementation (no persistence).
    TODO: Wire to ContentItemDB when table is created.
    
    Args:
        db: Database session
        project_id: Project/Campaign ID
        creative_id: Creative asset ID
        changes: Dict of fields to update (e.g., {"caption": "New text"})
    """
    # NOTE: No persistence layer available yet for ContentItem
    # Changes are accepted but not stored
    pass


def regenerate_creative(db: Session, project_id: int, creative_id: int) -> None:
    """
    Trigger regeneration of a creative asset.
    
    Phase 9.1: Stub implementation (no generation pipeline).
    TODO: Wire to creative generation service.
    
    Args:
        db: Database session
        project_id: Project/Campaign ID
        creative_id: Creative asset ID
    """
    # NOTE: No creative generation pipeline available yet
    pass


def delete_creative(db: Session, project_id: int, creative_id: int) -> None:
    """
    Delete/trash a creative asset.
    
    Phase 9.1: Stub implementation (no persistence).
    TODO: Wire to ContentItemDB soft delete.
    
    Args:
        db: Database session
        project_id: Project/Campaign ID
        creative_id: Creative asset ID
    """
    # NOTE: No persistence layer available yet
    pass


def bulk_approve_creatives(db: Session, project_id: int, ids: List[int]) -> None:
    """
    Bulk approve multiple creative assets.
    
    Phase 9.1: Updates campaign strategy_status as proxy.
    TODO: Wire to ContentItemDB when available.
    
    Args:
        db: Database session
        project_id: Project/Campaign ID
        ids: List of creative asset IDs to approve
    """
    # Proxy: Set campaign strategy to APPROVED as indication
    campaign = db.query(CampaignDB).filter(CampaignDB.id == project_id).first()
    if campaign and campaign.strategy_status != "APPROVED":
        campaign.strategy_status = "APPROVED"
        db.commit()


def bulk_schedule_creatives(db: Session, project_id: int, ids: List[int], schedule_params: Optional[Dict[str, Any]] = None) -> None:
    """
    Bulk schedule multiple creative assets for publishing.
    
    Phase 9.1: Stub implementation (no execution queue).
    TODO: Wire to execution scheduler.
    
    Args:
        db: Database session
        project_id: Project/Campaign ID
        ids: List of creative asset IDs to schedule
        schedule_params: Optional scheduling parameters (dates, times, etc.)
    """
    # NOTE: No execution queue/scheduler available yet
    # Would need ExecutionQueueDB or similar table
    pass


# ============================================================================
# LEAD MANAGEMENT - CRM OPERATIONS
# ============================================================================

def get_lead_detail(db: Session, campaign_id: int, lead_id: int) -> Dict[str, Any]:
    """
    Fetch complete lead record with all CRM fields.
    
    Phase A (Mini-CRM): Returns lead detail including new grading fields.
    
    Args:
        db: Database session
        campaign_id: Campaign/Project ID (for authorization)
        lead_id: Lead ID to fetch
        
    Returns:
        Dict with lead data including:
        - Basic: id, name, email, company
        - Company Info: company_size, industry, growth_rate, annual_revenue, etc.
        - Decision Maker: decision_maker_name, decision_maker_email, role, linkedin
        - Sales: budget_estimate_range, timeline_months, pain_points, buying_signals
        - Grading: lead_grade (A/B/C/D), conversion_probability, fit_score_for_service
        - Tracking: proposal_generated_at, contract_signed_at, referral_source
    """
    lead = db.query(LeadDB).filter(
        LeadDB.id == lead_id,
        LeadDB.campaign_id == campaign_id
    ).first()
    
    if not lead:
        return {"error": f"Lead {lead_id} not found"}
    
    return {
        # Basic fields
        "id": lead.id,
        "name": lead.name,
        "email": lead.email,
        "company": lead.company,
        "campaign_id": lead.campaign_id,
        "status": lead.status,
        "lead_score": lead.lead_score,
        
        # Company Info (Phase A)
        "company_size": lead.company_size,
        "industry": lead.industry,
        "growth_rate": lead.growth_rate,
        "annual_revenue": lead.annual_revenue,
        "employee_count": lead.employee_count,
        "company_website": lead.company_website,
        "company_headquarters": lead.company_headquarters,
        "founding_year": lead.founding_year,
        "funding_status": lead.funding_status,
        
        # Decision Maker (Phase A)
        "decision_maker_name": lead.decision_maker_name,
        "decision_maker_email": lead.decision_maker_email,
        "decision_maker_role": lead.decision_maker_role,
        "decision_maker_linkedin": lead.decision_maker_linkedin,
        
        # Sales (Phase A)
        "budget_estimate_range": lead.budget_estimate_range,
        "timeline_months": lead.timeline_months,
        "pain_points": lead.pain_points or [],
        "buying_signals": lead.buying_signals or {},
        
        # Grading (Phase A)
        "lead_grade": lead.lead_grade,
        "conversion_probability": lead.conversion_probability,
        "fit_score_for_service": lead.fit_score_for_service,
        "graded_at": lead.graded_at.isoformat() if lead.graded_at else None,
        "grade_reason": lead.grade_reason,
        
        # Tracking (Phase A)
        "proposal_generated_at": lead.proposal_generated_at.isoformat() if lead.proposal_generated_at else None,
        "proposal_content_id": lead.proposal_content_id,
        "contract_signed_at": lead.contract_signed_at.isoformat() if lead.contract_signed_at else None,
        "referral_source": lead.referral_source,
        "referred_by_name": lead.referred_by_name,
        
        # Timestamps
        "created_at": lead.created_at.isoformat() if lead.created_at else None,
        "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
    }


def update_lead_crm_fields(
    db: Session,
    campaign_id: int,
    lead_id: int,
    updates: Dict[str, Any],
    auto_regrade: bool = True,
) -> Dict[str, Any]:
    """
    Update lead CRM fields and optionally re-grade lead.
    
    Phase A (Mini-CRM): Supports updating all CRM fields. When auto_regrade=True,
    automatically recalculates lead grade after updating fields.
    
    Args:
        db: Database session
        campaign_id: Campaign/Project ID
        lead_id: Lead ID to update
        updates: Dict of field_name -> value pairs to update
        auto_regrade: If True, recalculate grade after update (default: True)
        
    Returns:
        Updated lead dict (from get_lead_detail) or error dict
    """
    lead = db.query(LeadDB).filter(
        LeadDB.id == lead_id,
        LeadDB.campaign_id == campaign_id
    ).first()
    
    if not lead:
        return {"error": f"Lead {lead_id} not found"}
    
    # List of allowed update fields
    allowed_fields = {
        "company_size", "industry", "growth_rate", "annual_revenue", "employee_count",
        "company_website", "company_headquarters", "founding_year", "funding_status",
        "decision_maker_name", "decision_maker_email", "decision_maker_role", "decision_maker_linkedin",
        "budget_estimate_range", "timeline_months", "pain_points", "buying_signals",
        "referral_source", "referred_by_name", "status", "phone",
    }
    
    # Apply updates
    for field, value in updates.items():
        if field in allowed_fields and hasattr(lead, field):
            setattr(lead, field, value)
    
    # Auto-regrade if enabled
    if auto_regrade:
        try:
            from aicmo.cam.domain import Lead
            from aicmo.cam.lead_grading import LeadGradeService
            
            # Convert LeadDB to domain model
            lead_domain = Lead(
                id=lead.id,
                name=lead.name,
                email=lead.email,
                company=lead.company,
                lead_score=lead.lead_score,
                company_size=lead.company_size,
                industry=lead.industry,
                growth_rate=lead.growth_rate,
                annual_revenue=lead.annual_revenue,
                employee_count=lead.employee_count,
                budget_estimate_range=lead.budget_estimate_range,
                timeline_months=lead.timeline_months,
                pain_points=lead.pain_points,
                buying_signals=lead.buying_signals,
            )
            
            # Re-grade using service
            LeadGradeService.update_lead_grade(db, lead_id, lead_domain)
        except Exception as e:
            # Graceful degradation - continue without grading if service fails
            pass
    
    db.commit()
    
    return get_lead_detail(db, campaign_id, lead_id)


def list_leads_by_grade(
    db: Session,
    campaign_id: int,
    grade: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> Dict[str, Any]:
    """
    List leads filtered by grade (A/B/C/D).
    
    Phase A (Mini-CRM): Queries leads by lead_grade and returns paginated results.
    
    Args:
        db: Database session
        campaign_id: Campaign/Project ID
        grade: Filter by grade ('A', 'B', 'C', 'D', or None for all)
        skip: Pagination offset
        limit: Maximum results to return
        
    Returns:
        Dict with keys:
        - total: Total matching leads
        - grade_filter: The grade filter applied (if any)
        - leads: List of lead dicts with key fields
    """
    query = db.query(LeadDB).filter(LeadDB.campaign_id == campaign_id)
    
    if grade and grade.upper() in ['A', 'B', 'C', 'D']:
        query = query.filter(LeadDB.lead_grade == grade.upper())
    
    total = query.count()
    leads_db = query.order_by(
        desc(LeadDB.lead_grade),
        desc(LeadDB.conversion_probability)
    ).offset(skip).limit(limit).all()
    
    leads = [
        {
            "id": lead.id,
            "name": lead.name,
            "email": lead.email,
            "company": lead.company,
            "lead_grade": lead.lead_grade,
            "conversion_probability": lead.conversion_probability,
            "fit_score_for_service": lead.fit_score_for_service,
            "budget_estimate_range": lead.budget_estimate_range,
            "timeline_months": lead.timeline_months,
            "status": lead.status,
            "lead_score": lead.lead_score,
        }
        for lead in leads_db
    ]
    
    return {
        "total": total,
        "grade_filter": grade.upper() if grade else None,
        "skip": skip,
        "limit": limit,
        "leads": leads,
    }


def get_lead_grade_distribution(db: Session, campaign_id: int) -> Dict[str, int]:
    """
    Get count of leads by grade for a campaign.
    
    Phase A (Mini-CRM): Returns grade counts (A, B, C, D).
    
    Args:
        db: Database session
        campaign_id: Campaign/Project ID
        
    Returns:
        Dict with grade counts: {'A': 5, 'B': 12, 'C': 20, 'D': 8, 'total': 45}
    """
    grades = ['A', 'B', 'C', 'D']
    distribution = {}
    
    for grade in grades:
        count = db.query(LeadDB).filter(
            LeadDB.campaign_id == campaign_id,
            LeadDB.lead_grade == grade
        ).count()
        distribution[grade] = count
    
    distribution['total'] = sum(distribution.values())
    
    return distribution


# ============================================================================
# CONTROL TOWER - TIMELINE
# ============================================================================

def get_execution_timeline(db: Session, project_id: Optional[int] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Fetch execution timeline for scheduled/completed posts.
    
    Uses OutreachAttemptDB as proxy for execution events.
    TODO: Integrate with ContentItem execution logs when available.
    
    Args:
        db: Database session
        project_id: Optional project/campaign filter
        limit: Maximum number of events
        
    Returns:
        List of timeline event dicts with keys: date, time, platform, status, message
    """
    query = db.query(OutreachAttemptDB).order_by(desc(OutreachAttemptDB.attempted_at))
    
    if project_id:
        query = query.filter(OutreachAttemptDB.campaign_id == project_id)
    
    attempts = query.limit(limit).all()
    
    timeline = []
    for attempt in attempts:
        lead = db.query(LeadDB).filter(LeadDB.id == attempt.lead_id).first()
        
        timeline.append({
            "date": attempt.attempted_at.strftime("%Y-%m-%d") if attempt.attempted_at else "Unknown",
            "time": attempt.attempted_at.strftime("%H:%M") if attempt.attempted_at else "--:--",
            "platform": attempt.channel,
            "status": attempt.status,
            "message": f"Step {attempt.step_number} to {lead.name if lead else 'Unknown'}",
        })
    
    return timeline


# ============================================================================
# CONTROL TOWER - GATEWAY STATUS & SYSTEM PAUSE
# ============================================================================

def get_gateway_status(db: Optional[Session] = None) -> Dict[str, str]:
    """
    Check health status of all gateway adapters.
    
    TODO: Implement real health checks by calling gateway adapter methods.
    Currently returns static status.
    
    Args:
        db: Optional database session (may not be needed for gateway checks)
        
    Returns:
        Dict mapping gateway name to status string ("ok", "warn", "bad")
    """
    # Phase 9.1: Basic health heuristics using real data
    if db is None:
        return {"error": "Database session required"}
    
    statuses = {}
    
    # LinkedIn: Check if we have recent outreach attempts
    recent_linkedin = db.query(OutreachAttemptDB).filter(
        OutreachAttemptDB.method == "linkedin"
    ).order_by(OutreachAttemptDB.sent_at.desc()).first()
    statuses["LinkedIn API"] = "ok" if recent_linkedin else "unknown"
    
    # Email: Similar checks
    recent_email = db.query(OutreachAttemptDB).filter(
        OutreachAttemptDB.method == "email"
    ).order_by(OutreachAttemptDB.sent_at.desc()).first()
    statuses["Email SMTP"] = "ok" if recent_email else "unknown"
    
    # OpenAI: Check if we have recent discovery jobs
    recent_discovery = db.query(DiscoveryJobDB).order_by(
        DiscoveryJobDB.created_at.desc()
    ).first()
    statuses["OpenAI"] = "ok" if recent_discovery else "unknown"
    
    # Apollo: Check lead sources
    apollo_leads = db.query(LeadDB).filter(LeadDB.source == "apollo").count()
    statuses["Apollo"] = "ok" if apollo_leads > 0 else "unknown"
    
    return statuses


def set_system_pause(db: Session, flag: bool) -> None:
    """
    Set system-wide execution pause flag.
    
    Phase 9.1: Stores in SafetySettingsDB for persistence.
    
    Args:
        db: Database session
        flag: True to pause, False to resume
    """
    # Get or create singleton safety settings record
    settings = db.query(SafetySettingsDB).first()
    if not settings:
        settings = SafetySettingsDB(id=1, data={}, system_paused=flag)
        db.add(settings)
    else:
        settings.system_paused = flag
    db.commit()


def get_system_pause(db: Session) -> bool:
    """
    Get current system-wide execution pause flag.
    
    Phase 9.1: Reads from SafetySettingsDB.
    
    Args:
        db: Database session
        
    Returns:
        True if system is paused, False otherwise
    """
    settings = db.query(SafetySettingsDB).first()
    return settings.system_paused if settings else False


# ============================================================================
# W2.1: UNIFIED FLOW & SUBSYSTEM VIEWS
# ============================================================================

def get_project_unified_view(db: Session, project_id: int) -> Dict[str, Any]:
    """
    W2.1: Get unified view of project with all subsystem outputs.
    
    Calls the unified Kaizen orchestrator to get:
    - Brand strategy
    - Media plan
    - Social trends
    - Analytics dashboard
    - PM tasks
    - Client approvals
    - Creatives
    
    Args:
        db: Database session
        project_id: Project/Campaign ID
        
    Returns:
        Dict with all subsystem outputs or error message
    """
    try:
        # Get campaign to build intake
        campaign = db.query(CampaignDB).filter(CampaignDB.id == project_id).first()
        if not campaign:
            return {"error": "Project not found"}
        
        # Build intake from campaign data
        intake = ClientIntake(
            brand_name=campaign.name,
            industry=campaign.target_niche or "General",
            primary_goal=campaign.intake_goal or "Campaign execution",
            target_audiences=[campaign.intake_audience or "Target audience"],
        )
        
        # Call unified orchestrator
        orchestrator = KaizenOrchestrator()
        result = orchestrator.run_full_kaizen_flow_for_project(
            intake=intake,
            project_id=str(project_id),
            total_budget=float(campaign.intake_budget) if campaign.intake_budget and campaign.intake_budget.replace('.','',1).isdigit() else 10000.0,
            skip_kaizen=True  # Use baseline for operator view
        )
        
        # Add campaign metadata
        result["campaign_id"] = campaign.id
        result["campaign_name"] = campaign.name
        result["strategy_status"] = campaign.strategy_status or "DRAFT"
        
        return result
        
    except Exception as e:
        return {"error": f"Failed to generate unified view: {str(e)}"}


def get_project_pm_dashboard(db: Session, project_id: int) -> Dict[str, Any]:
    """
    W2.1: Get PM dashboard for project with tasks, timeline, and capacity.
    
    Args:
        db: Database session
        project_id: Project/Campaign ID
        
    Returns:
        PM dashboard data or error
    """
    try:
        campaign = db.query(CampaignDB).filter(CampaignDB.id == project_id).first()
        if not campaign:
            return {"error": "Project not found"}
        
        # Build intake
        intake = ClientIntake(
            brand_name=campaign.name,
            primary_goal=campaign.intake_goal or "Campaign",
        )
        
        # Generate PM dashboard
        dashboard = generate_project_dashboard(
            intake=intake,
            project_id=str(project_id)
        )
        
        return {
            "project_id": project_id,
            "dashboard": dashboard,
        }
        
    except Exception as e:
        return {"error": f"Failed to generate PM dashboard: {str(e)}"}


def get_project_analytics_dashboard(db: Session, project_id: int) -> Dict[str, Any]:
    """
    W2.1: Get analytics dashboard for project.
    
    Args:
        db: Database session
        project_id: Project/Campaign ID
        
    Returns:
        Analytics dashboard data or error
    """
    try:
        campaign = db.query(CampaignDB).filter(CampaignDB.id == project_id).first()
        if not campaign:
            return {"error": "Project not found"}
        
        # Build intake
        intake = ClientIntake(
            brand_name=campaign.name,
            primary_goal=campaign.intake_goal or "Campaign",
        )
        
        # Generate analytics dashboard
        dashboard = generate_performance_dashboard(
            intake=intake,
            period_days=7
        )
        
        return {
            "project_id": project_id,
            "dashboard": dashboard,
        }
        
    except Exception as e:
        return {"error": f"Failed to generate analytics dashboard: {str(e)}"}


# ============================================================================
# PHASE 7.5: CREATIVE REVIEW SERVICE
# ============================================================================

class CreativeReviewService:
    """
    Service for managing creative review and optimization task approval.
    
    Provides operators with visibility into:
    - Pending optimization tasks
    - Variant suggestions
    - Performance metrics
    - Approval/rejection workflows
    """
    
    def __init__(self, optimization_optimizer=None, media_engine=None):
        """
        Initialize creative review service.
        
        Args:
            optimization_optimizer: CreativePerformanceOptimizer instance
            media_engine: MediaEngine instance
        """
        self.optimizer = optimization_optimizer
        self.media_engine = media_engine
        self.approval_history: List[Dict[str, Any]] = []
    
    def list_creative_optimization_tasks(
        self,
        client_id: str,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Get list of optimization tasks for review.
        
        Args:
            client_id: Client to get tasks for
            status: Filter by status (pending, approved, etc)
            limit: Max results
            
        Returns:
            List of task dicts with metadata for UI display
        """
        if not self.optimizer:
            return []
        
        try:
            # Get tasks from optimizer
            if status:
                tasks = self.optimizer.list_tasks_by_status(status)
            else:
                tasks = self.optimizer.list_all_tasks()
            
            # Format for UI
            result = []
            for task in tasks[:limit]:
                # Get asset info for display
                asset = None
                if self.media_engine:
                    asset = self.media_engine.assets.get(task.asset_id)
                
                task_data = {
                    "task_id": task.task_id,
                    "asset_id": task.asset_id,
                    "asset_name": asset.name if asset else "Unknown",
                    "asset_type": asset.media_type.value if asset else "unknown",
                    "reason": task.reason,
                    "action_type": task.action_type,
                    "status": task.status,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat(),
                    "metadata": task.metadata,
                }
                
                result.append(task_data)
            
            return result
            
        except Exception as e:
            return []
    
    def approve_creative_task(
        self,
        task_id: str,
        operator_id: str,
        notes: Optional[str] = None,
    ) -> bool:
        """
        Operator approves a task for execution.
        
        Args:
            task_id: Task to approve
            operator_id: Operator ID (for audit trail)
            notes: Optional approval notes
            
        Returns:
            True if approved, False otherwise
        """
        if not self.optimizer:
            return False
        
        try:
            # Update task status
            self.optimizer.mark_task_status(
                task_id=task_id,
                new_status="approved",
                metadata={
                    "approved_by": operator_id,
                    "approved_at": datetime.now().isoformat(),
                    "approval_notes": notes,
                },
            )
            
            # Log approval
            self.approval_history.append({
                "task_id": task_id,
                "operator_id": operator_id,
                "action": "approve",
                "timestamp": datetime.now(),
                "notes": notes,
            })
            
            return True
            
        except Exception:
            return False
    
    def reject_creative_task(
        self,
        task_id: str,
        operator_id: str,
        reason: Optional[str] = None,
    ) -> bool:
        """
        Operator rejects a task.
        
        Args:
            task_id: Task to reject
            operator_id: Operator ID (for audit trail)
            reason: Rejection reason
            
        Returns:
            True if rejected, False otherwise
        """
        if not self.optimizer:
            return False
        
        try:
            # Update task status
            self.optimizer.mark_task_status(
                task_id=task_id,
                new_status="rejected",
                metadata={
                    "rejected_by": operator_id,
                    "rejected_at": datetime.now().isoformat(),
                    "rejection_reason": reason,
                },
            )
            
            # Log rejection
            self.approval_history.append({
                "task_id": task_id,
                "operator_id": operator_id,
                "action": "reject",
                "timestamp": datetime.now(),
                "reason": reason,
            })
            
            return True
            
        except Exception:
            return False
    
    def trigger_task_execution(self, task_id: str) -> bool:
        """
        Trigger execution of an approved task.
        
        Args:
            task_id: Task to execute
            
        Returns:
            True if execution started, False otherwise
        """
        if not self.optimizer:
            return False
        
        try:
            task = self.optimizer.get_task(task_id)
            if not task:
                return False
            
            if task.status != "approved":
                return False
            
            # Execute based on action type
            if task.action_type == "generate_variants":
                success = self.optimizer.execute_task_generate_variants(task_id)
            elif task.action_type == "replace":
                success = self.optimizer.execute_task_replace(task_id)
            else:
                success = False
            
            return success
            
        except Exception:
            return False
    
    def get_dashboard_summary(self, client_id: str) -> Dict[str, Any]:
        """
        Get summary data for operator dashboard.
        
        Args:
            client_id: Client to get summary for
            
        Returns:
            Dashboard summary dict
        """
        if not self.optimizer:
            return {
                "pending_count": 0,
                "approved_count": 0,
                "executed_count": 0,
                "recent_activity": [],
            }
        
        try:
            # Count tasks by status
            pending_tasks = self.optimizer.list_tasks_by_status("pending")
            approved_tasks = self.optimizer.list_tasks_by_status("approved")
            executed_tasks = self.optimizer.list_tasks_by_status("executed")
            
            summary = {
                "pending_count": len(pending_tasks),
                "approved_count": len(approved_tasks),
                "executed_count": len(executed_tasks),
                "total_count": len(pending_tasks) + len(approved_tasks) + len(executed_tasks),
                "recent_activity": [
                    {
                        "task_id": activity["task_id"],
                        "action": activity["action"],
                        "operator_id": activity["operator_id"],
                        "timestamp": activity["timestamp"].isoformat(),
                    }
                    for activity in self.approval_history[-10:]
                ],
            }
            
            return summary
            
        except Exception:
            return {
                "pending_count": 0,
                "approved_count": 0,
                "executed_count": 0,
            }


# ============================================================================
# PHASE 14: OPERATOR DASHBOARD SERVICE
# ============================================================================

def get_operator_dashboard_service(
    brand_brain_repo: Optional[Any] = None,
    auto_brain_task_repo: Optional[Any] = None,
    scheduler_repo: Optional[Any] = None,
    feedback_loop: Optional[Any] = None,
) -> Any:
    """
    Factory for OperatorDashboardService.
    
    Initializes the service with available repositories.
    
    Args:
        brand_brain_repo: BrandBrainRepository (Phase 9)
        auto_brain_task_repo: AutoBrainTaskRepository (Phase 10)
        scheduler_repo: SchedulerRepository (Phase 12)
        feedback_loop: FeedbackLoop (Phase 13)
        
    Returns:
        OperatorDashboardService instance
    """
    from aicmo.operator.dashboard_service import OperatorDashboardService
    from aicmo.operator.automation_settings import AutomationSettingsRepository
    
    automation_settings_repo = AutomationSettingsRepository()
    
    return OperatorDashboardService(
        brand_brain_repo=brand_brain_repo,
        auto_brain_task_repo=auto_brain_task_repo,
        scheduler_repo=scheduler_repo,
        feedback_loop=feedback_loop,
        automation_settings_repo=automation_settings_repo,
    )


def get_brand_dashboard(
    brand_id: str,
    dashboard_service: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Get complete dashboard view for a brand.
    
    Returns JSON-serializable dict with:
    - Brand status (LBB data, analytics, risk flags)
    - Task queue (counts, recent tasks)
    - Schedule (upcoming, overdue, next tick)
    - Feedback (anomalies, last run)
    - Automation mode (manual, review_first, full_auto, dry_run)
    
    Args:
        brand_id: Brand UUID
        dashboard_service: OperatorDashboardService (if None, creates default)
        
    Returns:
        Dict with dashboard view
    """
    if dashboard_service is None:
        dashboard_service = get_operator_dashboard_service()
    
    try:
        view = dashboard_service.get_dashboard_view(brand_id)
        return view.to_dict()
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to get dashboard: {str(e)}",
        }


def update_automation_settings(
    brand_id: str,
    mode: str,
    dry_run: bool,
    dashboard_service: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Update automation settings for a brand.
    
    Modes:
    - "manual": Operator must explicitly trigger everything
    - "review_first": Operator approves before execution (default)
    - "full_auto": Auto-approve & execute safe tasks
    
    Args:
        brand_id: Brand UUID
        mode: Automation mode
        dry_run: If True, no external APIs called
        dashboard_service: OperatorDashboardService (if None, creates default)
        
    Returns:
        Dict with success/error status
    """
    if dashboard_service is None:
        dashboard_service = get_operator_dashboard_service()
    
    return dashboard_service.set_automation_mode(
        brand_id=brand_id,
        mode=mode,
        dry_run=dry_run,
    )


def trigger_auto_brain(
    brand_id: str,
    dashboard_service: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Trigger Agency Auto-Brain (AAB) scan for a brand.
    
    AAB detects what work needs to be done (SWOT, personas, messaging, etc.)
    and proposes tasks.
    
    Args:
        brand_id: Brand UUID
        dashboard_service: OperatorDashboardService (if None, creates default)
        
    Returns:
        Dict with execution summary
    """
    if dashboard_service is None:
        dashboard_service = get_operator_dashboard_service()
    
    return dashboard_service.run_auto_brain_for_brand(brand_id)


def trigger_execution_cycle(
    brand_id: str,
    max_tasks: int = 5,
    dashboard_service: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Trigger execution cycle for a brand.
    
    Based on automation mode:
    - "manual": Returns skipped (no execution)
    - "review_first": Only executes approved tasks
    - "full_auto": Auto-approves safe tasks, then executes
    
    Respects dry_run flag (no external APIs when True).
    
    Args:
        brand_id: Brand UUID
        max_tasks: Maximum tasks to execute
        dashboard_service: OperatorDashboardService (if None, creates default)
        
    Returns:
        Dict with execution results
    """
    if dashboard_service is None:
        dashboard_service = get_operator_dashboard_service()
    
    return dashboard_service.run_execution_cycle_for_brand(
        brand_id=brand_id,
        max_tasks=max_tasks,
    )


def trigger_scheduler_tick(
    brand_id: str,
    max_to_run: int = 10,
    dashboard_service: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Trigger scheduler tick for a brand.
    
    Finds tasks due for execution and runs them.
    
    Args:
        brand_id: Brand UUID
        max_to_run: Maximum tasks to execute in this tick
        dashboard_service: OperatorDashboardService (if None, creates default)
        
    Returns:
        Dict with execution results
    """
    if dashboard_service is None:
        dashboard_service = get_operator_dashboard_service()
    
    return dashboard_service.run_scheduler_tick_for_brand(
        brand_id=brand_id,
        max_to_run=max_to_run,
    )


def trigger_feedback_cycle(
    brand_id: str,
    dashboard_service: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Trigger feedback loop for a brand.
    
    Collects performance data, detects anomalies, proposes corrective tasks.
    Updates Learning Brain (Phase 9) with observations.
    
    Args:
        brand_id: Brand UUID
        dashboard_service: OperatorDashboardService (if None, creates default)
        
    Returns:
        Dict with feedback summary
    """
    if dashboard_service is None:
        dashboard_service = get_operator_dashboard_service()
    
    return dashboard_service.run_feedback_cycle_for_brand(brand_id)


# ============================================================================
# PHASE B: OUTREACH CHANNEL OPERATIONS
# ============================================================================

def send_outreach_message(
    db: Session,
    lead_id: int,
    message_body: str,
    subject: Optional[str] = None,
    force_channel: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Send outreach message via multi-channel sequencer.
    
    Initiates multi-channel outreach using ChannelSequencer:
    - Attempts Email first
    - Falls back to LinkedIn if Email fails
    - Falls back to Contact Form if LinkedIn fails
    
    Args:
        db: Database session
        lead_id: Lead ID to send to
        message_body: Message body text
        subject: Optional subject line (for email)
        force_channel: Optional channel to force (bypasses sequencer)
        
    Returns:
        Dict with:
        - success: Boolean result
        - message_id: UUID of sent message
        - channel_used: Which channel succeeded
        - attempts: List of all attempts made
    """
    from aicmo.cam.domain import OutreachMessage
    from aicmo.cam.outreach.sequencer import ChannelSequencer
    
    # Get lead
    lead = db.query(LeadDB).filter(LeadDB.id == lead_id).first()
    if not lead:
        return {
            'success': False,
            'error': f'Lead {lead_id} not found',
        }
    
    # Build message
    outreach_msg = OutreachMessage(
        body=message_body,
        subject=subject,
        personalization_data={
            'name': lead.name,
            'company': lead.company,
        }
    )
    
    # Execute sequence
    sequencer = ChannelSequencer()
    result = sequencer.execute_sequence(
        message=outreach_msg,
        recipient_email=lead.email,
        recipient_linkedin_id=getattr(lead, 'linkedin_id', None),
        form_url=getattr(lead, 'contact_form_url', None),
    )
    
    return result


def get_channel_config(db: Session, channel_name: str) -> Dict[str, Any]:
    """
    Get configuration for a channel.
    
    Args:
        db: Database session
        channel_name: Channel name (EMAIL, LINKEDIN, CONTACT_FORM)
        
    Returns:
        Dict with channel configuration
    """
    # TODO Phase 4: Replace with CAM query port (ChannelConfigQueryPort)
    from aicmo.cam.db_models import ChannelConfigDB
    
    config = db.query(ChannelConfigDB).filter(
        ChannelConfigDB.channel == channel_name
    ).first()
    
    if not config:
        return {
            'channel': channel_name,
            'configured': False,
        }
    
    return {
        'channel': channel_name,
        'configured': True,
        'enabled': config.enabled,
        'rate_limit_per_hour': config.rate_limit_per_hour,
        'rate_limit_per_day': config.rate_limit_per_day,
        'templates': config.templates or [],
        'settings': config.settings or {},
    }


def update_channel_config(
    db: Session,
    channel_name: str,
    enabled: Optional[bool] = None,
    rate_limit_per_hour: Optional[int] = None,
    rate_limit_per_day: Optional[int] = None,
    settings: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Update configuration for a channel.
    
    Args:
        db: Database session
        channel_name: Channel name (EMAIL, LINKEDIN, CONTACT_FORM)
        enabled: Whether channel is enabled
        rate_limit_per_hour: Max messages per hour
        rate_limit_per_day: Max messages per day
        settings: Channel-specific settings
        
    Returns:
        Updated configuration dict
    """
    # TODO Phase 4: Replace with CAM command port (ChannelConfigCommandPort)
    from aicmo.cam.db_models import ChannelConfigDB
    
    config = db.query(ChannelConfigDB).filter(
        ChannelConfigDB.channel == channel_name
    ).first()
    
    if not config:
        config = ChannelConfigDB(channel=channel_name)
        db.add(config)
    
    if enabled is not None:
        config.enabled = enabled
    if rate_limit_per_hour is not None:
        config.rate_limit_per_hour = rate_limit_per_hour
    if rate_limit_per_day is not None:
        config.rate_limit_per_day = rate_limit_per_day
    if settings is not None:
        config.settings = settings
    
    db.commit()
    
    return get_channel_config(db, channel_name)


def get_outreach_history(
    db: Session,
    lead_id: int,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Get outreach history for a lead.
    
    Args:
        db: Database session
        lead_id: Lead ID
        limit: Maximum records to return
        
    Returns:
        List of outreach attempts (newest first)
    """
    attempts = (
        db.query(OutreachAttemptDB)
        .filter(OutreachAttemptDB.lead_id == lead_id)
        .order_by(desc(OutreachAttemptDB.created_at))
        .limit(limit)
        .all()
    )
    
    return [
        {
            'id': a.id,
            'channel': a.channel if hasattr(a, 'channel') else None,
            'status': a.status if hasattr(a, 'status') else None,
            'message': a.outreach_message if hasattr(a, 'outreach_message') else None,
            'sent_at': a.created_at.isoformat() if a.created_at else None,
            'opened_at': a.opened_at.isoformat() if hasattr(a, 'opened_at') and a.opened_at else None,
            'replied_at': a.replied_at.isoformat() if hasattr(a, 'replied_at') and a.replied_at else None,
        }
        for a in attempts
    ]


def get_channel_metrics(
    db: Session,
    campaign_id: Optional[int] = None,
    days: int = 7,
) -> Dict[str, Any]:
    """
    Get channel performance metrics.
    
    Args:
        db: Database session
        campaign_id: Optional campaign to filter by
        days: Number of days to look back
        
    Returns:
        Dict with metrics per channel:
        - total_sent
        - delivery_rate
        - reply_rate
        - bounce_rate
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    query = db.query(OutreachAttemptDB).filter(
        OutreachAttemptDB.created_at >= cutoff
    )
    
    if campaign_id:
        query = query.join(LeadDB).filter(LeadDB.campaign_id == campaign_id)
    
    attempts = query.all()
    
    # Group by channel
    channels = {}
    for attempt in attempts:
        channel = getattr(attempt, 'channel', 'unknown')
        if channel not in channels:
            channels[channel] = {
                'total_sent': 0,
                'delivered': 0,
                'replied': 0,
                'bounced': 0,
            }
        
        channels[channel]['total_sent'] += 1
        
        status = getattr(attempt, 'status', None)
        if status and 'delivered' in str(status).lower():
            channels[channel]['delivered'] += 1
        if hasattr(attempt, 'replied_at') and attempt.replied_at:
            channels[channel]['replied'] += 1
        if status and 'bounce' in str(status).lower():
            channels[channel]['bounced'] += 1
    
    # Calculate rates
    metrics = {}
    for channel, stats in channels.items():
        total = stats['total_sent']
        metrics[channel] = {
            'total_sent': total,
            'delivery_rate': (stats['delivered'] / total * 100) if total > 0 else 0,
            'reply_rate': (stats['replied'] / total * 100) if total > 0 else 0,
            'bounce_rate': (stats['bounced'] / total * 100) if total > 0 else 0,
        }
    
    return metrics


# ============================================================================
# PHASE C: ANALYTICS & REPORTING OPERATOR SERVICES
# ============================================================================

def get_campaign_metrics(campaign_id: int, period: str = 'DAILY') -> Dict[str, any]:
    """
    Get campaign metrics for specified period.
    
    Args:
        campaign_id: Campaign ID
        period: Aggregation period (DAILY, WEEKLY, MONTHLY, etc.)
    
    Returns:
        Dictionary with campaign metrics
    """
    db = next(get_db())
    try:
        from aicmo.cam.analytics import MetricsCalculator
        from aicmo.cam.domain import MetricsPeriod
        
        calculator = MetricsCalculator(db)
        period_enum = MetricsPeriod[period]
        
        result = calculator.calculate_all_metrics(campaign_id, period_enum)
        logger.info(f"Retrieved metrics for campaign {campaign_id}")
        
        return {
            'campaign_id': campaign_id,
            'period': period,
            'metrics': result,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting campaign metrics: {e}")
        raise
    finally:
        db.close()


def get_channel_dashboard(campaign_id: int) -> Dict[str, any]:
    """
    Get channel performance dashboard data.
    
    Args:
        campaign_id: Campaign ID
    
    Returns:
        Dashboard data with channel breakdown
    """
    db = next(get_db())
    try:
        from aicmo.cam.analytics import DashboardService
        from aicmo.cam.domain import MetricsPeriod
        
        service = DashboardService(db)
        dashboard = service.get_channel_dashboard(campaign_id, MetricsPeriod.DAILY)
        
        logger.info(f"Retrieved channel dashboard for campaign {campaign_id}")
        return dashboard
    except Exception as e:
        logger.error(f"Error getting channel dashboard: {e}")
        raise
    finally:
        db.close()


def get_roi_analysis(campaign_id: int) -> Dict[str, any]:
    """
    Get ROI and profitability analysis for campaign.
    
    Args:
        campaign_id: Campaign ID
    
    Returns:
        ROI analysis with cost, revenue, and metrics
    """
    db = next(get_db())
    try:
        from aicmo.cam.analytics import DashboardService
        
        service = DashboardService(db)
        roi_data = service.get_roi_dashboard(campaign_id)
        
        logger.info(f"Retrieved ROI analysis for campaign {campaign_id}")
        return roi_data
    except Exception as e:
        logger.error(f"Error getting ROI analysis: {e}")
        raise
    finally:
        db.close()


def create_ab_test(
    campaign_id: int,
    test_name: str,
    hypothesis: str,
    test_type: str,
    control_variant: str,
    treatment_variant: str,
    sample_size: int,
    confidence_level: float = 0.95
) -> Dict[str, any]:
    """
    Create new A/B test configuration.
    
    Args:
        campaign_id: Campaign ID
        test_name: Unique test name
        hypothesis: Test hypothesis
        test_type: Type of test (MESSAGE, CHANNEL, TIMING, etc.)
        control_variant: Control variant description
        treatment_variant: Treatment variant description
        sample_size: Total sample size
        confidence_level: Statistical confidence (0.9, 0.95, 0.99)
    
    Returns:
        Test configuration with ID
    """
    db = next(get_db())
    try:
        from aicmo.cam.analytics import ABTestRunner
        from aicmo.cam.domain import ABTestType
        
        runner = ABTestRunner(db)
        test_type_enum = ABTestType[test_type]
        
        result = runner.create_test(
            campaign_id=campaign_id,
            test_name=test_name,
            hypothesis=hypothesis,
            test_type=test_type_enum,
            control_variant=control_variant,
            treatment_variant=treatment_variant,
            sample_size=sample_size,
            confidence_level=confidence_level
        )
        
        logger.info(f"Created A/B test '{test_name}' for campaign {campaign_id}")
        return result
    except Exception as e:
        logger.error(f"Error creating A/B test: {e}")
        raise
    finally:
        db.close()


def analyze_ab_test(
    test_config_id: int,
    control_metric_value: float,
    control_sample_size: int,
    treatment_metric_value: float,
    treatment_sample_size: int,
    metric_type: str = 'rate'
) -> Dict[str, any]:
    """
    Analyze A/B test results and compute statistical significance.
    
    Args:
        test_config_id: Test configuration ID
        control_metric_value: Control group metric value
        control_sample_size: Control group sample size
        treatment_metric_value: Treatment group metric value
        treatment_sample_size: Treatment group sample size
        metric_type: Type of metric (rate, mean, count)
    
    Returns:
        Statistical analysis results with p-value and winner
    """
    db = next(get_db())
    try:
        from aicmo.cam.analytics import ABTestRunner
        
        runner = ABTestRunner(db)
        results = runner.analyze_test(
            test_config_id=test_config_id,
            control_metric_value=control_metric_value,
            control_sample_size=control_sample_size,
            treatment_metric_value=treatment_metric_value,
            treatment_sample_size=treatment_sample_size,
            metric_type=metric_type
        )
        
        logger.info(f"Analyzed A/B test {test_config_id}: winner={results.get('winner')}")
        return results
    except Exception as e:
        logger.error(f"Error analyzing A/B test: {e}")
        raise
    finally:
        db.close()


def get_ab_test_dashboard(campaign_id: int, status: str = None) -> Dict[str, any]:
    """
    Get A/B test dashboard with all tests for campaign.
    
    Args:
        campaign_id: Campaign ID
        status: Filter by status (RUNNING, COMPLETED, etc.)
    
    Returns:
        A/B test dashboard data
    """
    db = next(get_db())
    try:
        from aicmo.cam.analytics import DashboardService
        
        service = DashboardService(db)
        dashboard = service.get_abtest_dashboard(campaign_id, status)
        
        logger.info(f"Retrieved A/B test dashboard for campaign {campaign_id}")
        return dashboard
    except Exception as e:
        logger.error(f"Error getting A/B test dashboard: {e}")
        raise
    finally:
        db.close()


def get_trend_analysis(
    campaign_id: int,
    days: int = 30,
    period: str = 'DAILY'
) -> Dict[str, any]:
    """
    Get historical trend analysis for campaign.
    
    Args:
        campaign_id: Campaign ID
        days: Number of days to include
        period: Aggregation period (DAILY, WEEKLY, MONTHLY)
    
    Returns:
        Trend data with time-series metrics
    """
    db = next(get_db())
    try:
        from aicmo.cam.analytics import DashboardService
        from aicmo.cam.domain import MetricsPeriod
        
        service = DashboardService(db)
        period_enum = MetricsPeriod[period]
        
        trend = service.get_trend_dashboard(campaign_id, days, period_enum)
        
        logger.info(f"Retrieved trend analysis for campaign {campaign_id}")
        return trend
    except Exception as e:
        logger.error(f"Error getting trend analysis: {e}")
        raise
    finally:
        db.close()


def generate_report(
    campaign_id: int,
    report_type: str = 'executive_summary',
    format: str = 'html'
) -> Dict[str, any]:
    """
    Generate campaign report in specified format.
    
    Args:
        campaign_id: Campaign ID
        report_type: Type of report (executive_summary, detailed_analysis, 
                     channel_comparison, roi_analysis)
        format: Output format (html, csv, json)
    
    Returns:
        Report content and metadata
    """
    db = next(get_db())
    try:
        from aicmo.cam.analytics import ReportGenerator
        
        generator = ReportGenerator(db)
        
        if report_type == 'executive_summary':
            content = generator.generate_executive_summary(campaign_id, format)
        elif report_type == 'detailed_analysis':
            content = generator.generate_detailed_analysis(campaign_id, format)
        elif report_type == 'channel_comparison':
            content = generator.generate_channel_comparison(campaign_id, format)
        elif report_type == 'roi_analysis':
            content = generator.generate_roi_analysis(campaign_id, format)
        else:
            raise ValueError(f"Unknown report type: {report_type}")
        
        logger.info(f"Generated {report_type} report for campaign {campaign_id}")
        
        return {
            'campaign_id': campaign_id,
            'report_type': report_type,
            'format': format,
            'content': content,
            'generated_at': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise
    finally:
        db.close()


def get_lead_dashboard(campaign_id: int) -> Dict[str, any]:
    """
    Get lead quality and status breakdown dashboard.
    
    Args:
        campaign_id: Campaign ID
    
    Returns:
        Lead dashboard with grade, status, and source breakdown
    """
    db = next(get_db())
    try:
        from aicmo.cam.analytics import DashboardService
        
        service = DashboardService(db)
        dashboard = service.get_lead_dashboard(campaign_id)
        
        logger.info(f"Retrieved lead dashboard for campaign {campaign_id}")
        return dashboard
    except Exception as e:
        logger.error(f"Error getting lead dashboard: {e}")
        raise
    finally:
        db.close()


def get_campaign_summary(campaign_id: int) -> Dict[str, any]:
    """
    Get high-level campaign summary with all KPIs.
    
    Args:
        campaign_id: Campaign ID
    
    Returns:
        Campaign summary with all key metrics
    """
    db = next(get_db())
    try:
        from aicmo.cam.analytics import DashboardService
        
        service = DashboardService(db)
        dashboard = service.get_campaign_dashboard(campaign_id)
        
        logger.info(f"Retrieved campaign summary for {campaign_id}")
        return dashboard
    except Exception as e:
        logger.error(f"Error getting campaign summary: {e}")
        raise
    finally:
        db.close()






