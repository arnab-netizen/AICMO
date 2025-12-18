"""
Generation Plan & Job Queue System

Converts UI checkboxes into a structured job DAG for the Autonomy module.
Each job specifies module, priority, dependencies, and execution context.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Set
from enum import Enum
import uuid


# ===================================================================
# CREATIVE-DEPENDENT EXECUTION JOBS
# ===================================================================
# Execution jobs that require visual/design assets from Creatives

CREATIVE_DEPENDENT_EXECUTION_JOBS = {
    "ig_posts_week1",           # Needs carousel/reel templates
    "fb_posts_week1",            # Needs image packs
    "reels_scripts_week1",       # Needs reel covers, thumbnails
    "content_calendar_week1",    # Needs full asset inventory
}

# Execution jobs that can proceed with text-only content (no creatives required)
TEXT_ONLY_EXECUTION_JOBS = {
    "linkedin_posts_week1",      # Professional text posts
    "hashtag_sets",              # Text-only optimization
    "email_sequence",            # Text-based email content
}


class JobModule(str, Enum):
    """Job modules matching artifact types"""
    STRATEGY = "strategy"
    CREATIVES = "creatives"
    EXECUTION = "execution"
    MONITORING = "monitoring"
    DELIVERY = "delivery"


class JobStatus(str, Enum):
    """Job execution status"""
    PENDING = "pending"
    READY = "ready"  # All dependencies satisfied
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"  # Dependencies not met


@dataclass
class Job:
    """Single generation job"""
    job_id: str
    module: JobModule
    job_type: str  # E.g., "icp_definition", "carousel_templates", etc.
    priority: int  # Lower number = higher priority
    depends_on: List[str] = field(default_factory=list)  # List of job_ids
    status: JobStatus = JobStatus.PENDING
    context: Dict[str, Any] = field(default_factory=dict)  # Job-specific parameters
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        """Create from dict"""
        if isinstance(data.get('module'), str):
            data['module'] = JobModule(data['module'])
        if isinstance(data.get('status'), str):
            data['status'] = JobStatus(data['status'])
        return cls(**data)


@dataclass
class GenerationPlan:
    """Complete generation plan with job DAG"""
    plan_id: str
    client_id: str
    engagement_id: str
    jobs: List[Job] = field(default_factory=list)
    created_at: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            "plan_id": self.plan_id,
            "client_id": self.client_id,
            "engagement_id": self.engagement_id,
            "jobs": [j.to_dict() for j in self.jobs],
            "created_at": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GenerationPlan':
        """Create from dict"""
        jobs = [Job.from_dict(j) for j in data.get('jobs', [])]
        return cls(
            plan_id=data['plan_id'],
            client_id=data['client_id'],
            engagement_id=data['engagement_id'],
            jobs=jobs,
            created_at=data.get('created_at', '')
        )
    
    def get_ready_jobs(self) -> List[Job]:
        """Get jobs that are ready to run (all dependencies completed)"""
        ready = []
        completed_ids = {j.job_id for j in self.jobs if j.status == JobStatus.COMPLETED}
        
        for job in self.jobs:
            if job.status == JobStatus.PENDING:
                # Check if all dependencies are completed
                deps_met = all(dep_id in completed_ids for dep_id in job.depends_on)
                if deps_met:
                    ready.append(job)
        
        # Sort by priority
        ready.sort(key=lambda j: j.priority)
        return ready
    
    def get_next_job(self) -> Optional[Job]:
        """Get next ready job to run"""
        ready = self.get_ready_jobs()
        return ready[0] if ready else None


# ===================================================================
# UPSTREAM DEPENDENCY RESOLUTION
# ===================================================================

def required_upstreams_for(artifact_type: str, selected_job_ids: Optional[List[str]] = None) -> Set[str]:
    """
    Determine required upstream artifact types for a given artifact type.
    
    Args:
        artifact_type: Target artifact type (strategy, creatives, execution, etc.)
        selected_job_ids: Optional list of selected job IDs (for execution/delivery dependency resolution)
    
    Returns:
        Set of required upstream artifact type strings (e.g., {"intake", "strategy"})
    
    Rules:
        - Strategy always requires: {intake}
        - Creatives always requires: {strategy}
        - Execution always requires: {strategy}
        - Execution conditionally requires: {creatives} if any selected_job_ids are creative-dependent
        - Monitoring requires: {execution}
        - Delivery CONDITIONALLY requires upstream artifacts based on what was generated:
          * Strategy-only plan: {strategy}
          * Strategy + Creatives: {strategy, creatives}
          * Strategy + Creatives + Execution: {strategy, creatives, execution}
          * Execution-only plan (rare): {strategy, execution}
    """
    selected_job_ids = selected_job_ids or []
    
    if artifact_type == "strategy":
        return {"intake"}
    
    elif artifact_type == "creatives":
        return {"strategy"}
    
    elif artifact_type == "execution":
        # Strategy is always required
        required = {"strategy"}
        
        # Check if any selected jobs are creative-dependent
        if any(job_id in CREATIVE_DEPENDENT_EXECUTION_JOBS for job_id in selected_job_ids):
            required.add("creatives")
        
        return required
    
    elif artifact_type == "monitoring":
        return {"execution"}
    
    elif artifact_type == "delivery":
        # CONDITIONAL LOGIC: Delivery packages what was generated
        # Inspect selected_job_ids to determine generation plan scope
        
        # Strategy is always required (Delivery always needs at least strategy)
        required = {"strategy"}
        
        # Check if creative jobs were selected (any job name containing "creative" or known creative jobs)
        creative_job_indicators = [
            "creative", "creatives", "asset", "content_library", "copy", "visual",
            "reel_covers", "image_prompts", "video_scripts", "thumbnails"
        ]
        has_creative_jobs = any(
            any(indicator in job_id.lower() for indicator in creative_job_indicators)
            for job_id in selected_job_ids
        )
        
        if has_creative_jobs:
            required.add("creatives")
        
        # Check if execution jobs were selected (any job containing "execution", "schedule", "calendar")
        execution_job_indicators = [
            "execution", "schedule", "calendar", "utm", "posts_week", "cadence"
        ]
        has_execution_jobs = any(
            any(indicator in job_id.lower() for indicator in execution_job_indicators)
            for job_id in selected_job_ids
        )
        
        if has_execution_jobs:
            required.add("execution")
        
        # Fallback: If no job IDs provided (legacy), default to SAFE minimum
        # Rationale: Prevents deadlocks from requiring all upstreams
        # QC will emit WARN for missing plan (visibility requirement)
        if not selected_job_ids:
            required = {"intake", "strategy"}
        
        return required
    
    else:
        # Intake, leadgen, or unknown types have no upstream requirements
        return set()


# ===================================================================
# GENERATION PLAN BUILDER
# ===================================================================

def build_generation_plan_from_checkboxes(
    client_id: str,
    engagement_id: str,
    strategy_jobs: List[str],
    creative_jobs: List[str],
    execution_jobs: List[str],
    monitoring_jobs: List[str],
    delivery_jobs: List[str]
) -> GenerationPlan:
    """
    Build generation plan from UI checkbox selections.
    
    Args:
        *_jobs: List of selected job types for each module
    
    Returns:
        GenerationPlan with jobs in dependency order
    """
    from datetime import datetime
    
    plan = GenerationPlan(
        plan_id=str(uuid.uuid4()),
        client_id=client_id,
        engagement_id=engagement_id,
        created_at=datetime.utcnow().isoformat()
    )
    
    # Priority scheme: Strategy (0-99), Creatives (100-199), Execution (200-299), Monitoring (300-399), Delivery (400-499)
    
    # ─── Strategy Jobs ───
    strategy_job_ids = {}
    base_priority = 0
    
    for idx, job_type in enumerate(strategy_jobs):
        job_id = str(uuid.uuid4())
        strategy_job_ids[job_type] = job_id
        
        job = Job(
            job_id=job_id,
            module=JobModule.STRATEGY,
            job_type=job_type,
            priority=base_priority + idx,
            depends_on=[],  # Strategy jobs don't depend on each other
            context={"module": "strategy", "type": job_type}
        )
        plan.jobs.append(job)
    
    # ─── Creative Jobs ───
    creative_job_ids = {}
    base_priority = 100
    
    # Creatives depend on strategy completion
    strategy_deps = list(strategy_job_ids.values())
    
    for idx, job_type in enumerate(creative_jobs):
        job_id = str(uuid.uuid4())
        creative_job_ids[job_type] = job_id
        
        job = Job(
            job_id=job_id,
            module=JobModule.CREATIVES,
            job_type=job_type,
            priority=base_priority + idx,
            depends_on=strategy_deps,  # Depend on all strategy jobs
            context={"module": "creatives", "type": job_type}
        )
        plan.jobs.append(job)
    
    # ─── Execution Jobs ───
    execution_job_ids = {}
    base_priority = 200
    
    # Execution depends on strategy + creatives
    execution_deps = list(strategy_job_ids.values()) + list(creative_job_ids.values())
    
    for idx, job_type in enumerate(execution_jobs):
        job_id = str(uuid.uuid4())
        execution_job_ids[job_type] = job_id
        
        job = Job(
            job_id=job_id,
            module=JobModule.EXECUTION,
            job_type=job_type,
            priority=base_priority + idx,
            depends_on=execution_deps,
            context={"module": "execution", "type": job_type}
        )
        plan.jobs.append(job)
    
    # ─── Monitoring Jobs ───
    monitoring_job_ids = {}
    base_priority = 300
    
    # Monitoring depends on execution
    monitoring_deps = list(execution_job_ids.values())
    
    for idx, job_type in enumerate(monitoring_jobs):
        job_id = str(uuid.uuid4())
        monitoring_job_ids[job_type] = job_id
        
        job = Job(
            job_id=job_id,
            module=JobModule.MONITORING,
            job_type=job_type,
            priority=base_priority + idx,
            depends_on=monitoring_deps,
            context={"module": "monitoring", "type": job_type}
        )
        plan.jobs.append(job)
    
    # ─── Delivery Jobs ───
    delivery_job_ids = {}
    base_priority = 400
    
    # Delivery depends on all upstream artifacts
    delivery_deps = (
        list(strategy_job_ids.values()) +
        list(creative_job_ids.values()) +
        list(execution_job_ids.values())
    )
    
    for idx, job_type in enumerate(delivery_jobs):
        job_id = str(uuid.uuid4())
        delivery_job_ids[job_type] = job_id
        
        job = Job(
            job_id=job_id,
            module=JobModule.DELIVERY,
            job_type=job_type,
            priority=base_priority + idx,
            depends_on=delivery_deps,
            context={"module": "delivery", "type": job_type}
        )
        plan.jobs.append(job)
    
    return plan


# ===================================================================
# JOB TYPE DEFINITIONS
# ===================================================================

STRATEGY_JOB_TYPES = [
    "icp_definition",
    "positioning",
    "messaging_framework",
    "content_pillars",
    "platform_strategy",
    "measurement_plan"
]

CREATIVE_JOB_TYPES = [
    "brand_kit_suggestions",
    "carousel_templates",
    "reel_cover_templates",
    "image_pack_prompts",
    "video_scripts",
    "thumbnails_banners"
]

EXECUTION_JOB_TYPES = [
    "content_calendar_week1",
    "ig_posts_week1",
    "fb_posts_week1",
    "linkedin_posts_week1",
    "reels_scripts_week1",
    "hashtag_sets",
    "email_sequence"
]

MONITORING_JOB_TYPES = [
    "tracking_checklist",
    "weekly_optimization"
]

DELIVERY_JOB_TYPES = [
    "pdf_report",
    "pptx_deck",
    "asset_zip"
]
