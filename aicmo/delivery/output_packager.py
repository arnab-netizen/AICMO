"""
Output Packager — Project Delivery Package Builder.

Phase 4: Bundle project outputs into deliverable packages.

This module packages completed project work into convenient formats:
- Generate strategy PDF from project strategy
- Generate creative/execution deck (PPTX) from creative outputs
- Generate HTML summary for web delivery
- Collate all deliverables with metadata
- Return structured ProjectPackageResult with paths and errors

Safety behavior:
- Each generator is wrapped in try/except; failures are recorded but don't stop processing
- Missing projects are handled gracefully
- If any file generation succeeds, result is marked as success=True
- Errors are logged but not raised from main function
- All operations are idempotent (safe to run multiple times)
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import logging
import os
from datetime import datetime

from aicmo.memory.engine import log_event


logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# PACKAGE RESULT DATACLASS
# ═══════════════════════════════════════════════════════════════════════


@dataclass
class ProjectPackageResult:
    """
    Result of packaging project outputs into deliverable formats.
    
    Contains paths to generated files and metadata about the package.
    """
    
    project_id: str
    
    # Generated file paths
    pdf_path: Optional[str] = None
    pptx_path: Optional[str] = None
    html_summary_path: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Status
    success: bool = False
    errors: List[str] = field(default_factory=list)
    
    created_at: Optional[str] = None
    
    def add_error(self, error_message: str) -> None:
        """Record an error in the package result."""
        if error_message not in self.errors:
            self.errors.append(error_message)
    
    def file_count(self) -> int:
        """Return count of generated files."""
        count = 0
        if self.pdf_path:
            count += 1
        if self.pptx_path:
            count += 1
        if self.html_summary_path:
            count += 1
        return count


# ═══════════════════════════════════════════════════════════════════════
# MAIN PACKAGER FUNCTION
# ═══════════════════════════════════════════════════════════════════════


def build_project_package(project_id: str) -> ProjectPackageResult:
    """
    Build complete deliverable package for a project.
    
    Generates PDF, PPTX, and HTML outputs from project data and stores
    references to generated files in the result. Each generation is
    wrapped in try/except to ensure partial success is useful.
    
    Safety behavior:
    - If project not found, returns result with success=False and error recorded
    - If any generator fails, continues with remaining generators
    - If any file is generated, success=True (partial success is ok)
    - Never raises exceptions from main function
    
    Args:
        project_id: Project UUID or ID string
        
    Returns:
        ProjectPackageResult with file paths and status
        
    Example:
        result = build_project_package("proj-123")
        if result.success:
            print(f"PDF: {result.pdf_path}")
            print(f"PPTX: {result.pptx_path}")
            print(f"HTML: {result.html_summary_path}")
        else:
            print(f"Errors: {result.errors}")
    """
    
    # Initialize result
    result = ProjectPackageResult(
        project_id=str(project_id),
        created_at=datetime.now().isoformat()
    )
    
    # Log package start
    log_event(
        "packaging.started",
        details={"project_id": str(project_id)},
        tags=["packaging", "phase4"]
    )
    
    # ─────────────────────────────────────────────────────────────
    # PHASE 1: Fetch project data
    # ─────────────────────────────────────────────────────────────
    project_data = None
    
    try:
        project_data = fetch_project_data(project_id)
        
        if project_data is None:
            error_msg = f"Project {project_id} not found"
            logger.warning(error_msg)
            log_event(
                "packaging.project_not_found",
                details={"project_id": str(project_id)},
                tags=["packaging", "error"]
            )
            result.add_error(error_msg)
            return result
        
        log_event(
            "packaging.project_fetched",
            details={"project_id": str(project_id)},
            tags=["packaging", "phase4"]
        )
    except Exception as e:
        error_msg = f"fetch_project_data failed: {str(e)}"
        logger.error(error_msg)
        log_event(
            "packaging.error",
            details={
                "stage": "fetch_project",
                "project_id": str(project_id),
                "error": str(e),
            },
            tags=["packaging", "error"]
        )
        result.add_error(error_msg)
        return result
    
    # ─────────────────────────────────────────────────────────────
    # PHASE 2: Generate strategy PDF
    # ─────────────────────────────────────────────────────────────
    try:
        pdf_path = generate_strategy_pdf(project_data)
        
        if pdf_path:
            result.pdf_path = pdf_path
            result.metadata["pdf_generated"] = True
            
            log_event(
                "packaging.pdf_generated",
                details={
                    "project_id": str(project_id),
                    "path": pdf_path,
                },
                tags=["packaging", "pdf"]
            )
        else:
            error_msg = "PDF generation returned None"
            logger.warning(error_msg)
            result.add_error(error_msg)
            
    except Exception as e:
        error_msg = f"generate_strategy_pdf failed: {str(e)}"
        logger.error(error_msg)
        log_event(
            "packaging.error",
            details={
                "stage": "pdf_generation",
                "project_id": str(project_id),
                "error": str(e),
            },
            tags=["packaging", "error"]
        )
        result.add_error(error_msg)
    
    # ─────────────────────────────────────────────────────────────
    # PHASE 3: Generate creative/execution deck (PPTX)
    # ─────────────────────────────────────────────────────────────
    try:
        pptx_path = generate_full_deck_pptx(project_data)
        
        if pptx_path:
            result.pptx_path = pptx_path
            result.metadata["pptx_generated"] = True
            
            log_event(
                "packaging.pptx_generated",
                details={
                    "project_id": str(project_id),
                    "path": pptx_path,
                },
                tags=["packaging", "pptx"]
            )
        else:
            error_msg = "PPTX generation returned None"
            logger.warning(error_msg)
            result.add_error(error_msg)
            
    except Exception as e:
        error_msg = f"generate_full_deck_pptx failed: {str(e)}"
        logger.error(error_msg)
        log_event(
            "packaging.error",
            details={
                "stage": "pptx_generation",
                "project_id": str(project_id),
                "error": str(e),
            },
            tags=["packaging", "error"]
        )
        result.add_error(error_msg)
    
    # ─────────────────────────────────────────────────────────────
    # PHASE 4: Generate HTML summary
    # ─────────────────────────────────────────────────────────────
    try:
        html_path = generate_html_summary(project_data)
        
        if html_path:
            result.html_summary_path = html_path
            result.metadata["html_generated"] = True
            
            log_event(
                "packaging.html_generated",
                details={
                    "project_id": str(project_id),
                    "path": html_path,
                },
                tags=["packaging", "html"]
            )
        else:
            error_msg = "HTML generation returned None"
            logger.warning(error_msg)
            result.add_error(error_msg)
            
    except Exception as e:
        error_msg = f"generate_html_summary failed: {str(e)}"
        logger.error(error_msg)
        log_event(
            "packaging.error",
            details={
                "stage": "html_generation",
                "project_id": str(project_id),
                "error": str(e),
            },
            tags=["packaging", "error"]
        )
        result.add_error(error_msg)
    
    # ─────────────────────────────────────────────────────────────
    # PHASE 5: Populate metadata and determine success
    # ─────────────────────────────────────────────────────────────
    
    # Success = any file generated
    result.success = result.file_count() > 0
    
    # Add summary metadata
    result.metadata["total_files"] = result.file_count()
    result.metadata["error_count"] = len(result.errors)
    result.metadata["files_generated"] = []
    
    if result.pdf_path:
        result.metadata["files_generated"].append("pdf")
    if result.pptx_path:
        result.metadata["files_generated"].append("pptx")
    if result.html_summary_path:
        result.metadata["files_generated"].append("html")
    
    # ─────────────────────────────────────────────────────────────
    # Build and return package result
    # ─────────────────────────────────────────────────────────────
    log_event(
        "packaging.completed",
        details={
            "project_id": str(project_id),
            "success": result.success,
            "files_generated": result.metadata.get("files_generated", []),
            "error_count": len(result.errors),
        },
        tags=["packaging", "phase4", "complete"]
    )
    
    return result


# ═══════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS (Generator Adapters)
# ═══════════════════════════════════════════════════════════════════════


def fetch_project_data(project_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch complete project data including strategy, creative, and execution.
    
    Args:
        project_id: Project UUID or ID
        
    Returns:
        Dictionary with project data, or None if not found
        
    Raises:
        Exception: On database or fetch errors
    """
    # TODO: Implement fetch from CampaignDB or Project store
    # Should retrieve:
    # - Project metadata
    # - Strategy document
    # - Creative assets
    # - Content calendar
    # - Execution results
    logger.debug(f"fetch_project_data: {project_id}")
    return None


def generate_strategy_pdf(project_data: Dict[str, Any]) -> Optional[str]:
    """
    Generate strategy PDF from project strategy document.
    
    Creates a formatted PDF of the strategy recommendations, market analysis,
    and implementation roadmap.
    
    Args:
        project_data: Project dictionary from fetch_project_data
        
    Returns:
        Path to generated PDF file, or None if generation failed
        
    Raises:
        Exception: On PDF generation errors
    """
    # TODO: Implement PDF generation
    # Should call underlying report generator or PDF library
    # Expected to exist as generate_strategy_pdf in reporting module
    logger.debug("generate_strategy_pdf")
    return None


def generate_full_deck_pptx(project_data: Dict[str, Any]) -> Optional[str]:
    """
    Generate creative/execution deck as PowerPoint PPTX.
    
    Creates a formatted presentation of creative assets, content calendar,
    and execution plan.
    
    Args:
        project_data: Project dictionary from fetch_project_data
        
    Returns:
        Path to generated PPTX file, or None if generation failed
        
    Raises:
        Exception: On PPTX generation errors
    """
    # TODO: Implement PPTX generation
    # Should call underlying deck generator or PPTX library
    # Expected to exist as generate_full_deck in reporting module
    logger.debug("generate_full_deck_pptx")
    return None


def generate_html_summary(project_data: Dict[str, Any]) -> Optional[str]:
    """
    Generate HTML summary for web delivery.
    
    Creates a web-friendly HTML document with project overview,
    key insights, and deliverables.
    
    Args:
        project_data: Project dictionary from fetch_project_data
        
    Returns:
        Path to generated HTML file, or None if generation failed
        
    Raises:
        Exception: On HTML generation errors
    """
    # TODO: Implement HTML generation
    # Should create HTML file or call template renderer
    # Expected to exist as generate_html_summary in reporting module
    logger.debug("generate_html_summary")
    return None
