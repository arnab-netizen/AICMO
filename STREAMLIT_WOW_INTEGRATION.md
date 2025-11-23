# WOW Templates Integration Guide for Streamlit

This document shows how to integrate the WOW template system into your Streamlit operator interface.

## Overview

The WOW system is now fully integrated into the backend (`backend/main.py`). When you call the `/aicmo/generate` endpoint with WOW parameters, you'll get back:

```json
{
  "marketing_plan": { ... },
  "campaign_blueprint": { ... },
  "social_calendar": { ... },
  "wow_markdown": "# Brand Name – Package Label\n\n...",
  "wow_package_key": "quick_social_basic",
  ...
}
```

## Streamlit Integration Pattern

### 1. Add package selector to your form

```python
import streamlit as st

# In your form where users select service packs
PACKAGE_OPTIONS = {
    "Quick Social Pack (Basic)": "quick_social_basic",
    "Strategy + Campaign Pack (Standard)": "strategy_campaign_standard",
    "Full-Funnel Growth Suite (Premium)": "full_funnel_premium",
    "Launch & GTM Pack": "launch_gtm",
    "Brand Turnaround Lab": "brand_turnaround",
    "Retention & CRM Booster": "retention_crm",
    "Performance Audit & Revamp": "performance_audit",
}

selected_label = st.selectbox(
    "Select WOW Package",
    list(PACKAGE_OPTIONS.keys()),
    help="Choose a WOW template package. Leave blank for standard generation."
)

selected_key = PACKAGE_OPTIONS.get(selected_label) if selected_label else None
```

### 2. Pass WOW parameters to the API

```python
import requests

# Build the API request
request_payload = {
    "brief": brief_dict,
    "generate_marketing_plan": True,
    "generate_campaign_blueprint": True,
    "generate_social_calendar": True,
    "generate_performance_review": False,
    "generate_creatives": True,
    "include_agency_grade": False,
    "wow_enabled": True,
    "wow_package_key": selected_key,  # Pass the selected package key
}

# Call the backend
response = requests.post(
    "http://localhost:8000/aicmo/generate",
    json=request_payload
)

report = response.json()
```

### 3. Display the WOW markdown and PDF

```python
# Display the WOW report if available
if report.get("wow_markdown"):
    st.markdown("### 📋 WOW Report")
    st.markdown(report["wow_markdown"])
    
    # Optionally: Convert to PDF and offer download
    # (You can use reportlab or similar to generate PDF bytes)
    # st.download_button(
    #     "📥 Download PDF",
    #     data=pdf_bytes,
    #     file_name=f"report_{report['wow_package_key']}.pdf",
    #     mime="application/pdf"
    # )
else:
    st.info("No WOW package selected. Showing standard report.")
    # Display regular report sections
```

### 4. Optional: Show rules for the selected package

```python
from backend.services.wow_reports import get_wow_rules_for_package

# Display what the client should expect for this package
if selected_key:
    rules = get_wow_rules_for_package(selected_key)
    
    if rules:
        with st.expander("📊 Package Guidelines"):
            for rule_name, rule_value in rules.items():
                st.metric(rule_name, rule_value)
```

## Complete Example

Here's a complete example of integrating WOW into a Streamlit page:

```python
import streamlit as st
import requests
import json
from datetime import datetime

st.set_page_config(page_title="AICMO WOW Generator", layout="wide")
st.title("AICMO WOW Report Generator")

# Package selection
PACKAGE_OPTIONS = {
    "Quick Social Pack (Basic)": "quick_social_basic",
    "Strategy + Campaign Pack (Standard)": "strategy_campaign_standard",
    "Full-Funnel Growth Suite (Premium)": "full_funnel_premium",
    "Launch & GTM Pack": "launch_gtm",
    "Brand Turnaround Lab": "brand_turnaround",
    "Retention & CRM Booster": "retention_crm",
    "Performance Audit & Revamp": "performance_audit",
}

col1, col2 = st.columns([2, 1])

with col1:
    selected_label = st.selectbox(
        "Select WOW Package",
        ["(No WOW Package)"] + list(PACKAGE_OPTIONS.keys()),
    )
    selected_key = PACKAGE_OPTIONS.get(selected_label) if selected_label != "(No WOW Package)" else None

with col2:
    if selected_key:
        st.success(f"✅ {selected_label}")
    else:
        st.info("Standard report (no WOW wrapper)")

# Brief input (simplified for example)
st.subheader("Client Brief")

col_left, col_right = st.columns(2)

with col_left:
    brand_name = st.text_input("Brand Name", value="Acme Corp")
    category = st.text_input("Category", value="B2B SaaS")
    primary_goal = st.text_input("Primary Goal", value="Lead generation")

with col_right:
    target_audience = st.text_input("Target Audience", value="Marketing managers at mid-market companies")
    city = st.text_input("City", value="San Francisco")
    region = st.text_input("Region", value="USA")

# Generate button
if st.button("🚀 Generate WOW Report", type="primary"):
    # Build brief dict
    brief_dict = {
        "brand": {
            "brand_name": brand_name,
            "industry": category,
            "city": city,
        },
        "goal": {
            "primary_goal": primary_goal,
        },
        "audience": {
            "primary_customer": target_audience,
        },
        "strategy_extras": {
            "brand_adjectives": ["innovative", "reliable"],
        }
    }
    
    # API request
    with st.spinner("Generating report..."):
        try:
            response = requests.post(
                "http://localhost:8000/aicmo/generate",
                json={
                    "brief": brief_dict,
                    "generate_marketing_plan": True,
                    "generate_campaign_blueprint": True,
                    "generate_social_calendar": True,
                    "wow_enabled": True,
                    "wow_package_key": selected_key,
                }
            )
            
            if response.status_code == 200:
                report = response.json()
                
                # Display WOW markdown if available
                if report.get("wow_markdown"):
                    st.success(f"✅ WOW Report Generated ({selected_label})")
                    st.markdown(report["wow_markdown"])
                    
                    # Download button
                    st.download_button(
                        "📥 Download as Markdown",
                        data=report["wow_markdown"],
                        file_name=f"wow_report_{selected_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                        mime="text/markdown"
                    )
                else:
                    st.info("Standard report generated (no WOW wrapper).")
                    if report.get("marketing_plan"):
                        st.subheader("Marketing Plan")
                        st.json(report["marketing_plan"], expanded=False)
            else:
                st.error(f"API Error: {response.status_code}")
                st.text(response.text)
                
        except Exception as e:
            st.error(f"Request failed: {e}")
```

## Testing Locally

To test the WOW integration:

```bash
# 1. Ensure backend is running
python -m uvicorn backend.main:app --reload

# 2. Run Streamlit
streamlit run streamlit_app.py

# 3. Fill out the form and select a WOW package
# 4. Check that wow_markdown appears in the response
```

## API Response Structure

When you request with WOW enabled, the response includes:

```json
{
  "marketing_plan": { ... },
  "campaign_blueprint": { ... },
  "social_calendar": { ... },
  "performance_review": null,
  "creatives": { ... },
  "persona_cards": [ ... ],
  "action_plan": { ... },
  "extra_sections": {},
  "auto_detected_competitors": null,
  "competitor_visual_benchmark": null,
  "wow_markdown": "# Brand Name – Quick Social Pack (Basic)\n\n## 14-Day Social Calendar\n\n{{calendar_14_day_table}}\n\n...",
  "wow_package_key": "quick_social_basic"
}
```

## Troubleshooting

### "wow_markdown is null"
- Check that `wow_enabled: true` was sent
- Check that `wow_package_key` is one of the valid keys
- Check backend logs for any WOW processing errors

### "Placeholders still showing as {{...}}"
- This means some placeholder keys weren't found in the brief
- This is normal and the placeholders will be stripped in the final output
- Check that all required brief fields are provided (brand_name, category, etc.)

### "Backend responding with 400/422"
- Validate your brief dict matches the ClientInputBrief schema
- Check that all required fields are present
- See backend logs for detailed validation errors

## Next Steps

1. **PDF Export**: Integrate PDF generation using reportlab or similar
2. **Custom Templates**: Add more WOW templates in `aicmo/presets/wow_templates.py`
3. **Custom Rules**: Add or modify rules in `aicmo/presets/wow_rules.py`
4. **Email Integration**: Send reports via email using the wow_markdown
5. **Template Versioning**: Add versioning to handle template updates

## Questions?

See `aicmo/presets/INTEGRATION_GUIDE.py` for additional Python code examples.
