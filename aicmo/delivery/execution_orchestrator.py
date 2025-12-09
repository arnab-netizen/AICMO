"""
Execution Orchestrator — Safe Content/Plan Execution Layer.

Phase 3: Safe orchestration for executing marketing plans and content delivery.

This module implements controlled execution of strategy/content plans:
- Execute strategy recommendations across channels (email, social, CRM)
- Respect execution_enabled flag (default: False = no send)
- Respect dry_run mode (default: True = preview only)
- Track execution results with ExecutionResult domain model
- Log all events via learning system
- Handle failures gracefully (no exceptions raised from main function)

All operations are wrapped in safety limits and enabled flags.
By default, execution_enabled=False ensures no real content is sent.
By default, dry_run=True ensures operations are previewed without side effects.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import logging
import os

from aicmo.domain.execution import ExecutionResult, ExecutionStatus
from aicmo.domain.project import Project
from aicmo.gateways import get_email_sender, get_social_poster, get_crm_syncer
from aicmo.memory.engine import log_event


logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# CONFIG AND REPORT DATACLASSES
# ═══════════════════════════════════════════════════════════════════════


@dataclass
class ExecutionConfig:
    """
    Configuration for plan execution.
    
    Controls whether execution is allowed and whether operations are dry-run.
    """
    
    execution_enabled: bool = False  # DEFAULT: Never execute
    dry_run: bool = True  # DEFAULT: Preview-only mode
    channels_enabled: List[str] = field(default_factory=lambda: ["email"])


@dataclass
class ExecutionReport:
    """
    Report of plan execution for a project.
    
    Captures counts and errors from execution phases.
    """
    
    project_id: str
    total_items_processed: int = 0
    items_sent_successfully: int = 0
    items_failed: int = 0
    channels_used: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    execution_results: List[ExecutionResult] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════
# CONFIG READER FUNCTION
# ═══════════════════════════════════════════════════════════════════════


def get_execution_config() -> ExecutionConfig:
    """
    Read execution configuration from environment or use defaults.
    
    Environment variables:
    - EXECUTION_ENABLED (bool): Whether execution is enabled (default: False)
    - EXECUTION_DRY_RUN (bool): Whether to run in dry-run mode (default: True)
    - EXECUTION_CHANNELS (str): Comma-separated list of enabled channels (default: "email")
    
    Returns:
        ExecutionConfig with loaded or default values
        
    Example:
        config = get_execution_config()
        # EXECUTION_ENABLED=true EXECUTION_DRY_RUN=false to enable real execution
    """
    
    # Read from environment with safe defaults
    execution_enabled = os.getenv("EXECUTION_ENABLED", "false").lower() in ("true", "1", "yes")
    dry_run = os.getenv("EXECUTION_DRY_RUN", "true").lower() in ("true", "1", "yes")
    channels_str = os.getenv("EXECUTION_CHANNELS", "email")
    channels_enabled = [c.strip() for c in channels_str.split(",") if c.strip()]
    
    return ExecutionConfig(
        execution_enabled=execution_enabled,
        dry_run=dry_run,
        channels_enabled=channels_enabled
    )


# ═══════════════════════════════════════════════════════════════════════
# MAIN EXECUTION FUNCTION
# ═══════════════════════════════════════════════════════════════════════


def execute_plan_for_project(
    project_id: str,
    override_dry_run: Optional[bool] = None,
) -> ExecutionReport:
    """
    Execute marketing plan for a project across enabled channels.
    
    Processes strategy recommendations and content items, routing them
    through appropriate gateways (email, social, CRM) based on channel
    and content type.
    
    Safety behavior:
    - If execution_enabled=False (default), returns 0 items processed
    - If dry_run=True (default), calls gateways in preview mode
    - All errors are caught and logged, no exceptions raised
    - Each failed item is recorded but processing continues
    
    Args:
        project_id: Project UUID or ID string
        override_dry_run: If provided, overrides config dry_run setting
        
    Returns:
        ExecutionReport with success/failure counts and results
        
    Example:
        # Execute with defaults (safe: execution disabled, dry-run enabled)
        report = execute_plan_for_project("proj-123")
        
        # Execute with dry_run override (preview only, even if config says execute)
        report = execute_plan_for_project("proj-123", override_dry_run=True)
    """
    
    # Initialize report
    report = ExecutionReport(project_id=str(project_id))
    
    # Get configuration
    config = get_execution_config()
    
    # Determine effective dry_run setting
    effective_dry_run = override_dry_run if override_dry_run is not None else config.dry_run
    
    # Log execution start
    log_event(
        "execution.started",
        details={
            "project_id": str(project_id),
            "execution_enabled": config.execution_enabled,
            "dry_run": effective_dry_run,
            "channels_enabled": config.channels_enabled,
        },
        tags=["execution", "phase3"]
    )
    
    # ─────────────────────────────────────────────────────────────
    # SAFETY CHECK: If execution is disabled, return early
    # ─────────────────────────────────────────────────────────────
    if not config.execution_enabled:
        log_event(
            "execution.disabled",
            details={
                "project_id": str(project_id),
                "reason": "EXECUTION_ENABLED=False",
            },
            tags=["execution", "phase3", "safety"]
        )
        return report  # Return empty report
    
    # ─────────────────────────────────────────────────────────────
    # PHASE 1: Fetch project and plan items
    # ─────────────────────────────────────────────────────────────
    project = None
    plan_items = []
    
    try:
        project = fetch_project_and_plan(project_id)
        if project is None:
            error_msg = f"Project {project_id} not found"
            logger.warning(error_msg)
            log_event(
                "execution.project_not_found",
                details={"project_id": str(project_id)},
                tags=["execution", "error"]
            )
            report.errors.append(error_msg)
            return report
        
        plan_items = extract_plan_items(project)
        report.total_items_processed = len(plan_items)
        
        log_event(
            "execution.plan_fetched",
            details={
                "project_id": str(project_id),
                "items_count": len(plan_items),
            },
            tags=["execution", "phase3"]
        )
    except Exception as e:
        error_msg = f"fetch_project_and_plan failed: {str(e)}"
        logger.error(error_msg)
        log_event(
            "execution.error",
            details={
                "stage": "fetch_plan",
                "project_id": str(project_id),
                "error": str(e),
            },
            tags=["execution", "error"]
        )
        report.errors.append(error_msg)
        return report
    
    # ─────────────────────────────────────────────────────────────
    # PHASE 2: Route items to appropriate gateways
    # ─────────────────────────────────────────────────────────────
    
    # Separate items by channel
    email_items = [item for item in plan_items if item.get("channel") == "email"]
    social_items = [item for item in plan_items if item.get("channel") in ("linkedin", "instagram", "twitter")]
    crm_items = [item for item in plan_items if item.get("channel") == "crm"]
    
    report.channels_used = []
    if email_items and "email" in config.channels_enabled:
        report.channels_used.append("email")
    if social_items and any(ch in config.channels_enabled for ch in ["linkedin", "instagram", "twitter"]):
        report.channels_used.extend([ch for ch in ["linkedin", "instagram", "twitter"] if ch in config.channels_enabled])
    if crm_items and "crm" in config.channels_enabled:
        report.channels_used.append("crm")
    
    # ─────────────────────────────────────────────────────────────
    # PHASE 3: Execute email items
    # ─────────────────────────────────────────────────────────────
    if email_items and "email" in config.channels_enabled:
        try:
            executed = execute_email_items(
                email_items,
                project=project,
                dry_run=effective_dry_run,
            )
            report.items_sent_successfully += executed.get("success", 0)
            report.items_failed += executed.get("failed", 0)
            report.execution_results.extend(executed.get("results", []))
            
            log_event(
                "execution.email_executed",
                details={
                    "project_id": str(project_id),
                    "success": executed.get("success", 0),
                    "failed": executed.get("failed", 0),
                    "dry_run": effective_dry_run,
                },
                tags=["execution", "email"]
            )
        except Exception as e:
            error_msg = f"execute_email_items failed: {str(e)}"
            logger.error(error_msg)
            log_event(
                "execution.error",
                details={
                    "stage": "email_execution",
                    "project_id": str(project_id),
                    "error": str(e),
                },
                tags=["execution", "error"]
            )
            report.errors.append(error_msg)
            report.items_failed += len(email_items)
    
    # ─────────────────────────────────────────────────────────────
    # PHASE 4: Execute social media items
    # ─────────────────────────────────────────────────────────────
    if social_items and any(ch in config.channels_enabled for ch in ["linkedin", "instagram", "twitter"]):
        try:
            executed = execute_social_items(
                social_items,
                project=project,
                channels_enabled=config.channels_enabled,
                dry_run=effective_dry_run,
            )
            report.items_sent_successfully += executed.get("success", 0)
            report.items_failed += executed.get("failed", 0)
            report.execution_results.extend(executed.get("results", []))
            
            log_event(
                "execution.social_executed",
                details={
                    "project_id": str(project_id),
                    "success": executed.get("success", 0),
                    "failed": executed.get("failed", 0),
                    "dry_run": effective_dry_run,
                },
                tags=["execution", "social"]
            )
        except Exception as e:
            error_msg = f"execute_social_items failed: {str(e)}"
            logger.error(error_msg)
            log_event(
                "execution.error",
                details={
                    "stage": "social_execution",
                    "project_id": str(project_id),
                    "error": str(e),
                },
                tags=["execution", "error"]
            )
            report.errors.append(error_msg)
            report.items_failed += len(social_items)
    
    # ─────────────────────────────────────────────────────────────
    # PHASE 5: Execute CRM sync items
    # ─────────────────────────────────────────────────────────────
    if crm_items and "crm" in config.channels_enabled:
        try:
            executed = execute_crm_items(
                crm_items,
                project=project,
                dry_run=effective_dry_run,
            )
            report.items_sent_successfully += executed.get("success", 0)
            report.items_failed += executed.get("failed", 0)
            report.execution_results.extend(executed.get("results", []))
            
            log_event(
                "execution.crm_executed",
                details={
                    "project_id": str(project_id),
                    "success": executed.get("success", 0),
                    "failed": executed.get("failed", 0),
                    "dry_run": effective_dry_run,
                },
                tags=["execution", "crm"]
            )
        except Exception as e:
            error_msg = f"execute_crm_items failed: {str(e)}"
            logger.error(error_msg)
            log_event(
                "execution.error",
                details={
                    "stage": "crm_execution",
                    "project_id": str(project_id),
                    "error": str(e),
                },
                tags=["execution", "error"]
            )
            report.errors.append(error_msg)
            report.items_failed += len(crm_items)
    
    # ─────────────────────────────────────────────────────────────
    # Build and return execution report
    # ─────────────────────────────────────────────────────────────
    log_event(
        "execution.completed",
        details={
            "project_id": str(project_id),
            "total_processed": report.total_items_processed,
            "success": report.items_sent_successfully,
            "failed": report.items_failed,
            "channels_used": report.channels_used,
            "error_count": len(report.errors),
        },
        tags=["execution", "phase3", "complete"]
    )
    
    return report


# ═══════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS (Execution Phases)
# ═══════════════════════════════════════════════════════════════════════


def fetch_project_and_plan(project_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch project and associated execution plan from database.
    
    Args:
        project_id: Project UUID or ID
        
    Returns:
        Dictionary with project data and plan items, or None if not found
        
    Raises:
        Exception: On database or fetch errors
    """
    # TODO: Implement fetch from CampaignDB or Project store
    # For now, return a stub that can be mocked in tests
    logger.debug(f"fetch_project_and_plan: {project_id}")
    return None


def extract_plan_items(project: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract executable items from project plan.
    
    Converts strategy recommendations and content calendar into
    a list of items ready for execution (email, social, CRM sync).
    
    Args:
        project: Project dictionary from fetch_project_and_plan
        
    Returns:
        List of executable items with channel, content, recipient info
        
    Raises:
        Exception: On extraction errors
    """
    # TODO: Implement plan item extraction
    # For now, return empty list for stub
    logger.debug("extract_plan_items")
    return []


def execute_email_items(
    items: List[Dict[str, Any]],
    project: Optional[Dict[str, Any]] = None,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """
    Execute email items via email gateway.
    
    Routes email items (newsletters, outreach, follow-ups) through
    the email sender gateway. In dry_run mode, emails are previewed
    but not sent.
    
    Args:
        items: List of email items to execute
        project: Project context (optional)
        dry_run: If True, preview only; if False, send real emails
        
    Returns:
        Dictionary with success/failed counts and ExecutionResult list
        
    Raises:
        Exception: On gateway errors
    """
    # TODO: Implement email execution via gateway
    logger.debug(f"execute_email_items: {len(items)} items, dry_run={dry_run}")
    return {"success": 0, "failed": 0, "results": []}


def execute_social_items(
    items: List[Dict[str, Any]],
    project: Optional[Dict[str, Any]] = None,
    channels_enabled: Optional[List[str]] = None,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """
    Execute social media items via social poster gateway.
    
    Routes social posts (LinkedIn, Instagram, Twitter) through
    appropriate social poster gateway. In dry_run mode, posts are
    previewed but not published.
    
    Args:
        items: List of social items to execute
        project: Project context (optional)
        channels_enabled: List of enabled social channels
        dry_run: If True, preview only; if False, publish real posts
        
    Returns:
        Dictionary with success/failed counts and ExecutionResult list
        
    Raises:
        Exception: On gateway errors
    """
    # TODO: Implement social media execution via gateway
    logger.debug(f"execute_social_items: {len(items)} items, dry_run={dry_run}")
    return {"success": 0, "failed": 0, "results": []}


def execute_crm_items(
    items: List[Dict[str, Any]],
    project: Optional[Dict[str, Any]] = None,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """
    Execute CRM sync items via CRM syncer gateway.
    
    Routes CRM items (contact updates, pipeline moves, deal stages)
    through the CRM syncer gateway. In dry_run mode, changes are
    previewed but not synced to CRM.
    
    Args:
        items: List of CRM items to execute
        project: Project context (optional)
        dry_run: If True, preview only; if False, sync to real CRM
        
    Returns:
        Dictionary with success/failed counts and ExecutionResult list
        
    Raises:
        Exception: On gateway errors
    """
    # TODO: Implement CRM execution via gateway
    logger.debug(f"execute_crm_items: {len(items)} items, dry_run={dry_run}")
    return {"success": 0, "failed": 0, "results": []}
