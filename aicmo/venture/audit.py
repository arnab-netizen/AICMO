"""
Audit logging for compliance.

MODULE 7: Track all critical actions.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from dataclasses import dataclass

from sqlalchemy import Column, Integer, String, DateTime, JSON, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import Session

from aicmo.core.db import Base


class AuditLogDB(Base):
    """
    Audit Log: Immutable record of all critical actions.
    
    Enables:
    - Compliance (who did what when)
    - Debugging (trace decision timeline)
    - Attribution (what led to this outcome)
    - Security (detect unauthorized actions)
    """
    __tablename__ = "audit_log"
    
    id = Column(Integer, primary_key=True)
    entity_type = Column(String, nullable=False)  # "campaign", "lead", "distribution", etc.
    entity_id = Column(String, nullable=False)  # ID of the entity
    action = Column(String, nullable=False)  # "created", "approved", "sent", "dnc_marked", etc.
    actor = Column(String, nullable=False)  # "system", "operator@example.com", "api_key_123"
    context = Column(JSON, nullable=True)  # Additional context (renamed from metadata to avoid SQLAlchemy conflict)
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    __table_args__ = (
        Index('idx_audit_entity', 'entity_type', 'entity_id'),
        Index('idx_audit_action', 'action'),
        Index('idx_audit_timestamp', 'timestamp'),
    )


def log_audit(
    session: Session,
    entity_type: str,
    entity_id: str,
    action: str,
    actor: str = "system",
    metadata: Optional[Dict[str, Any]] = None
) -> AuditLogDB:
    """
    Log an audit event.
    
    Args:
        session: Database session
        entity_type: Type of entity (campaign, lead, distribution, etc.)
        entity_id: ID of the entity
        action: Action taken (created, sent, dnc_marked, etc.)
        actor: Who performed the action
        metadata: Additional context
        
    Returns:
        AuditLogDB record
    """
    log = AuditLogDB(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor=actor,
        context=metadata or {},  # Use context field instead of metadata
        timestamp=datetime.now(timezone.utc)
    )
    session.add(log)
    session.commit()
    return log


def get_audit_trail(
    session: Session,
    entity_type: str,
    entity_id: str
) -> list[AuditLogDB]:
    """
    Get full audit trail for an entity.
    
    Returns all audit logs in chronological order.
    """
    return session.query(AuditLogDB).filter(
        AuditLogDB.entity_type == entity_type,
        AuditLogDB.entity_id == entity_id
    ).order_by(AuditLogDB.timestamp).all()
