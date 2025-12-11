"""
AutoBrainTaskScanner: Detects what work needs to be done.

Scans briefs to determine:
1. What tasks are needed (based on brief content, goals, industry)
2. What's already been done (based on generation history)
3. What's blocked (dependencies not met)
4. What's highest priority (goals, time constraints, ROI)
"""

import logging
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Set
from collections import defaultdict

from aicmo.agency.auto_brain import (
    AutoBrainTask,
    AutoBrainPlan,
    TaskType,
    TaskPriority,
    TaskStatus,
    TaskDependency,
)
from aicmo.io.client_reports import ClientInputBrief
from aicmo.brand.memory import BrandMemory

logger = logging.getLogger(__name__)


class AutoBrainTaskScanner:
    """
    Automatically detects tasks needed to complete a brief.
    
    Detection is based on:
    - Brief content (goals, audience, platforms, etc.)
    - What's already generated (brand memory)
    - Industry best practices (task dependencies)
    - Time/resource constraints
    """
    
    # Task dependency graph: what tasks must come before others
    TASK_DEPENDENCIES = {
        TaskType.SWOT_ANALYSIS: [],  # No dependencies
        TaskType.PERSONA_GENERATION: [],  # No dependencies
        TaskType.AUDIENCE_RESEARCH: [],  # No dependencies
        
        TaskType.MESSAGING_PILLARS: [
            TaskDependency(TaskType.SWOT_ANALYSIS, "Need to understand market position"),
            TaskDependency(TaskType.PERSONA_GENERATION, "Need to understand audience"),
        ],
        TaskType.BRAND_POSITIONING: [
            TaskDependency(TaskType.SWOT_ANALYSIS, "Need market analysis"),
            TaskDependency(TaskType.COMPETITIVE_ANALYSIS, "Need competitive landscape"),
        ],
        TaskType.COMPETITIVE_ANALYSIS: [
            TaskDependency(TaskType.SWOT_ANALYSIS, "SWOT includes competitors"),
        ],
        
        TaskType.CREATIVE_DIRECTIONS: [
            TaskDependency(TaskType.MESSAGING_PILLARS, "Creative must align with messaging"),
            TaskDependency(TaskType.PERSONA_GENERATION, "Creative must resonate with personas"),
        ],
        TaskType.CREATIVE_VARIANTS: [
            TaskDependency(TaskType.CREATIVE_DIRECTIONS, "Variants build on directions"),
        ],
        TaskType.BRAND_GUIDELINES: [
            TaskDependency(TaskType.BRAND_POSITIONING, "Guidelines based on positioning"),
        ],
        
        TaskType.SOCIAL_CALENDAR: [
            TaskDependency(TaskType.MESSAGING_PILLARS, "Social posts follow messaging"),
            TaskDependency(TaskType.PERSONA_GENERATION, "Know who to target"),
        ],
        TaskType.VIDEO_BRIEFS: [
            TaskDependency(TaskType.CREATIVE_DIRECTIONS, "Video directions defined first"),
        ],
        TaskType.EMAIL_CAMPAIGNS: [
            TaskDependency(TaskType.MESSAGING_PILLARS, "Email follows messaging"),
            TaskDependency(TaskType.PERSONA_GENERATION, "Emails targeted to personas"),
        ],
        
        TaskType.KPI_DEFINITION: [
            TaskDependency(TaskType.BRAND_POSITIONING, "KPIs from positioning"),
        ],
        TaskType.SUCCESS_METRICS: [
            TaskDependency(TaskType.KPI_DEFINITION, "Metrics define success"),
        ],
        TaskType.ANALYTICS_SETUP: [
            TaskDependency(TaskType.SUCCESS_METRICS, "Track what matters"),
        ],
    }
    
    # Task definitions: title, description, estimated time
    TASK_DEFINITIONS = {
        TaskType.SWOT_ANALYSIS: {
            "title": "SWOT Analysis",
            "description": "Analyze market Strengths, Weaknesses, Opportunities, Threats",
            "min_minutes": 5,
            "max_minutes": 20,
            "generators": ["swot_generator"],
        },
        TaskType.PERSONA_GENERATION: {
            "title": "Buyer Personas",
            "description": "Create detailed buyer personas for target audience",
            "min_minutes": 10,
            "max_minutes": 30,
            "generators": ["persona_generator"],
        },
        TaskType.AUDIENCE_RESEARCH: {
            "title": "Audience Research",
            "description": "Deep dive into audience demographics, psychographics, behaviors",
            "min_minutes": 15,
            "max_minutes": 45,
            "generators": ["audience_research_generator"],
        },
        
        TaskType.MESSAGING_PILLARS: {
            "title": "Messaging Pillars",
            "description": "Develop core messaging pillars and talking points",
            "min_minutes": 5,
            "max_minutes": 15,
            "generators": ["messaging_pillars_generator"],
        },
        TaskType.BRAND_POSITIONING: {
            "title": "Brand Positioning",
            "description": "Define unique brand positioning and value proposition",
            "min_minutes": 10,
            "max_minutes": 20,
            "generators": ["brand_positioning_generator"],
        },
        TaskType.COMPETITIVE_ANALYSIS: {
            "title": "Competitive Analysis",
            "description": "Analyze competitors and differentiation opportunities",
            "min_minutes": 10,
            "max_minutes": 25,
            "generators": ["competitive_analysis_generator"],
        },
        
        TaskType.CREATIVE_DIRECTIONS: {
            "title": "Creative Directions",
            "description": "Define creative territories and design directions",
            "min_minutes": 10,
            "max_minutes": 30,
            "generators": ["directions_engine"],
        },
        TaskType.CREATIVE_VARIANTS: {
            "title": "Creative Variants",
            "description": "Generate creative variations and alternatives",
            "min_minutes": 10,
            "max_minutes": 25,
            "generators": ["creative_variants_generator"],
        },
        TaskType.BRAND_GUIDELINES: {
            "title": "Brand Guidelines",
            "description": "Document brand visual and tone guidelines",
            "min_minutes": 15,
            "max_minutes": 40,
            "generators": ["brand_guidelines_generator"],
        },
        
        TaskType.SOCIAL_CALENDAR: {
            "title": "Social Calendar",
            "description": "Generate social media post calendar (7+ days planned)",
            "min_minutes": 5,
            "max_minutes": 15,
            "generators": ["social_calendar_generator"],
        },
        TaskType.VIDEO_BRIEFS: {
            "title": "Video Briefs",
            "description": "Create briefs for video production or editing",
            "min_minutes": 15,
            "max_minutes": 30,
            "generators": ["video_brief_generator"],
        },
        TaskType.EMAIL_CAMPAIGNS: {
            "title": "Email Campaigns",
            "description": "Design email campaign sequences and templates",
            "min_minutes": 15,
            "max_minutes": 40,
            "generators": ["email_campaign_generator"],
        },
        
        TaskType.KPI_DEFINITION: {
            "title": "KPI Definition",
            "description": "Define key performance indicators for campaign",
            "min_minutes": 10,
            "max_minutes": 20,
            "generators": ["kpi_generator"],
        },
        TaskType.SUCCESS_METRICS: {
            "title": "Success Metrics",
            "description": "Define success metrics and measurement approach",
            "min_minutes": 10,
            "max_minutes": 20,
            "generators": ["metrics_generator"],
        },
        TaskType.ANALYTICS_SETUP: {
            "title": "Analytics Setup",
            "description": "Configure analytics tracking and dashboards",
            "min_minutes": 20,
            "max_minutes": 45,
            "generators": ["analytics_generator"],
        },
    }
    
    def __init__(self):
        """Initialize the task scanner."""
        pass
    
    def scan_brief(
        self,
        brief: ClientInputBrief,
        brand_id: str,
        brand_memory: Optional[BrandMemory] = None,
        time_budget_minutes: Optional[int] = None,
    ) -> AutoBrainPlan:
        """
        Scan a brief and create a task plan.
        
        Args:
            brief: The ClientInputBrief to analyze
            brand_id: Which brand this is for
            brand_memory: Existing brand memory (to avoid duplicate work)
            time_budget_minutes: If set, prioritize to fit in this time
        
        Returns:
            AutoBrainPlan with detected tasks ordered by priority
        """
        plan = AutoBrainPlan(
            plan_id=str(uuid.uuid4()),
            brand_id=brand_id,
            brief_id=getattr(brief, "brief_id", None),
        )
        
        # Detect what work is needed
        detected_tasks = self._detect_needed_tasks(brief, brand_memory)
        
        # Assess what's already done
        already_done = self._assess_completed_tasks(brand_memory)
        
        # Build task list (only add tasks not already done)
        for task_type, context in detected_tasks.items():
            if task_type not in already_done:
                task = self._create_task(task_type, context)
                plan.tasks.append(task)
        
        # Set dependencies
        for task in plan.tasks:
            task.dependencies = self.TASK_DEPENDENCIES.get(task.task_type, [])
        
        # Calculate total time and priority
        plan.total_estimated_minutes = sum(t.estimated_minutes for t in plan.tasks)
        
        # Adjust for time budget if specified
        if time_budget_minutes:
            plan = self._prioritize_for_time_budget(plan, time_budget_minutes)
        
        # Organize into phases
        plan.phase_count = len(plan.get_tasks_by_phase())
        
        # Count priorities
        plan.critical_count = sum(1 for t in plan.tasks if t.priority == TaskPriority.CRITICAL)
        plan.high_count = sum(1 for t in plan.tasks if t.priority == TaskPriority.HIGH)
        
        logger.info(
            f"Scanned brief {getattr(brief, 'brief_id', 'unknown')}: "
            f"Found {len(plan.tasks)} tasks ({plan.total_estimated_minutes}m total)"
        )
        
        return plan
    
    def _detect_needed_tasks(
        self,
        brief: ClientInputBrief,
        brand_memory: Optional[BrandMemory] = None,
    ) -> Dict[TaskType, Dict[str, str]]:
        """Detect which tasks are needed based on brief content."""
        needed: Dict[TaskType, Dict[str, str]] = {}
        
        # Strategy tasks (always needed)
        needed[TaskType.SWOT_ANALYSIS] = {"reason": "Foundation for all strategy"}
        needed[TaskType.PERSONA_GENERATION] = {"reason": "Understand audience"}
        
        # If brand new and has positioning goal
        if brief.goal and brief.goal.primary_goal:
            goal_lower = brief.goal.primary_goal.lower()
            
            if "position" in goal_lower or "differentiate" in goal_lower:
                needed[TaskType.BRAND_POSITIONING] = {"reason": "Explicit positioning goal"}
            
            if "message" in goal_lower or "communicate" in goal_lower:
                needed[TaskType.MESSAGING_PILLARS] = {"reason": "Explicit messaging goal"}
        
        # If has platforms/channels
        if brief.platform and brief.platform.platform_list:
            platforms = [p.lower() for p in brief.platform.platform_list]
            
            if any(p in platforms for p in ["instagram", "tiktok", "twitter", "facebook", "linkedin"]):
                needed[TaskType.SOCIAL_CALENDAR] = {"reason": "Social platforms selected"}
            
            if "email" in platforms:
                needed[TaskType.EMAIL_CAMPAIGNS] = {"reason": "Email in platform list"}
        
        # If creative goal
        if brief.goal and brief.goal.primary_goal:
            goal_lower = brief.goal.primary_goal.lower()
            if any(w in goal_lower for w in ["creative", "design", "visual", "brand"]):
                needed[TaskType.CREATIVE_DIRECTIONS] = {"reason": "Creative goals detected"}
        
        # Measurement (always good to have)
        needed[TaskType.KPI_DEFINITION] = {"reason": "Define success metrics"}
        
        return needed
    
    def _assess_completed_tasks(self, brand_memory: Optional[BrandMemory] = None) -> Set[TaskType]:
        """Assess which tasks have already been completed."""
        completed: Set[TaskType] = set()
        
        if not brand_memory:
            return completed
        
        # Map generator types to task types
        generator_to_task = {
            "swot_generator": TaskType.SWOT_ANALYSIS,
            "persona_generator": TaskType.PERSONA_GENERATION,
            "messaging_pillars_generator": TaskType.MESSAGING_PILLARS,
            "social_calendar_generator": TaskType.SOCIAL_CALENDAR,
            "directions_engine": TaskType.CREATIVE_DIRECTIONS,
        }
        
        # Check what generators have been run
        for record in brand_memory.generation_history:
            if record.generator_type in generator_to_task:
                completed.add(generator_to_task[record.generator_type])
        
        return completed
    
    def _create_task(self, task_type: TaskType, context: Dict[str, str]) -> AutoBrainTask:
        """Create an AutoBrainTask from a task type."""
        defn = self.TASK_DEFINITIONS[task_type]
        
        # Determine priority based on task type
        if task_type in [TaskType.SWOT_ANALYSIS, TaskType.PERSONA_GENERATION]:
            priority = TaskPriority.CRITICAL  # Foundation tasks
        elif task_type in [TaskType.MESSAGING_PILLARS, TaskType.BRAND_POSITIONING]:
            priority = TaskPriority.HIGH  # Strategy tasks
        elif task_type in [TaskType.CREATIVE_DIRECTIONS, TaskType.SOCIAL_CALENDAR]:
            priority = TaskPriority.HIGH  # Execution tasks
        else:
            priority = TaskPriority.MEDIUM
        
        return AutoBrainTask(
            task_id=str(uuid.uuid4()),
            task_type=task_type,
            title=defn["title"],
            description=defn["description"],
            priority=priority,
            estimated_minutes=(defn["min_minutes"] + defn["max_minutes"]) // 2,
            min_estimated_minutes=defn["min_minutes"],
            max_estimated_minutes=defn["max_minutes"],
            detection_reason=context.get("reason", ""),
            related_generators=defn["generators"],
            confidence=0.8,
        )
    
    def _prioritize_for_time_budget(
        self,
        plan: AutoBrainPlan,
        time_budget_minutes: int
    ) -> AutoBrainPlan:
        """
        Adjust priorities if time budget is tight.
        Prioritize high-ROI tasks that fit in the budget.
        """
        total = sum(t.estimated_minutes for t in plan.tasks)
        
        if total <= time_budget_minutes:
            return plan  # Everything fits
        
        # Need to deprioritize low-ROI tasks
        # Sort tasks: keep foundation (critical) and drop low-priority (optional)
        for task in plan.tasks:
            if task.estimated_minutes > time_budget_minutes // 2:
                # Too expensive, deprioritize
                if task.priority == TaskPriority.LOW:
                    task.priority = TaskPriority.OPTIONAL
        
        return plan
