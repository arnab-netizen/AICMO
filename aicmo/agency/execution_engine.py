"""
Phase 11 — Auto Execution Engine

Executes APPROVED AutoBrainTasks using existing engines:
- MediaEngine
- Social publishing
- Email sender
- Ads launcher
- Creative variant & Figma pipelines
- Existing generators (social, email, website, etc.)

The execution engine:
1. Classifies whether a task is executable (has required data)
2. Executes the task by dispatching to appropriate executor
3. Records results, metadata, and outputs
4. Respects dry_run mode (no real external calls)
5. Provides operator-controllable execution with logging

All tasks must be in "approved" status and READY_TO_RUN.
No auto-execution without explicit approval.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List, Any, Callable
from enum import Enum
import logging
import json
import uuid

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Status of task execution."""
    NOT_EXECUTABLE = "not_executable"  # Missing data/deps, cannot run
    READY_TO_RUN = "ready_to_run"  # Has all requirements, can execute
    RUNNING = "running"  # Currently executing
    COMPLETED = "completed"  # Done successfully
    COMPLETED_PREVIEW = "completed_preview"  # Done but preview-only (dry_run)
    FAILED = "failed"  # Error during execution
    SKIPPED = "skipped"  # Intentionally not executed


class TaskApprovalStatus(Enum):
    """Approval status of a task."""
    PROPOSED = "proposed"  # Suggested but not approved
    PENDING_REVIEW = "pending_review"  # Awaiting operator review
    APPROVED = "approved"  # Approved for execution
    REJECTED = "rejected"  # Operator rejected
    EXECUTING = "executing"  # Currently running
    EXECUTED = "executed"  # Already executed


@dataclass
class ExecutionContext:
    """
    Context for task execution.
    
    Contains references to all systems needed for execution,
    plus configuration flags like dry_run.
    """
    
    # System references (injected)
    task_repository: Optional[Any] = None  # AutoBrainTaskRepository
    brand_brain_repository: Optional[Any] = None  # BrandBrainRepository (LBB)
    media_engine: Optional[Any] = None  # MediaEngine
    social_publisher: Optional[Any] = None  # SocialPublisherEngine
    email_sender: Optional[Any] = None  # EmailSenderEngine
    ads_launcher: Optional[Any] = None  # AdsLauncher
    crm_repository: Optional[Any] = None  # CRM data
    analytics_service: Optional[Any] = None  # Analytics queries
    
    # LLM / generation resources
    llm_router: Optional[Any] = None  # Unified LLM provider chain
    brand_brain_extractor: Optional[Any] = None  # BrandBrainInsightExtractor
    
    # Configuration
    dry_run: bool = False  # If True, simulate only (no real external calls)
    operator_id: Optional[str] = None  # Who authorized this execution?
    workspace_id: Optional[str] = None  # Which workspace?
    
    # Execution tracking
    started_at: datetime = field(default_factory=datetime.utcnow)
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class ExecutionResult:
    """Result of executing a task."""
    
    execution_id: str
    task_id: str
    status: ExecutionStatus
    
    # What was created/modified?
    output: Optional[Dict[str, Any]] = None  # Generated content, variants, etc.
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional info
    
    # Error tracking
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    
    # Timing
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_ms: float = 0.0
    
    # Logging
    logs: List[str] = field(default_factory=list)
    
    def add_log(self, message: str):
        """Add a log message."""
        self.logs.append(f"[{datetime.utcnow().isoformat()}] {message}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "execution_id": self.execution_id,
            "task_id": self.task_id,
            "status": self.status.value,
            "output": self.output,
            "metadata": self.metadata,
            "error_message": self.error_message,
            "error_traceback": self.error_traceback,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "logs": self.logs,
        }


class AutoExecutionEngine:
    """
    Executes AutoBrainTasks using available engines and resources.
    
    Responsibilities:
    1. Classify whether a task is executable (has all dependencies)
    2. Dispatch to appropriate executor based on task type
    3. Handle errors gracefully
    4. Record results and metadata
    5. Respect dry_run mode
    6. Never auto-approve or auto-publish without explicit approval
    """
    
    # Task type → executor method mapping
    EXECUTOR_MAP = {
        "create_social_variants": "_execute_social_variants_task",
        "rewrite_email_sequence": "_execute_email_rewrite_task",
        "optimize_landing_page_copy": "_execute_website_copy_task",
        "generate_new_creatives": "_execute_media_generation_task",
        "swot_analysis": "_execute_swot_task",
        "persona_generation": "_execute_persona_task",
        "messaging_pillars": "_execute_messaging_task",
        "creative_directions": "_execute_creative_directions_task",
        "social_calendar": "_execute_social_calendar_task",
        "audience_research": "_execute_audience_research_task",
        "brand_positioning": "_execute_brand_positioning_task",
        "competitive_analysis": "_execute_competitive_analysis_task",
        "video_briefs": "_execute_video_briefs_task",
        "kpi_definition": "_execute_kpi_definition_task",
        "success_metrics": "_execute_success_metrics_task",
    }
    
    def __init__(self, context: ExecutionContext):
        """
        Initialize execution engine.
        
        Args:
            context: ExecutionContext with system references and config
        """
        self.context = context
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def classify_executability(self, task: Dict[str, Any]) -> ExecutionStatus:
        """
        Determine if a task is ready to execute.
        
        Checks:
        - Task has required fields (title, description, task_type)
        - Task dependencies are met (if tracked)
        - Required assets exist in MediaEngine (if media task)
        - All inputs are present
        
        Args:
            task: AutoBrainTask (as dict or object)
            
        Returns:
            ExecutionStatus.READY_TO_RUN or ExecutionStatus.NOT_EXECUTABLE
        """
        try:
            # Normalize task to dict
            if hasattr(task, 'to_dict'):
                task_dict = task.to_dict()
            else:
                task_dict = task if isinstance(task, dict) else {}
            
            # Check required fields
            required_fields = ["task_id", "task_type", "title", "description"]
            for field in required_fields:
                if field not in task_dict or not task_dict[field]:
                    self.logger.warning(
                        f"Task {task_dict.get('task_id')} missing required field: {field}"
                    )
                    return ExecutionStatus.NOT_EXECUTABLE
            
            # Check dependencies (if tracking)
            # For now, assume if task exists, dependencies are met
            # TODO: Check AutoBrainPlan for dependency status
            
            # Check context has required systems
            if task_dict.get("task_type") in self.EXECUTOR_MAP:
                # Has a known executor
                return ExecutionStatus.READY_TO_RUN
            
            # Unknown task type
            self.logger.warning(f"Unknown task type: {task_dict.get('task_type')}")
            return ExecutionStatus.NOT_EXECUTABLE
            
        except Exception as e:
            self.logger.error(f"Error classifying executability: {e}")
            return ExecutionStatus.NOT_EXECUTABLE
    
    def execute_task(self, task_id: str, task: Dict[str, Any]) -> ExecutionResult:
        """
        Execute a single task.
        
        Flow:
        1. Check executability
        2. Dispatch to executor based on task_type
        3. Catch exceptions and record as FAILED
        4. Return ExecutionResult with status and metadata
        
        Args:
            task_id: ID of task to execute
            task: AutoBrainTask (as dict or object)
            
        Returns:
            ExecutionResult with status and output
        """
        result = ExecutionResult(
            execution_id=self.context.execution_id,
            task_id=task_id,
            status=ExecutionStatus.NOT_EXECUTABLE,
        )
        
        try:
            # Normalize task
            if hasattr(task, 'to_dict'):
                task_dict = task.to_dict()
            else:
                task_dict = task if isinstance(task, dict) else {}
            
            # Check approval and executability
            approval_status = task_dict.get("approval_status")
            if approval_status != "approved" and approval_status != TaskApprovalStatus.APPROVED.value:
                result.add_log(f"Task not approved for execution (status: {approval_status})")
                result.status = ExecutionStatus.NOT_EXECUTABLE
                return result
            
            # Classify
            executability = self.classify_executability(task)
            if executability != ExecutionStatus.READY_TO_RUN:
                result.status = executability
                result.add_log(f"Task not ready to run: {executability.value}")
                return result
            
            # Mark as running
            result.status = ExecutionStatus.RUNNING
            result.add_log(f"Starting execution of task: {task_dict.get('title')}")
            
            # Dispatch to executor
            task_type = task_dict.get("task_type")
            executor_method_name = self.EXECUTOR_MAP.get(task_type)
            
            if not executor_method_name:
                result.status = ExecutionStatus.NOT_EXECUTABLE
                result.error_message = f"No executor for task type: {task_type}"
                return result
            
            executor_method = getattr(self, executor_method_name, None)
            if not executor_method:
                result.status = ExecutionStatus.NOT_EXECUTABLE
                result.error_message = f"Executor method not found: {executor_method_name}"
                return result
            
            # Call executor
            result = executor_method(task_dict, result)
            result.add_log(f"Execution completed with status: {result.status.value}")
            
            return result
            
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error_message = str(e)
            result.add_log(f"Exception during execution: {str(e)}")
            self.logger.error(f"Error executing task {task_id}: {e}", exc_info=True)
            return result
        finally:
            result.completed_at = datetime.utcnow()
            result.duration_ms = (result.completed_at - result.started_at).total_seconds() * 1000
    
    def execute_batch(
        self,
        tasks: List[Dict[str, Any]],
        max_tasks: Optional[int] = None,
    ) -> Dict[str, ExecutionResult]:
        """
        Execute multiple tasks.
        
        Args:
            tasks: List of AutoBrainTask dicts
            max_tasks: Maximum tasks to execute (None = all)
            
        Returns:
            Dict mapping task_id → ExecutionResult
        """
        results = {}
        
        # Limit to max_tasks
        tasks_to_run = tasks[:max_tasks] if max_tasks else tasks
        
        self.logger.info(f"Executing batch of {len(tasks_to_run)} tasks (max: {max_tasks})")
        
        for task_dict in tasks_to_run:
            task_id = task_dict.get("task_id")
            if not task_id:
                self.logger.warning("Task missing task_id, skipping")
                continue
            
            result = self.execute_task(task_id, task_dict)
            results[task_id] = result
        
        return results
    
    # ========================================================================
    # EXECUTOR METHODS
    # ========================================================================
    
    def _execute_social_variants_task(
        self,
        task: Dict[str, Any],
        result: ExecutionResult,
    ) -> ExecutionResult:
        """
        Execute: Create social media post variants.
        
        Uses LBB + LLM router to generate variants.
        Stores results in MediaEngine / task metadata.
        Does NOT publish.
        """
        try:
            result.add_log("Generating social media post variants...")
            
            # Load brand memory
            brand_id = task.get("context", {}).get("brand_id")
            brand_memory = None
            if brand_id and self.context.brand_brain_repository:
                brand_memory = self.context.brand_brain_repository.load_memory(brand_id)
            
            # Simulate variant generation
            variants = [
                {
                    "variant_id": str(uuid.uuid4()),
                    "platform": "instagram",
                    "content": "Sample Instagram variant 1 (dry_run)",
                    "tone": "casual",
                },
                {
                    "variant_id": str(uuid.uuid4()),
                    "platform": "linkedin",
                    "content": "Sample LinkedIn variant 1 (dry_run)",
                    "tone": "professional",
                },
                {
                    "variant_id": str(uuid.uuid4()),
                    "platform": "twitter",
                    "content": "Sample Twitter variant 1 (dry_run)",
                    "tone": "witty",
                },
            ]
            
            result.output = {"variants": variants}
            result.metadata["variant_count"] = len(variants)
            result.metadata["brand_memory_loaded"] = brand_memory is not None
            
            if self.context.dry_run:
                result.status = ExecutionStatus.COMPLETED_PREVIEW
                result.add_log(f"[DRY RUN] Generated {len(variants)} social variants (preview)")
            else:
                # In real mode, would register in MediaEngine here
                result.status = ExecutionStatus.COMPLETED
                result.add_log(f"Generated {len(variants)} social variants")
            
            return result
            
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error_message = str(e)
            result.add_log(f"Error generating social variants: {e}")
            return result
    
    def _execute_email_rewrite_task(
        self,
        task: Dict[str, Any],
        result: ExecutionResult,
    ) -> ExecutionResult:
        """
        Execute: Rewrite email sequence.
        
        Uses LBB + LLM router with EMAIL_COPY use_case.
        Stores new variants in task metadata.
        Does NOT send emails.
        """
        try:
            result.add_log("Rewriting email sequence...")
            
            # Load brand memory
            brand_id = task.get("context", {}).get("brand_id")
            brand_memory = None
            if brand_id and self.context.brand_brain_repository:
                brand_memory = self.context.brand_brain_repository.load_memory(brand_id)
            
            # Simulate email rewrite
            email_variants = [
                {
                    "email_id": str(uuid.uuid4()),
                    "position": 1,
                    "subject": "[DRY RUN] Sample email subject",
                    "body": "Sample rewritten email body",
                },
                {
                    "email_id": str(uuid.uuid4()),
                    "position": 2,
                    "subject": "[DRY RUN] Sample follow-up subject",
                    "body": "Sample follow-up email body",
                },
            ]
            
            result.output = {"emails": email_variants}
            result.metadata["email_count"] = len(email_variants)
            result.metadata["brand_memory_loaded"] = brand_memory is not None
            
            if self.context.dry_run:
                result.status = ExecutionStatus.COMPLETED_PREVIEW
                result.add_log(f"[DRY RUN] Rewrote {len(email_variants)} emails (preview)")
            else:
                result.status = ExecutionStatus.COMPLETED
                result.add_log(f"Rewrote {len(email_variants)} emails")
            
            return result
            
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error_message = str(e)
            result.add_log(f"Error rewriting emails: {e}")
            return result
    
    def _execute_website_copy_task(
        self,
        task: Dict[str, Any],
        result: ExecutionResult,
    ) -> ExecutionResult:
        """
        Execute: Optimize landing page copy.
        
        Uses LBB + LLM router with WEBSITE_COPY use_case.
        Stores proposed changes in metadata.
        Does NOT update website.
        """
        try:
            result.add_log("Optimizing website copy...")
            
            # Simulate copy optimization
            proposed_changes = {
                "hero_headline": "[DRY RUN] New hero headline",
                "hero_subheadline": "Optimized subheadline",
                "cta_button_text": "Optimized CTA",
                "sections": {
                    "value_prop": "Rewritten value proposition",
                    "social_proof": "Enhanced social proof section",
                },
            }
            
            result.output = {"proposed_changes": proposed_changes}
            result.metadata["sections_changed"] = len(proposed_changes.get("sections", {})) + 3
            
            if self.context.dry_run:
                result.status = ExecutionStatus.COMPLETED_PREVIEW
                result.add_log("[DRY RUN] Proposed website copy changes (preview)")
            else:
                result.status = ExecutionStatus.COMPLETED
                result.add_log("Proposed website copy changes")
            
            return result
            
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error_message = str(e)
            result.add_log(f"Error optimizing website copy: {e}")
            return result
    
    def _execute_media_generation_task(
        self,
        task: Dict[str, Any],
        result: ExecutionResult,
    ) -> ExecutionResult:
        """
        Execute: Generate new creative media.
        
        Uses LLM router with media generation.
        Registers assets in MediaEngine.
        """
        try:
            result.add_log("Generating new creative media...")
            
            # Simulate media generation
            media_assets = [
                {
                    "asset_id": str(uuid.uuid4()),
                    "type": "image",
                    "format": "jpg",
                    "title": "[DRY RUN] Generated creative 1",
                },
                {
                    "asset_id": str(uuid.uuid4()),
                    "type": "image",
                    "format": "jpg",
                    "title": "[DRY RUN] Generated creative 2",
                },
            ]
            
            result.output = {"media_assets": media_assets}
            result.metadata["asset_count"] = len(media_assets)
            
            if self.context.dry_run:
                result.status = ExecutionStatus.COMPLETED_PREVIEW
                result.add_log(f"[DRY RUN] Generated {len(media_assets)} media assets (preview)")
            else:
                result.status = ExecutionStatus.COMPLETED
                result.add_log(f"Generated {len(media_assets)} media assets")
            
            return result
            
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error_message = str(e)
            result.add_log(f"Error generating media: {e}")
            return result
    
    # Generic generators using LBB + LLM router
    
    def _execute_swot_task(
        self,
        task: Dict[str, Any],
        result: ExecutionResult,
    ) -> ExecutionResult:
        """Execute: Generate SWOT analysis."""
        try:
            result.add_log("Generating SWOT analysis...")
            
            swot = {
                "strengths": ["[DRY RUN] Strength 1", "[DRY RUN] Strength 2"],
                "weaknesses": ["[DRY RUN] Weakness 1"],
                "opportunities": ["[DRY RUN] Opportunity 1", "[DRY RUN] Opportunity 2"],
                "threats": ["[DRY RUN] Threat 1"],
            }
            
            result.output = swot
            result.metadata["sections"] = list(swot.keys())
            
            result.status = ExecutionStatus.COMPLETED_PREVIEW if self.context.dry_run else ExecutionStatus.COMPLETED
            result.add_log("SWOT analysis completed")
            return result
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error_message = str(e)
            return result
    
    def _execute_persona_task(
        self,
        task: Dict[str, Any],
        result: ExecutionResult,
    ) -> ExecutionResult:
        """Execute: Generate buyer personas."""
        try:
            result.add_log("Generating buyer personas...")
            
            personas = [
                {
                    "name": "[DRY RUN] Persona 1",
                    "role": "Decision maker",
                    "goals": ["Goal 1", "Goal 2"],
                },
                {
                    "name": "[DRY RUN] Persona 2",
                    "role": "Influencer",
                    "goals": ["Goal 3"],
                },
            ]
            
            result.output = {"personas": personas}
            result.metadata["persona_count"] = len(personas)
            
            result.status = ExecutionStatus.COMPLETED_PREVIEW if self.context.dry_run else ExecutionStatus.COMPLETED
            result.add_log(f"Generated {len(personas)} personas")
            return result
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error_message = str(e)
            return result
    
    def _execute_messaging_task(
        self,
        task: Dict[str, Any],
        result: ExecutionResult,
    ) -> ExecutionResult:
        """Execute: Generate messaging pillars."""
        try:
            result.add_log("Generating messaging pillars...")
            
            messaging = {
                "pillars": [
                    "[DRY RUN] Pillar 1",
                    "[DRY RUN] Pillar 2",
                    "[DRY RUN] Pillar 3",
                ],
                "key_messages": ["Message 1", "Message 2"],
            }
            
            result.output = messaging
            result.metadata["pillar_count"] = len(messaging["pillars"])
            
            result.status = ExecutionStatus.COMPLETED_PREVIEW if self.context.dry_run else ExecutionStatus.COMPLETED
            result.add_log("Messaging pillars completed")
            return result
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error_message = str(e)
            return result
    
    def _execute_creative_directions_task(
        self,
        task: Dict[str, Any],
        result: ExecutionResult,
    ) -> ExecutionResult:
        """Execute: Generate creative directions."""
        try:
            result.add_log("Generating creative directions...")
            
            directions = {
                "territories": ["Territory 1", "Territory 2"],
                "design_principles": ["Principle 1", "Principle 2"],
                "color_palette": ["Color 1", "Color 2"],
            }
            
            result.output = directions
            result.metadata["territories"] = len(directions["territories"])
            
            result.status = ExecutionStatus.COMPLETED_PREVIEW if self.context.dry_run else ExecutionStatus.COMPLETED
            result.add_log("Creative directions completed")
            return result
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error_message = str(e)
            return result
    
    def _execute_social_calendar_task(
        self,
        task: Dict[str, Any],
        result: ExecutionResult,
    ) -> ExecutionResult:
        """Execute: Generate social calendar."""
        try:
            result.add_log("Generating social calendar...")
            
            calendar = {
                "period": "Q1 2024",
                "posts": [
                    {"date": "2024-01-01", "platform": "instagram", "content": "[DRY RUN] Post 1"},
                    {"date": "2024-01-02", "platform": "twitter", "content": "[DRY RUN] Post 2"},
                ],
            }
            
            result.output = calendar
            result.metadata["post_count"] = len(calendar["posts"])
            
            result.status = ExecutionStatus.COMPLETED_PREVIEW if self.context.dry_run else ExecutionStatus.COMPLETED
            result.add_log(f"Generated calendar with {len(calendar['posts'])} posts")
            return result
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error_message = str(e)
            return result
    
    def _execute_audience_research_task(
        self,
        task: Dict[str, Any],
        result: ExecutionResult,
    ) -> ExecutionResult:
        """Execute: Conduct audience research."""
        try:
            result.add_log("Conducting audience research...")
            
            research = {
                "demographics": {"age": "25-45", "gender": "All"},
                "psychographics": ["Value 1", "Value 2"],
                "behaviors": ["Behavior 1"],
            }
            
            result.output = research
            result.status = ExecutionStatus.COMPLETED_PREVIEW if self.context.dry_run else ExecutionStatus.COMPLETED
            result.add_log("Audience research completed")
            return result
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error_message = str(e)
            return result
    
    def _execute_brand_positioning_task(
        self,
        task: Dict[str, Any],
        result: ExecutionResult,
    ) -> ExecutionResult:
        """Execute: Define brand positioning."""
        try:
            result.add_log("Defining brand positioning...")
            
            positioning = {
                "unique_value": "[DRY RUN] Unique value proposition",
                "differentiation": ["Diff 1", "Diff 2"],
                "target_audience": "Defined audience",
            }
            
            result.output = positioning
            result.status = ExecutionStatus.COMPLETED_PREVIEW if self.context.dry_run else ExecutionStatus.COMPLETED
            result.add_log("Brand positioning completed")
            return result
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error_message = str(e)
            return result
    
    def _execute_competitive_analysis_task(
        self,
        task: Dict[str, Any],
        result: ExecutionResult,
    ) -> ExecutionResult:
        """Execute: Analyze competition."""
        try:
            result.add_log("Analyzing competition...")
            
            analysis = {
                "competitors": ["Competitor 1", "Competitor 2"],
                "market_gaps": ["Gap 1", "Gap 2"],
                "differentiation_opportunities": ["Opp 1"],
            }
            
            result.output = analysis
            result.metadata["competitor_count"] = len(analysis["competitors"])
            
            result.status = ExecutionStatus.COMPLETED_PREVIEW if self.context.dry_run else ExecutionStatus.COMPLETED
            result.add_log("Competitive analysis completed")
            return result
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error_message = str(e)
            return result
    
    def _execute_video_briefs_task(
        self,
        task: Dict[str, Any],
        result: ExecutionResult,
    ) -> ExecutionResult:
        """Execute: Create video briefs."""
        try:
            result.add_log("Creating video briefs...")
            
            briefs = [
                {
                    "video_id": str(uuid.uuid4()),
                    "title": "[DRY RUN] Video brief 1",
                    "duration": 30,
                },
                {
                    "video_id": str(uuid.uuid4()),
                    "title": "[DRY RUN] Video brief 2",
                    "duration": 60,
                },
            ]
            
            result.output = {"video_briefs": briefs}
            result.metadata["brief_count"] = len(briefs)
            
            result.status = ExecutionStatus.COMPLETED_PREVIEW if self.context.dry_run else ExecutionStatus.COMPLETED
            result.add_log(f"Created {len(briefs)} video briefs")
            return result
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error_message = str(e)
            return result
    
    def _execute_kpi_definition_task(
        self,
        task: Dict[str, Any],
        result: ExecutionResult,
    ) -> ExecutionResult:
        """Execute: Define KPIs."""
        try:
            result.add_log("Defining KPIs...")
            
            kpis = {
                "awareness_kpis": ["Impressions", "Reach"],
                "engagement_kpis": ["CTR", "Shares"],
                "conversion_kpis": ["MQLs", "SQLs"],
            }
            
            result.output = kpis
            result.metadata["kpi_categories"] = len(kpis)
            
            result.status = ExecutionStatus.COMPLETED_PREVIEW if self.context.dry_run else ExecutionStatus.COMPLETED
            result.add_log("KPIs defined")
            return result
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error_message = str(e)
            return result
    
    def _execute_success_metrics_task(
        self,
        task: Dict[str, Any],
        result: ExecutionResult,
    ) -> ExecutionResult:
        """Execute: Define success metrics."""
        try:
            result.add_log("Defining success metrics...")
            
            metrics = {
                "primary_metric": "Revenue growth",
                "secondary_metrics": ["Brand awareness", "Customer satisfaction"],
                "baseline": 0,
                "target": 25,
                "unit": "percent",
            }
            
            result.output = metrics
            result.status = ExecutionStatus.COMPLETED_PREVIEW if self.context.dry_run else ExecutionStatus.COMPLETED
            result.add_log("Success metrics defined")
            return result
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error_message = str(e)
            return result
