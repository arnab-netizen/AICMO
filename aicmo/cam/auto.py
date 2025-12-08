"""
CAM-AUTO orchestration.

Phase CAM-6: Automated outreach with AICMO-powered personalization.
"""

from typing import Optional

from sqlalchemy.orm import Session

from aicmo.cam.domain import Channel
from aicmo.cam.messaging import SequenceConfig
from aicmo.cam.personalization import generate_strategy_for_lead
from aicmo.cam.messaging import generate_personalized_messages_for_lead
from aicmo.cam.sender import send_messages_email_auto, send_messages_social_auto
from aicmo.cam.db_models import LeadDB, LeadStatus
from aicmo.gateways.interfaces import EmailSender, SocialPoster


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
