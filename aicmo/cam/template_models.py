"""
Template registry database models.

MODULE 6: Template Registry + Guardrails
Stores email/message templates with validation and safe rendering.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.sql import func

from aicmo.core.db import Base


class MessageTemplateDB(Base):
    """
    Message template for campaigns.
    
    Templates are validated on save to prevent broken placeholders.
    Supports Jinja2 syntax with strict mode (undefined variables raise errors).
    """
    
    __tablename__ = "cam_message_templates"
    
    id = Column(Integer, primary_key=True)
    
    # Template identification
    name = Column(String, nullable=False)  # "cold_outreach_v1", "follow_up_after_reply"
    channel = Column(String, nullable=False, default="email")  # email, linkedin, sms
    template_type = Column(String, nullable=False, default="outreach")  # outreach, follow_up, nurture
    
    # Template content
    subject = Column(String, nullable=True)  # Email subject line (null for non-email channels)
    body = Column(Text, nullable=False)  # Message body with Jinja2 placeholders
    
    # Validation metadata
    required_vars = Column(JSON, nullable=False, default=[])  # ["lead_name", "company", "value_prop"]
    optional_vars = Column(JSON, nullable=False, default=[])  # ["industry", "pain_point"]
    
    # Safety flags
    is_validated = Column(Boolean, nullable=False, default=False)  # Passed validation on save
    validation_error = Column(Text, nullable=True)  # Error message if validation failed
    has_placeholders = Column(Boolean, nullable=False, default=False)  # Contains {{, TODO, TBD, [PLACEHOLDER]
    
    # Campaign association
    campaign_id = Column(Integer, ForeignKey("cam_campaigns.id"), nullable=True)  # Null = global template
    venture_id = Column(String, ForeignKey("ventures.id"), nullable=True)
    
    # Usage tracking
    times_used = Column(Integer, nullable=False, default=0)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Ownership
    created_by = Column(String, nullable=False)  # operator@example.com or "system"
    
    # Active status
    active = Column(Boolean, nullable=False, default=True)  # Can be archived
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    
    __table_args__ = (
        UniqueConstraint('name', 'campaign_id', name='uq_template_name_campaign'),
    )


class TemplateRenderLogDB(Base):
    """
    Audit log of template renderings.
    
    Tracks every time a template is rendered for debugging and compliance.
    """
    
    __tablename__ = "cam_template_render_logs"
    
    id = Column(Integer, primary_key=True)
    
    # What was rendered
    template_id = Column(Integer, ForeignKey("cam_message_templates.id"), nullable=False)
    campaign_id = Column(Integer, ForeignKey("cam_campaigns.id"), nullable=True)
    lead_id = Column(Integer, ForeignKey("cam_leads.id"), nullable=True)
    
    # Render context (variables passed in)
    render_vars = Column(JSON, nullable=False)  # {"lead_name": "John", "company": "Acme"}
    
    # Render result
    rendered_subject = Column(String, nullable=True)
    rendered_body = Column(Text, nullable=True)
    render_success = Column(Boolean, nullable=False, default=True)
    render_error = Column(Text, nullable=True)
    
    # Safety check results
    contained_placeholders = Column(Boolean, nullable=False, default=False)  # Did output have {{, TODO, etc?
    placeholder_details = Column(Text, nullable=True)  # Which placeholders found
    
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
