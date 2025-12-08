"""
CAM runner - CLI orchestration.

Phase CAM-5: Command-line interface for Client Acquisition Mode.

Usage:
    python -m aicmo.cam.runner import-csv --path data/leads.csv
    python -m aicmo.cam.runner run-once --channel linkedin --batch-size 20
"""

import argparse
from typing import List

from sqlalchemy.orm import Session

from aicmo.core.db import SessionLocal
from aicmo.cam.config import settings
from aicmo.cam.domain import Channel
from aicmo.cam.db_models import CampaignDB, LeadDB
from aicmo.cam.sources import CSVSourceConfig, load_leads_from_csv, persist_leads
from aicmo.cam.messaging import SequenceConfig, generate_messages_for_lead
from aicmo.cam.scheduler import find_leads_to_contact
from aicmo.cam.sender import send_messages_console


def _get_db() -> Session:
    """Get database session."""
    return SessionLocal()


def ensure_campaign(db: Session, name: str) -> CampaignDB:
    """
    Ensure a campaign exists, create if not.
    
    Args:
        db: Database session
        name: Campaign name
        
    Returns:
        CampaignDB instance
    """
    campaign = (
        db.query(CampaignDB)
        .filter(CampaignDB.name == name)
        .order_by(CampaignDB.id.desc())
        .first()
    )
    if campaign:
        return campaign
    campaign = CampaignDB(name=name, description="AICMO prospecting campaign")
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


def cmd_import_csv(args: argparse.Namespace) -> None:
    """
    Import leads from CSV file into campaign.
    
    Args:
        args: Command-line arguments with 'path' and 'campaign_name'
    """
    db = _get_db()
    campaign = ensure_campaign(db, args.campaign_name)

    cfg = CSVSourceConfig(path=args.path, campaign_id=campaign.id)
    leads = load_leads_from_csv(cfg)
    persist_leads(db, leads)
    print(f"✓ Imported {len(leads)} leads into campaign '{campaign.name}'")


def cmd_run_once(args: argparse.Namespace) -> None:
    """
    Generate and print outreach messages for one batch of leads.
    
    Args:
        args: Command-line arguments with campaign, channel, batch_size, steps
    """
    db = _get_db()
    campaign = ensure_campaign(db, args.campaign_name)

    channel = Channel(args.channel)
    leads: List[LeadDB] = find_leads_to_contact(
        db, campaign_id=campaign.id, channel=channel, limit=args.batch_size
    )
    if not leads:
        print("No leads found to contact.")
        return

    seq_cfg = SequenceConfig(channel=channel, steps=args.steps)

    all_messages = []
    for lead in leads:
        msgs = generate_messages_for_lead(
            db=db, lead_id=lead.id, channel=channel, sequence=seq_cfg
        )
        all_messages.extend(msgs)

    print(f"\n✓ Generated {len(all_messages)} messages for {len(leads)} leads\n")
    send_messages_console(db=db, messages=all_messages)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Client Acquisition Mode (CAM) for AICMO")
    sub = parser.add_subparsers(dest="command", required=True)

    # Import CSV command
    p_import = sub.add_parser("import-csv", help="Import leads from CSV")
    p_import.add_argument("--path", required=True, help="Path to CSV file")
    p_import.add_argument(
        "--campaign-name",
        default=settings.CAM_DEFAULT_CAMPAIGN_NAME,
        help="Campaign name",
    )
    p_import.set_defaults(func=cmd_import_csv)

    # Run once command
    p_run = sub.add_parser("run-once", help="Run one CAM batch (manual send)")
    p_run.add_argument(
        "--campaign-name",
        default=settings.CAM_DEFAULT_CAMPAIGN_NAME,
        help="Campaign name",
    )
    p_run.add_argument(
        "--channel",
        default=settings.CAM_DEFAULT_CHANNEL,
        choices=[c.value for c in Channel],
        help="Channel to generate outreach for",
    )
    p_run.add_argument(
        "--batch-size",
        type=int,
        default=settings.CAM_DAILY_BATCH_SIZE,
        help="Max leads per run",
    )
    p_run.add_argument(
        "--steps",
        type=int,
        default=3,
        help="Number of steps per lead in sequence",
    )
    p_run.set_defaults(func=cmd_run_once)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
