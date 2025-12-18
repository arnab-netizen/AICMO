"""
PDF Renderer for AICMO Delivery Packages

Uses reportlab to generate professional client-facing PDFs.
"""

import os
from typing import Dict, Any
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def render_delivery_pdf(
    path: str,
    manifest: Dict[str, Any],
    artifacts: Dict[str, Any],
    branding: Dict[str, Any]
) -> str:
    """
    Generate PDF delivery report.
    
    Args:
        path: Output file path
        manifest: Delivery manifest dict
        artifacts: Dict of artifact_type -> Artifact
        branding: Branding configuration
    
    Returns:
        Path to generated PDF
    """
    # Create document
    doc = SimpleDocTemplate(
        path,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )
    
    # Build story
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor(branding.get("primary_color", "#1E3A8A")),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor(branding.get("primary_color", "#1E3A8A")),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Title Page
    story.append(Spacer(1, 2*inch))
    story.append(Paragraph(f"Campaign Delivery Report", title_style))
    story.append(Spacer(1, 0.3*inch))
    
    campaign_id = manifest["ids"].get("campaign_id", "Unknown")
    client_id = manifest["ids"].get("client_id", "Unknown")
    
    story.append(Paragraph(f"Campaign: {campaign_id}", styles['Normal']))
    story.append(Paragraph(f"Client: {client_id}", styles['Normal']))
    story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d')}", styles['Normal']))
    story.append(Spacer(1, 0.5*inch))
    
    footer_text = branding.get("footer_text", "").replace("{client_name}", client_id)
    story.append(Paragraph(footer_text, styles['Normal']))
    story.append(Paragraph(f"Prepared by {branding.get('agency_name', 'AICMO')}", styles['Normal']))
    
    story.append(PageBreak())
    
    # Table of Contents
    story.append(Paragraph("Table of Contents", heading_style))
    story.append(Spacer(1, 0.2*inch))
    
    toc_items = []
    if artifacts.get("intake"):
        toc_items.append("1. Intake Summary")
    if artifacts.get("strategy"):
        toc_items.append("2. Strategy Contract")
    if artifacts.get("creatives"):
        toc_items.append("3. Creatives Summary")
    if artifacts.get("execution"):
        toc_items.append("4. Execution Plan")
    if artifacts.get("monitoring"):
        toc_items.append("5. Monitoring Setup")
    
    for item in toc_items:
        story.append(Paragraph(item, styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
    
    story.append(PageBreak())
    
    # Sections
    section_num = 1
    
    # Intake Section
    if artifacts.get("intake"):
        story.extend(_render_intake_section(artifacts["intake"], section_num, heading_style, styles))
        story.append(PageBreak())
        section_num += 1
    
    # Strategy Section
    if artifacts.get("strategy"):
        story.extend(_render_strategy_section(artifacts["strategy"], section_num, heading_style, styles))
        story.append(PageBreak())
        section_num += 1
    
    # Creatives Section
    if artifacts.get("creatives"):
        story.extend(_render_creatives_section(artifacts["creatives"], section_num, heading_style, styles))
        story.append(PageBreak())
        section_num += 1
    
    # Execution Section
    if artifacts.get("execution"):
        story.extend(_render_execution_section(artifacts["execution"], section_num, heading_style, styles))
        story.append(PageBreak())
        section_num += 1
    
    # Monitoring Section
    if artifacts.get("monitoring"):
        story.extend(_render_monitoring_section(artifacts["monitoring"], section_num, heading_style, styles))
        story.append(PageBreak())
        section_num += 1
    
    # Build PDF
    doc.build(story)
    
    return path


def _render_intake_section(intake, section_num, heading_style, styles):
    """Render Intake section"""
    story = []
    story.append(Paragraph(f"{section_num}. Intake Summary", heading_style))
    story.append(Spacer(1, 0.2*inch))
    
    content = intake.content
    
    # Key fields
    fields = [
        ("Client Name", content.get("client_name", "N/A")),
        ("Website", content.get("website", "N/A")),
        ("Industry", content.get("industry", "N/A")),
        ("Geography", content.get("geography", "N/A")),
        ("Primary Offer", content.get("primary_offer", "N/A")),
        ("Objective", content.get("objective", "N/A")),
        ("Target Audience", content.get("target_audience", "N/A")),
    ]
    
    for label, value in fields:
        story.append(Paragraph(f"<b>{label}:</b> {value}", styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
    
    return story


def _render_strategy_section(strategy, section_num, heading_style, styles):
    """Render Strategy section with 8 layers"""
    story = []
    story.append(Paragraph(f"{section_num}. Strategy Contract", heading_style))
    story.append(Spacer(1, 0.2*inch))
    
    content = strategy.content
    
    # Layer 1: Business Reality
    if "layer1_business_reality" in content:
        story.append(Paragraph("<b>Layer 1: Business Reality Alignment</b>", styles['Heading3']))
        layer1 = content["layer1_business_reality"]
        story.append(Paragraph(f"Business Model: {layer1.get('business_model_summary', 'N/A')}", styles['Normal']))
        story.append(Paragraph(f"Revenue Streams: {layer1.get('revenue_streams', 'N/A')}", styles['Normal']))
        story.append(Paragraph(f"Bottleneck: {layer1.get('bottleneck', 'N/A')}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
    
    # Layer 2: Market Truth
    if "layer2_market_truth" in content:
        story.append(Paragraph("<b>Layer 2: Market & Competitive Truth</b>", styles['Heading3']))
        layer2 = content["layer2_market_truth"]
        story.append(Paragraph(f"Category Maturity: {layer2.get('category_maturity', 'N/A')}", styles['Normal']))
        story.append(Paragraph(f"White Space: {layer2.get('white_space_logic', 'N/A')}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
    
    # Layer 3: Audience Psychology
    if "layer3_audience_psychology" in content:
        story.append(Paragraph("<b>Layer 3: Audience Decision Psychology</b>", styles['Heading3']))
        layer3 = content["layer3_audience_psychology"]
        story.append(Paragraph(f"Awareness State: {layer3.get('awareness_state', 'N/A')}", styles['Normal']))
        story.append(Paragraph(f"Objections: {layer3.get('objection_hierarchy', 'N/A')}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
    
    # Layer 4: Value Architecture
    if "layer4_value_architecture" in content:
        story.append(Paragraph("<b>Layer 4: Value Proposition Architecture</b>", styles['Heading3']))
        layer4 = content["layer4_value_architecture"]
        story.append(Paragraph(f"Core Promise: {layer4.get('core_promise', 'N/A')}", styles['Normal']))
        story.append(Paragraph(f"Differentiation: {layer4.get('differentiation_logic', 'N/A')}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
    
    # Layer 5: Narrative
    if "layer5_narrative" in content:
        story.append(Paragraph("<b>Layer 5: Strategic Narrative</b>", styles['Heading3']))
        layer5 = content["layer5_narrative"]
        story.append(Paragraph(f"Problem: {layer5.get('narrative_problem', 'N/A')}", styles['Normal']))
        story.append(Paragraph(f"Resolution: {layer5.get('narrative_resolution', 'N/A')}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
    
    # Layer 6: Channel Strategy
    if "layer6_channel_strategy" in content:
        story.append(Paragraph("<b>Layer 6: Channel Strategy</b>", styles['Heading3']))
        layer6 = content["layer6_channel_strategy"]
        channels = layer6.get("channels", [])
        for ch in channels[:3]:  # Show first 3
            story.append(Paragraph(f"• {ch.get('name', 'N/A')}: {ch.get('strategic_role', 'N/A')}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
    
    # Layer 7: Constraints
    if "layer7_constraints" in content:
        story.append(Paragraph("<b>Layer 7: Execution Constraints</b>", styles['Heading3']))
        layer7 = content["layer7_constraints"]
        story.append(Paragraph(f"Tone: {layer7.get('tone_boundaries', 'N/A')}", styles['Normal']))
        story.append(Paragraph(f"Compliance: {layer7.get('compliance_rules', 'N/A')}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
    
    # Layer 8: Measurement
    if "layer8_measurement" in content:
        story.append(Paragraph("<b>Layer 8: Measurement & Learning</b>", styles['Heading3']))
        layer8 = content["layer8_measurement"]
        story.append(Paragraph(f"Success Definition: {layer8.get('success_definition', 'N/A')}", styles['Normal']))
        story.append(Paragraph(f"Leading Indicators: {layer8.get('leading_indicators', 'N/A')}", styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
    
    return story


def _render_creatives_section(creatives, section_num, heading_style, styles):
    """Render Creatives section"""
    story = []
    story.append(Paragraph(f"{section_num}. Creatives Summary", heading_style))
    story.append(Spacer(1, 0.2*inch))
    
    content = creatives.content
    
    story.append(Paragraph(f"<b>Status:</b> {creatives.status.value}", styles['Normal']))
    story.append(Paragraph(f"<b>Version:</b> {creatives.version}", styles['Normal']))
    
    # Show brief or summary if available
    if "brief" in content:
        brief = content["brief"]
        if isinstance(brief, dict):
            theme = brief.get("campaign_theme", "N/A")
            story.append(Paragraph(f"<b>Campaign Theme:</b> {theme}", styles['Normal']))
    
    story.append(Spacer(1, 0.2*inch))
    
    return story


def _render_execution_section(execution, section_num, heading_style, styles):
    """Render Execution section"""
    story = []
    story.append(Paragraph(f"{section_num}. Execution Plan", heading_style))
    story.append(Spacer(1, 0.2*inch))
    
    content = execution.content
    
    story.append(Paragraph(f"<b>Status:</b> {execution.status.value}", styles['Normal']))
    story.append(Paragraph(f"<b>Version:</b> {execution.version}", styles['Normal']))
    
    if "timeline" in content:
        story.append(Paragraph(f"<b>Timeline:</b> {content['timeline']}", styles['Normal']))
    
    story.append(Spacer(1, 0.2*inch))
    
    return story


def _render_monitoring_section(monitoring, section_num, heading_style, styles):
    """Render Monitoring section"""
    story = []
    story.append(Paragraph(f"{section_num}. Monitoring Setup", heading_style))
    story.append(Spacer(1, 0.2*inch))
    
    content = monitoring.content
    
    story.append(Paragraph(f"<b>Status:</b> {monitoring.status.value}", styles['Normal']))
    story.append(Paragraph(f"<b>Version:</b> {monitoring.version}", styles['Normal']))
    
    if "kpi_config" in content:
        kpi_config = content["kpi_config"]
        if isinstance(kpi_config, dict):
            kpis = kpi_config.get("selected_kpis", [])
            if kpis:
                story.append(Paragraph(f"<b>KPIs:</b> {', '.join(kpis)}", styles['Normal']))
    
    story.append(Spacer(1, 0.2*inch))
    
    return story
