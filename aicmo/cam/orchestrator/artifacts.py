"""
Artifacts generator for Campaign Orchestrator.

Creates proof artifacts:
- leads.csv (lead states)
- attempts.csv (distribution job history)
- summary.md (execution summary)
- proof.sql (verification queries)
"""

import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from aicmo.cam.db_models import LeadDB
from aicmo.venture.distribution_models import DistributionJobDB
from aicmo.cam.orchestrator.models import OrchestratorRunDB


def generate_artifacts(
    session: Session,
    campaign_id: int,
    output_dir: Optional[str] = None,
) -> str:
    """
    Generate all proof artifacts for a campaign.
    
    Returns:
        Path to artifacts directory
    """
    if output_dir is None:
        output_dir = f"artifacts/campaign_{campaign_id}"
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate each artifact
    generate_leads_csv(session, campaign_id, output_dir)
    generate_attempts_csv(session, campaign_id, output_dir)
    generate_summary_md(session, campaign_id, output_dir)
    generate_proof_sql(campaign_id, output_dir)
    
    return output_dir


def generate_leads_csv(session: Session, campaign_id: int, output_dir: str):
    """Export lead states to CSV."""
    leads = (
        session.query(LeadDB)
        .filter(LeadDB.campaign_id == campaign_id)
        .order_by(LeadDB.id)
        .all()
    )
    
    filepath = os.path.join(output_dir, "leads.csv")
    
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "lead_id",
            "email",
            "status",
            "consent_status",
            "routing_sequence",
            "next_action_at",
            "last_contacted_at",
            "engagement_notes",
        ])
        
        for lead in leads:
            writer.writerow([
                lead.id,
                lead.email,
                lead.status,
                lead.consent_status,
                lead.routing_sequence or "",
                lead.next_action_at.isoformat() if lead.next_action_at else "",
                lead.last_contacted_at.isoformat() if lead.last_contacted_at else "",
                (lead.engagement_notes or "")[:100],  # Truncate for CSV
            ])
    
    print(f"Generated {filepath} ({len(leads)} leads)")


def generate_attempts_csv(session: Session, campaign_id: int, output_dir: str):
    """Export distribution jobs to CSV."""
    jobs = (
        session.query(DistributionJobDB)
        .filter(DistributionJobDB.campaign_id == campaign_id)
        .order_by(DistributionJobDB.created_at)
        .all()
    )
    
    filepath = os.path.join(output_dir, "attempts.csv")
    
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "job_id",
            "lead_id",
            "message_id",
            "channel",
            "status",
            "idempotency_key",
            "step_index",
            "retry_count",
            "created_at",
            "sent_at",
        ])
        
        for job in jobs:
            writer.writerow([
                job.id,
                job.lead_id,
                job.message_id or "",
                job.channel,
                job.status,
                job.idempotency_key or "",
                job.step_index,
                job.retry_count,
                job.created_at.isoformat(),
                job.sent_at.isoformat() if job.sent_at else "",
            ])
    
    print(f"Generated {filepath} ({len(jobs)} attempts)")


def generate_summary_md(session: Session, campaign_id: int, output_dir: str):
    """Generate execution summary markdown."""
    # Query stats
    total_leads = session.query(LeadDB).filter(LeadDB.campaign_id == campaign_id).count()
    contacted_leads = session.query(LeadDB).filter(
        LeadDB.campaign_id == campaign_id,
        LeadDB.status == "CONTACTED",
    ).count()
    
    total_jobs = session.query(DistributionJobDB).filter(
        DistributionJobDB.campaign_id == campaign_id
    ).count()
    
    sent_jobs = session.query(DistributionJobDB).filter(
        DistributionJobDB.campaign_id == campaign_id,
        DistributionJobDB.status.in_(["SENT", "SENT_PROOF"]),
    ).count()
    
    failed_jobs = session.query(DistributionJobDB).filter(
        DistributionJobDB.campaign_id == campaign_id,
        DistributionJobDB.status.in_(["FAILED", "FAILED_PERMANENT"]),
    ).count()
    
    # Get last run
    last_run = (
        session.query(OrchestratorRunDB)
        .filter(OrchestratorRunDB.campaign_id == campaign_id)
        .order_by(OrchestratorRunDB.started_at.desc())
        .first()
    )
    
    filepath = os.path.join(output_dir, "summary.md")
    
    with open(filepath, "w") as f:
        f.write(f"# Campaign {campaign_id} - Orchestrator Summary\n\n")
        f.write(f"**Generated:** {datetime.utcnow().isoformat()}Z\n\n")
        f.write("## Statistics\n\n")
        f.write(f"- **Total Leads:** {total_leads}\n")
        f.write(f"- **Contacted Leads:** {contacted_leads}\n")
        f.write(f"- **Contact Rate:** {contacted_leads / total_leads * 100:.1f}%\n\n" if total_leads > 0 else "- **Contact Rate:** N/A\n\n")
        f.write(f"- **Total Jobs:** {total_jobs}\n")
        f.write(f"- **Sent Jobs:** {sent_jobs}\n")
        f.write(f"- **Failed Jobs:** {failed_jobs}\n")
        f.write(f"- **Success Rate:** {sent_jobs / total_jobs * 100:.1f}%\n\n" if total_jobs > 0 else "- **Success Rate:** N/A\n\n")
        
        if last_run:
            f.write("## Last Run\n\n")
            f.write(f"- **Run ID:** {last_run.id}\n")
            f.write(f"- **Status:** {last_run.status}\n")
            f.write(f"- **Started:** {last_run.started_at.isoformat()}Z\n")
            if last_run.completed_at:
                f.write(f"- **Completed:** {last_run.completed_at.isoformat()}Z\n")
                duration = (last_run.completed_at - last_run.started_at).total_seconds()
                f.write(f"- **Duration:** {duration:.1f}s\n")
            f.write(f"- **Leads Processed:** {last_run.leads_processed}\n")
            f.write(f"- **Jobs Created:** {last_run.jobs_created}\n")
            f.write(f"- **Attempts Succeeded:** {last_run.attempts_succeeded}\n")
            f.write(f"- **Attempts Failed:** {last_run.attempts_failed}\n")
            if last_run.last_error:
                f.write(f"- **Last Error:** {last_run.last_error}\n")
        
        f.write("\n## Files\n\n")
        f.write("- `leads.csv` - Lead states with contact history\n")
        f.write("- `attempts.csv` - Distribution job history\n")
        f.write("- `proof.sql` - Verification queries\n")
    
    print(f"Generated {filepath}")


def generate_proof_sql(campaign_id: int, output_dir: str):
    """Generate SQL verification queries."""
    filepath = os.path.join(output_dir, "proof.sql")
    
    with open(filepath, "w") as f:
        f.write(f"-- Campaign {campaign_id} - Proof Queries\n\n")
        
        f.write("-- 1. Lead status distribution\n")
        f.write(f"SELECT status, COUNT(*) as count\n")
        f.write(f"FROM cam_leads\n")
        f.write(f"WHERE campaign_id = {campaign_id}\n")
        f.write(f"GROUP BY status;\n\n")
        
        f.write("-- 2. Distribution job status distribution\n")
        f.write(f"SELECT status, COUNT(*) as count\n")
        f.write(f"FROM distribution_jobs\n")
        f.write(f"WHERE campaign_id = {campaign_id}\n")
        f.write(f"GROUP BY status;\n\n")
        
        f.write("-- 3. Idempotency check (should return 0 rows)\n")
        f.write(f"SELECT idempotency_key, COUNT(*) as count\n")
        f.write(f"FROM distribution_jobs\n")
        f.write(f"WHERE campaign_id = {campaign_id}\n")
        f.write(f"  AND idempotency_key IS NOT NULL\n")
        f.write(f"GROUP BY idempotency_key\n")
        f.write(f"HAVING COUNT(*) > 1;\n\n")
        
        f.write("-- 4. Recent orchestrator runs\n")
        f.write(f"SELECT id, status, started_at, completed_at,\n")
        f.write(f"       leads_processed, jobs_created,\n")
        f.write(f"       attempts_succeeded, attempts_failed\n")
        f.write(f"FROM cam_orchestrator_runs\n")
        f.write(f"WHERE campaign_id = {campaign_id}\n")
        f.write(f"ORDER BY started_at DESC\n")
        f.write(f"LIMIT 10;\n\n")
        
        f.write("-- 5. Leads contacted today\n")
        f.write(f"SELECT COUNT(*)\n")
        f.write(f"FROM cam_leads\n")
        f.write(f"WHERE campaign_id = {campaign_id}\n")
        f.write(f"  AND last_contacted_at >= CURRENT_DATE;\n\n")
        
        f.write("-- 6. Jobs by step index\n")
        f.write(f"SELECT step_index, COUNT(*) as count\n")
        f.write(f"FROM distribution_jobs\n")
        f.write(f"WHERE campaign_id = {campaign_id}\n")
        f.write(f"GROUP BY step_index\n")
        f.write(f"ORDER BY step_index;\n\n")
        
        f.write("-- 7. Retry statistics\n")
        f.write(f"SELECT retry_count, COUNT(*) as count\n")
        f.write(f"FROM distribution_jobs\n")
        f.write(f"WHERE campaign_id = {campaign_id}\n")
        f.write(f"  AND retry_count > 0\n")
        f.write(f"GROUP BY retry_count\n")
        f.write(f"ORDER BY retry_count;\n\n")
    
    print(f"Generated {filepath}")
