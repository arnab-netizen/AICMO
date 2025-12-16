"""
E2E test helpers for deterministic cleanup and diagnostics.

MODULE: E2E Test Infrastructure
Provides safe, deterministic test data reset for Playwright tests.
"""

import os
from typing import Dict, Any, List
from sqlalchemy import text
from sqlalchemy.orm import Session

from aicmo.core.db import get_session


def is_e2e_mode() -> bool:
    """Check if running in E2E test mode."""
    return os.getenv("AICMO_E2E_MODE") == "1"


def is_e2e_diagnostics_enabled() -> bool:
    """Check if E2E diagnostics panel should be shown."""
    return os.getenv("AICMO_E2E_DIAGNOSTICS") == "1"


def hard_reset_test_data(session: Session) -> Dict[str, int]:
    """
    Hard reset all business tables for E2E test isolation.
    
    CRITICAL: This ONLY deletes business data, NOT alembic_version or schema.
    Safe to call even if tables are empty.
    
    Returns:
        Dict of table_name -> rows_deleted
    """
    tables_to_truncate = [
        # CAM business tables (order matters for FK constraints)
        "cam_template_render_logs",
        "cam_import_batches",
        "cam_outreach_attempts",
        "cam_leads",
        "cam_campaigns",
        "cam_message_templates",
        
        # Workflow business tables (if any in future)
        # Add as needed when workflow integration is complete
    ]
    
    deleted_counts = {}
    
    # Disable FK checks temporarily (SQLite)
    session.execute(text("PRAGMA foreign_keys = OFF"))
    
    try:
        for table_name in tables_to_truncate:
            # Check if table exists first
            result = session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name=:table"),
                {"table": table_name}
            )
            if result.fetchone() is None:
                deleted_counts[table_name] = 0
                continue
            
            # Get count before delete
            count_result = session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            count_before = count_result.scalar()
            
            # Delete all rows
            session.execute(text(f"DELETE FROM {table_name}"))
            
            deleted_counts[table_name] = count_before or 0
        
        session.commit()
        
    finally:
        # Re-enable FK checks
        session.execute(text("PRAGMA foreign_keys = ON"))
        session.commit()
    
    return deleted_counts


def get_diagnostics_data(session: Session, campaign_id: int = None) -> Dict[str, Any]:
    """
    Get diagnostic data for E2E test verification.
    
    Args:
        session: Database session
        campaign_id: Optional campaign ID to filter by
    
    Returns:
        Dict with counts and recent events
    """
    diagnostics = {
        "campaign_id": campaign_id,
        "counts": {},
        "recent_events": []
    }
    
    # Count leads
    if campaign_id:
        lead_count = session.execute(
            text("SELECT COUNT(*) FROM cam_leads WHERE campaign_id = :cid"),
            {"cid": campaign_id}
        ).scalar()
    else:
        lead_count = session.execute(text("SELECT COUNT(*) FROM cam_leads")).scalar()
    
    diagnostics["counts"]["leads"] = lead_count or 0
    
    # Count outreach attempts
    if campaign_id:
        attempt_count = session.execute(
            text("SELECT COUNT(*) FROM cam_outreach_attempts WHERE campaign_id = :cid"),
            {"cid": campaign_id}
        ).scalar()
    else:
        attempt_count = session.execute(text("SELECT COUNT(*) FROM cam_outreach_attempts")).scalar()
    
    diagnostics["counts"]["outreach_attempts"] = attempt_count or 0
    
    # Count templates
    template_count = session.execute(text("SELECT COUNT(*) FROM cam_message_templates")).scalar()
    diagnostics["counts"]["templates"] = template_count or 0
    
    # Count import batches
    batch_count = session.execute(text("SELECT COUNT(*) FROM cam_import_batches")).scalar()
    diagnostics["counts"]["import_batches"] = batch_count or 0
    
    # Get recent outreach attempts (last 10)
    if campaign_id:
        recent_attempts = session.execute(
            text("""
                SELECT id, lead_id, channel, status, created_at 
                FROM cam_outreach_attempts 
                WHERE campaign_id = :cid
                ORDER BY created_at DESC 
                LIMIT 10
            """),
            {"cid": campaign_id}
        ).fetchall()
    else:
        recent_attempts = session.execute(
            text("""
                SELECT id, lead_id, channel, status, created_at 
                FROM cam_outreach_attempts 
                ORDER BY created_at DESC 
                LIMIT 10
            """)
        ).fetchall()
    
    diagnostics["recent_events"] = [
        {
            "id": row[0],
            "lead_id": row[1],
            "channel": row[2],
            "status": row[3],
            "created_at": str(row[4])
        }
        for row in recent_attempts
    ]
    
    return diagnostics


def get_campaign_status(session: Session, campaign_id: int) -> Dict[str, Any]:
    """
    Get campaign status information.
    
    Returns:
        Dict with campaign details
    """
    result = session.execute(
        text("SELECT id, name, active, mode FROM cam_campaigns WHERE id = :cid"),
        {"cid": campaign_id}
    ).fetchone()
    
    if not result:
        return {"error": "Campaign not found"}
    
    return {
        "id": result[0],
        "name": result[1],
        "active": result[2],
        "mode": result[3]
    }
