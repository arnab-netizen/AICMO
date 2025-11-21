import io
import json
import os
import re
from typing import Dict, Any, Optional, List

import requests
import streamlit as st
from openai import OpenAI

from aicmo.io.client_reports import (
    ClientInputBrief,
    AICMOOutputReport,
    generate_output_report_markdown,
)

# Try to import industry presets if available
try:
    from aicmo.presets.industry_presets import INDUSTRY_PRESETS
except Exception:  # optional dependency
    INDUSTRY_PRESETS: Dict[str, Any] = {}


# -------------------------------------------------
# Page config
# -------------------------------------------------

st.set_page_config(
    page_title="AICMO – Operator Cockpit",
    layout="wide",
)

st.title("AICMO – Operator Cockpit")
st.caption(
    "Step 1: Brief & generate → Step 2: Workshop → Step 3: Learn & improve → Step 4: Deliver."
)

# -------------------------------------------------
# Session state setup
# -------------------------------------------------

defaults = {
    "raw_client_text": "",
    "client_brief_json": "",
    "aicmo_output_json": "",
    "current_version": 0,
    "status_message": "",
    "final_report_md": "",
    "industry_key": None,
    "case_name": "New Client Case",
    "client_name": "",
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# -------------------------------------------------
# Helper: extract text from uploaded file
# -------------------------------------------------


def extract_text_from_uploaded_file(upload) -> str:
    """
    Try to extract text from PDF / DOCX / TXT / MD.

    NOTE:
    - For PDFs and DOCX, you need extra libs installed:
        pip install pdfplumber python-docx
    """
    if upload is None:
        return ""

    filename = upload.name.lower()
    data = upload.read()

    if filename.endswith(".txt") or filename.endswith(".md"):
        try:
            return data.decode("utf-8", errors="ignore")
        except Exception:
            return ""

    if filename.endswith(".pdf"):
        try:
            import pdfplumber  # type: ignore

            text_chunks = []
            with pdfplumber.open(io.BytesIO(data)) as pdf:
                for page in pdf.pages:
                    text_chunks.append(page.extract_text() or "")
            return "\n\n".join(text_chunks)
        except Exception as e:
            st.error(f"PDF extraction failed: {e}")
            return ""

    if filename.endswith(".docx"):
        try:
            import docx  # type: ignore

            doc = docx.Document(io.BytesIO(data))
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception as e:
            st.error(f"DOCX extraction failed: {e}")
            return ""

    # Fallback – try to treat everything else as text
    try:
        return data.decode("utf-8", errors="ignore")
    except Exception:
        return ""


# -------------------------------------------------
# LLM helper – premium rewrite for key sections
# -------------------------------------------------


@st.cache_resource(show_spinner=False)
def get_openai_client() -> Optional[OpenAI]:
    """Create a cached OpenAI client if API key is available."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def enhance_marketing_plan_with_llm(
    brief: ClientInputBrief,
    output: AICMOOutputReport,
) -> None:
    """
    Use gpt-4o-mini to rewrite the Executive Summary + Strategy sections
    so they feel like a senior strategist wrote them – specific, on-brief, and non-generic.

    This does NOT change any structure or models, only replaces text fields.
    If anything fails, it silently keeps the original draft.
    """
    client = get_openai_client()
    if client is None:
        return  # no API key → keep stub version

    model = os.getenv("AICMO_MODEL_MAIN", "gpt-4o-mini")

    # Safety: if marketing_plan is missing, do nothing
    mp = getattr(output, "marketing_plan", None)
    if mp is None:
        return

    prompt = f"""
You are a senior marketing strategist at a top global agency.

You are given:
1) A structured client brief (JSON).
2) A basic draft for the marketing plan.

Your job:
- Rewrite ONLY the Executive Summary and Strategy sections.
- Make them SPECIFIC to the brand, audience, industry, and primary goal.
- Avoid generic phrases like "system" or "random acts of marketing".
- Talk directly to the real context (e.g. B2B SaaS, workflow automation, demo bookings).

Return STRICT JSON with exactly these keys:

{{
  "executive_summary": "...",
  "strategy": "..."
}}

[CLIENT BRIEF JSON]
{brief.model_dump_json(indent=2)}

[CURRENT EXECUTIVE SUMMARY]
{mp.executive_summary or ""}

[CURRENT STRATEGY]
{mp.strategy or ""}
"""

    try:
        resp = client.messages.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=900,
        )
        text = resp.choices[0].message.content.strip()

        data = json.loads(text)
        new_exec = data.get("executive_summary")
        new_strat = data.get("strategy")

        if isinstance(new_exec, str) and new_exec.strip():
            mp.executive_summary = new_exec.strip()

        if isinstance(new_strat, str) and new_strat.strip():
            mp.strategy = new_strat.strip()

    except Exception as e:
        # For safety, we don't break the UI if LLM fails
        st.debug(f"LLM enhancement failed, keeping base draft. Error: {e}")
        return


# -------------------------------------------------
# Helper: build ClientInputBrief from raw text
# -------------------------------------------------

# -------------------------------------------------
# Helper parsers for structured brief extraction
# -------------------------------------------------


def _parse_kv_lines(lines: List[str]) -> dict:
    """
    Parse simple 'Key: Value' lines, including markdown like '**Key:** Value'.
    Keys are normalised to lowercase without surrounding punctuation.
    """
    kv: dict[str, str] = {}
    for raw in lines:
        line = raw.strip()
        if not line or ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        # strip markdown and punctuation from key
        key = re.sub(r"^\W+|\W+$", "", key)
        key = key.lower()

        value = value.strip()
        if key and value:
            kv[key] = value
    return kv


def _collect_block_after_heading(
    lines: List[str],
    heading_substring: str,
    as_list: bool = True,
) -> List[str] | str | None:
    """
    Collect text lines after a heading that contains heading_substring (case-insensitive),
    until a blank line or another heading-like line.

    If as_list=True, returns list of cleaned bullet lines.
    If as_list=False, returns a single joined string.
    """
    heading_substring = heading_substring.lower()
    capture = False
    collected: List[str] = []

    for raw in lines:
        line = raw.rstrip("\n")
        stripped = line.strip()
        lower = stripped.lower()

        if not capture:
            # detect heading lines like '## Primary Goal' or 'Primary Goal'
            if heading_substring in lower and (
                stripped.startswith("#") or stripped.lower().startswith(heading_substring)
            ):
                capture = True
            continue

        # once capturing, decide when to stop
        if not stripped:
            if collected:
                break
            else:
                continue

        # stop if a new markdown heading starts
        if stripped.startswith("#"):
            break

        # heuristically stop on a new labelled section like 'Something:'
        if re.match(r"^[A-Z0-9\*\_].+:", stripped):
            break

        # otherwise, treat as content
        cleaned = stripped.lstrip("-*•").strip()
        if cleaned:
            collected.append(cleaned)

    if not collected:
        return None

    if as_list:
        return collected
    return " ".join(collected)


def _split_csv_like(value: str) -> List[str]:
    return [part.strip() for part in re.split(r"[,\|/]", value) if part.strip()]


def _normalise_business_type(raw: str | None) -> str | None:
    if not raw:
        return None
    low = raw.lower()
    if "b2b" in low:
        if "b2c" in low or "both" in low or "hybrid" in low:
            return "Hybrid"
        return "B2B"
    if "b2c" in low:
        return "B2C"
    return None


def build_brief_from_text(raw_text: str, industry_key: Optional[str] = None) -> ClientInputBrief:
    """
    Parse a semi-structured client brief (like the FlowOps example or the
    AICMO intake template) into a ClientInputBrief.

    - Uses 'Key: Value' style lines where possible.
    - Uses headings like 'Primary Goal', 'Primary Customers', etc. to
      collect bullet lists and paragraphs.
    - NEVER writes literal 'Not specified' – missing fields are None or [].
    """
    lines = raw_text.splitlines()
    kv = _parse_kv_lines(lines)

    # ----- BRAND BASICS -----
    brand_name = kv.get("brand name") or kv.get("brand") or "Client"
    website = kv.get("website") or kv.get("website url")
    industry = kv.get("industry")

    locations_raw = kv.get("location(s)") or kv.get("locations") or kv.get("headquarters")
    locations: List[str] = _split_csv_like(locations_raw) if locations_raw else []

    business_type = _normalise_business_type(kv.get("type of business") or kv.get("business type"))

    # brief description: try explicit, else first non-empty paragraph
    description = kv.get("brief description of the business")
    if not description:
        paragraphs: List[str] = []
        buf: List[str] = []
        for raw in lines:
            stripped = raw.strip()
            if not stripped:
                if buf:
                    paragraphs.append(" ".join(buf))
                    buf = []
                continue
            # ignore very short headings
            if stripped.startswith("#"):
                continue
            buf.append(stripped)
        if buf:
            paragraphs.append(" ".join(buf))
        if paragraphs:
            description = paragraphs[0][:400]

    # ----- AUDIENCE -----
    # Try headings first
    primary_customer_block = _collect_block_after_heading(lines, "primary customer", as_list=False)
    secondary_customer_block = _collect_block_after_heading(
        lines, "secondary customer", as_list=False
    )

    primary_customer = (
        primary_customer_block or kv.get("primary customer") or kv.get("primary customers")
    )
    secondary_customer = secondary_customer_block or kv.get("secondary customer")

    pain_points_block = _collect_block_after_heading(lines, "pain points", as_list=True)
    pain_points: List[str] = pain_points_block or []

    hangouts_block = _collect_block_after_heading(
        lines, "where do they spend time online", as_list=True
    )
    if not hangouts_block:
        hangouts_block = _collect_block_after_heading(
            lines, "where they spend time online", as_list=True
        )
    online_hangouts = hangouts_block or []

    # ----- GOALS -----
    primary_goal = kv.get("primary goal")
    if not primary_goal:
        pg_block = _collect_block_after_heading(lines, "primary goal", as_list=False)
        if pg_block:
            primary_goal = pg_block

    secondary_goal = kv.get("secondary goal")

    timeline = kv.get("goal timeline") or kv.get("timeline")
    kpis_raw = kv.get("kpis that matter most to you") or kv.get("kpis")
    important_kpis = _split_csv_like(kpis_raw) if kpis_raw else []

    # ----- BRAND VOICE -----
    tone_raw = kv.get("tone of voice") or kv.get("tone")
    tone_of_voice = []
    if tone_raw:
        tone_of_voice = [t.strip().lower() for t in _split_csv_like(tone_raw)]

    has_guidelines = bool(kv.get("do you have brand guidelines") or kv.get("brand guidelines"))
    guidelines_link = kv.get("if yes, please share link") or kv.get("guidelines link")
    preferred_colors = kv.get("preferred colors / visual style") or kv.get(
        "preferred colours / visual style"
    )

    competitors_like = _split_csv_like(kv.get("competitors you like (links)") or "")
    competitors_dislike = _split_csv_like(kv.get("competitors you dislike (links)") or "")

    # ----- STRATEGIC INPUTS -----
    brand_adjectives_raw = kv.get("3 adjectives that define your brand")
    brand_adjectives = _split_csv_like(brand_adjectives_raw) if brand_adjectives_raw else []

    success_30 = kv.get("what does success look like in the next 30 days")
    must_include = kv.get("messages you must include")
    must_avoid = kv.get("messages you must avoid")
    tagline = kv.get("tagline")
    extra_notes = kv.get("anything else we should know")

    # ----- BUILD ClientInputBrief -----
    brief = ClientInputBrief(
        brand={
            "brand_name": brand_name,
            "website": website,
            "social_links": [],
            "industry": industry,
            "locations": locations,
            "business_type": business_type,
            "description": description,
        },
        audience={
            "primary_customer": primary_customer or "Primary customer not yet summarised",
            "secondary_customer": secondary_customer,
            "pain_points": pain_points,
            "online_hangouts": online_hangouts,
        },
        goal={
            "primary_goal": primary_goal,
            "secondary_goal": secondary_goal,
            "timeline": timeline,
            "kpis": important_kpis,
        },
        voice={
            "tone_of_voice": tone_of_voice,
            "has_guidelines": has_guidelines,
            "guidelines_link": guidelines_link,
            "preferred_colors": preferred_colors,
            "competitors_like": competitors_like,
            "competitors_dislike": competitors_dislike,
        },
        product_service={
            "items": [],
            "current_offers": None,
            "testimonials_or_proof": None,
        },
        assets_constraints={
            "already_posting": False,
            "current_social_links": [],
            "content_that_worked": None,
            "content_that_failed": None,
            "constraints": [],
            "focus_platforms": [],
            "avoid_platforms": [],
        },
        operations={
            "approval_frequency": None,
            "needs_calendar": True,
            "wants_posting_and_scheduling": False,
            "upcoming_events": None,
            "promo_budget_range": None,
        },
        strategy_extras={
            "brand_adjectives": brand_adjectives,
            "success_30_days": success_30,
            "must_include_messages": must_include,
            "must_avoid_messages": must_avoid,
            "tagline": tagline,
            "extra_notes": extra_notes,
        },
    )

    return brief


# -------------------------------------------------
# Helpers: backend calls
# -------------------------------------------------


def _prepare_payload(data: Any) -> str:
    """
    Convert Pydantic models and other non-JSON objects to JSON string.
    Handles HttpUrl and other special types.
    """
    return json.dumps(data, default=str)


def call_backend_generate(
    api_base_url: str,
    brief: ClientInputBrief,
    options: Dict[str, bool],
) -> AICMOOutputReport:
    """
    Call FastAPI backend to generate a PRELIMINARY AICMOOutputReport.
    """
    payload: Dict[str, Any] = {
        "brief": brief.model_dump(),
        "generate_marketing_plan": options["marketing_plan"],
        "generate_campaign_blueprint": options["campaign_blueprint"],
        "generate_social_calendar": options["social_calendar"],
        "generate_performance_review": options["performance_review"],
        "generate_creatives": options["creatives"],
    }

    resp = requests.post(
        f"{api_base_url}/aicmo/generate",
        data=_prepare_payload(payload),
        headers={"Content-Type": "application/json"},
    )
    resp.raise_for_status()
    return AICMOOutputReport(**resp.json())


def call_backend_revision(
    api_base_url: str,
    brief: ClientInputBrief,
    current_output: AICMOOutputReport,
    instructions: str,
    attachment: Optional[bytes],
    attachment_name: Optional[str],
) -> AICMOOutputReport:
    """
    Call backend to revise the draft based on operator feedback
    + optional external reports/analysis attachments.
    """
    meta = {
        "brief": brief.model_dump(),
        "current_output": current_output.model_dump(),
        "instructions": instructions,
    }

    files: Dict[str, Any] = {
        "meta": (None, json.dumps(meta, default=str), "application/json"),
    }

    if attachment is not None and attachment_name:
        files["attachment"] = (attachment_name, attachment, "application/octet-stream")

    resp = requests.post(f"{api_base_url}/aicmo/revise", files=files)
    resp.raise_for_status()
    return AICMOOutputReport(**resp.json())


def call_backend_export_zip(
    api_base_url: str,
    brief: ClientInputBrief,
    output: AICMOOutputReport,
) -> bytes:
    payload = {
        "brief": brief.model_dump(),
        "output": output.model_dump(),
    }
    resp = requests.post(
        f"{api_base_url}/aicmo/export/zip",
        data=_prepare_payload(payload),
        headers={"Content-Type": "application/json"},
    )
    resp.raise_for_status()
    return resp.content


def call_backend_export_pdf(
    api_base_url: str,
    report_md: str,
) -> bytes:
    payload = {"markdown": report_md}
    resp = requests.post(f"{api_base_url}/aicmo/export/pdf", json=payload)
    resp.raise_for_status()
    return resp.content


def call_backend_export_pptx(
    api_base_url: str,
    brief: ClientInputBrief,
    output: AICMOOutputReport,
) -> bytes:
    payload = {
        "brief": brief.model_dump(),
        "output": output.model_dump(),
    }
    resp = requests.post(f"{api_base_url}/aicmo/export/pptx", json=payload)
    resp.raise_for_status()
    return resp.content


# -------------------------------------------------
# Top navigation (no sidebar)
# -------------------------------------------------

tab_brief, tab_workshop, tab_learn, tab_deliver = st.tabs(
    ["1️⃣ Brief & Generate", "2️⃣ Workshop", "3️⃣ Learn & Improve", "4️⃣ Deliverables"]
)

# -------------------------------------------------
# TAB 1 – Brief & Generate
# -------------------------------------------------

with tab_brief:
    st.subheader("1. Client Brief & Generation")

    col_top_left, col_top_right = st.columns([2, 1])

    with col_top_left:
        st.session_state["case_name"] = st.text_input(
            "Case name",
            value=st.session_state["case_name"],
        )
        st.session_state["client_name"] = st.text_input(
            "Client / Brand name",
            value=st.session_state["client_name"],
        )

    with col_top_right:
        api_base_url = st.text_input(
            "API base URL",
            value="http://localhost:8000",
            help="FastAPI backend base URL, e.g. http://localhost:8000",
        )

        if st.session_state["status_message"]:
            st.info(st.session_state["status_message"])
        else:
            st.caption("No status yet.")

    st.markdown("---")

    # Industry presets inside Brief tab
    col_industry, col_industry_desc = st.columns([1, 2])
    with col_industry:
        if INDUSTRY_PRESETS:
            current_key = st.session_state.get("industry_key") or list(INDUSTRY_PRESETS.keys())[0]
            industry_key = st.selectbox(
                "Industry preset",
                options=list(INDUSTRY_PRESETS.keys()),
                index=list(INDUSTRY_PRESETS.keys()).index(current_key),
                format_func=lambda x: INDUSTRY_PRESETS[x].name,
            )
            st.session_state["industry_key"] = industry_key
        else:
            st.caption("No industry presets configured yet.")
            industry_key = None
    with col_industry_desc:
        if INDUSTRY_PRESETS and industry_key:
            st.markdown(f"**Preset:** {INDUSTRY_PRESETS[industry_key].description}")

    st.markdown("---")
    st.markdown("#### Attach client brief or paste text")

    uploaded_brief = st.file_uploader(
        "Attach client input (PDF / DOCX / TXT / MD)",
        type=["pdf", "docx", "txt", "md", "markdown"],
    )

    col_a, col_b = st.columns([1, 2])

    with col_a:
        if st.button("📄 Extract text from attached file"):
            if uploaded_brief is None:
                st.error("Please attach a file first.")
            else:
                text = extract_text_from_uploaded_file(uploaded_brief)
                if text.strip():
                    st.session_state["raw_client_text"] = text
                    st.success("Text extracted. Review or edit it on the right.")
                else:
                    st.error("No text could be extracted from this file.")

    with col_b:
        st.caption("You can still paste or edit the client brief manually.")

    raw_text = st.text_area(
        "Client input (plain text – NOT JSON)",
        value=st.session_state["raw_client_text"],
        height=260,
        placeholder=(
            "Paste client brief / notes / email here.\n\n"
            "Suggested structure:\n"
            "- Who they are\n"
            "- Who they sell to\n"
            "- Goals (1–3 months)\n"
            "- Main platforms\n"
            "- Constraints (no paid ads, approvals, etc.)"
        ),
    )
    st.session_state["raw_client_text"] = raw_text

    st.markdown("---")
    st.markdown("#### What should AICMO generate?")

    col_opts1, col_opts2 = st.columns(2)
    with col_opts1:
        opt_mp = st.checkbox("Strategic marketing plan", value=True)
        opt_cb = st.checkbox("Campaign blueprint", value=True)
        opt_sc = st.checkbox("Social / content calendar", value=True)
    with col_opts2:
        opt_pr = st.checkbox("Performance review (if data exists)", value=False)
        opt_cr = st.checkbox("Creatives (hooks, captions, scripts, variants)", value=True)

    options = {
        "marketing_plan": opt_mp,
        "campaign_blueprint": opt_cb,
        "social_calendar": opt_sc,
        "performance_review": opt_pr,
        "creatives": opt_cr,
    }

    st.caption(
        "Note: Advanced elements like messaging pyramid, SWOT, competitor snapshot, persona cards, "
        "30-day action plan, CTA library and offer angles are bundled inside these 5 modules."
    )

    if st.button("🚀 Run AICMO – generate draft"):
        if not raw_text.strip():
            st.error("Please provide some client input text (or attach a file).")
        else:
            try:
                industry_key = st.session_state.get("industry_key") or "b2b_saas"
                brief_obj = build_brief_from_text(raw_text, industry_key)
                st.session_state["client_brief_json"] = brief_obj.model_dump_json(indent=2)

                with st.spinner("AICMO is generating the preliminary draft…"):
                    output_obj = call_backend_generate(api_base_url, brief_obj, options)

                    # OPTIONAL premium rewrite of key sections via gpt-4o-mini
                    try:
                        enhance_marketing_plan_with_llm(brief_obj, output_obj)
                    except Exception as e:
                        st.warning(f"LLM enhancement failed, using base draft as-is. Error: {e}")

                st.session_state["aicmo_output_json"] = output_obj.model_dump_json(indent=2)
                st.session_state["current_version"] += 1
                st.session_state["status_message"] = (
                    f"Draft v{st.session_state['current_version']} generated."
                )
                st.success("Draft generated. Go to the Workshop tab to review section by section.")
            except Exception as e:
                st.session_state["status_message"] = f"Generation failed: {e}"
                st.exception(e)

    if st.session_state["client_brief_json"]:
        st.markdown("##### Quick snapshot")
        try:
            b = ClientInputBrief.model_validate_json(st.session_state["client_brief_json"])
            st.markdown(
                f"- **Brand:** {b.brand.brand_name}\n"
                f"- **Primary customer:** {b.audience.primary_customer}\n"
                f"- **Primary goal:** {b.goal.primary_goal}\n"
                f"- **Preset:** "
                f"{INDUSTRY_PRESETS[st.session_state['industry_key']].name if INDUSTRY_PRESETS and st.session_state.get('industry_key') else 'None'}"
            )
        except Exception:
            st.caption(
                "Structured brief exists but could not be parsed – will be rebuilt on next run."
            )


# -------------------------------------------------
# TAB 2 – Workshop (section-by-section report)
# -------------------------------------------------

with tab_workshop:
    st.subheader("2. Workshop – Full report, section by section")

    if not st.session_state["client_brief_json"] or not st.session_state["aicmo_output_json"]:
        st.warning("You need a generated draft from the Brief tab first.")
    else:
        brief_obj = ClientInputBrief.model_validate_json(st.session_state["client_brief_json"])
        output_obj = AICMOOutputReport.model_validate_json(st.session_state["aicmo_output_json"])

        client_name = st.session_state["client_name"] or brief_obj.brand.brand_name
        st.markdown(
            f"Working on **{client_name}** – version **v{st.session_state['current_version']}**"
        )

        # Section 1: Brand & objectives
        with st.expander("1. Brand & objectives", expanded=True):
            st.markdown(f"**Brand:** {brief_obj.brand.brand_name}")
            st.markdown(f"**Industry:** {brief_obj.brand.industry or 'Not specified'}")
            st.markdown(f"**Primary customer:** {brief_obj.audience.primary_customer}")
            st.markdown(f"**Primary goal:** {brief_obj.goal.primary_goal}")
            st.markdown(f"**Timeline:** {brief_obj.goal.timeline or 'Not specified'}")
            if brief_obj.strategy_extras.brand_adjectives:
                st.markdown(
                    "**Brand adjectives:** " + ", ".join(brief_obj.strategy_extras.brand_adjectives)
                )

        # Section 2: Strategic marketing plan
        mp = output_obj.marketing_plan
        with st.expander("2. Strategic marketing plan", expanded=True):
            st.markdown("### Executive summary")
            st.markdown(mp.executive_summary)

            st.markdown("### Situation analysis")
            st.markdown(mp.situation_analysis)

            st.markdown("### Strategy")
            st.markdown(mp.strategy)

            st.markdown("### Strategy pillars")
            if mp.pillars:
                for p in mp.pillars:
                    st.markdown(
                        f"- **{p.name}** – {p.description or ''} "
                        f"_(KPI impact: {p.kpi_impact or 'N/A'})_"
                    )
            else:
                st.caption("No explicit pillars defined.")

            if getattr(mp, "messaging_pyramid", None):
                mpyr = mp.messaging_pyramid
                st.markdown("### Messaging pyramid")
                st.markdown(f"**Brand promise:** {mpyr.promise}")
                if mpyr.key_messages:
                    st.markdown("**Key messages:**")
                    for msg in mpyr.key_messages:
                        st.markdown(f"- {msg}")
                if mpyr.proof_points:
                    st.markdown("**Proof points:**")
                    for pr_item in mpyr.proof_points:
                        st.markdown(f"- {pr_item}")
                if mpyr.values:
                    st.markdown("**Values / personality:**")
                    for v in mpyr.values:
                        st.markdown(f"- {v}")

            if getattr(mp, "swot", None):
                sw = mp.swot
                st.markdown("### SWOT snapshot")
                col_s, col_w, col_o, col_t = st.columns(4)
                with col_s:
                    st.markdown("**Strengths**")
                    for x in sw.strengths:
                        st.markdown(f"- {x}")
                with col_w:
                    st.markdown("**Weaknesses**")
                    for x in sw.weaknesses:
                        st.markdown(f"- {x}")
                with col_o:
                    st.markdown("**Opportunities**")
                    for x in sw.opportunities:
                        st.markdown(f"- {x}")
                with col_t:
                    st.markdown("**Threats**")
                    for x in sw.threats:
                        st.markdown(f"- {x}")

            if getattr(mp, "competitor_snapshot", None):
                cs = mp.competitor_snapshot
                st.markdown("### Competitor snapshot")
                st.markdown(cs.narrative)
                if cs.common_patterns:
                    st.markdown("**Common patterns:**")
                    for ptn in cs.common_patterns:
                        st.markdown(f"- {ptn}")
                if cs.differentiation_opportunities:
                    st.markdown("**Differentiation opportunities:**")
                    for opp in cs.differentiation_opportunities:
                        st.markdown(f"- {opp}")

        # Section 3: Campaign blueprint
        cb = output_obj.campaign_blueprint
        with st.expander("3. Campaign blueprint", expanded=True):
            st.markdown("### Big idea")
            st.markdown(cb.big_idea)

            st.markdown("### Objectives")
            st.markdown(f"- Primary: {cb.objective.primary}")
            if cb.objective.secondary:
                st.markdown(f"- Secondary: {cb.objective.secondary}")

            if cb.audience_persona:
                ap = cb.audience_persona
                st.markdown("### Core audience persona")
                st.markdown(f"**{ap.name}**")
                if ap.description:
                    st.markdown(ap.description)

            if getattr(output_obj, "persona_cards", None):
                st.markdown("### Detailed persona cards")
                for pc in output_obj.persona_cards:
                    with st.expander(pc.name, expanded=False):
                        st.markdown(f"**Demographics:** {pc.demographics}")
                        st.markdown(f"**Psychographics:** {pc.psychographics}")
                        if pc.pain_points:
                            st.markdown("**Pain points:**")
                            for item in pc.pain_points:
                                st.markdown(f"- {item}")
                        if pc.triggers:
                            st.markdown("**Triggers:**")
                            for item in pc.triggers:
                                st.markdown(f"- {item}")
                        if pc.objections:
                            st.markdown("**Objections:**")
                            for item in pc.objections:
                                st.markdown(f"- {item}")
                        if pc.content_preferences:
                            st.markdown("**Content preferences:**")
                            for item in pc.content_preferences:
                                st.markdown(f"- {item}")
                        if pc.primary_platforms:
                            st.markdown("**Primary platforms:** " + ", ".join(pc.primary_platforms))
                        st.markdown(f"**Tone preference:** {pc.tone_preference}")

        # Section 4: Content calendar
        cal = output_obj.social_calendar
        with st.expander("4. Content calendar", expanded=True):
            st.markdown(f"### Calendar period: {cal.start_date} → {cal.end_date}")
            st.table(
                [
                    {
                        "Date": p.date,
                        "Platform": p.platform,
                        "Theme": p.theme,
                        "Hook": p.hook,
                        "CTA": p.cta,
                        "Asset": p.asset_type,
                        "Status": p.status or "",
                    }
                    for p in cal.posts
                ]
            )

        # Section 5: Performance review
        if getattr(output_obj, "performance_review", None):
            pr = output_obj.performance_review
            with st.expander("5. Performance review", expanded=True):
                st.markdown("### Growth summary")
                st.markdown(pr.summary.growth_summary)

                st.markdown("### Wins")
                st.markdown(pr.summary.wins)

                st.markdown("### Failures")
                st.markdown(pr.summary.failures)

                st.markdown("### Opportunities")
                st.markdown(pr.summary.opportunities)
        else:
            with st.expander("5. Performance review", expanded=False):
                st.info("No performance review generated for this draft.")

        # Section 6: Action plan
        if getattr(output_obj, "action_plan", None):
            ap = output_obj.action_plan
            with st.expander("6. Next 30 days – Action plan", expanded=True):
                if ap.quick_wins:
                    st.markdown("**Quick wins:**")
                    for item in ap.quick_wins:
                        st.markdown(f"- {item}")
                if ap.next_10_days:
                    st.markdown("**Next 10 days:**")
                    for item in ap.next_10_days:
                        st.markdown(f"- {item}")
                if ap.next_30_days:
                    st.markdown("**Next 30 days:**")
                    for item in ap.next_30_days:
                        st.markdown(f"- {item}")
                if ap.risks:
                    st.markdown("**Risks & watchouts:**")
                    for item in ap.risks:
                        st.markdown(f"- {item}")
        else:
            with st.expander("6. Next 30 days – Action plan", expanded=False):
                st.info("No explicit action plan attached to this draft.")

        # Section 7: Creatives & multi-channel
        cr = output_obj.creatives
        with st.expander("7. Creatives & multi-channel adaptation", expanded=True):
            if cr is None:
                st.info("No creatives block was generated for this draft.")
            else:
                st.markdown("### Creatives overview")

                if getattr(cr, "rationale", None):
                    st.markdown("#### Creative rationale")
                    st.markdown(cr.rationale.strategy_summary)
                    if cr.rationale.psychological_triggers:
                        st.markdown("**Psychological triggers used:**")
                        for t in cr.rationale.psychological_triggers:
                            st.markdown(f"- {t}")
                    st.markdown(f"**Audience fit:** {cr.rationale.audience_fit}")
                    if cr.rationale.risk_notes:
                        st.markdown(f"**Risks / guardrails:** {cr.rationale.risk_notes}")

                st.markdown("---")
                st.markdown("#### Platform-specific variants")
                if cr.channel_variants:
                    st.table(
                        [
                            {
                                "Platform": v.platform,
                                "Format": v.format,
                                "Hook": v.hook,
                                "Caption": v.caption,
                            }
                            for v in cr.channel_variants
                        ]
                    )
                else:
                    st.caption("No platform-specific variants generated.")

                st.markdown("---")
                st.markdown("#### Email subject lines")
                if cr.email_subject_lines:
                    for sline in cr.email_subject_lines:
                        st.markdown(f"- {sline}")
                else:
                    st.caption("No email subject lines generated.")

                st.markdown("---")
                st.markdown("#### Tone/style variants")
                if cr.tone_variants:
                    for tv in cr.tone_variants:
                        st.markdown(f"- **{tv.tone_label}:** {tv.example_caption}")
                else:
                    st.caption("No tone variants generated.")

                if getattr(cr, "hook_insights", None):
                    st.markdown("---")
                    st.markdown("#### Hook insights (why these work)")
                    for hi in cr.hook_insights:
                        st.markdown(f"- **{hi.hook}** – {hi.insight}")

                if getattr(cr, "cta_library", None):
                    st.markdown("---")
                    st.markdown("#### CTA library")
                    st.table(
                        [
                            {
                                "Label": cta.label,
                                "CTA": cta.text,
                                "Context": cta.usage_context,
                            }
                            for cta in cr.cta_library
                        ]
                    )

                if getattr(cr, "offer_angles", None):
                    st.markdown("---")
                    st.markdown("#### Offer angles")
                    for angle in cr.offer_angles:
                        st.markdown(f"- **{angle.label}:** {angle.description}")
                        st.markdown(f"  - Example: {angle.example_usage}")

                st.markdown("---")
                st.markdown("#### Generic hooks & captions")

                if cr.hooks:
                    st.markdown("**Hooks:**")
                    for h in cr.hooks:
                        st.markdown(f"- {h}")

                if cr.captions:
                    st.markdown("**Captions:**")
                    for c in cr.captions:
                        st.markdown(f"- {c}")

                if getattr(cr, "scripts", None):
                    st.markdown("**Ad script snippets:**")
                    for stext in cr.scripts:
                        st.markdown(f"- {stext}")


# -------------------------------------------------
# TAB 3 – Learn & Improve (feedback + external attachments)
# -------------------------------------------------

with tab_learn:
    st.subheader("3. Learn & improve – operator feedback")

    if not st.session_state["client_brief_json"] or not st.session_state["aicmo_output_json"]:
        st.warning("You need a generated draft from the Brief tab first.")
    else:
        brief_obj = ClientInputBrief.model_validate_json(st.session_state["client_brief_json"])
        output_obj = AICMOOutputReport.model_validate_json(st.session_state["aicmo_output_json"])

        client_name = st.session_state["client_name"] or brief_obj.brand.brand_name
        st.markdown(
            f"Currently editing **{client_name}** – version **v{st.session_state['current_version']}**"
        )

        st.markdown("#### Feedback for this draft")
        instructions = st.text_area(
            "Tell AICMO what to improve or change",
            placeholder=(
                "Examples:\n"
                "- Make tone less formal and more conversational.\n"
                "- Add 3 extra LinkedIn posts targeting B2B founders.\n"
                "- Shift focus from awareness to leads.\n"
                "- Tighten executive summary to 2 paragraphs.\n"
            ),
            height=180,
        )

        st.markdown("#### Optional: attach external reports / analysis")
        st.caption(
            "Attach PDFs, DOCX, or other analysis (e.g. existing agency reports, audits, "
            "market studies) for AICMO to learn from."
        )
        attachment = st.file_uploader(
            "Attach external report (PDF / DOCX / TXT)",
            type=["pdf", "docx", "txt"],
            key="feedback_attachment",
        )

        api_base_url_fb = st.text_input(
            "Backend API base URL for revision",
            value="http://localhost:8000",
            help="Can be same as above; kept here so you can point to a different environment if needed.",
        )

        if st.button("✏️ Apply feedback and regenerate draft"):
            if not instructions.strip():
                st.error("Please type some feedback first.")
            else:
                try:
                    attachment_bytes: Optional[bytes] = None
                    attachment_name: Optional[str] = None
                    if attachment is not None:
                        attachment_bytes = attachment.read()
                        attachment_name = attachment.name

                    with st.spinner("Sending feedback and learning from attachments…"):
                        revised = call_backend_revision(
                            api_base_url_fb,
                            brief_obj,
                            output_obj,
                            instructions.strip(),
                            attachment_bytes,
                            attachment_name,
                        )

                    st.session_state["aicmo_output_json"] = revised.model_dump_json(indent=2)
                    st.session_state["current_version"] += 1
                    st.session_state["status_message"] = (
                        f"Draft updated – now v{st.session_state['current_version']}."
                    )
                    st.success("Draft updated. Review the new version in the Workshop tab.")
                except Exception as e:
                    st.session_state["status_message"] = f"Revision failed: {e}"
                    st.exception(e)


# -------------------------------------------------
# TAB 4 – Deliverables (report preview + exports)
# -------------------------------------------------

with tab_deliver:
    st.subheader("4. Deliverables – client-facing package")

    if not st.session_state["client_brief_json"] or not st.session_state["aicmo_output_json"]:
        st.warning("You need a draft (after any edits) before generating final deliverables.")
    else:
        brief_obj = ClientInputBrief.model_validate_json(st.session_state["client_brief_json"])
        output_obj = AICMOOutputReport.model_validate_json(st.session_state["aicmo_output_json"])

        case_name = st.session_state["case_name"]
        client_name = st.session_state["client_name"] or brief_obj.brand.brand_name

        st.markdown(
            f"Preparing final package for **{client_name}** "
            f"(case: **{case_name}**, version v{st.session_state['current_version']})."
        )

        report_md = generate_output_report_markdown(brief_obj, output_obj)
        st.session_state["final_report_md"] = report_md

        col_left, col_right = st.columns([2, 1])

        with col_left:
            st.markdown("### Final client-facing report (preview)")
            st.markdown(report_md)

        with col_right:
            st.markdown("### Export report")

            st.download_button(
                label="⬇️ Download Markdown (.md)",
                data=report_md,
                file_name=f"aicmo_report_{case_name}.md",
                mime="text/markdown",
                key="dl_md",
            )

            api_base_url_exp = st.text_input(
                "Backend API base URL for exports",
                value="http://localhost:8000",
                help="Same backend used for PDF / PPTX / ZIP generation.",
            )

            if st.button("⬇️ Generate PDF (via backend)"):
                try:
                    with st.spinner("Generating PDF via backend…"):
                        pdf_bytes = call_backend_export_pdf(api_base_url_exp, report_md)
                    st.download_button(
                        label="Download PDF",
                        data=pdf_bytes,
                        file_name=f"aicmo_report_{case_name}.pdf",
                        mime="application/pdf",
                        key="dl_pdf",
                    )
                except Exception as e:
                    st.exception(e)

            if st.button("⬇️ Generate PPTX deck (via backend)"):
                try:
                    with st.spinner("Generating PPTX via backend…"):
                        pptx_bytes = call_backend_export_pptx(
                            api_base_url_exp, brief_obj, output_obj
                        )
                    st.download_button(
                        label="Download PPTX",
                        data=pptx_bytes,
                        file_name=f"aicmo_report_{case_name}.pptx",
                        mime=(
                            "application/vnd.openxmlformats-officedocument."
                            "presentationml.presentation"
                        ),
                        key="dl_pptx",
                    )
                except Exception as e:
                    st.exception(e)

        st.markdown("---")
        st.markdown("### Full package (report + creatives)")

        st.caption(
            "Ask backend to bundle everything into a ZIP with folders like "
            "`01_Strategy`, `02_Campaign_Blueprint`, `03_Content_Calendar`, `04_Creatives`."
        )

        if st.button("📦 Download full client package (ZIP)"):
            try:
                with st.spinner("Requesting ZIP package from backend…"):
                    zip_bytes = call_backend_export_zip(api_base_url_exp, brief_obj, output_obj)
                st.download_button(
                    label="Download ZIP",
                    data=zip_bytes,
                    file_name=f"aicmo_{case_name}_package.zip",
                    mime="application/zip",
                    key="dl_zip",
                )
            except Exception as e:
                st.exception(e)
