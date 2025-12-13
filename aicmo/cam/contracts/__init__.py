"""
Contracts for CAM module communication.

This module defines all input/output contracts (Pydantic models) 
for cross-module communication. Modules MUST NOT import each other's internals;
they communicate only through these contracts.

Versioning: v1 (schema versioning for future compatibility)
"""

import warnings
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field

# Suppress Pydantic v2 deprecation warnings for Config classes
# (TODO: migrate to ConfigDict in future update)
warnings.filterwarnings("ignore", message="Support for class-based `config` is deprecated")


# ─────────────────────────────────────────────────────────────────
# ENUMS (Shared state definitions)
# ─────────────────────────────────────────────────────────────────

class ReplyClassificationEnum(str, Enum):
    """Classification of an inbound reply."""
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    OOO = "OOO"
    BOUNCE = "BOUNCE"
    UNSUB = "UNSUB"
    NEUTRAL = "NEUTRAL"


class LeadStateEnum(str, Enum):
    """Valid lead states."""
    PROSPECT = "PROSPECT"
    INTERESTED = "INTERESTED"
    REJECTED = "REJECTED"
    UNSUBSCRIBED = "UNSUBSCRIBED"
    DEAD = "DEAD"
    QUALIFIED = "QUALIFIED"


class WorkerStatusEnum(str, Enum):
    """Worker heartbeat status."""
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    DEAD = "DEAD"


# ─────────────────────────────────────────────────────────────────
# INPUT CONTRACTS (Inbound to module)
# ─────────────────────────────────────────────────────────────────

class SendEmailRequest(BaseModel):
    """Request to send an outbound email (EmailModule.send_email API)."""
    
    campaign_id: int
    lead_id: int
    to_email: str
    subject: str
    html_body: str
    text_body: Optional[str] = None
    sequence_number: Optional[int] = None
    campaign_sequence_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "campaign_id": 123,
                "lead_id": 456,
                "to_email": "prospect@company.com",
                "subject": "Outreach",
                "html_body": "<p>Hello</p>",
                "sequence_number": 1
            }
        }


class ClassifyReplyRequest(BaseModel):
    """Request to classify a reply (ClassificationModule.classify API)."""
    
    subject: str
    body: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "subject": "RE: Outreach",
                "body": "I'm interested! Let's talk."
            }
        }


class ProcessReplyRequest(BaseModel):
    """Request to process a classified reply (FollowUpModule.process_reply API)."""
    
    lead_id: int
    inbound_email_id: int
    classification: ReplyClassificationEnum
    
    class Config:
        json_schema_extra = {
            "example": {
                "lead_id": 456,
                "inbound_email_id": 789,
                "classification": "POSITIVE"
            }
        }


class FetchInboxRequest(BaseModel):
    """Request to fetch new replies (InboxModule.fetch_new_replies API)."""
    
    since: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "since": "2025-12-12T10:00:00Z"
            }
        }


# ─────────────────────────────────────────────────────────────────
# OUTPUT CONTRACTS (Outbound from module)
# ─────────────────────────────────────────────────────────────────

class SendEmailResponse(BaseModel):
    """Response from SendEmail (success/failure with tracking ID)."""
    
    success: bool
    outbound_email_id: Optional[int] = None
    provider_message_id: Optional[str] = None
    error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "outbound_email_id": 999,
                "provider_message_id": "uuid-from-resend"
            }
        }


class ClassifyReplyResponse(BaseModel):
    """Response from ClassifyReply."""
    
    classification: ReplyClassificationEnum
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "classification": "POSITIVE",
                "confidence": 0.95,
                "reason": "Matched 'interested' keyword"
            }
        }


class EmailReplyModel(BaseModel):
    """A reply email fetched from inbox (outbound from InboxModule)."""
    
    from_email: str
    to_email: Optional[str] = None
    subject: Optional[str] = None
    body: str
    received_at: datetime
    message_id: str
    uid: str  # Provider-specific UID (IMAP UID, etc.)
    
    class Config:
        json_schema_extra = {
            "example": {
                "from_email": "prospect@company.com",
                "to_email": "sales@ourcompany.com",
                "subject": "RE: Let's connect",
                "body": "Sounds good. Let's set up a call.",
                "received_at": "2025-12-12T15:30:00Z",
                "message_id": "msg-123",
                "uid": "imap-uid-456"
            }
        }


class FetchInboxResponse(BaseModel):
    """Response from FetchInbox (list of new replies)."""
    
    replies: List[EmailReplyModel]
    fetch_timestamp: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "replies": [
                    {
                        "from_email": "p@c.com",
                        "body": "Interested",
                        "received_at": "2025-12-12T15:30:00Z",
                        "message_id": "msg-1",
                        "uid": "imap-1"
                    }
                ],
                "fetch_timestamp": "2025-12-12T15:35:00Z"
            }
        }


class CampaignMetricsModel(BaseModel):
    """Campaign metrics snapshot (outbound from DecisionModule)."""
    
    campaign_id: int
    sent_count: int
    reply_count: int
    positive_count: int
    negative_count: int
    bounce_count: int
    ooo_count: int
    unsub_count: int
    neutral_count: int
    
    @property
    def reply_rate(self) -> float:
        """Reply rate as percentage."""
        if self.sent_count == 0:
            return 0.0
        return (self.reply_count / self.sent_count) * 100.0
    
    @property
    def positive_rate(self) -> float:
        """Positive reply rate as percentage."""
        if self.reply_count == 0:
            return 0.0
        return (self.positive_count / self.reply_count) * 100.0
    
    class Config:
        json_schema_extra = {
            "example": {
                "campaign_id": 123,
                "sent_count": 100,
                "reply_count": 15,
                "positive_count": 10,
                "negative_count": 3,
                "bounce_count": 2,
                "ooo_count": 0,
                "unsub_count": 0,
                "neutral_count": 0
            }
        }


# ─────────────────────────────────────────────────────────────────
# EVENT CONTRACTS (For optional event bus)
# ─────────────────────────────────────────────────────────────────

class EmailSentEvent(BaseModel):
    """Event: email was sent."""
    event_type: str = "email.sent"
    outbound_email_id: int
    campaign_id: int
    lead_id: int
    to_email: str
    timestamp: datetime


class ReplyReceivedEvent(BaseModel):
    """Event: reply was received."""
    event_type: str = "reply.received"
    inbound_email_id: int
    campaign_id: Optional[int]
    lead_id: Optional[int]
    from_email: str
    timestamp: datetime


class ReplyClassifiedEvent(BaseModel):
    """Event: reply was classified."""
    event_type: str = "reply.classified"
    inbound_email_id: int
    classification: ReplyClassificationEnum
    confidence: float
    timestamp: datetime


class LeadAdvancedEvent(BaseModel):
    """Event: lead state advanced."""
    event_type: str = "lead.advanced"
    lead_id: int
    campaign_id: int
    from_state: LeadStateEnum
    to_state: LeadStateEnum
    trigger: str  # e.g., "POSITIVE_REPLY"
    timestamp: datetime


class AlertSentEvent(BaseModel):
    """Event: alert was sent to human."""
    event_type: str = "alert.sent"
    alert_type: str
    lead_id: Optional[int]
    campaign_id: Optional[int]
    recipients: List[str]
    timestamp: datetime


# ─────────────────────────────────────────────────────────────────
# HEALTH/DIAGNOSTICS CONTRACTS
# ─────────────────────────────────────────────────────────────────

class ModuleHealthModel(BaseModel):
    """Health status of a module."""
    
    module_name: str
    is_healthy: bool
    status_message: str
    last_check_at: datetime
    capabilities: List[str]  # e.g., ["send_email", "fetch_inbox"]


class WorkerHealthModel(BaseModel):
    """Health of the worker."""
    
    is_running: bool
    last_cycle_at: Optional[datetime]
    cycle_count: int
    error_count: int
    status_message: str


# ─────────────────────────────────────────────────────────────────
# METERING/USAGE CONTRACTS
# ─────────────────────────────────────────────────────────────────

class UsageEventModel(BaseModel):
    """A single usage event (for metering)."""
    
    module: str  # e.g., "email", "inbox", "alerts"
    action: str  # e.g., "send", "fetch", "alert"
    count: int = 1
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────
# ERROR CONTRACT
# ─────────────────────────────────────────────────────────────────

class ModuleErrorModel(BaseModel):
    """Standard error response from a module."""
    
    error_code: str  # e.g., "EMAIL_SEND_FAILED", "IMAP_CONNECTION_FAILED"
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime
