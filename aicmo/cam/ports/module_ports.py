"""
Module Ports (Formal Interfaces)

Each port is a Protocol/ABC that defines the contract for a specific capability.
Modules implement these ports; consumers call through ports.

RULE: Modules communicate ONLY through ports (not by importing each other's internals).
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from aicmo.cam.contracts import (
    SendEmailRequest,
    SendEmailResponse,
    ClassifyReplyRequest,
    ClassifyReplyResponse,
    ProcessReplyRequest,
    FetchInboxRequest,
    FetchInboxResponse,
    EmailReplyModel,
    CampaignMetricsModel,
    ModuleHealthModel,
    UsageEventModel,
)


# ─────────────────────────────────────────────────────────────────
# EMAIL MODULE PORT
# ─────────────────────────────────────────────────────────────────

class EmailModule(ABC):
    """Port: Send outbound emails."""
    
    @abstractmethod
    def send_email(self, request: SendEmailRequest) -> SendEmailResponse:
        """
        Send an outbound email.
        
        Contract:
        - Idempotent: same request twice = same response (no duplicate sends)
        - Never raises: returns SendEmailResponse with success=False on error
        - Updates: lead.last_contacted_at
        - Persists: OutboundEmailDB record
        
        Args:
            request: SendEmailRequest with campaign, lead, email details
        
        Returns:
            SendEmailResponse with success status and tracking ID
        """
        ...
    
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if email provider is properly configured."""
        ...
    
    @abstractmethod
    def health(self) -> ModuleHealthModel:
        """Return health status of email module."""
        ...


# ─────────────────────────────────────────────────────────────────
# REPLY CLASSIFICATION PORT
# ─────────────────────────────────────────────────────────────────

class ClassificationModule(ABC):
    """Port: Classify inbound replies."""
    
    @abstractmethod
    def classify(self, request: ClassifyReplyRequest) -> ClassifyReplyResponse:
        """
        Classify a reply email.
        
        Contract:
        - Stateless: no side effects, pure function
        - Never raises: always returns valid response
        - Deterministic: same input = same output
        
        Args:
            request: ClassifyReplyRequest with subject and body
        
        Returns:
            ClassifyReplyResponse with classification, confidence, reason
        """
        ...


# ─────────────────────────────────────────────────────────────────
# FOLLOW-UP / STATE TRANSITION PORT
# ─────────────────────────────────────────────────────────────────

class FollowUpModule(ABC):
    """Port: Process replies and advance lead state."""
    
    @abstractmethod
    def process_reply(self, request: ProcessReplyRequest) -> bool:
        """
        Process a classified reply and update lead state.
        
        Contract:
        - Idempotent: same request twice = same state (idempotency key: lead_id + email_id)
        - Updates: lead.status based on classification
        - Persists: state transition audit trail
        - Never raises: returns bool success
        
        Side effects:
        - LeadDB.status updated
        - OutreachAttemptDB record updated
        
        Args:
            request: ProcessReplyRequest with lead, email, classification
        
        Returns:
            bool: True if state advanced, False otherwise
        """
        ...


# ─────────────────────────────────────────────────────────────────
# INBOX/POLLING PORT
# ─────────────────────────────────────────────────────────────────

class InboxModule(ABC):
    """Port: Fetch and ingest replies from external mail server."""
    
    @abstractmethod
    def fetch_new_replies(self, request: FetchInboxRequest) -> FetchInboxResponse:
        """
        Fetch new replies from inbox since given time.
        
        Contract:
        - Idempotent: replayed requests return same emails (idempotency: provider UID)
        - Persists: InboundEmailDB records created for each email
        - Never raises: returns empty list on error
        - Manages cursor: internally tracks last polled time/UID
        
        Args:
            request: FetchInboxRequest with since datetime
        
        Returns:
            FetchInboxResponse with list of EmailReplyModel
        """
        ...
    
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if inbox provider is properly configured."""
        ...


# ─────────────────────────────────────────────────────────────────
# DECISION/METRICS PORT
# ─────────────────────────────────────────────────────────────────

class DecisionModule(ABC):
    """Port: Compute metrics and make campaign decisions."""
    
    @abstractmethod
    def compute_metrics(self, campaign_id: int) -> CampaignMetricsModel:
        """
        Compute current metrics for a campaign.
        
        Contract:
        - Stateless query: reads from DB, no side effects
        - Never raises: returns metrics with counts (may be zeros)
        
        Args:
            campaign_id: Campaign to compute metrics for
        
        Returns:
            CampaignMetricsModel with all counts and derived rates
        """
        ...
    
    @abstractmethod
    def evaluate_campaign(self, campaign_id: int) -> bool:
        """
        Evaluate campaign rules and apply actions (pause, degrade).
        
        Contract:
        - May update: campaign.status if rules trigger
        - Returns: True if campaign is still active, False if paused/degraded
        - Never raises
        
        Args:
            campaign_id: Campaign to evaluate
        
        Returns:
            bool: True if campaign active, False if paused
        """
        ...


# ─────────────────────────────────────────────────────────────────
# ALERT PROVIDER PORT
# ─────────────────────────────────────────────────────────────────

class AlertModule(ABC):
    """Port: Send alerts to humans."""
    
    @abstractmethod
    def send_alert(
        self,
        alert_type: str,
        title: str,
        message: str,
        lead_id: Optional[int] = None,
        campaign_id: Optional[int] = None,
        inbound_email_id: Optional[int] = None,
        recipients: Optional[List[str]] = None,
    ) -> bool:
        """
        Send an alert to configured recipients.
        
        Contract:
        - Idempotent: same alert twice = logged once (idempotency key: lead_id + alert_type)
        - Never raises: returns bool success
        - Persists: HumanAlertLogDB record for audit trail
        
        Args:
            alert_type: Type of alert (e.g., "POSITIVE_REPLY")
            title: Alert title
            message: Alert message
            lead_id: Associated lead (optional)
            campaign_id: Associated campaign (optional)
            inbound_email_id: Associated inbound email (optional)
            recipients: Override default recipients (optional)
        
        Returns:
            bool: True if sent successfully
        """
        ...
    
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if alert provider is configured."""
        ...


# ─────────────────────────────────────────────────────────────────
# LOCKING PORT (For worker coordination)
# ─────────────────────────────────────────────────────────────────

class LockProvider(ABC):
    """Port: Acquire/release single-worker lock."""
    
    @abstractmethod
    def acquire(self, worker_id: str, ttl_seconds: int = 300) -> bool:
        """
        Attempt to acquire exclusive worker lock.
        
        Contract:
        - Returns False if lock held by another worker
        - Returns True if lock acquired by this worker
        - TTL: auto-releases if not updated for ttl_seconds
        
        Args:
            worker_id: Unique worker identifier
            ttl_seconds: Time-to-live for lock (default 5 min)
        
        Returns:
            bool: True if lock acquired
        """
        ...
    
    @abstractmethod
    def release(self, worker_id: str) -> bool:
        """Release the lock."""
        ...
    
    @abstractmethod
    def is_held(self) -> bool:
        """Check if any worker holds the lock."""
        ...


# ─────────────────────────────────────────────────────────────────
# USAGE METERING PORT
# ─────────────────────────────────────────────────────────────────

class MeteringModule(ABC):
    """Port: Record usage events for billing/metrics."""
    
    @abstractmethod
    def record_usage(self, event: UsageEventModel) -> bool:
        """
        Record a usage event.
        
        Contract:
        - Async-safe: non-blocking
        - Never raises
        
        Args:
            event: Usage event to record
        
        Returns:
            bool: True if recorded
        """
        ...
    
    @abstractmethod
    def get_usage(self, module: str, start_date: datetime, end_date: datetime) -> dict:
        """Get usage summary for a module during date range."""
        ...


# ─────────────────────────────────────────────────────────────────
# HEALTH CHECKER PORT
# ─────────────────────────────────────────────────────────────────

class HealthModule(ABC):
    """Port: Check health of all modules."""
    
    @abstractmethod
    def check_all(self) -> dict:
        """
        Check health of all modules.
        
        Returns:
            {
                "modules": [ModuleHealthModel, ...],
                "timestamp": datetime,
                "is_healthy": bool  # True if all modules healthy
            }
        """
        ...
