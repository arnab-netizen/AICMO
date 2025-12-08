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
    CampaignDB,
    LeadDB,
    OutreachAttemptDB,
    ContactEventDB,
    DiscoveryJobDB,
    SafetySettingsDB,
)


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
    
    Returns project data with stage information for grouping into columns.
    
    TODO: Wire to Project table when available in DB schema.
    For now, derives projects from CAM campaigns + leads.
    
    Args:
        db: Database session
        
    Returns:
        List of project dicts with keys: id, name, stage, clarity
    """
    # TODO: Replace with actual Project table query when available
    # For now, derive from campaigns as proxy
    campaigns = db.query(CampaignDB).filter(CampaignDB.active == True).all()
    
    projects = []
    for campaign in campaigns:
        # Count leads to derive "clarity" metric
        lead_count = db.query(LeadDB).filter(LeadDB.campaign_id == campaign.id).count()
        clarity = min(100, lead_count * 10)  # Simple heuristic
        
        # Derive stage from campaign activity
        recent_attempts = db.query(OutreachAttemptDB).filter(
            OutreachAttemptDB.campaign_id == campaign.id
        ).order_by(desc(OutreachAttemptDB.attempted_at)).first()
        
        if recent_attempts:
            stage = "EXECUTION"
        elif lead_count > 5:
            stage = "CREATIVE"
        elif lead_count > 0:
            stage = "STRATEGY"
        else:
            stage = "INTAKE"
        
        projects.append({
            "id": campaign.id,
            "name": campaign.name,
            "stage": stage,
            "clarity": clarity
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
    
    Phase 9.1: Returns synthetic creatives based on campaign context.
    TODO: Wire to actual ContentItem persistence when available.
    
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
    
    # Generate synthetic creatives based on campaign strategy status
    platform_templates = [
        ("LinkedIn", "Professional post about {niche}"),
        ("Twitter", "Thread on {niche} best practices"),
        ("Email", "Weekly newsletter for {niche} audience"),
    ]
    
    creatives = []
    for idx, (platform, template) in enumerate(platform_templates, start=1):
        niche = campaign.target_niche or "target audience"
        creatives.append({
            "id": f"{project_id}_{idx}",
            "platform": platform,
            "caption": template.format(niche=niche),
            "status": "APPROVED" if campaign.strategy_status == "APPROVED" else "DRAFT",
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

