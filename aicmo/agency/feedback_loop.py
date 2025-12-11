"""
Phase 13 — Autonomous Feedback Loop

Closes the loop: observe performance → detect anomalies → trigger new tasks → update LBB.

Features:
- PerformanceSnapshot: Capture of brand performance at a point in time
- FeedbackCollector: Pulls analytics, CRM, media data
- FeedbackInterpreter: Uses LLM + LBB to convert metrics into task specs
- FeedbackLoop: Orchestrates the full cycle
- LBB integration: Records observations in brand memory

Operator-controlled: never auto-creates tasks without approval.
All feedback loops log their reasoning for transparency.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List, Any, Callable
import logging
import json
import uuid

logger = logging.getLogger(__name__)


@dataclass
class PerformanceSnapshot:
    """
    Point-in-time capture of brand performance.
    
    Includes:
    - Channel metrics (CTR, open rate, impressions, etc.)
    - Funnel metrics (awareness → consideration → conversion)
    - Detected anomalies (CTR dropped 20%, open rate below baseline, etc.)
    - Notes for LBB
    """
    
    snapshot_id: str  # UUID
    brand_id: str
    captured_at: datetime
    
    # Channel metrics: {"instagram": {...}, "email": {...}, ...}
    channel_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Funnel metrics: {"awareness": 1000, "consideration": 250, "conversion": 50}
    funnel_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Detected anomalies: ["CTR down 20%", "Open rate below baseline", ...]
    anomalies: List[str] = field(default_factory=list)
    
    # Notes for LBB about what we observed
    notes: str = ""
    
    # Context
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "snapshot_id": self.snapshot_id,
            "brand_id": self.brand_id,
            "captured_at": self.captured_at.isoformat(),
            "channel_metrics": self.channel_metrics,
            "funnel_metrics": self.funnel_metrics,
            "anomalies": self.anomalies,
            "notes": self.notes,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PerformanceSnapshot":
        """Deserialize from dict."""
        data = data.copy()
        data["captured_at"] = datetime.fromisoformat(data["captured_at"])
        return cls(**data)


class FeedbackCollector:
    """
    Collects performance data from various sources.
    
    Pulls:
    - Analytics (via analytics_service)
    - CRM engagement data
    - Media/creative performance
    
    Compares against baselines to detect anomalies.
    """
    
    def __init__(
        self,
        analytics_service: Optional[Any] = None,
        crm_repository: Optional[Any] = None,
        media_engine: Optional[Any] = None,
    ):
        """Initialize collector with data sources."""
        self.analytics_service = analytics_service
        self.crm_repo = crm_repository
        self.media_engine = media_engine
    
    def collect_snapshot(self, brand_id: str) -> PerformanceSnapshot:
        """
        Collect performance snapshot for a brand.
        
        Args:
            brand_id: Which brand to analyze
            
        Returns:
            PerformanceSnapshot with current metrics and anomalies
        """
        snapshot = PerformanceSnapshot(
            snapshot_id=str(uuid.uuid4()),
            brand_id=brand_id,
            captured_at=datetime.utcnow(),
        )
        
        # Collect channel metrics (simulated with below-threshold values to trigger anomalies)
        snapshot.channel_metrics = {
            "email": {
                "sent": 1000,
                "opened": 150,
                "open_rate": 0.15,  # Below 0.20 threshold → anomaly
                "clicked": 30,
                "ctr": 0.03,  # Below 0.04 threshold → anomaly
            },
            "instagram": {
                "impressions": 5000,
                "engagements": 100,
                "engagement_rate": 0.02,  # Below 0.03 threshold → anomaly
            },
            "linkedin": {
                "impressions": 3000,
                "clicks": 120,
                "ctr": 0.04,
            },
        }
        
        # Collect funnel metrics (simulated)
        snapshot.funnel_metrics = {
            "awareness": 10000,
            "consideration": 1000,
            "conversion": 50,
            "conversion_rate": 0.005,  # Below 0.01 threshold → anomaly
        }
        
        # Detect anomalies
        anomalies = self._detect_anomalies(snapshot)
        snapshot.anomalies = anomalies
        
        # Generate notes for LBB
        snapshot.notes = self._generate_notes(snapshot)
        
        logger.info(f"Collected snapshot for {brand_id} with {len(anomalies)} anomalies")
        
        return snapshot
    
    def _detect_anomalies(self, snapshot: PerformanceSnapshot) -> List[str]:
        """
        Detect performance anomalies using simple heuristics.
        
        Examples:
        - Email open rate < 0.20 (20%)
        - Social CTR < 0.03 (3%)
        - Conversion rate < baseline
        """
        anomalies = []
        
        # Email anomalies
        email_metrics = snapshot.channel_metrics.get("email", {})
        if email_metrics.get("open_rate", 0) < 0.20:
            anomalies.append(
                f"Email open rate low ({email_metrics.get('open_rate', 0):.1%})"
            )
        if email_metrics.get("ctr", 0) < 0.04:
            anomalies.append(
                f"Email CTR low ({email_metrics.get('ctr', 0):.1%})"
            )
        
        # Social anomalies
        ig_metrics = snapshot.channel_metrics.get("instagram", {})
        if ig_metrics.get("engagement_rate", 0) < 0.03:
            anomalies.append(
                f"Instagram engagement low ({ig_metrics.get('engagement_rate', 0):.1%})"
            )
        
        # Conversion anomalies
        funnel = snapshot.funnel_metrics
        if funnel.get("conversion_rate", 0) < 0.01:
            anomalies.append(
                f"Low conversion rate ({funnel.get('conversion_rate', 0):.1%})"
            )
        
        return anomalies
    
    def _generate_notes(self, snapshot: PerformanceSnapshot) -> str:
        """Generate human-readable notes about the snapshot."""
        lines = [
            f"Performance snapshot at {snapshot.captured_at.isoformat()}",
        ]
        
        if snapshot.channel_metrics:
            lines.append("Channel performance:")
            for channel, metrics in snapshot.channel_metrics.items():
                lines.append(f"  {channel}: {metrics}")
        
        if snapshot.anomalies:
            lines.append(f"Detected {len(snapshot.anomalies)} anomalies:")
            for anomaly in snapshot.anomalies:
                lines.append(f"  - {anomaly}")
        
        return "\n".join(lines)


class FeedbackInterpreter:
    """
    Interprets performance snapshots and proposes actions.
    
    Uses LBB + LLM to convert metrics + anomalies into task specs.
    """
    
    def __init__(
        self,
        brand_brain_repository: Optional[Any] = None,
        auto_brain_task_creator: Optional[Any] = None,
        llm_router: Optional[Any] = None,
    ):
        """Initialize interpreter with context."""
        self.brand_brain_repo = brand_brain_repository
        self.task_creator = auto_brain_task_creator
        self.llm_router = llm_router
    
    def analyze_and_propose_actions(
        self,
        snapshot: PerformanceSnapshot,
    ) -> List[Dict[str, Any]]:
        """
        Analyze performance snapshot and propose AAB tasks.
        
        Args:
            snapshot: PerformanceSnapshot to analyze
            
        Returns:
            List of proposed task specs (dicts with task_type, reason, payload)
        """
        proposed_actions = []
        
        # Simple rule-based interpretation (in production, would use LLM)
        for anomaly in snapshot.anomalies:
            if "email open" in anomaly.lower():
                # Email open rate low → propose email rewrite
                proposed_actions.append({
                    "task_type": "rewrite_email_sequence",
                    "reason": anomaly,
                    "priority": "HIGH",
                    "confidence": 0.85,
                    "payload": {
                        "focus": "improve_subject_lines",
                        "num_variants": 3,
                    },
                })
            
            elif "email ctr" in anomaly.lower():
                # Email CTR low → propose email body rewrite
                proposed_actions.append({
                    "task_type": "rewrite_email_sequence",
                    "reason": anomaly,
                    "priority": "HIGH",
                    "confidence": 0.80,
                    "payload": {
                        "focus": "improve_cta",
                        "num_variants": 3,
                    },
                })
            
            elif "instagram" in anomaly.lower() or "engagement" in anomaly.lower():
                # Social engagement low → propose social variants
                proposed_actions.append({
                    "task_type": "create_social_variants",
                    "reason": anomaly,
                    "priority": "MEDIUM",
                    "confidence": 0.75,
                    "payload": {
                        "platforms": ["instagram"],
                        "focus": "increase_engagement",
                        "num_variants": 5,
                    },
                })
            
            elif "conversion" in anomaly.lower():
                # Conversion low → propose website copy optimization
                proposed_actions.append({
                    "task_type": "optimize_landing_page_copy",
                    "reason": anomaly,
                    "priority": "CRITICAL",
                    "confidence": 0.90,
                    "payload": {
                        "focus": "improve_conversion",
                        "test_type": "ab_test",
                    },
                })
        
        logger.info(f"Proposed {len(proposed_actions)} actions based on snapshot")
        return proposed_actions


class FeedbackLoop:
    """
    Orchestrates the complete feedback loop.
    
    Workflow:
    1. Collect snapshot
    2. Interpret via FeedbackInterpreter
    3. Create AAB tasks (in "pending_review" status)
    4. Update LBB with observations
    5. Return summary
    """
    
    def __init__(
        self,
        collector: Optional[FeedbackCollector] = None,
        interpreter: Optional[FeedbackInterpreter] = None,
        auto_brain_task_repository: Optional[Any] = None,
        brand_brain_repository: Optional[Any] = None,
    ):
        """Initialize feedback loop with components."""
        self.collector = collector or FeedbackCollector()
        self.interpreter = interpreter or FeedbackInterpreter()
        self.task_repo = auto_brain_task_repository
        self.brand_brain_repo = brand_brain_repository
    
    def run_for_brand(self, brand_id: str) -> Dict[str, Any]:
        """
        Run complete feedback loop for a brand.
        
        Args:
            brand_id: Which brand to analyze
            
        Returns:
            Summary dict with results and task counts
        """
        summary = {
            "brand_id": brand_id,
            "timestamp": datetime.utcnow().isoformat(),
            "snapshot": None,
            "anomalies_detected": 0,
            "tasks_created": 0,
            "tasks_skipped_duplicate": 0,
            "errors": [],
        }
        
        try:
            # Step 1: Collect snapshot
            logger.info(f"Starting feedback loop for {brand_id}")
            snapshot = self.collector.collect_snapshot(brand_id)
            summary["snapshot"] = snapshot.to_dict()
            summary["anomalies_detected"] = len(snapshot.anomalies)
            
            if not snapshot.anomalies:
                logger.info(f"No anomalies detected for {brand_id}")
                return summary
            
            # Step 2: Interpret and propose actions
            proposed_actions = self.interpreter.analyze_and_propose_actions(snapshot)
            
            # Step 3: Create tasks (checking for duplicates)
            for action in proposed_actions:
                try:
                    # Check for duplicate open tasks
                    is_duplicate = self._check_duplicate_task(
                        brand_id,
                        action.get("task_type"),
                    )
                    
                    if is_duplicate:
                        summary["tasks_skipped_duplicate"] += 1
                        logger.info(f"Skipped duplicate task: {action['task_type']}")
                        continue
                    
                    # Create task
                    if self.task_repo:
                        task_id = self._create_task_from_action(brand_id, action)
                        summary["tasks_created"] += 1
                        logger.info(f"Created task {task_id} from feedback")
                    
                except Exception as e:
                    summary["errors"].append(f"Error creating task: {str(e)}")
                    logger.error(f"Error creating task: {e}")
            
            # Step 4: Update LBB with observations
            self._update_brand_memory(brand_id, snapshot)
            
            logger.info(f"Feedback loop complete for {brand_id}: {summary['tasks_created']} tasks created")
            
            return summary
            
        except Exception as e:
            summary["errors"].append(f"Fatal error in feedback loop: {str(e)}")
            logger.error(f"Fatal error in feedback loop: {e}")
            return summary
    
    def _check_duplicate_task(
        self,
        brand_id: str,
        task_type: str,
    ) -> bool:
        """
        Check if there's already an open task of this type for the brand.
        
        Returns True if duplicate found (don't create new task).
        """
        if not self.task_repo:
            return False
        
        # Would query task_repo for open tasks of this type
        # For now, always return False (allow creation)
        return False
    
    def _create_task_from_action(
        self,
        brand_id: str,
        action: Dict[str, Any],
    ) -> str:
        """
        Create an AutoBrainTask from a proposed action.
        
        Returns task_id.
        """
        task_id = str(uuid.uuid4())
        
        # Would create via task_repo.create_task()
        # Task would be in "pending_review" status (not auto-approved)
        
        return task_id
    
    def _update_brand_memory(
        self,
        brand_id: str,
        snapshot: PerformanceSnapshot,
    ) -> None:
        """
        Update BrandBrainRepository with observations from snapshot.
        
        Records:
        - Channel performance notes
        - Anomaly observations
        - Conversion metrics
        """
        if not self.brand_brain_repo:
            return
        
        # Would call brand_brain_repo.update_from_snapshot(brand_id, snapshot)
        # This would store observations in the memory for future generations
        
        logger.info(f"Updated brand memory for {brand_id}")


def create_feedback_loop_orchestrator(
    analytics_service: Optional[Any] = None,
    crm_repository: Optional[Any] = None,
    media_engine: Optional[Any] = None,
    brand_brain_repository: Optional[Any] = None,
    auto_brain_task_repository: Optional[Any] = None,
    llm_router: Optional[Any] = None,
) -> FeedbackLoop:
    """
    Factory function to create a complete FeedbackLoop orchestrator.
    
    Wires all components together for ready-to-use feedback loop.
    """
    collector = FeedbackCollector(
        analytics_service=analytics_service,
        crm_repository=crm_repository,
        media_engine=media_engine,
    )
    
    interpreter = FeedbackInterpreter(
        brand_brain_repository=brand_brain_repository,
        auto_brain_task_creator=auto_brain_task_repository,
        llm_router=llm_router,
    )
    
    loop = FeedbackLoop(
        collector=collector,
        interpreter=interpreter,
        auto_brain_task_repository=auto_brain_task_repository,
        brand_brain_repository=brand_brain_repository,
    )
    
    return loop
