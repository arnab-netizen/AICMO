"""
Tests for MODULE 7: Audit Logging.

Verifies:
- Audit logs are created
- Audit trail is retrievable
- Metadata is preserved
"""

import pytest
from sqlalchemy.orm import Session

from aicmo.venture.audit import log_audit, get_audit_trail, AuditLogDB


def test_audit_log_created(db_session: Session):
    """Audit log is created and persisted."""
    log = log_audit(
        db_session,
        entity_type="campaign",
        entity_id="camp_123",
        action="created",
        actor="operator@example.com",
        metadata={"campaign_name": "Test Campaign"}
    )
    
    assert log.id is not None
    assert log.entity_type == "campaign"
    assert log.entity_id == "camp_123"
    assert log.action == "created"
    assert log.actor == "operator@example.com"
    assert log.context["campaign_name"] == "Test Campaign"
    assert log.timestamp is not None


def test_audit_trail_retrieved_chronologically(db_session: Session):
    """Audit trail is retrieved in chronological order."""
    # Create multiple logs
    log_audit(db_session, "lead", "lead_123", "captured", "system")
    log_audit(db_session, "lead", "lead_123", "contacted", "system")
    log_audit(db_session, "lead", "lead_123", "replied", "system")
    
    trail = get_audit_trail(db_session, "lead", "lead_123")
    
    assert len(trail) == 3
    assert trail[0].action == "captured"
    assert trail[1].action == "contacted"
    assert trail[2].action == "replied"


def test_audit_trail_filtered_by_entity(db_session: Session):
    """Audit trail only returns logs for specific entity."""
    log_audit(db_session, "lead", "lead_1", "captured", "system")
    log_audit(db_session, "lead", "lead_2", "captured", "system")
    log_audit(db_session, "lead", "lead_1", "contacted", "system")
    
    trail = get_audit_trail(db_session, "lead", "lead_1")
    
    assert len(trail) == 2
    assert all(log.entity_id == "lead_1" for log in trail)


def test_metadata_preserved(db_session: Session):
    """Complex metadata is preserved."""
    metadata = {
        "campaign_id": 123,
        "reason": "Operator approval",
        "approver": "john@example.com",
        "notes": "Looks good, ship it",
        "nested": {
            "key": "value"
        }
    }
    
    log = log_audit(
        db_session,
        entity_type="strategy",
        entity_id="strat_456",
        action="approved",
        actor="john@example.com",
        metadata=metadata
    )
    
    assert log.context == metadata
    assert log.context["nested"]["key"] == "value"


def test_default_actor_is_system(db_session: Session):
    """Default actor is 'system' if not specified."""
    log = log_audit(
        db_session,
        entity_type="distribution",
        entity_id="dist_789",
        action="sent"
    )
    
    assert log.actor == "system"
