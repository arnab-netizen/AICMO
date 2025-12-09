"""
CAM Autonomous Runner — Phase 5 Worker/Orchestration.

Integrates all Phase 4 engine modules to run complete CAM cycles.
Orchestrates lead discovery, enrichment, and outreach using ports & adapters.

Usage:
    python -m aicmo.cam.auto_runner run-cycle --campaign-id 1 --dry-run
    python -m aicmo.cam.auto_runner run-all --dry-run
    python -m aicmo.cam.auto_runner import-csv --path leads.csv --campaign-id 1
"""

import argparse
import logging
from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session

from aicmo.core.db import SessionLocal
from aicmo.cam.db_models import CampaignDB
from aicmo.cam.domain import Campaign
from aicmo.cam.engine.lead_pipeline import fetch_and_insert_new_leads, enrich_and_score_leads
from aicmo.cam.engine.outreach_engine import execute_due_outreach, get_outreach_stats
from aicmo.cam.engine.targets_tracker import compute_campaign_metrics, should_pause_campaign
from aicmo.cam.engine.reply_engine import process_new_replies
from aicmo.gateways.factory import get_lead_source, get_lead_enricher, get_email_verifier

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# ═══════════════════════════════════════════════════════════════════════
# SINGLE CAMPAIGN CYCLE
# ═══════════════════════════════════════════════════════════════════════


def run_cam_cycle_for_campaign(
    db: Session,
    campaign_id: int,
    dry_run: bool = True,
    max_new_leads: int = 50,
    max_enriched: int = 100,
    now: datetime = None,
) -> dict:
    """
    Run complete CAM cycle for a single campaign.
    
    Flow:
    1. Load campaign from database
    2. Fetch new leads from configured sources
    3. Enrich and score leads
    4. Execute due outreach
    5. Update campaign status if goals met
    6. Return summary
    
    Args:
        db: Database session
        campaign_id: Campaign ID to run
        dry_run: If True, don't send real emails
        max_new_leads: Max leads to fetch
        max_enriched: Max leads to enrich
        now: Current datetime (defaults to utcnow)
        
    Returns:
        Dictionary with statistics
    """
    if now is None:
        now = datetime.utcnow()
    
    # Load campaign
    campaign_db = db.query(CampaignDB).filter(CampaignDB.id == campaign_id).first()
    if not campaign_db:
        logger.error(f"Campaign {campaign_id} not found")
        return {"error": f"Campaign {campaign_id} not found"}
    
    if not campaign_db.active:
        logger.info(f"Campaign {campaign_id} is inactive, skipping")
        return {"campaign_id": campaign_id, "status": "inactive"}
    
    logger.info(f"Running CAM cycle for campaign: {campaign_db.name}")
    
    # Convert to Pydantic
    campaign = Campaign(
        id=campaign_db.id,
        name=campaign_db.name,
        target_niche=campaign_db.target_niche,
        service_key=campaign_db.service_key,
        target_clients=campaign_db.target_clients,
        target_mrr=campaign_db.target_mrr,
        channels_enabled=campaign_db.channels_enabled or ["email"],
    )
    
    stats = {
        "campaign_id": campaign_id,
        "campaign_name": campaign_db.name,
        "leads_discovered": 0,
        "leads_enriched": 0,
        "outreach_sent": 0,
        "outreach_failed": 0,
        "outreach_skipped": 0,
        "errors": [],
    }
    
    try:
        # Phase 1: Discover new leads
        logger.info("Phase 1: Discovering new leads...")
        lead_sources = [get_lead_source()]
        discovered = fetch_and_insert_new_leads(
            db,
            campaign,
            campaign_db,
            lead_sources,
            max_leads=max_new_leads,
            now=now,
        )
        stats["leads_discovered"] = discovered
        logger.info(f"  Discovered {discovered} new leads")
        
    except Exception as e:
        logger.error(f"Error in lead discovery: {e}")
        stats["errors"].append(f"Lead discovery: {str(e)}")
    
    try:
        # Phase 2: Enrich and score leads
        logger.info("Phase 2: Enriching and scoring leads...")
        lead_enrichers = [get_lead_enricher()]
        email_verifier = get_email_verifier()
        enriched = enrich_and_score_leads(
            db,
            campaign,
            campaign_db,
            lead_enrichers,
            email_verifier,
            max_leads=max_enriched,
            now=now,
        )
        stats["leads_enriched"] = enriched
        logger.info(f"  Enriched {enriched} leads")
        
    except Exception as e:
        logger.error(f"Error in enrichment: {e}")
        stats["errors"].append(f"Enrichment: {str(e)}")
    
    try:
        # Phase 3: Execute outreach
        logger.info("Phase 3: Executing outreach...")
        sent, failed, skipped = execute_due_outreach(
            db,
            campaign,
            campaign_db,
            now=now,
            dry_run=dry_run,
        )
        stats["outreach_sent"] = sent
        stats["outreach_failed"] = failed
        stats["outreach_skipped"] = skipped
        logger.info(f"  Sent: {sent}, Failed: {failed}, Skipped: {skipped}")
        
    except Exception as e:
        logger.error(f"Error in outreach: {e}")
        stats["errors"].append(f"Outreach: {str(e)}")
    
    try:
        # Phase 3b: Process incoming replies (Phase 10)
        logger.info("Phase 3b: Processing incoming replies...")
        reply_results = process_new_replies(db, now=now)
        stats["replies_processed"] = reply_results.get("processed_count", 0)
        stats["replies_positive"] = reply_results.get("positive_count", 0)
        stats["replies_negative"] = reply_results.get("negative_count", 0)
        logger.info(f"  Processed {stats['replies_processed']} replies")
        
    except Exception as e:
        logger.error(f"Error processing replies: {e}")
        stats["errors"].append(f"Reply processing: {str(e)}")
    
    try:
        # Phase 4: Check if goals met and pause if needed
        logger.info("Phase 4: Checking campaign goals...")
        metrics = compute_campaign_metrics(db, campaign_id)
        logger.info(f"  Metrics: {metrics.total_leads} total, {metrics.status_qualified} qualified")
        
        should_pause, reason = should_pause_campaign(db, campaign_db)
        if should_pause:
            campaign_db.active = False
            db.commit()
            logger.info(f"  Campaign paused: {reason}")
            stats["campaign_paused"] = reason
        
    except Exception as e:
        logger.error(f"Error checking goals: {e}")
        stats["errors"].append(f"Goal checking: {str(e)}")
    
    logger.info(f"CAM cycle complete for {campaign_db.name}")
    return stats


# ═══════════════════════════════════════════════════════════════════════
# MULTI-CAMPAIGN ORCHESTRATION
# ═══════════════════════════════════════════════════════════════════════


def run_cam_cycle_for_all(
    db: Session,
    dry_run: bool = True,
    now: datetime = None,
) -> List[dict]:
    """
    Run CAM cycle for all active campaigns.
    
    Args:
        db: Database session
        dry_run: If True, don't send real emails
        now: Current datetime (defaults to utcnow)
        
    Returns:
        List of statistics dictionaries, one per campaign
    """
    if now is None:
        now = datetime.utcnow()
    
    # Load all active campaigns
    campaigns = db.query(CampaignDB).filter(CampaignDB.active == True).all()
    
    logger.info(f"Running CAM cycles for {len(campaigns)} active campaigns")
    
    all_stats = []
    for campaign_db in campaigns:
        try:
            stats = run_cam_cycle_for_campaign(
                db,
                campaign_db.id,
                dry_run=dry_run,
                now=now,
            )
            all_stats.append(stats)
        except Exception as e:
            logger.error(f"Unhandled error for campaign {campaign_db.id}: {e}")
            all_stats.append({
                "campaign_id": campaign_db.id,
                "error": str(e),
            })
    
    return all_stats


# ═══════════════════════════════════════════════════════════════════════
# CLI INTERFACE
# ═══════════════════════════════════════════════════════════════════════


def main():
    """CLI entry point for CAM autonomous runner."""
    parser = argparse.ArgumentParser(
        description="CAM Autonomous Client Acquisition Runner"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # run-cycle command
    run_cycle_parser = subparsers.add_parser(
        "run-cycle",
        help="Run CAM cycle for a specific campaign",
    )
    run_cycle_parser.add_argument("--campaign-id", type=int, required=True)
    run_cycle_parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Don't send real emails (default: True)",
    )
    run_cycle_parser.add_argument(
        "--no-dry-run",
        dest="dry_run",
        action="store_false",
        help="Actually send emails",
    )
    run_cycle_parser.add_argument(
        "--max-new-leads",
        type=int,
        default=50,
    )
    
    # run-all command
    run_all_parser = subparsers.add_parser(
        "run-all",
        help="Run CAM cycle for all active campaigns",
    )
    run_all_parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
    )
    run_all_parser.add_argument(
        "--no-dry-run",
        dest="dry_run",
        action="store_false",
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute command
    db = SessionLocal()
    
    try:
        if args.command == "run-cycle":
            stats = run_cam_cycle_for_campaign(
                db,
                args.campaign_id,
                dry_run=args.dry_run,
                max_new_leads=args.max_new_leads,
            )
            print("\n" + "=" * 60)
            print(f"Campaign {args.campaign_id} Cycle Results:")
            print("=" * 60)
            for key, value in stats.items():
                if key != "errors":
                    print(f"  {key}: {value}")
            if stats.get("errors"):
                print("  Errors:")
                for error in stats["errors"]:
                    print(f"    - {error}")
            print("=" * 60 + "\n")
        
        elif args.command == "run-all":
            all_stats = run_cam_cycle_for_all(db, dry_run=args.dry_run)
            print("\n" + "=" * 60)
            print("All Campaigns CAM Cycle Results:")
            print("=" * 60)
            for stats in all_stats:
                campaign_name = stats.get("campaign_name", f"ID {stats.get('campaign_id')}")
                print(f"\n{campaign_name}:")
                for key, value in stats.items():
                    if key not in ("campaign_id", "campaign_name", "errors"):
                        print(f"  {key}: {value}")
                if stats.get("errors"):
                    print("  Errors:")
                    for error in stats["errors"]:
                        print(f"    - {error}")
            print("=" * 60 + "\n")
    
    finally:
        db.close()


if __name__ == "__main__":
    main()
