"""
Validation/contracts layer for AICMO services.

Ensures major services produce valid, non-placeholder, structurally correct outputs.
Prevents garbage data (empty strings, placeholders, broken shapes) from propagating.
"""

from typing import Any, List, Optional
import re


# Known placeholder strings that indicate incomplete/invalid data
PLACEHOLDER_STRINGS = {
    "TBD",
    "tbd",
    "Not specified",
    "not specified",
    "lorem ipsum",
    "Lorem Ipsum",
    "n/a",
    "N/A",
    "TODO",
    "FIXME",
    "PLACEHOLDER",
    "[Insert",
    "{{",
    "}}",
}


# Generic validation helpers
def ensure_non_empty_string(value: str, field_name: str) -> str:
    """
    Ensure a string field is not empty or whitespace-only.
    
    Args:
        value: String to validate
        field_name: Name of field for error messages
        
    Returns:
        The validated string
        
    Raises:
        ValueError: If string is empty/whitespace
    """
    if not value or not value.strip():
        raise ValueError(f"{field_name} cannot be empty or whitespace-only")
    return value


def ensure_non_empty_list(value: Any, field_name: str) -> Any:
    """
    Ensure a list field is not empty.
    
    Args:
        value: List to validate
        field_name: Name of field for error messages
        
    Returns:
        The validated list
        
    Raises:
        ValueError: If list is empty or None
    """
    if not value or len(value) == 0:
        raise ValueError(f"{field_name} cannot be empty")
    return value


def ensure_no_placeholders(text: str, context: str) -> str:
    """
    Ensure text does not contain known placeholder strings.
    
    Args:
        text: Text to check
        context: Context for error messages
        
    Returns:
        The validated text
        
    Raises:
        ValueError: If text contains placeholder strings
    """
    text_lower = text.lower()
    for placeholder in PLACEHOLDER_STRINGS:
        if placeholder.lower() in text_lower:
            raise ValueError(
                f"{context} contains placeholder text '{placeholder}': {text[:100]}"
            )
    return text


def ensure_min_length(text: str, min_length: int, field_name: str) -> str:
    """
    Ensure text meets minimum length requirement.
    
    Args:
        text: Text to check
        min_length: Minimum acceptable length
        field_name: Name of field for error messages
        
    Returns:
        The validated text
        
    Raises:
        ValueError: If text is too short
    """
    if len(text.strip()) < min_length:
        raise ValueError(
            f"{field_name} must be at least {min_length} characters, got {len(text.strip())}"
        )
    return text


# Domain-specific validators
def validate_strategy_doc(doc: Any) -> Any:
    """
    Validate StrategyDoc has required fields and no placeholders.
    
    Args:
        doc: StrategyDoc instance
        
    Returns:
        The validated doc
        
    Raises:
        ValueError: If validation fails
    """
    from aicmo.domain.strategy import StrategyDoc
    
    if not isinstance(doc, StrategyDoc):
        raise ValueError(f"Expected StrategyDoc, got {type(doc)}")
    
    # Check critical fields
    ensure_non_empty_string(doc.executive_summary, "executive_summary")
    ensure_min_length(doc.executive_summary, 50, "executive_summary")
    ensure_no_placeholders(doc.executive_summary, "Executive summary")
    
    ensure_non_empty_string(doc.situation_analysis, "situation_analysis")
    ensure_no_placeholders(doc.situation_analysis, "Situation analysis")
    
    ensure_non_empty_string(doc.strategy_narrative, "strategy_narrative")
    ensure_no_placeholders(doc.strategy_narrative, "Strategy narrative")
    
    ensure_non_empty_list(doc.pillars, "pillars")
    for i, pillar in enumerate(doc.pillars):
        ensure_non_empty_string(pillar.name, f"pillar[{i}].name")
        ensure_non_empty_string(pillar.description, f"pillar[{i}].description")
        ensure_no_placeholders(pillar.name, f"Pillar {i} name")
        ensure_no_placeholders(pillar.description, f"Pillar {i} description")
    
    return doc


def validate_creative_assets(assets: List[Any]) -> List[Any]:
    """
    Validate list of CreativeVariant objects.
    
    Args:
        assets: List of CreativeVariant instances
        
    Returns:
        The validated assets list
        
    Raises:
        ValueError: If validation fails
    """
    from aicmo.domain.execution import CreativeVariant
    
    ensure_non_empty_list(assets, "creative_assets")
    
    for i, asset in enumerate(assets):
        if not isinstance(asset, CreativeVariant):
            raise ValueError(f"Asset {i} is not a CreativeVariant, got {type(asset)}")
        
        ensure_non_empty_string(asset.platform, f"asset[{i}].platform")
        ensure_non_empty_string(asset.format, f"asset[{i}].format")
        ensure_non_empty_string(asset.hook, f"asset[{i}].hook")
        
        # Check caption if present
        if asset.caption:
            ensure_no_placeholders(asset.caption, f"Asset {i} caption")
            ensure_min_length(asset.caption, 20, f"asset[{i}].caption")
    
    return assets


def validate_media_plan(plan: Any) -> Any:
    """
    Validate MediaCampaignPlan has required structure.
    
    Args:
        plan: MediaCampaignPlan instance
        
    Returns:
        The validated plan
        
    Raises:
        ValueError: If validation fails
    """
    from aicmo.media.domain import MediaCampaignPlan
    
    if not isinstance(plan, MediaCampaignPlan):
        raise ValueError(f"Expected MediaCampaignPlan, got {type(plan)}")
    
    ensure_non_empty_list(plan.channels, "channels")
    
    for i, channel in enumerate(plan.channels):
        # MediaChannel has channel_type (enum), not name
        if channel.budget_allocated <= 0:
            raise ValueError(f"Channel {i} budget must be positive, got {channel.budget_allocated}")
    
    if plan.total_budget <= 0:
        raise ValueError(f"Total budget must be positive, got {plan.total_budget}")
    
    return plan


def validate_performance_dashboard(dashboard: Any) -> Any:
    """
    Validate PerformanceDashboard has metrics.
    
    Args:
        dashboard: PerformanceDashboard instance
        
    Returns:
        The validated dashboard
        
    Raises:
        ValueError: If validation fails
    """
    from aicmo.analytics.domain import PerformanceDashboard
    
    if not isinstance(dashboard, PerformanceDashboard):
        raise ValueError(f"Expected PerformanceDashboard, got {type(dashboard)}")
    
    # Check that current_metrics dict is not empty
    if not dashboard.current_metrics or len(dashboard.current_metrics) == 0:
        raise ValueError("current_metrics cannot be empty")
    
    return dashboard


def validate_pm_task(task: Any) -> Any:
    """
    Validate PM Task has required fields.
    
    Args:
        task: Task instance
        
    Returns:
        The validated task
        
    Raises:
        ValueError: If validation fails
    """
    from aicmo.pm.domain import Task
    
    if not isinstance(task, Task):
        raise ValueError(f"Expected Task, got {type(task)}")
    
    ensure_non_empty_string(task.title, "task.title")
    ensure_no_placeholders(task.title, "Task title")
    
    if task.description:
        ensure_no_placeholders(task.description, "Task description")
    
    return task


def validate_approval_request(req: Any) -> Any:
    """
    Validate ApprovalRequest has required fields.
    
    Args:
        req: ApprovalRequest instance
        
    Returns:
        The validated request
        
    Raises:
        ValueError: If validation fails
    """
    from aicmo.portal.domain import ApprovalRequest
    
    if not isinstance(req, ApprovalRequest):
        raise ValueError(f"Expected ApprovalRequest, got {type(req)}")
    
    ensure_non_empty_string(req.asset_name, "approval_request.asset_name")
    ensure_no_placeholders(req.asset_name, "Approval request asset name")
    
    if req.submission_notes:
        ensure_no_placeholders(req.submission_notes, "Approval request submission notes")
    
    return req


def validate_pitch_deck(deck: Any) -> Any:
    """
    Validate PitchDeck has required slides.
    
    Args:
        deck: PitchDeck instance
        
    Returns:
        The validated deck
        
    Raises:
        ValueError: If validation fails
    """
    from aicmo.pitch.domain import PitchDeck
    
    if not isinstance(deck, PitchDeck):
        raise ValueError(f"Expected PitchDeck, got {type(deck)}")
    
    ensure_non_empty_list(deck.sections, "pitch_deck.sections")
    
    for i, section in enumerate(deck.sections):
        ensure_non_empty_string(section.title, f"section[{i}].title")
        ensure_non_empty_string(section.content, f"section[{i}].content")
        ensure_no_placeholders(section.title, f"Section {i} title")
        ensure_no_placeholders(section.content, f"Section {i} content")
    
    return deck


def validate_brand_core(brand: Any) -> Any:
    """
    Validate BrandCore has required elements.
    
    Args:
        brand: BrandCore instance
        
    Returns:
        The validated brand
        
    Raises:
        ValueError: If validation fails
    """
    from aicmo.brand.domain import BrandCore
    
    if not isinstance(brand, BrandCore):
        raise ValueError(f"Expected BrandCore, got {type(brand)}")
    
    ensure_non_empty_string(brand.purpose, "purpose")
    ensure_no_placeholders(brand.purpose, "Brand purpose")
    
    ensure_non_empty_string(brand.vision, "vision")
    ensure_no_placeholders(brand.vision, "Brand vision")
    
    ensure_non_empty_string(brand.mission, "mission")
    ensure_no_placeholders(brand.mission, "Brand mission")
    
    ensure_non_empty_list(brand.values, "brand.values")
    for i, value in enumerate(brand.values):
        ensure_non_empty_string(value, f"brand.values[{i}]")
        ensure_no_placeholders(value, f"Brand value {i}")
    
    return brand
