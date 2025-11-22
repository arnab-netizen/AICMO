#!/usr/bin/env python3
"""
How to Use the AICMO Humanization Layer

This guide shows practical examples of using the humanization wrapper.
"""

import os

from backend.humanization_wrapper import (
    HumanizationWrapper,
    PersonaConfig,
    default_wrapper,
)

# ============================================================================
# EXAMPLE 1: Basic Usage - Dashboard Integration (ALREADY DONE)
# ============================================================================

# This is already integrated into streamlit_pages/aicmo_operator.py
# When you click "Generate draft report" in Tab 1, it automatically:

# 1. Calls AICMO backend to generate raw report
# 2. Extracts brand context from session state
# 3. Applies humanization wrapper
# 4. Stores humanized version in session_state["draft_report"]
# 5. Displays in Tab 2 (Workshop)

# The code looks like:
"""
if st.button("Generate draft report"):
    report_md = call_backend_generate(stage="draft")
    brand_name = st.session_state["client_brief_meta"].get("brand_name")
    objectives = st.session_state["client_brief_meta"].get("objectives")
    humanized_report = _apply_humanization(report_md, brand_name, objectives)
    st.session_state["draft_report"] = humanized_report
"""

# ============================================================================
# EXAMPLE 2: Direct Python Usage
# ============================================================================

# If you want to use the humanizer in other code:

# Option A: Use the default singleton
raw_text = "Here are some ways to improve your strategy. In conclusion..."
humanized = default_wrapper.process_text(raw_text)
print(humanized)

# Option B: Create custom wrapper with your own persona
my_persona = PersonaConfig(
    name="Conversion Copywriter",
    description=(
        "You're a conversion copywriter with 10+ years of e-commerce experience. "
        "You think in terms of funnels, friction points, and desire. "
        "You hate unnecessary words."
    ),
    style_notes="Be bold. Use power words. Emphasize benefits over features.",
)

custom_wrapper = HumanizationWrapper(persona=my_persona)
humanized_copy = custom_wrapper.process_text(raw_text)
print(humanized_copy)

# ============================================================================
# EXAMPLE 3: Process Entire Reports
# ============================================================================

# If you have a report dictionary and want to humanize multiple fields:

report = {
    "title": "Q4 Marketing Strategy",
    "executive_summary": "Here are the key points...",
    "strategy": "In conclusion, you should focus on...",
    "tactics": "Overall, here's what to do:",
    "budget": "$50,000",  # Won't be processed (not text)
}

humanized_report = default_wrapper.process_report(
    report,
    fields=["executive_summary", "strategy", "tactics"],
    brand_voice="Professional, conversational, direct",
    extra_context="B2B SaaS, enterprise customers",
)

print(humanized_report["executive_summary"])  # Humanized
print(humanized_report["strategy"])  # Humanized
print(humanized_report["tactics"])  # Humanized
print(humanized_report["budget"])  # Original (not processed)

# ============================================================================
# EXAMPLE 4: With Brand Context
# ============================================================================

# You can pass brand voice and objectives to customize humanization:

humanized = default_wrapper.process_text(
    raw_text,
    brand_voice="Startup, informal, direct, data-driven",
    extra_context="Growth marketing for SaaS, targeting CTOs",
)

# The wrapper will take this into account when rewriting.
# For example, it might:
# - Use "we" instead of formal tone
# - Emphasize data/ROI over brand values
# - Use technical language appropriate for CTOs

# ============================================================================
# EXAMPLE 5: Error Handling
# ============================================================================

# The wrapper is designed to never break:

text = "Some content"
try:
    result = default_wrapper.process_text(text)
    # Even if API fails, you get text back (original if processing failed)
    print(f"Success: {result}")
except Exception as e:
    # This almost never happens - wrapper catches internal errors
    print(f"Unexpected: {e}")

# Graceful fallback means:
# - No OpenAI key? Uses heuristics instead
# - API timeout? Returns original text
# - Model error? Returns original text
# - Any exception? Safely returns something

# ============================================================================
# EXAMPLE 6: Configuration via Environment
# ============================================================================

# Control which model is used for humanization:

# Use faster (cheaper) model for testing:
os.environ["AICMO_HUMANIZER_MODEL"] = "gpt-4o-mini"  # Default

# Use more powerful model for production:
os.environ["AICMO_HUMANIZER_MODEL"] = "gpt-4"

# Need OpenAI API key:
os.environ["OPENAI_API_KEY"] = "sk-..."

# ============================================================================
# EXAMPLE 7: Custom Personas for Different Contexts
# ============================================================================

# SaaS Growth Marketer
growth_persona = PersonaConfig(
    name="Growth Marketer",
    description=(
        "You're a growth marketer who thinks in terms of experimentation, "
        "channels, and metrics. You're direct, data-driven, and results-oriented."
    ),
    style_notes="Use specific metrics. Talk channel by channel. Be direct.",
)

# High-end Brand Strategist
brand_persona = PersonaConfig(
    name="Brand Strategist",
    description=(
        "You're a brand strategist at a top-tier agency. You think in terms of "
        "positioning, storytelling, and emotional connection. Sophisticated but clear."
    ),
    style_notes="Be literary but clear. Focus on brand differentiation. Sound authoritative.",
)

# Non-profit Communications Director
nonprofit_persona = PersonaConfig(
    name="Communications Director",
    description=(
        "You're a communications director for a mission-driven non-profit. "
        "You need to inspire, communicate impact, and be transparent."
    ),
    style_notes="Be authentic. Show impact. Tell real stories. Be honest.",
)

# Use them:
growth_wrapper = HumanizationWrapper(persona=growth_persona)
brand_wrapper = HumanizationWrapper(persona=brand_persona)
nonprofit_wrapper = HumanizationWrapper(persona=nonprofit_persona)

# ============================================================================
# EXAMPLE 8: Batch Processing
# ============================================================================

# Process multiple pieces of content:

copy_variants = [
    "Here are some ways to improve your conversion rate...",
    "In conclusion, you should test these approaches...",
    "To summarize, focus on these channels...",
]

humanized_variants = [default_wrapper.process_text(variant) for variant in copy_variants]

# Now you have humanized versions of all variants

# ============================================================================
# EXAMPLE 9: Monitor What Happened
# ============================================================================

# If you want to see what was removed/changed:

original = "Here are some ways to improve. In conclusion, you should..."
humanized = default_wrapper.process_text(original)

print(f"Original length: {len(original)}")
print(f"Humanized length: {len(humanized)}")
print(f"Reduction: {len(original) - len(humanized)} chars")

# The humanization typically:
# - Removes 10-20% boilerplate
# - Adds natural variation (may increase or decrease total length)
# - Changes tone and structure significantly

# ============================================================================
# EXAMPLE 10: Integration with your own LLM pipeline
# ============================================================================

# If you have your own content generation:


def my_content_generator(prompt):
    """Your own LLM call."""
    from openai import OpenAI

    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


# Generate content
raw_content = my_content_generator("Write a marketing strategy for...")

# Humanize it
humanized_content = default_wrapper.process_text(
    raw_content, brand_voice="Professional SaaS", extra_context="B2B, targeting founders"
)

# Use humanized version
print(humanized_content)

# ============================================================================
# QUICK REFERENCE - COMMON PATTERNS
# ============================================================================

# Pattern 1: Simple text humanization
# from backend.humanization_wrapper import default_wrapper
# humanized = default_wrapper.process_text(raw_text)

# Pattern 2: With brand context
# humanized = default_wrapper.process_text(
#     raw_text,
#     brand_voice="Professional, direct",
#     extra_context="B2B SaaS"
# )

# Pattern 3: Entire report dict
# humanized_report = default_wrapper.process_report(
#     report_dict,
#     fields=["summary", "strategy", "tactics"]
# )

# Pattern 4: Custom persona
# from backend.humanization_wrapper import HumanizationWrapper, PersonaConfig
# persona = PersonaConfig(name="...", description="...", style_notes="...")
# wrapper = HumanizationWrapper(persona=persona)
# humanized = wrapper.process_text(raw_text)

# ============================================================================
# WHERE IT'S CURRENTLY USED
# ============================================================================

# 1. AICMO Dashboard (streamlit_pages/aicmo_operator.py)
#    - Line 556: Applied after "Generate draft report" (Tab 1)
#    - Line 629: Applied after "Apply feedback" (Tab 2)
#
# 2. Integration Function (_apply_humanization at line 399)
#    - Extracts brand context from session state
#    - Calls default_wrapper.process_text()
#    - Returns humanized text

# ============================================================================
# TESTING IT OUT
# ============================================================================

# To see it in action:
# 1. Start the Streamlit app: streamlit run streamlit_pages/aicmo_operator.py
# 2. Go to Tab 1 (Client Input)
# 3. Fill in brand name, objectives
# 4. Click "Generate draft report"
# 5. Check Tab 2 (Workshop) - output will be humanized!

# ============================================================================
# PERFORMANCE EXPECTATIONS
# ============================================================================

# Humanization adds time per generation:
# - Draft generation: +6-10 seconds
# - Feedback refinement: +6-10 seconds
#
# Cost per operation:
# - Two LLM calls at ~$0.001 each = ~$0.002 per report
# - Negligible for most workflows

# ============================================================================
# CONFIGURATION OPTIONS
# ============================================================================

# Enable full humanization:
# export OPENAI_API_KEY="sk-..."
#
# Use different model:
# export AICMO_HUMANIZER_MODEL="gpt-4"
#
# Without OPENAI_API_KEY:
# - Falls back to heuristic cleanup only
# - Still removes some boilerplate
# - Skips full 3-layer humanization
# - App still works fine

# ============================================================================
# SUPPORT & DOCUMENTATION
# ============================================================================

# For more details, see:
# - HUMANIZATION_LAYER.md (full guide)
# - HUMANIZATION_QUICK_REFERENCE.md (quick lookup)
# - HUMANIZATION_DEPLOYMENT.md (deployment info)
# - HUMANIZATION_COMPLETE.md (implementation summary)

print("✅ Humanization layer is integrated and ready to use!")
print("   See HUMANIZATION_COMPLETE.md for deployment status.")
