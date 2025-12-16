"""
Template registry service for managing message templates.

MODULE 6: Template Registry + Guardrails
CRUD operations, validation, and safe template management.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from aicmo.cam.template_models import MessageTemplateDB, TemplateRenderLogDB
from aicmo.cam.template_renderer import (
    validate_template_safe,
    render_message_template,
    extract_template_variables,
    detect_placeholders,
    RenderResult
)


@dataclass
class TemplateCreateInput:
    """Input for creating a new template."""
    name: str
    channel: str
    template_type: str
    subject: Optional[str]
    body: str
    required_vars: List[str]
    optional_vars: List[str]
    campaign_id: Optional[int]
    venture_id: Optional[str]
    created_by: str


class TemplateValidationError(Exception):
    """Raised when template validation fails."""
    pass


def create_template(
    session: Session,
    template_input: TemplateCreateInput
) -> MessageTemplateDB:
    """
    Create and validate a new message template.
    
    Args:
        session: Database session
        template_input: Template data
    
    Returns:
        Created MessageTemplateDB instance
    
    Raises:
        TemplateValidationError: If template syntax invalid or has placeholders
        IntegrityError: If template name already exists for campaign
    """
    # Validate template syntax and required vars
    is_valid, error_msg = validate_template_safe(
        subject_template=template_input.subject,
        body_template=template_input.body,
        required_vars=template_input.required_vars
    )
    
    if not is_valid:
        raise TemplateValidationError(f"Template validation failed: {error_msg}")
    
    # Note: We don't check for placeholders in template SOURCE
    # (Jinja2 templates contain {{ }} by design)
    # Placeholder detection happens at RENDER time on the OUTPUT
    
    # Create template record
    template = MessageTemplateDB(
        name=template_input.name,
        channel=template_input.channel,
        template_type=template_input.template_type,
        subject=template_input.subject,
        body=template_input.body,
        required_vars=template_input.required_vars,
        optional_vars=template_input.optional_vars,
        is_validated=True,
        validation_error=None,
        has_placeholders=False,  # Template source is OK (checked at render time)
        campaign_id=template_input.campaign_id,
        venture_id=template_input.venture_id,
        created_by=template_input.created_by,
        active=True
    )
    
    session.add(template)
    
    try:
        session.commit()
    except IntegrityError as e:
        session.rollback()
        raise TemplateValidationError(
            f"Template name '{template_input.name}' already exists for this campaign"
        ) from e
    
    return template


def get_template(
    session: Session,
    template_id: int
) -> Optional[MessageTemplateDB]:
    """Retrieve template by ID."""
    return session.query(MessageTemplateDB).filter_by(id=template_id).first()


def get_template_by_name(
    session: Session,
    name: str,
    campaign_id: Optional[int] = None
) -> Optional[MessageTemplateDB]:
    """Retrieve template by name and campaign."""
    query = session.query(MessageTemplateDB).filter_by(name=name)
    if campaign_id is not None:
        query = query.filter_by(campaign_id=campaign_id)
    else:
        query = query.filter_by(campaign_id=None)  # Global templates
    
    return query.first()


def list_templates(
    session: Session,
    campaign_id: Optional[int] = None,
    channel: Optional[str] = None,
    active_only: bool = True
) -> List[MessageTemplateDB]:
    """
    List templates with optional filters.
    
    Args:
        session: Database session
        campaign_id: Filter by campaign (None = global templates only)
        channel: Filter by channel (email, linkedin, etc.)
        active_only: Only return active templates
    
    Returns:
        List of MessageTemplateDB instances
    """
    query = session.query(MessageTemplateDB)
    
    # Filter by campaign_id (explicitly check for None to get global templates)
    if campaign_id is not None:
        query = query.filter_by(campaign_id=campaign_id)
    else:
        query = query.filter_by(campaign_id=None)  # Only global templates
    
    if channel:
        query = query.filter_by(channel=channel)
    
    if active_only:
        query = query.filter_by(active=True)
    
    return query.order_by(MessageTemplateDB.created_at.desc()).all()


def render_template_for_lead(
    session: Session,
    template_id: int,
    context: Dict[str, Any],
    campaign_id: Optional[int] = None,
    lead_id: Optional[int] = None,
    log_render: bool = True
) -> RenderResult:
    """
    Render template with context and optionally log the render.
    
    Args:
        session: Database session
        template_id: Template to render
        context: Variables for rendering
        campaign_id: Campaign context (for logging)
        lead_id: Lead context (for logging)
        log_render: Whether to create audit log entry
    
    Returns:
        RenderResult with rendered message
    
    Raises:
        ValueError: If template not found or inactive
    """
    # Fetch template
    template = get_template(session, template_id)
    if not template:
        raise ValueError(f"Template {template_id} not found")
    
    if not template.active:
        raise ValueError(f"Template {template_id} is inactive")
    
    # Render template
    result = render_message_template(
        subject_template=template.subject,
        body_template=template.body,
        context=context
    )
    
    # Update usage tracking
    template.times_used += 1
    template.last_used_at = datetime.now(timezone.utc)
    
    # Log render (if enabled)
    if log_render:
        log = TemplateRenderLogDB(
            template_id=template_id,
            campaign_id=campaign_id,
            lead_id=lead_id,
            render_vars=context,
            rendered_subject=result.subject,
            rendered_body=result.body,
            render_success=result.success,
            render_error=result.error,
            contained_placeholders=result.has_placeholders,
            placeholder_details=result.placeholder_details
        )
        session.add(log)
    
    session.commit()
    
    return result


def deactivate_template(
    session: Session,
    template_id: int
) -> bool:
    """
    Deactivate (soft delete) a template.
    
    Returns True if template was deactivated, False if not found.
    """
    template = get_template(session, template_id)
    if not template:
        return False
    
    template.active = False
    session.commit()
    return True


def update_template(
    session: Session,
    template_id: int,
    subject: Optional[str] = None,
    body: Optional[str] = None,
    required_vars: Optional[List[str]] = None,
    optional_vars: Optional[List[str]] = None
) -> MessageTemplateDB:
    """
    Update existing template with validation.
    
    Args:
        session: Database session
        template_id: Template to update
        subject: New subject (if provided)
        body: New body (if provided)
        required_vars: New required vars (if provided)
        optional_vars: New optional vars (if provided)
    
    Returns:
        Updated MessageTemplateDB
    
    Raises:
        ValueError: If template not found
        TemplateValidationError: If updated template invalid
    """
    template = get_template(session, template_id)
    if not template:
        raise ValueError(f"Template {template_id} not found")
    
    # Prepare updated values
    new_subject = subject if subject is not None else template.subject
    new_body = body if body is not None else template.body
    new_required_vars = required_vars if required_vars is not None else template.required_vars
    
    # Validate updated template
    is_valid, error_msg = validate_template_safe(
        subject_template=new_subject,
        body_template=new_body,
        required_vars=new_required_vars
    )
    
    if not is_valid:
        raise TemplateValidationError(f"Updated template validation failed: {error_msg}")
    
    # Apply updates
    if subject is not None:
        template.subject = subject
    if body is not None:
        template.body = body
    if required_vars is not None:
        template.required_vars = required_vars
    if optional_vars is not None:
        template.optional_vars = optional_vars
    
    # Note: Placeholder detection happens at render time, not on template source
    template.is_validated = True
    template.validation_error = None
    
    session.commit()
    return template
