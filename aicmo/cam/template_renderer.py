"""
Safe template rendering with placeholder detection.

MODULE 6: Template Registry + Guardrails
Renders Jinja2 templates with strict mode and validates output for broken placeholders.
"""

import re
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

from jinja2 import Template, Environment, StrictUndefined, TemplateSyntaxError, UndefinedError, meta


# Placeholder patterns that indicate broken/incomplete templates
PLACEHOLDER_PATTERNS = [
    r'\{\{',           # Remaining Jinja2 variables
    r'\}\}',           # Remaining Jinja2 variables
    r'\bTODO\b',       # TODO markers
    r'\bTBD\b',        # To Be Determined markers
    r'\[PLACEHOLDER\]', # Explicit placeholder markers
    r'\[.*?\]',        # Square bracket placeholders like [COMPANY_NAME]
    r'<.*?>',          # Angle bracket placeholders like <INSERT_VALUE>
]


@dataclass
class RenderResult:
    """Result of template rendering."""
    success: bool
    subject: Optional[str]
    body: Optional[str]
    error: Optional[str]
    has_placeholders: bool
    placeholder_details: Optional[str]


def detect_placeholders(text: str) -> Tuple[bool, Optional[str]]:
    """
    Detect broken placeholders in rendered text.
    
    Returns:
        (has_placeholders, details_string)
    """
    found = []
    
    for pattern in PLACEHOLDER_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            found.extend(matches)
    
    if found:
        details = f"Found placeholders: {', '.join(set(found[:10]))}"  # Show first 10 unique
        return True, details
    
    return False, None


def validate_template_syntax(template_str: str) -> Tuple[bool, Optional[str]]:
    """
    Validate Jinja2 template syntax without rendering.
    
    Returns:
        (is_valid, error_message)
    """
    try:
        env = Environment(undefined=StrictUndefined)
        env.from_string(template_str)
        return True, None
    except TemplateSyntaxError as e:
        return False, f"Template syntax error at line {e.lineno}: {e.message}"
    except Exception as e:
        return False, f"Template validation error: {str(e)}"


def extract_template_variables(template_str: str) -> List[str]:
    """
    Extract all variable names from Jinja2 template.
    
    Example: "Hello {{name}}, welcome to {{company}}" -> ["name", "company"]
    """
    env = Environment(undefined=StrictUndefined)
    try:
        parsed = env.parse(template_str)
        variables = list(meta.find_undeclared_variables(parsed))
        return variables
    except Exception:
        # If parsing fails, use regex fallback
        pattern = r'\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}'
        return list(set(re.findall(pattern, template_str)))


def render_template(
    template_str: str,
    context: Dict[str, Any],
    strict: bool = True
) -> RenderResult:
    """
    Render Jinja2 template with context variables.
    
    Args:
        template_str: Jinja2 template string
        context: Dictionary of variables to render
        strict: If True, raise error on undefined variables (recommended)
    
    Returns:
        RenderResult with success status, rendered text, and placeholder detection
    """
    try:
        # Create Jinja2 environment with strict mode
        env = Environment(undefined=StrictUndefined if strict else None)
        template = env.from_string(template_str)
        
        # Render template
        rendered = template.render(**context)
        
        # Check for broken placeholders in output
        has_placeholders, placeholder_details = detect_placeholders(rendered)
        
        return RenderResult(
            success=True,
            subject=None,  # Subject handled separately
            body=rendered,
            error=None,
            has_placeholders=has_placeholders,
            placeholder_details=placeholder_details
        )
        
    except UndefinedError as e:
        return RenderResult(
            success=False,
            subject=None,
            body=None,
            error=f"Missing required variable: {str(e)}",
            has_placeholders=False,
            placeholder_details=None
        )
    except TemplateSyntaxError as e:
        return RenderResult(
            success=False,
            subject=None,
            body=None,
            error=f"Template syntax error: {str(e)}",
            has_placeholders=False,
            placeholder_details=None
        )
    except Exception as e:
        return RenderResult(
            success=False,
            subject=None,
            body=None,
            error=f"Rendering error: {str(e)}",
            has_placeholders=False,
            placeholder_details=None
        )


def render_message_template(
    subject_template: Optional[str],
    body_template: str,
    context: Dict[str, Any]
) -> RenderResult:
    """
    Render complete message (subject + body) with validation.
    
    Args:
        subject_template: Email subject line template (optional for non-email)
        body_template: Message body template
        context: Variables for rendering
    
    Returns:
        RenderResult with both subject and body rendered
    """
    # Render body
    body_result = render_template(body_template, context)
    if not body_result.success:
        return body_result
    
    # Render subject (if provided)
    rendered_subject = None
    if subject_template:
        subject_result = render_template(subject_template, context)
        if not subject_result.success:
            return RenderResult(
                success=False,
                subject=None,
                body=body_result.body,
                error=f"Subject rendering failed: {subject_result.error}",
                has_placeholders=body_result.has_placeholders,
                placeholder_details=body_result.placeholder_details
            )
        rendered_subject = subject_result.body
        
        # Check subject for placeholders too
        if subject_result.has_placeholders:
            return RenderResult(
                success=True,
                subject=rendered_subject,
                body=body_result.body,
                error=None,
                has_placeholders=True,
                placeholder_details=f"Subject: {subject_result.placeholder_details}"
            )
    
    return RenderResult(
        success=True,
        subject=rendered_subject,
        body=body_result.body,
        error=None,
        has_placeholders=body_result.has_placeholders,
        placeholder_details=body_result.placeholder_details
    )


def validate_template_safe(
    subject_template: Optional[str],
    body_template: str,
    required_vars: List[str]
) -> Tuple[bool, Optional[str]]:
    """
    Validate template is safe to save (syntax valid, all required vars present).
    
    Args:
        subject_template: Subject line template
        body_template: Body template
        required_vars: List of required variable names
    
    Returns:
        (is_valid, error_message)
    """
    # Validate body syntax
    is_valid, error = validate_template_syntax(body_template)
    if not is_valid:
        return False, f"Body: {error}"
    
    # Validate subject syntax (if provided)
    if subject_template:
        is_valid, error = validate_template_syntax(subject_template)
        if not is_valid:
            return False, f"Subject: {error}"
    
    # Extract all variables from templates
    body_vars = set(extract_template_variables(body_template))
    subject_vars = set(extract_template_variables(subject_template)) if subject_template else set()
    all_template_vars = body_vars | subject_vars
    
    # Check all required vars are used in template
    required_set = set(required_vars)
    missing_in_template = required_set - all_template_vars
    if missing_in_template:
        return False, f"Required variables not used in template: {', '.join(missing_in_template)}"
    
    return True, None


def should_block_send(render_result: RenderResult) -> bool:
    """
    Determine if message should be blocked from sending due to placeholders.
    
    Returns True if message contains broken placeholders and should NOT be sent.
    """
    return render_result.has_placeholders
