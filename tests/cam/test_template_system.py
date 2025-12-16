"""
Tests for MODULE 6: Template Registry + Guardrails

Validates:
- Template creation with validation
- Safe rendering (Jinja2 strict mode)
- Placeholder detection ({{, TODO, TBD, [PLACEHOLDER])
- Broken templates blocked from sending
- Template CRUD operations
- Render audit logging
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from aicmo.core.db import Base
from aicmo.cam.template_models import MessageTemplateDB, TemplateRenderLogDB
from aicmo.cam.template_service import (
    create_template,
    get_template,
    get_template_by_name,
    list_templates,
    render_template_for_lead,
    deactivate_template,
    update_template,
    TemplateCreateInput,
    TemplateValidationError
)
from aicmo.cam.template_renderer import (
    render_template,
    render_message_template,
    validate_template_syntax,
    extract_template_variables,
    detect_placeholders,
    should_block_send
)


@pytest.fixture
def db_session() -> Session:
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


def test_template_renders_successfully(db_session: Session):
    """Test that valid template renders with all variables."""
    template_input = TemplateCreateInput(
        name="cold_outreach_v1",
        channel="email",
        template_type="outreach",
        subject="Quick question for {{lead_name}}",
        body="Hi {{lead_name}},\n\nI noticed {{company}} is in the {{industry}} space. {{value_prop}}\n\nBest,\n{{sender_name}}",
        required_vars=["lead_name", "company", "industry", "value_prop", "sender_name"],
        optional_vars=[],
        campaign_id=None,
        venture_id=None,
        created_by="operator@test.com"
    )
    
    template = create_template(db_session, template_input)
    assert template.id is not None
    assert template.is_validated is True
    assert template.has_placeholders is False  # No broken placeholders in source
    
    # Render with full context
    result = render_template_for_lead(
        session=db_session,
        template_id=template.id,
        context={
            "lead_name": "John Doe",
            "company": "Acme Corp",
            "industry": "SaaS",
            "value_prop": "We can help you scale faster.",
            "sender_name": "Alice"
        }
    )
    
    assert result.success is True
    assert result.subject == "Quick question for John Doe"
    assert "Hi John Doe," in result.body
    assert "Acme Corp" in result.body
    assert result.has_placeholders is False
    assert result.error is None


def test_send_blocked_if_placeholders_remain(db_session: Session):
    """Test that messages with broken placeholders are blocked."""
    # Create template with TODO marker (will be detected at render time)
    template_input = TemplateCreateInput(
        name="broken_template",
        channel="email",
        subject="Hello {{lead_name}}",
        body="Hi {{lead_name}},\n\nTODO: Add personalized value prop here.\n\nBest,\nAlice",
        template_type="outreach",
        required_vars=["lead_name"],
        optional_vars=[],
        campaign_id=None,
        venture_id=None,
        created_by="system"
    )
    
    template = create_template(db_session, template_input)
    # Note: has_placeholders is False for template SOURCE (Jinja2 syntax is OK)
    # Placeholder detection happens at RENDER time on OUTPUT
    
    # Render template
    result = render_template_for_lead(
        session=db_session,
        template_id=template.id,
        context={"lead_name": "John"}
    )
    
    assert result.success is True  # Rendering succeeded
    assert "TODO" in result.body  # But TODO remains in output
    assert result.has_placeholders is True  # Placeholder detected in OUTPUT
    assert should_block_send(result) is True  # Should NOT send this message


def test_missing_variable_fails_render(db_session: Session):
    """Test that missing required variables cause render failure in strict mode."""
    template_input = TemplateCreateInput(
        name="strict_template",
        channel="email",
        subject="Message for {{lead_name}}",
        body="Hi {{lead_name}}, from {{company}}.",
        template_type="outreach",
        required_vars=["lead_name", "company"],
        optional_vars=[],
        campaign_id=None,
        venture_id=None,
        created_by="system"
    )
    
    template = create_template(db_session, template_input)
    
    # Render with missing variable
    result = render_template_for_lead(
        session=db_session,
        template_id=template.id,
        context={"lead_name": "John"}  # Missing 'company'
    )
    
    assert result.success is False
    assert result.error is not None
    assert "company" in result.error.lower()  # Error mentions missing variable


def test_placeholder_detection_comprehensive(db_session: Session):
    """Test detection of various placeholder patterns."""
    test_cases = [
        ("Hello {{name}}", True, "{{"),  # Jinja2 variable
        ("Hi John, TODO: add details", True, "TODO"),
        ("Message TBD", True, "TBD"),
        ("[PLACEHOLDER] goes here", True, "[PLACEHOLDER]"),
        ("[COMPANY_NAME] is great", True, "["),
        ("<INSERT_VALUE> here", True, "<INSERT_VALUE>"),
        ("Clean message with no placeholders", False, None),
        ("Email: john@example.com", False, None),  # @ shouldn't trigger
    ]
    
    for text, should_detect, expected_pattern in test_cases:
        has_placeholders, details = detect_placeholders(text)
        assert has_placeholders == should_detect, f"Failed for: {text}"
        if should_detect:
            assert expected_pattern in details if details else False


def test_template_validation_rejects_bad_syntax(db_session: Session):
    """Test that templates with invalid Jinja2 syntax are rejected."""
    template_input = TemplateCreateInput(
        name="bad_syntax",
        channel="email",
        subject="Hello",
        body="Hi {{lead_name}, missing closing brace",  # Syntax error
        template_type="outreach",
        required_vars=["lead_name"],
        optional_vars=[],
        campaign_id=None,
        venture_id=None,
        created_by="system"
    )
    
    with pytest.raises(TemplateValidationError) as exc_info:
        create_template(db_session, template_input)
    
    assert "syntax" in str(exc_info.value).lower()


def test_template_crud_operations(db_session: Session):
    """Test create, read, update, deactivate operations."""
    # Create
    template_input = TemplateCreateInput(
        name="test_crud",
        channel="email",
        subject="Subject v1",
        body="Body v1 with {{lead_name}}",
        template_type="outreach",
        required_vars=["lead_name"],
        optional_vars=[],
        campaign_id=None,
        venture_id=None,
        created_by="system"
    )
    
    template = create_template(db_session, template_input)
    template_id = template.id
    
    # Read by ID
    fetched = get_template(db_session, template_id)
    assert fetched is not None
    assert fetched.name == "test_crud"
    
    # Read by name
    fetched_by_name = get_template_by_name(db_session, "test_crud")
    assert fetched_by_name is not None
    assert fetched_by_name.id == template_id
    
    # Update
    updated = update_template(
        db_session,
        template_id,
        subject="Subject v2",
        body="Body v2 with {{lead_name}}"
    )
    assert updated.subject == "Subject v2"
    assert updated.body == "Body v2 with {{lead_name}}"
    
    # List active templates
    active_templates = list_templates(db_session, active_only=True)
    assert len(active_templates) == 1
    assert active_templates[0].id == template_id
    
    # Deactivate
    deactivated = deactivate_template(db_session, template_id)
    assert deactivated is True
    
    # Verify not in active list
    active_templates = list_templates(db_session, active_only=True)
    assert len(active_templates) == 0


def test_render_audit_log_created(db_session: Session):
    """Test that rendering creates audit log entry."""
    template_input = TemplateCreateInput(
        name="audited_template",
        channel="email",
        subject="Hi {{name}}",
        body="Message for {{name}}",
        template_type="outreach",
        required_vars=["name"],
        optional_vars=[],
        campaign_id=None,
        venture_id=None,
        created_by="system"
    )
    
    template = create_template(db_session, template_input)
    
    # Render with logging enabled
    result = render_template_for_lead(
        session=db_session,
        template_id=template.id,
        context={"name": "John"},
        campaign_id=123,
        lead_id=456,
        log_render=True
    )
    
    assert result.success is True
    
    # Verify log entry created
    logs = db_session.query(TemplateRenderLogDB).filter_by(template_id=template.id).all()
    assert len(logs) == 1
    
    log = logs[0]
    assert log.campaign_id == 123
    assert log.lead_id == 456
    assert log.render_vars == {"name": "John"}
    assert log.rendered_subject == "Hi John"
    assert log.rendered_body == "Message for John"
    assert log.render_success is True
    assert log.contained_placeholders is False


def test_duplicate_template_name_per_campaign_rejected(db_session: Session):
    """Test that duplicate template names for same campaign are rejected."""
    template_input = TemplateCreateInput(
        name="duplicate_test",
        channel="email",
        subject="Subject",
        body="Body {{var}}",
        template_type="outreach",
        required_vars=["var"],
        optional_vars=[],
        campaign_id=1,
        venture_id=None,
        created_by="system"
    )
    
    # Create first template
    create_template(db_session, template_input)
    
    # Try to create duplicate
    with pytest.raises(TemplateValidationError) as exc_info:
        create_template(db_session, template_input)
    
    assert "already exists" in str(exc_info.value).lower()


def test_template_usage_tracking(db_session: Session):
    """Test that template usage is tracked."""
    template_input = TemplateCreateInput(
        name="usage_tracked",
        channel="email",
        subject="Hi",
        body="Message {{var}}",
        template_type="outreach",
        required_vars=["var"],
        optional_vars=[],
        campaign_id=None,
        venture_id=None,
        created_by="system"
    )
    
    template = create_template(db_session, template_input)
    assert template.times_used == 0
    assert template.last_used_at is None
    
    # Render once
    render_template_for_lead(
        session=db_session,
        template_id=template.id,
        context={"var": "value"}
    )
    
    # Check usage incremented
    db_session.refresh(template)
    assert template.times_used == 1
    assert template.last_used_at is not None
    
    # Render again
    render_template_for_lead(
        session=db_session,
        template_id=template.id,
        context={"var": "value2"}
    )
    
    db_session.refresh(template)
    assert template.times_used == 2


def test_extract_template_variables():
    """Test variable extraction from Jinja2 templates."""
    template = "Hello {{name}}, welcome to {{company}}. Your {{role}} is important."
    variables = extract_template_variables(template)
    
    assert "name" in variables
    assert "company" in variables
    assert "role" in variables
    assert len(variables) == 3


def test_global_vs_campaign_templates(db_session: Session):
    """Test separation of global and campaign-specific templates."""
    # Create global template
    global_input = TemplateCreateInput(
        name="global_template",
        channel="email",
        subject="Global",
        body="Body {{var}}",
        template_type="outreach",
        required_vars=["var"],
        optional_vars=[],
        campaign_id=None,  # Global
        venture_id=None,
        created_by="system"
    )
    create_template(db_session, global_input)
    
    # Create campaign-specific template
    campaign_input = TemplateCreateInput(
        name="campaign_template",
        channel="email",
        subject="Campaign",
        body="Body {{var}}",
        template_type="outreach",
        required_vars=["var"],
        optional_vars=[],
        campaign_id=1,  # Campaign-specific
        venture_id=None,
        created_by="system"
    )
    create_template(db_session, campaign_input)
    
    # List global templates
    global_templates = list_templates(db_session, campaign_id=None)
    assert len(global_templates) == 1
    assert global_templates[0].name == "global_template"
    
    # List campaign templates
    campaign_templates = list_templates(db_session, campaign_id=1)
    assert len(campaign_templates) == 1
    assert campaign_templates[0].name == "campaign_template"


def test_inactive_template_cannot_be_rendered(db_session: Session):
    """Test that deactivated templates cannot be rendered."""
    template_input = TemplateCreateInput(
        name="to_deactivate",
        channel="email",
        subject="Subject",
        body="Body {{var}}",
        template_type="outreach",
        required_vars=["var"],
        optional_vars=[],
        campaign_id=None,
        venture_id=None,
        created_by="system"
    )
    
    template = create_template(db_session, template_input)
    template_id = template.id
    
    # Deactivate template
    deactivate_template(db_session, template_id)
    
    # Try to render
    with pytest.raises(ValueError) as exc_info:
        render_template_for_lead(
            session=db_session,
            template_id=template_id,
            context={"var": "value"}
        )
    
    assert "inactive" in str(exc_info.value).lower()
