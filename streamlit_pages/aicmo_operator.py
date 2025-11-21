"""AICMO Operator Dashboard – Generate, revise, and export marketing reports."""

import json
import os
from typing import Any, Optional

import httpx
import streamlit as st

# Phase 5: Import industry presets
from aicmo.presets.industry_presets import list_available_industries, get_industry_preset

API_BASE = os.getenv("API_BASE_URL") or os.getenv("API_BASE") or "http://localhost:8000"


def _api_base_for_request():
    b = (os.getenv("API_BASE_URL") if os.getenv("API_BASE_URL") is not None else API_BASE) or ""
    return b.rstrip("/")


TIMEOUT = int(os.getenv("API_TIMEOUT", "20"))


def _api_url(path: str, base: Optional[str] = None) -> str:
    base_val = base if base is not None else _api_base_for_request()
    base_str = base_val.rstrip("/") if base_val else ""
    path = f"/{path.lstrip('/')}"
    return f"{base_str}{path}"


def _http_client(timeout: int) -> httpx.Client:
    return httpx.Client(timeout=timeout, headers={"Accept": "application/json"})


def post_json(
    path: str,
    payload: dict[str, Any],
    *,
    base: Optional[str] = None,
    timeout: Optional[int] = None,
) -> dict[str, Any]:
    url = _api_url(path, base)
    with _http_client(timeout or TIMEOUT) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
    return {"url": url, "ok": True, "data": data}


st.set_page_config(page_title="AICMO Operator", page_icon="🎯", layout="wide")

st.title("AICMO Operator Dashboard")

with st.sidebar:
    st.subheader("Settings")
    api_base_input = st.text_input("API Base", value=API_BASE, help="e.g., http://localhost:8000")
    timeout_input = st.number_input(
        "Timeout (seconds)", value=TIMEOUT, min_value=5, max_value=120, step=5
    )

    # Phase 5: Industry selector
    st.divider()
    st.subheader("Industry Preset (Optional)")
    available_industries = list_available_industries()
    industry_key = st.selectbox(
        "Select Industry",
        options=["none"] + available_industries,
        help="Choose an industry preset to guide content generation",
    )

    # Display selected preset info
    if industry_key != "none":
        preset = get_industry_preset(industry_key)
        if preset:
            st.info(f"**{preset.name}**: {preset.description}")
            with st.expander("View preset details"):
                st.markdown("**Priority Channels**: " + ", ".join(preset.priority_channels))
                st.markdown("**Sample KPIs**: " + ", ".join(preset.sample_kpis))
                st.markdown("**Default Tone**: " + preset.default_tone)

# ========== TAB 1: BRIEF INTAKE & GENERATION ==========

tab_brief, tab_plan, tab_creatives, tab_export = st.tabs(
    ["Brief & Generate", "Marketing Plan", "Creatives", "Export"]
)

with tab_brief:
    st.header("Client Brief & Generation")
    st.caption("Fill in the brief below and generate your marketing report.")

    # Simplified brief form (operator enters as JSON)
    brief_json_text = st.text_area(
        "Client Brief (JSON)",
        height=300,
        placeholder=json.dumps(
            {
                "brand": {
                    "brand_name": "TestBrand",
                    "industry": "SaaS",
                    "description": "Marketing automation tool",
                },
                "audience": {
                    "primary_customer": "Marketing directors",
                    "pain_points": ["Too many tools", "Inconsistent messaging"],
                    "online_hangouts": ["LinkedIn", "Twitter"],
                },
                "goal": {
                    "primary_goal": "Increase lead generation",
                    "timeline": "90 days",
                },
                "voice": {"tone_of_voice": ["professional", "clear"]},
                "product_service": {"items": []},
                "assets_constraints": {"focus_platforms": ["LinkedIn", "Twitter"]},
                "operations": {"needs_calendar": True},
                "strategy_extras": {
                    "brand_adjectives": ["reliable", "innovative"],
                    "success_30_days": "3 qualified leads per day",
                },
            },
            indent=2,
        ),
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        gen_marketing = st.checkbox("Marketing Plan", value=True)
    with col2:
        gen_campaign = st.checkbox("Campaign Blueprint", value=True)
    with col3:
        gen_creatives = st.checkbox("Creatives", value=True)

    if st.button("Generate Report"):
        try:
            brief_data = json.loads(brief_json_text)
            payload = {
                "brief": brief_data,
                "generate_marketing_plan": gen_marketing,
                "generate_campaign_blueprint": gen_campaign,
                "generate_social_calendar": True,
                "generate_performance_review": False,
                "generate_creatives": gen_creatives,
                "industry_key": None if industry_key == "none" else industry_key,  # Phase 5
            }

            result = post_json(
                "/aicmo/generate",
                payload,
                base=api_base_input,
                timeout=int(timeout_input),
            )

            if result.get("ok"):
                st.session_state.output_report = result["data"]
                st.session_state.input_brief = brief_data
                st.success("Report generated successfully!")
                st.rerun()
            else:
                st.error("Failed to generate report")
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON: {e}")
        except httpx.RequestError as e:
            st.error(f"Request error: {e}")
        except httpx.HTTPStatusError as e:
            st.error(f"HTTP {e.response.status_code}: {e.response.text}")


# ========== TAB 2: MARKETING PLAN ==========

with tab_plan:
    if "output_report" not in st.session_state:
        st.info("Generate a report in the 'Brief & Generate' tab first.")
    else:
        output_obj = st.session_state.output_report

        st.header("Marketing Plan & Strategy")

        mp = output_obj.get("marketing_plan")
        if not mp:
            st.warning("No marketing plan in this report.")
        else:
            st.markdown("### Executive Summary")
            st.markdown(mp.get("executive_summary", ""))

            st.markdown("### Situation Analysis")
            st.markdown(mp.get("situation_analysis", ""))

            st.markdown("### Strategy")
            st.markdown(mp.get("strategy", ""))

            st.markdown("### Strategy Pillars")
            pillars = mp.get("pillars", [])
            if pillars:
                for p in pillars:
                    st.markdown(
                        f"- **{p.get('name')}** – {p.get('description') or ''} "
                        f"_(KPI impact: {p.get('kpi_impact') or 'N/A'})_"
                    )
            else:
                st.caption("No explicit pillars defined.")

            # Messaging pyramid
            messaging_pyramid = mp.get("messaging_pyramid")
            if messaging_pyramid:
                st.markdown("### Messaging Pyramid")
                st.markdown(f"**Brand promise:** {messaging_pyramid.get('promise', '')}")
                if messaging_pyramid.get("key_messages"):
                    st.markdown("**Key messages:**")
                    for msg in messaging_pyramid.get("key_messages", []):
                        st.markdown(f"- {msg}")
                if messaging_pyramid.get("proof_points"):
                    st.markdown("**Proof points:**")
                    for pr_item in messaging_pyramid.get("proof_points", []):
                        st.markdown(f"- {pr_item}")
                if messaging_pyramid.get("values"):
                    st.markdown("**Values / personality:**")
                    for v in messaging_pyramid.get("values", []):
                        st.markdown(f"- {v}")

            # SWOT
            swot = mp.get("swot")
            if swot:
                st.markdown("### SWOT Snapshot")
                col_s, col_w, col_o, col_t = st.columns(4)
                with col_s:
                    st.markdown("**Strengths**")
                    for x in swot.get("strengths", []):
                        st.markdown(f"- {x}")
                with col_w:
                    st.markdown("**Weaknesses**")
                    for x in swot.get("weaknesses", []):
                        st.markdown(f"- {x}")
                with col_o:
                    st.markdown("**Opportunities**")
                    for x in swot.get("opportunities", []):
                        st.markdown(f"- {x}")
                with col_t:
                    st.markdown("**Threats**")
                    for x in swot.get("threats", []):
                        st.markdown(f"- {x}")

            # Competitor snapshot
            competitor_snapshot = mp.get("competitor_snapshot")
            if competitor_snapshot:
                st.markdown("### Competitor Snapshot")
                st.markdown(competitor_snapshot.get("narrative", ""))
                if competitor_snapshot.get("common_patterns"):
                    st.markdown("**Common patterns:**")
                    for ptn in competitor_snapshot.get("common_patterns", []):
                        st.markdown(f"- {ptn}")
                if competitor_snapshot.get("differentiation_opportunities"):
                    st.markdown("**Differentiation opportunities:**")
                    for opp in competitor_snapshot.get("differentiation_opportunities", []):
                        st.markdown(f"- {opp}")

            # Persona cards
            persona_cards = output_obj.get("persona_cards", [])
            if persona_cards:
                st.markdown("### Persona Cards")
                for pc in persona_cards:
                    with st.expander(pc.get("name", "Persona"), expanded=False):
                        st.markdown(f"**Demographics:** {pc.get('demographics', '')}")
                        st.markdown(f"**Psychographics:** {pc.get('psychographics', '')}")
                        if pc.get("pain_points"):
                            st.markdown("**Pain points:**")
                            for item in pc.get("pain_points", []):
                                st.markdown(f"- {item}")
                        if pc.get("triggers"):
                            st.markdown("**Triggers:**")
                            for item in pc.get("triggers", []):
                                st.markdown(f"- {item}")
                        if pc.get("objections"):
                            st.markdown("**Objections:**")
                            for item in pc.get("objections", []):
                                st.markdown(f"- {item}")
                        if pc.get("content_preferences"):
                            st.markdown("**Content preferences:**")
                            for item in pc.get("content_preferences", []):
                                st.markdown(f"- {item}")
                        if pc.get("primary_platforms"):
                            st.markdown(
                                f"**Primary platforms:** {', '.join(pc.get('primary_platforms', []))}"
                            )
                        st.markdown(f"**Tone preference:** {pc.get('tone_preference', '')}")

            # Action plan
            action_plan = output_obj.get("action_plan")
            if action_plan:
                st.markdown("### Next 30 days – Action plan")
                if action_plan.get("quick_wins"):
                    st.markdown("**Quick wins:**")
                    for item in action_plan.get("quick_wins", []):
                        st.markdown(f"- {item}")
                if action_plan.get("next_10_days"):
                    st.markdown("**Next 10 days:**")
                    for item in action_plan.get("next_10_days", []):
                        st.markdown(f"- {item}")
                if action_plan.get("next_30_days"):
                    st.markdown("**Next 30 days:**")
                    for item in action_plan.get("next_30_days", []):
                        st.markdown(f"- {item}")
                if action_plan.get("risks"):
                    st.markdown("**Risks & watchouts:**")
                    for item in action_plan.get("risks", []):
                        st.markdown(f"- {item}")


# ========== TAB 3: CREATIVES ==========

with tab_creatives:
    if "output_report" not in st.session_state:
        st.info("Generate a report in the 'Brief & Generate' tab first.")
    else:
        output_obj = st.session_state.output_report
        cr = output_obj.get("creatives")

        st.header("Creatives & Multi-Channel Adaptation")

        if cr is None:
            st.info("No creatives block was generated for this draft.")
        else:
            # Creative rationale
            rationale = cr.get("rationale")
            if rationale:
                st.markdown("#### Creative rationale")
                st.markdown(rationale.get("strategy_summary", ""))
                if rationale.get("psychological_triggers"):
                    st.markdown("**Psychological triggers used:**")
                    for t in rationale.get("psychological_triggers", []):
                        st.markdown(f"- {t}")
                st.markdown(f"**Audience fit:** {rationale.get('audience_fit', '')}")
                if rationale.get("risk_notes"):
                    st.markdown(f"**Risks / guardrails:** {rationale.get('risk_notes', '')}")

            st.markdown("---")
            st.markdown("#### Platform-specific adaptations")

            channel_variants = cr.get("channel_variants", [])
            if channel_variants:
                table_data = [
                    {
                        "Platform": v.get("platform", ""),
                        "Format": v.get("format", ""),
                        "Hook": v.get("hook", ""),
                        "Caption": v.get("caption", ""),
                    }
                    for v in channel_variants
                ]
                st.table(table_data)
            else:
                st.caption("No platform-specific variants generated.")

            st.markdown("---")
            st.markdown("#### Email subject lines")
            email_subject_lines = cr.get("email_subject_lines", [])
            if email_subject_lines:
                for sline in email_subject_lines:
                    st.markdown(f"- {sline}")
            else:
                st.caption("No email subject lines generated.")

            st.markdown("---")
            st.markdown("#### Tone/style variants")
            tone_variants = cr.get("tone_variants", [])
            if tone_variants:
                for tv in tone_variants:
                    st.markdown(
                        f"- **{tv.get('tone_label', '')}:** {tv.get('example_caption', '')}"
                    )
            else:
                st.caption("No tone variants generated.")

            # Hook insights
            hook_insights = cr.get("hook_insights", [])
            if hook_insights:
                st.markdown("---")
                st.markdown("#### Hook insights (why these work)")
                for hi in hook_insights:
                    st.markdown(f"- **{hi.get('hook', '')}** – {hi.get('insight', '')}")

            # CTA library
            cta_library = cr.get("cta_library", [])
            if cta_library:
                st.markdown("---")
                st.markdown("#### CTA library")
                table_data = [
                    {
                        "Label": cta.get("label", ""),
                        "CTA": cta.get("text", ""),
                        "Context": cta.get("usage_context", ""),
                    }
                    for cta in cta_library
                ]
                st.table(table_data)

            # Offer angles
            offer_angles = cr.get("offer_angles", [])
            if offer_angles:
                st.markdown("---")
                st.markdown("#### Offer angles")
                for angle in offer_angles:
                    st.markdown(f"- **{angle.get('label', '')}:** {angle.get('description', '')}")
                    st.markdown(f"  - Example: {angle.get('example_usage', '')}")

            st.markdown("---")
            st.markdown("#### Generic hooks & captions")

            hooks = cr.get("hooks", [])
            if hooks:
                st.markdown("**Hooks:**")
                for h in hooks:
                    st.markdown(f"- {h}")

            captions = cr.get("captions", [])
            if captions:
                st.markdown("**Captions:**")
                for c in captions:
                    st.markdown(f"- {c}")

            scripts = cr.get("scripts", [])
            if scripts:
                st.markdown("**Ad script snippets:**")
                for stext in scripts:
                    st.markdown(f"- {stext}")


# ========== TAB 4: EXPORT ==========

with tab_export:
    if "output_report" not in st.session_state or "input_brief" not in st.session_state:
        st.info("Generate a report in the 'Brief & Generate' tab first.")
    else:
        st.header("Export Report")

        export_format = st.selectbox("Export format", ["PDF", "PPTX", "ZIP"])

        if st.button("Export"):
            try:
                payload = {
                    "brief": st.session_state.input_brief,
                    "output": st.session_state.output_report,
                }

                if export_format == "PDF":
                    # For PDF, we need to pass markdown
                    from aicmo.io.client_reports import generate_output_report_markdown

                    md = generate_output_report_markdown(
                        st.session_state.input_brief,
                        st.session_state.output_report,
                    )
                    payload["markdown"] = md

                    result = post_json(
                        "/aicmo/export/pdf",
                        {"markdown": md},
                        base=api_base_input,
                        timeout=int(timeout_input),
                    )

                elif export_format == "PPTX":
                    result = post_json(
                        "/aicmo/export/pptx",
                        payload,
                        base=api_base_input,
                        timeout=int(timeout_input),
                    )

                else:  # ZIP
                    result = post_json(
                        "/aicmo/export/zip",
                        payload,
                        base=api_base_input,
                        timeout=int(timeout_input),
                    )

                if result.get("ok"):
                    st.success("Export successful!")
                    # In a real scenario, you'd download the file here
                    st.code(f"File ready at: {result['url']}", language="text")
                else:
                    st.error("Export failed")

            except httpx.RequestError as e:
                st.error(f"Request error: {e}")
            except httpx.HTTPStatusError as e:
                st.error(f"HTTP {e.response.status_code}: {e.response.text}")
            except Exception as e:
                st.error(f"Error: {e}")
