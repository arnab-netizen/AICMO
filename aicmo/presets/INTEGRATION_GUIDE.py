"""
Integration guide for WOW templates and PDF export system.

This file contains example code showing how to integrate the WOW templates,
rules, and PDF export utilities into existing generation endpoints.

DO NOT USE THIS FILE DIRECTLY - it's reference documentation.
Copy patterns from here into your actual backend/routes/*.py files.
"""

from __future__ import annotations

# ============================================================================
# Example 1: Basic Template Usage
# ============================================================================

# In any generation endpoint, you can use:

from aicmo.presets.wow_templates import get_wow_template
from aicmo.presets.wow_rules import get_wow_rules


def build_wow_report(package_key: str, filled_placeholders: dict) -> str:
    """
    Build a WOW report by filling template placeholders.

    Args:
        package_key: One of "quick_social_basic", "strategy_campaign_standard", etc
        filled_placeholders: Dict of {{placeholder}} -> value mappings

    Returns:
        Complete markdown report ready for display or PDF export
    """
    template = get_wow_template(package_key)
    rules = get_wow_rules(package_key)

    # Your generation logic should already have produced blocks like:
    # - calendar_14_day_table
    # - sample_captions_block
    # - hashtags_location
    # etc.
    #
    # Rules can be used to ensure you generate enough items:
    if "min_captions" in rules:
        min_captions = rules["min_captions"]
        # if len(captions) < min_captions: generate more captions

    # Simple placeholder replacement: {{key}} -> value
    report_md = template
    for key, value in filled_placeholders.items():
        # Handle None/missing values gracefully
        if value is None:
            value = f"[{key} not provided]"
        report_md = report_md.replace(f"{{{{{key}}}}}", str(value))

    return report_md


# ============================================================================
# Example 2: Using PDF Export Helper
# ============================================================================

from backend.export.pdf_utils import ensure_pdf_for_report


def generate_and_export_report(package_key: str, request_data: dict) -> dict:
    """
    Example endpoint that generates a report AND exports it as PDF.

    This is the pattern to follow for all report generation endpoints.
    """
    # 1) Generate the markdown report (your existing logic)
    filled = build_filled_placeholders(request_data)  # your function
    report_md = build_wow_report(package_key, filled)

    # 2) Create a report ID (however you already track reports)
    report_id = create_report_id()

    # 3) ALWAYS make a PDF before returning
    pdf_meta = ensure_pdf_for_report(
        report_id=report_id,
        markdown=report_md,
        meta={
            "title": request_data.get("brand_name"),
            "brand_name": request_data.get("brand_name"),
        },
    )

    # 4) Return both markdown + PDF URL in the API response
    return {
        "report_id": report_id,
        "package_key": package_key,
        "markdown": report_md,
        "pdf_url": pdf_meta["pdf_url"],
        # Keep anything else you already returned:
        # "raw_sections": filled,
        # "summary": summary_block,
    }


# ============================================================================
# Example 3: Streamlit Integration (aicmo_operator.py)
# ============================================================================

"""
In your Streamlit operator where users select a package:

# 1) Map dropdown labels to internal keys
PACKAGE_OPTIONS = {
    "Quick Social Pack (Basic)": "quick_social_basic",
    "Strategy + Campaign Pack (Standard)": "strategy_campaign_standard",
    "Full-Funnel Growth Suite (Premium)": "full_funnel_premium",
    "Launch & GTM Pack": "launch_gtm",
    "Brand Turnaround Lab": "brand_turnaround",
    "Retention & CRM Booster": "retention_crm",
    "Performance Audit & Revamp": "performance_audit",
}

# 2) Get the selected key
selected_label = st.selectbox("Choose Package", list(PACKAGE_OPTIONS.keys()))
package_key = PACKAGE_OPTIONS[selected_label]

# 3) Call the API (or local function)
response = requests.post(
    API_URL + "/api/generate/report",
    json={"package_key": package_key, "brief": form_data}
).json()

# 4) Display markdown in the app
report_md = response["markdown"]
st.markdown(report_md)

# 5) Always show PDF download button
pdf_url = response.get("pdf_url")
if pdf_url:
    pdf_bytes = requests.get(API_URL + pdf_url).content
    st.download_button(
        "📥 Download full report (PDF)",
        data=pdf_bytes,
        file_name=f"{response['report_id']}.pdf",
        mime="application/pdf",
    )
    # OR just show a link if you prefer not to pull bytes through Streamlit:
    # st.markdown(f"[📥 Download PDF]({API_URL + pdf_url})")
"""


# ============================================================================
# Example 4: Preset Metadata Access
# ============================================================================

from backend.export.pdf_utils import get_preset_by_key, load_wow_presets


def list_all_presets():
    """Show all available presets to a user."""
    config = load_wow_presets()
    return config.get("presets", [])


def get_preset_sections(package_key: str):
    """Get the list of sections that should be in a specific package."""
    preset = get_preset_by_key(package_key)
    if preset:
        return preset.get("sections", [])
    return []


# ============================================================================
# Example 5: Validation - Ensure Rules Are Met
# ============================================================================


def validate_report_against_rules(
    package_key: str,
    report_data: dict,
) -> tuple[bool, list[str]]:
    """
    Validate that a generated report meets WOW rules for its package.

    Returns:
        (is_valid, list of issues if any)
    """
    rules = get_wow_rules(package_key)
    issues = []

    if not rules:
        return True, []  # No rules defined = pass

    # Check minimum calendar days
    if "min_days_in_calendar" in rules:
        min_days = rules["min_days_in_calendar"]
        calendar = report_data.get("calendar_section", "")
        days_found = calendar.count("\n")  # rough heuristic
        if days_found < min_days:
            issues.append(f"Calendar has {days_found} days but minimum is {min_days}")

    # Check minimum captions
    if "min_captions" in rules:
        min_captions = rules["min_captions"]
        captions = report_data.get("captions", [])
        if len(captions) < min_captions:
            issues.append(f"Only {len(captions)} captions but minimum is {min_captions}")

    # Check minimum hashtags
    if "min_hashtags" in rules:
        min_hashtags = rules["min_hashtags"]
        hashtags = report_data.get("hashtags", [])
        if len(hashtags) < min_hashtags:
            issues.append(f"Only {len(hashtags)} hashtags but minimum is {min_hashtags}")

    return len(issues) == 0, issues


# ============================================================================
# Summary: Integration Checklist
# ============================================================================

"""
To integrate WOW templates into your system:

1. ✅ Import from aicmo.presets:
   from aicmo.presets.wow_templates import get_wow_template
   from aicmo.presets.wow_rules import get_wow_rules

2. ✅ Use templates in generation:
   template = get_wow_template(package_key)
   rules = get_wow_rules(package_key)
   # Fill placeholders with your generated content

3. ✅ Always export PDF:
   from backend.export.pdf_utils import ensure_pdf_for_report
   pdf_meta = ensure_pdf_for_report(report_id, markdown, meta)

4. ✅ Return both markdown and PDF URL:
   return {
       "markdown": report_md,
       "pdf_url": pdf_meta["pdf_url"],
   }

5. ✅ In Streamlit: Show markdown + download button
   st.markdown(response["markdown"])
   st.download_button(..., data=pdf_bytes, ...)

6. ✅ (Optional) Validate against rules:
   is_valid, issues = validate_report_against_rules(package_key, report_data)
   if not is_valid:
       # regenerate missing sections

No breaking changes. These are pure Python utilities that can coexist
with your current code.
"""
