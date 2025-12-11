"""
Phase 6: Auto Creative Performance Loop

Automatically detects underperforming creatives and creates optimizer actions.
Closed-loop optimization system for continuous creative improvement.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

# Performance thresholds for optimization triggering
LOW_CTR_THRESHOLD = 0.02  # 2% CTR triggers optimization
LOW_ENGAGEMENT_THRESHOLD = 10  # Minimum engagement count
OPTIMIZATION_MIN_FILE_SIZE_MB = 5  # Only optimize if file is large enough


class OptimizationTaskStatus(str, Enum):
    """Status values for optimization tasks."""
    PENDING = "pending"
    GENERATED = "generated"
    APPROVED = "approved"
    EXECUTED = "executed"
    REJECTED = "rejected"
    FAILED = "failed"


class OptimizationActionType(str, Enum):
    """Types of optimization actions."""
    GENERATE_VARIANTS = "generate_variants"
    COMPRESS = "compress"
    REPLACE = "replace"
    RESIZE = "resize"
    FORMAT_CHANGE = "format_change"
    RECOLOR = "recolor"


@dataclass
class CreativeOptimizationTask:
    """
    A single optimization task for an underperforming creative.
    
    Tracks optimization actions needed, status, and execution history.
    """
    
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    """Unique task identifier"""
    
    asset_id: str = ""
    """Asset to optimize"""
    
    reason: str = ""
    """Why optimization was triggered (e.g., 'Low CTR: 1.5%')"""
    
    action_type: str = OptimizationActionType.GENERATE_VARIANTS
    """Type of optimization action"""
    
    status: str = OptimizationTaskStatus.PENDING
    """Current status: pending, generated, approved, executed, rejected, failed"""
    
    created_at: datetime = field(default_factory=datetime.now)
    """When task was created"""
    
    updated_at: datetime = field(default_factory=datetime.now)
    """When task was last updated"""
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional task metadata (metrics, suggestions, etc.)"""
    
    executed_at: Optional[datetime] = None
    """When task was executed (if applicable)"""
    
    result: Optional[Dict[str, Any]] = None
    """Result of task execution"""


class CreativePerformanceOptimizer:
    """
    Automatically detects underperforming creatives and creates tasks.
    
    Scans performance data and analytics to identify assets needing optimization,
    then creates actionable optimization tasks for review and execution.
    """
    
    def __init__(self, media_engine=None, analytics_service=None):
        """
        Initialize performance optimizer.
        
        Args:
            media_engine: MediaEngine instance for asset operations
            analytics_service: Analytics service for performance data
        """
        self.media_engine = media_engine
        self.analytics_service = analytics_service
        self.tasks: Dict[str, CreativeOptimizationTask] = {}
        self._task_counter = 0
    
    def scan_and_create_tasks(
        self,
        client_id: str,
        campaign_ids: Optional[List[str]] = None,
    ) -> List[CreativeOptimizationTask]:
        """
        Scan asset performance and create optimization tasks.
        
        Steps:
        1. Read performance data from media engine
        2. Read analytics from analytics service
        3. Identify low-performing assets
        4. Create optimization tasks with appropriate actions
        5. Avoid duplicate tasks for same asset/reason
        
        Args:
            client_id: Client to scan
            campaign_ids: Optional list of campaigns to scan (default: all)
            
        Returns:
            List of newly created optimization tasks
        """
        created_tasks = []
        
        try:
            if not self.media_engine:
                logger.warning("No media_engine provided, cannot scan performance")
                return []
            
            logger.info(
                f"Scanning creatives for client {client_id} "
                f"across {len(campaign_ids or [])} campaigns"
            )
            
            # Collect all assets and their performance
            assets_to_check = []
            for asset_id, asset in self.media_engine.assets.items():
                perf_data = self.media_engine.get_asset_performance(asset_id)
                if perf_data:
                    assets_to_check.append((asset_id, asset, perf_data))
            
            logger.info(f"Found {len(assets_to_check)} assets with performance data")
            
            # Analyze each asset
            for asset_id, asset, perf_list in assets_to_check:
                # Calculate average metrics
                total_ctr = sum(p.ctr for p in perf_list)
                avg_ctr = total_ctr / len(perf_list) if perf_list else 0
                
                total_engagement = sum(
                    (p.clicks or 0) + (p.engagements or 0)
                    for p in perf_list
                )
                
                # Trigger conditions
                if avg_ctr < LOW_CTR_THRESHOLD:
                    task = self._create_task(
                        asset_id=asset_id,
                        reason=f"Low CTR: {avg_ctr:.2%}",
                        action_type=OptimizationActionType.GENERATE_VARIANTS,
                        metadata={
                            "current_ctr": avg_ctr,
                            "threshold": LOW_CTR_THRESHOLD,
                            "performance_samples": len(perf_list),
                        },
                    )
                    if task:
                        created_tasks.append(task)
                
                if total_engagement < LOW_ENGAGEMENT_THRESHOLD:
                    task = self._create_task(
                        asset_id=asset_id,
                        reason=f"Low engagement: {total_engagement} actions",
                        action_type=OptimizationActionType.REPLACE,
                        metadata={
                            "current_engagement": total_engagement,
                            "threshold": LOW_ENGAGEMENT_THRESHOLD,
                        },
                    )
                    if task:
                        created_tasks.append(task)
            
            logger.info(f"Created {len(created_tasks)} new optimization tasks")
            
            return created_tasks
            
        except Exception as e:
            logger.error(f"Error scanning creatives: {e}", exc_info=True)
            return []
    
    def _create_task(
        self,
        asset_id: str,
        reason: str,
        action_type: str,
        metadata: Optional[Dict] = None,
    ) -> Optional[CreativeOptimizationTask]:
        """
        Create optimization task if one doesn't already exist for this condition.
        
        Args:
            asset_id: Asset to optimize
            reason: Reason for optimization
            action_type: Type of action
            metadata: Optional metadata
            
        Returns:
            Created task, or None if duplicate already exists
        """
        # Check for existing task with same asset and reason
        for existing_task in self.tasks.values():
            if (existing_task.asset_id == asset_id and
                existing_task.reason == reason and
                existing_task.status in (
                    OptimizationTaskStatus.PENDING,
                    OptimizationTaskStatus.GENERATED,
                )):
                logger.info(
                    f"Task already exists for {asset_id}: {reason}"
                )
                return None
        
        # Create new task
        task = CreativeOptimizationTask(
            task_id=f"opt_{self._task_counter:06d}",
            asset_id=asset_id,
            reason=reason,
            action_type=action_type,
            status=OptimizationTaskStatus.PENDING,
            metadata=metadata or {},
        )
        
        self._task_counter += 1
        self.tasks[task.task_id] = task
        
        logger.info(
            f"Created task {task.task_id} for asset {asset_id}: {reason}"
        )
        
        return task
    
    def list_pending_tasks(self) -> List[CreativeOptimizationTask]:
        """Get all pending optimization tasks."""
        return [
            task for task in self.tasks.values()
            if task.status == OptimizationTaskStatus.PENDING
        ]
    
    def list_tasks_by_status(
        self,
        status: str,
    ) -> List[CreativeOptimizationTask]:
        """Get tasks by status."""
        return [
            task for task in self.tasks.values()
            if task.status == status
        ]
    
    def mark_task_status(
        self,
        task_id: str,
        new_status: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[CreativeOptimizationTask]:
        """
        Update task status.
        
        Args:
            task_id: Task to update
            new_status: New status value
            metadata: Optional metadata to merge
            
        Returns:
            Updated task, or None if not found
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return None
        
        task.status = new_status
        task.updated_at = datetime.now()
        
        if new_status == OptimizationTaskStatus.EXECUTED:
            task.executed_at = datetime.now()
        
        if metadata:
            task.metadata.update(metadata)
        
        logger.info(f"Updated task {task_id} status to {new_status}")
        
        return task
    
    def execute_task_generate_variants(
        self,
        task_id: str,
        num_variants: int = 3,
    ) -> bool:
        """
        Execute a generate_variants optimization task.
        
        Uses MediaEngine to create variant assets.
        
        Args:
            task_id: Task to execute
            num_variants: Number of variants to create
            
        Returns:
            True if successful, False otherwise
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return False
        
        if task.action_type != OptimizationActionType.GENERATE_VARIANTS:
            logger.error(f"Task {task_id} is not a generate_variants task")
            return False
        
        try:
            if not self.media_engine:
                logger.error("No media_engine available")
                return False
            
            # Get asset to use as basis
            asset = self.media_engine.assets.get(task.asset_id)
            if not asset:
                logger.error(f"Asset {task.asset_id} not found")
                return False
            
            # Generate variants
            sizes = [(512, 512), (1024, 1024), (256, 256)][:num_variants]
            
            variant_ids = self.media_engine.generate_variants_from_asset(
                asset_id=task.asset_id,
                sizes=sizes,
            )
            
            # Mark task as executed
            self.mark_task_status(
                task_id=task_id,
                new_status=OptimizationTaskStatus.EXECUTED,
                metadata={
                    "variant_ids": variant_ids,
                    "variant_count": len(variant_ids),
                },
            )
            
            logger.info(
                f"Executed task {task_id}: generated {len(variant_ids)} variants"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing task {task_id}: {e}", exc_info=True)
            self.mark_task_status(
                task_id=task_id,
                new_status=OptimizationTaskStatus.FAILED,
                metadata={"error": str(e)},
            )
            return False
    
    def execute_task_replace(
        self,
        task_id: str,
        replacement_asset_id: Optional[str] = None,
    ) -> bool:
        """
        Execute a replace optimization task.
        
        Args:
            task_id: Task to execute
            replacement_asset_id: Asset to use as replacement (optional)
            
        Returns:
            True if successful, False otherwise
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return False
        
        if task.action_type != OptimizationActionType.REPLACE:
            logger.error(f"Task {task_id} is not a replace task")
            return False
        
        try:
            # In a real implementation, would actually replace the asset
            # For now, mark as executed with suggestion
            self.mark_task_status(
                task_id=task_id,
                new_status=OptimizationTaskStatus.EXECUTED,
                metadata={
                    "replacement_suggested": True,
                    "replacement_asset_id": replacement_asset_id,
                },
            )
            
            logger.info(
                f"Executed task {task_id}: replacement suggested"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing task {task_id}: {e}", exc_info=True)
            self.mark_task_status(
                task_id=task_id,
                new_status=OptimizationTaskStatus.FAILED,
                metadata={"error": str(e)},
            )
            return False
    
    def get_task(self, task_id: str) -> Optional[CreativeOptimizationTask]:
        """Get task by ID."""
        return self.tasks.get(task_id)
    
    def list_all_tasks(self) -> List[CreativeOptimizationTask]:
        """List all tasks."""
        return list(self.tasks.values())
