"""
INTEGRATION GUIDE: Package Presets & Section Templates

This guide explains how to use the new package presets and section templates
in your AICMO report generation workflow.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. PACKAGE PRESETS (aicmo/presets/package_presets.py)
────────────────────────────────────────────────────────

Each package defines:
- sections: List of section keys to generate
- requires_research: Boolean for research/context gathering
- complexity: "low", "medium", "medium-high", or "high"

PACKAGES (7 total):
- Quick Social Pack (Basic): 10 sections, low complexity
- Strategy + Campaign Pack (Standard): 17 sections, medium
- Full-Funnel Growth Suite (Premium): 21 sections, high
- Launch & GTM Pack: 18 sections, medium-high
- Brand Turnaround Lab: 18 sections, high
- Retention & CRM Booster: 14 sections, medium
- Performance Audit & Revamp: 15 sections, medium-high

USAGE:
    from aicmo.presets.package_presets import PACKAGE_PRESETS

    # Get a package config
    package_config = PACKAGE_PRESETS["Strategy + Campaign Pack (Standard)"]
    
    # Iterate through sections to generate
    for section_key in package_config["sections"]:
        # Use section_key to look up template in SECTION_PROMPT_TEMPLATES
        generate_section(section_key)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2. SECTION TEMPLATES (aicmo/presets/section_templates.py)
──────────────────────────────────────────────────────────

Each section template contains:
- name: Human-readable section name
- prompt: LLM prompt template (with {{variable}} placeholders)
- output_format: "markdown" or "markdown_table"

62 SECTION TEMPLATES available:
- Core sections: overview, campaign_objective, messaging_framework, etc.
- Channel sections: channel_plan, email_flows, sms_flows, etc.
- Advanced sections: market_landscape, competitor_analysis, funnel_breakdown, etc.
- Specialty sections: risk_analysis, turnaround_milestones, etc.

USAGE:
    from aicmo.presets.section_templates import SECTION_PROMPT_TEMPLATES

    # Get a section template
    template = SECTION_PROMPT_TEMPLATES["overview"]
    
    # Render prompt with variables
    rendered_prompt = template["prompt"].format(
        brand_name="Acme Co",
        business_type="SaaS",
        location="US East",
        primary_offer="Project management tool",
        campaign_duration="90 days",
        target_audience="Startup founders",
        brand_tone="Casual and energetic"
    )
    
    # Call LLM with rendered prompt
    section_content = call_openai(rendered_prompt)
    
    # Return as markdown or table based on output_format
    output = format_output(section_content, template["output_format"])

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

3. INTEGRATION PATTERN (Recommended Flow)
─────────────────────────────────────────

    def generate_full_report(client_brief, selected_package):
        '''Generate a complete report for a selected package'''
        
        from aicmo.presets.package_presets import PACKAGE_PRESETS
        from aicmo.presets.section_templates import SECTION_PROMPT_TEMPLATES
        
        # 1. Get package configuration
        package_config = PACKAGE_PRESETS[selected_package]
        section_keys = package_config["sections"]
        
        # 2. Prepare context variables from client_brief
        context = {
            "brand_name": client_brief.brand_name,
            "business_type": client_brief.business_type,
            "location": client_brief.location,
            "primary_offer": client_brief.product_service,
            "campaign_duration": client_brief.campaign_duration,
            "target_audience": client_brief.target_audience,
            "brand_tone": client_brief.brand_tone,
            # ... more variables
        }
        
        # 3. Generate each section
        report_parts = []
        for section_key in section_keys:
            template = SECTION_PROMPT_TEMPLATES[section_key]
            
            # Render prompt with context
            prompt = template["prompt"].format(**context)
            
            # Call LLM
            section_content = llm.generate(prompt)
            
            # Format output
            formatted = format_by_type(section_content, template["output_format"])
            
            # Add to report
            report_parts.append(f"## {template['name']}\n\n{formatted}")
        
        # 4. Combine all sections
        full_report = "\n\n---\n\n".join(report_parts)
        
        return full_report

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

4. PLACEMENT IN BACKEND FLOW
────────────────────────────

Recommended location in backend/main.py:

    # In aicmo_generate() or api_aicmo_generate_report():
    
    1. Load client brief → Build context dict
    2. Select package → Get section list from PACKAGE_PRESETS
    3. For each section:
       a. Fetch template from SECTION_PROMPT_TEMPLATES
       b. Render prompt with context
       c. Call LLM (or research phase if requires_research=True)
       d. Collect result
    4. Assemble all sections into final markdown
    5. Apply humanization (FIX #4: skip for >8KB)
    6. Return to Streamlit

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

5. VARIABLE REFERENCE (Template Placeholders)
──────────────────────────────────────────────

Common placeholders used in templates:
- {{brand_name}}: The brand/company name
- {{business_type}}: Type of business (e.g. SaaS, E-commerce)
- {{location}}: Primary geography/market
- {{primary_offer}}: Main product or service
- {{campaign_duration}}: Campaign length (e.g. "90 days", "Q1")
- {{target_audience}}: Primary audience description
- {{brand_tone}}: Tone of voice (e.g. "professional", "casual", "energetic")
- {{budget_level}}: Budget tier (e.g. "SMB", "mid-market", "enterprise")
- {{primary_channels}}: Main channels to focus on
- {{campaign_objective}}: What the campaign aims to achieve
- {{product_name}}: Product name (for launches)

Add more context variables as needed per your client brief structure.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

6. KEY GUARANTEES
─────────────────

✅ EVERY pack generates a full, agency-grade report (10-21 sections)
✅ No pack ever stops early
✅ Complexity scales appropriately (basic→standard→premium)
✅ Premium packs use deeper research + multi-stage generation
✅ Basic packs are still professional but lighter/faster
✅ All templates are production-ready

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

NEXT STEPS:
1. Import these modules in your backend generator
2. Update api_aicmo_generate_report() to use PACKAGE_PRESETS
3. Update section generation to fetch from SECTION_PROMPT_TEMPLATES
4. Test with different packages to ensure all sections are generated
5. Monitor report length to ensure no truncation
"""
