"""
CAM-AUTO orchestration.

Phase CAM-6: Automated outreach with AICMO-powered personalization.
Phase B: Multi-channel sequencing with smart fallback.
"""

from typing import Optional

from sqlalchemy.orm import Session

from aicmo.cam.domain import Channel, OutreachMessage
from aicmo.cam.messaging import SequenceConfig
from aicmo.cam.personalization import generate_strategy_for_lead
from aicmo.cam.messaging import generate_personalized_messages_for_lead
from aicmo.cam.sender import send_messages_email_auto, send_messages_social_auto
from aicmo.cam.lead_grading import LeadGradeService
from aicmo.cam.outreach.sequencer import ChannelSequencer
from aicmo.cam.db_models import LeadDB, LeadStatus
from aicmo.gateways.interfaces import EmailSender, SocialPoster
multichannel_batch(
    db: Session,
    campaign_id: int,
    email_sender: Optional[EmailSender] = None,
    batch_size: int = 10,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None,
    dry_run: bool = False,
) -> dict:
    """
    Run automated multi-channel outreach batch for a campaign.
    
    Process:
    1. Select leads with status NEW (up to batch_size)
    2. For each lead:
       a. Generate AICMO strategy
       b. Create personalized message
       c. Execute multi-channel sequence (Email → LinkedIn → Contact Form)
       d. Track attempt in database
       e. Update lead status and last_outreach_at
    
    Uses ChannelSequencer to intelligently route through channels,
    falling back if primary channel fails.
    
    Args:
        db: Database session
        campaign_id: Campaign ID to process
        email_sender: Optional EmailSender gateway (for email channel)
        batch_size: Maximum leads to process (default 10)
        from_email: Sender email address
        from_name: Sender display name
        dry_run: If True, generate messages but don't execute sequences
        
    Returns:
        dict with summary stats (processed, multichannel_sent, email_sent,
        linkedin_sent, form_sent, failed)
    """
    # Select leads to process
    leads = (
        db.query(LeadDB)
        .filter(
            LeadDB.campaign_id == campaign_id,
            LeadDB.status == LeadStatus.NEW,
        )
        .limit(batch_size)
        .all()
    )
    
    stats = {
        "processed": 0,
        "multichannel_sent": 0,
        "email_sent": 0,
        "linkedin_sent": 0,
        "form_sent": 0,
        "failed": 0,
        "dry_run": dry_run,
    }
    
    sequencer = ChannelSequencer()
    
    for lead_db in leads:
        try:
            # Generate AICMO strategy for this lead
            strategy_doc = generate_strategy_for_lead(db, lead_db.id)
            
            # Generate personalized message
            messages = generate_personalized_messages_for_lead(
                db=db,
                lead_id=lead_db.id,
                channel=Channel.EMAIL,
                sequence=SequenceConfig(channel=Channel.EMAIL, steps=1),
                strategy_doc=strategy_doc,
            )
            
            if not messages:
                stats["failed"] += 1
                continue
            
            # Build OutreachMessage domain object
            base_msg = messages[0]
            outreach_msg = OutreachMessage(
                body=base_msg.body,
                subject=base_msg.subject if hasattr(base_msg, 'subject') else None,
                template_name=None,
                personalization_data={
                    'name': lead_db.name,
                    'company': lead_db.company,
                    'role': lead_db.role,
                }
            )
            
            if not dry_run:
                # Grade the lead
                from aicmo.cam.domain import Lead
                lead_domain = Lead(
                    name=lead_db.name,
                    company=lead_db.company,
                    role=lead_db.role,
                    email=lead_db.email,
                    lead_score=lead_db.lead_score,
                    tags=lead_db.tags or [],
                    budget_estimate_range=lead_db.budget_estimate_range,
                    timeline_months=lead_db.timeline_months,
                    pain_points=lead_db.pain_points,
                )
                LeadGradeService.update_lead_grade(db, lead_db.id, lead_domain)
                
                # Execute multi-channel sequence
                sequence_result = sequencer.execute_sequence(
                    message=outreach_msg,
                    recipient_email=lead_db.email,
                    recipient_linkedin_id=lead_db.linkedin_id if hasattr(lead_db, 'linkedin_id') else None,
                    form_url=lead_db.contact_form_url if hasattr(lead_db, 'contact_form_url') else None,
                )
                
                # Track channel usage
                if sequence_result['success']:
                    stats["multichannel_sent"] += 1
                    channel = sequence_result.get('channel_used', 'unknown')
                    if channel == 'EMAIL':
                        stats["email_sent"] += 1
                    elif channel == 'LINKEDIN':
                        stats["linkedin_sent"] += 1
                    elif channel == 'CONTACT_FORM':
                        stats["form_sent"] += 1
                    
                    # Update lead status
                    lead_db.status = LeadStatus.CONTACTED
                    if hasattr(lead_db, 'last_outreach_at'):
                        from datetime import datetime
                        lead_db.last_outreach_at = datetime.utcnow()
                    
                    db.commit()
                else:
                    stats["failed"] += 1
            else:
                # Dry run: show what would happen
                sequence_result = sequencer.execute_sequence(
                    message=outreach_msg,
                    recipient_email=lead_db.email,
                    recipient_linkedin_id=lead_db.linkedin_id if hasattr(lead_db, 'linkedin_id') else None,
                    form_url=lead_db.contact_form_url if hasattr(lead_db, 'contact_form_url') else None,
                )
                print(f"\n[DRY RUN] Multi-channel sequence for {lead_db.email}:")
                for attempt in sequence_result.get('attempts', []):
                    print(f"  {attempt['channel']}: {'SUCCESS' if attempt['success'] else 'FAILED'}")
            
            stats["processed"] += 1
            
        except Exception as e:
            stats["failed"] += 1
            print(f"Error processing lead {lead_db.id} in multichannel batch: {e}")
            continue
    
    return stats




async def run_auto_email_batch(
    db: Session,
    campaign_id: int,
    email_sender: EmailSender,
    batch_size: int = 10,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None,
    dry_run: bool = False,
) -> dict:
    """
    Run automated email outreach batch for a campaign.
    
    Process:
    1. Select leads with status NEW (up to batch_size)
    2. For each lead:
       a. Generate AICMO strategy
       b. Create personalized messages
       c. Send via email gateway
       d. Update lead status to CONTACTED
    
    Args:
        db: Database session
        campaign_id: Campaign ID to process
        email_sender: EmailSender gateway implementation
        batch_size: Maximum leads to process (default 10)
        from_email: Sender email address
        from_name: Sender display name
        dry_run: If True, generate messages but don't send
        
    Returns:
        dict with summary stats (processed, sent, failed)
    """
    # Select leads to process
    leads = (
        db.query(LeadDB)
        .filter(
            LeadDB.campaign_id == campaign_id,
            LeadDB.status == LeadStatus.NEW,
        )
        .limit(batch_size)
        .all()
    )
    
    stats = {
        "processed": 0,
        "sent": 0,
        "failed": 0,
        "dry_run": dry_run,
    }
    
    sequence = SequenceConfig(channel=Channel.EMAIL, steps=3)
    
    for lead_db in leads:
        try:
            # Generate AICMO strategy for this lead
            strategy_doc = generate_strategy_for_lead(db, lead_db.id)
            
            # Generate personalized messages using strategy
            messages = generate_personalized_messages_for_lead(
                db=db,
                lead_id=lead_db.id,
                channel=Channel.EMAIL,
                sequence=sequence,
                strategy_doc=strategy_doc,
            )
            
            # Phase A: Grade the lead based on enrichment
            from aicmo.cam.domain import Lead
            lead_domain = Lead(
                name=lead_db.name,
                company=lead_db.company,
                role=lead_db.role,
                email=lead_db.email,
                lead_score=lead_db.lead_score,
                tags=lead_db.tags or [],
                budget_estimate_range=lead_db.budget_estimate_range,
                timeline_months=lead_db.timeline_months,
                pain_points=lead_db.pain_points,
            )
            LeadGradeService.update_lead_grade(db, lead_db.id, lead_domain)
            
            if not dry_run:
                # Send messages via email gateway
                await send_messages_email_auto(
                    db=db,
                    messages=messages,
                    email_sender=email_sender,
                    from_email=from_email,
                    from_name=from_name,
                )
                
                # Update lead status
                lead_db.status = LeadStatus.CONTACTED
                db.commit()
                
                stats["sent"] += 1
            else:
                # Dry run: just print first message
                if messages:
                    print(f"\n[DRY RUN] Would send to {lead_db.email}:")
                    print(f"Subject: {messages[0].subject}")
                    print(f"Body: {messages[0].body[:200]}...")
            
            stats["processed"] += 1
            
        except Exception as e:
            stats["failed"] += 1
            print(f"Error processing lead {lead_db.id}: {e}")
            continue
    
    return stats


async def run_auto_social_batch(
    db: Session,
    campaign_id: int,
    social_poster: SocialPoster,
    batch_size: int = 10,
    dry_run: bool = False,
) -> dict:
    """
    Run automated social outreach batch for a campaign.
    
    Process:
    1. Select leads with status NEW (up to batch_size)
    2. For each lead:
       a. Generate AICMO strategy
       b. Create personalized messages
       c. Send via social gateway (LinkedIn DM)
       d. Update lead status to CONTACTED
    
    Args:
        db: Database session
        campaign_id: Campaign ID to process
        social_poster: SocialPoster gateway implementation
        batch_size: Maximum leads to process (default 10)
        dry_run: If True, generate messages but don't send
        
    Returns:
        dict with summary stats (processed, sent, failed)
    """
    # Select leads to process
    leads = (
        db.query(LeadDB)
        .filter(
            LeadDB.campaign_id == campaign_id,
            LeadDB.status == LeadStatus.NEW,
        )
        .limit(batch_size)
        .all()
    )
    
    stats = {
        "processed": 0,
        "sent": 0,
        "failed": 0,
        "dry_run": dry_run,
    }
    
    sequence = SequenceConfig(channel=Channel.LINKEDIN, steps=3)
    
    for lead_db in leads:
        try:
            # Generate AICMO strategy for this lead
            strategy_doc = generate_strategy_for_lead(db, lead_db.id)
            
            # Generate personalized messages using strategy
            messages = generate_personalized_messages_for_lead(
                db=db,
                lead_id=lead_db.id,
                channel=Channel.LINKEDIN,
                sequence=sequence,
                strategy_doc=strategy_doc,
            )
            
            if not dry_run:
                # Send messages via social gateway
                await send_messages_social_auto(
                    db=db,
                    messages=messages,
                    social_poster=social_poster,
                )
                
                # Update lead status
                lead_db.status = LeadStatus.CONTACTED
                db.commit()
                
                stats["sent"] += 1
            else:
                # Dry run: just print first message
                if messages:
                    print(f"\n[DRY RUN] Would send LinkedIn DM to {lead_db.name}:")
                    print(f"Body: {messages[0].body[:200]}...")
            
            stats["processed"] += 1
            
        except Exception as e:
            stats["failed"] += 1
            print(f"Error processing lead {lead_db.id}: {e}")
            continue
    
    return stats
