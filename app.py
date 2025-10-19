import os
import time
import json
import requests
import streamlit as st

# ------------------------------
# Basic page setup
# ------------------------------
st.set_page_config(page_title="AI-CMO Dashboard", layout="centered")

st.title("AI-CMO — Simple Dashboard")
st.caption(
    "Paste client info, pick a feature, click Run. Supports CopyHook (Day 1) and VisualGen (Day 2)."
)

# ------------------------------
# Config inputs (non-technical)
# ------------------------------
with st.expander("Setup (edit once, then reuse)", expanded=True):
    colA, colB = st.columns(2)
    with colA:
        api_base = st.text_input(
            "API Base URL",
            value=os.getenv("AICMO_API_BASE", "https://YOUR_SERVICE_HOST"),
            help="Example: https://copyhook.example.com (if separate hosts, use the Conductor URL or the module host)",
        )
        api_key = st.text_input(
            "API Key (X-API-Key header)",
            value=os.getenv("AICMO_API_KEY", ""),
            type="password",
            help="Ask your backend for an API key; required for authenticated calls.",
        )
        poll_seconds = st.number_input(
            "Max wait (seconds)",
            min_value=5,
            max_value=120,
            value=25,
            step=5,
            help="How long to wait before timing out (status polling).",
        )
    with colB:
        copyhook_prefix = st.text_input(
            "CopyHook route prefix",
            value="/api/copyhook",
            help="Leave as /api/copyhook unless you changed it in the service",
        )
        visualgen_prefix = st.text_input(
            "VisualGen route prefix",
            value="/api/visualgen",
            help="Leave as /api/visualgen unless you changed it in the service",
        )
        verify_ssl = st.checkbox("Verify HTTPS certificates", value=True)


# Tiny helper for building URLs safely
def url_join(base: str, path: str) -> str:
    return (base.rstrip("/") + "/" + path.lstrip("/")).rstrip("/")


# Shared HTTP helpers
def _headers():
    h = {}
    if api_key.strip():
        h["X-API-Key"] = api_key.strip()
    return h


def post_json(url: str, payload: dict) -> dict:
    r = requests.post(url, json=payload, headers=_headers(), verify=verify_ssl, timeout=30)
    # Raise for 4xx/5xx so we can catch and show details
    try:
        r.raise_for_status()
        return r.json() if r.text else {}
    except requests.HTTPError:
        # Try to parse detail payloads from 422, etc.
        try:
            return {"__error__": True, "status_code": r.status_code, "body": r.json()}
        except Exception:
            return {"__error__": True, "status_code": r.status_code, "body": r.text}


def get_json(url: str) -> dict:
    r = requests.get(url, headers=_headers(), verify=verify_ssl, timeout=30)
    try:
        r.raise_for_status()
        return r.json() if r.text else {}
    except requests.HTTPError:
        try:
            return {"__error__": True, "status_code": r.status_code, "body": r.json()}
        except Exception:
            return {"__error__": True, "status_code": r.status_code, "body": r.text}


# ------------------------------
# Client data form (simple)
# ------------------------------
st.markdown("### Client details")
with st.form("client_form"):
    col1, col2 = st.columns(2)
    with col1:
        client_id = st.text_input(
            "Client ID (anything unique)", value="00000000-0000-0000-0000-000000000001"
        )
        brand = st.text_input("Brand name", value="Acme")
        tone = st.text_input("Tone (comma separated)", value="confident, simple")
        website = st.text_input("Website (optional)", value="https://example.com")
        main_cta = st.text_input("Main CTA", value="Book a demo")
    with col2:
        audience = st.text_input("Audience (one line)", value="B2B founders, seed to Series A")
        benefits = st.text_area(
            "Top 3 benefits (bullets or comma separated)",
            value="Ship faster, Reduce ops cost, Centralize workflows",
        )
        must_use = st.text_area("Must-use phrases (comma separated)", value="")
        must_avoid = st.text_area(
            "Must-avoid phrases (comma separated)", value="free forever, guaranteed ROI"
        )

    st.markdown("### Choose feature & options")
    feature = st.selectbox(
        "Feature to run", ["CopyHook (Headlines/CTAs/Ads)", "VisualGen (Creatives)"]
    )

    # VisualGen-specific simple inputs (kept basic)
    colv1, colv2 = st.columns(2)
    with colv1:
        vg_size = st.text_input("VisualGen size (e.g., 1200x628)", value="1200x628")
        vg_count = st.number_input("How many variants?", min_value=1, max_value=8, value=3, step=1)
    with colv2:
        vg_aspect = st.text_input("Aspect ratio (e.g., 1.91:1)", value="1.91:1")
        vg_template = st.text_input("Template tag (optional)", value="universal")

    submitted = st.form_submit_button("Run")


# ------------------------------
# Runners for each module
# ------------------------------
def run_copyhook():
    constraints = {
        "tone": tone,
        "brand": brand,
        "brand_id": client_id,
        "must_use": [s.strip() for s in must_use.split(",") if s.strip()],
        "must_avoid": [s.strip() for s in must_avoid.split(",") if s.strip()],
        "main_cta": main_cta,
        "audience": audience,
        "benefits": [s.strip() for s in benefits.replace("\n", ",").split(",") if s.strip()],
    }
    sources = [{"type": "url", "value": website}] if website.strip() else []
    payload = {
        "project_id": client_id,
        "goal": f"3 landing page hero variants for {brand}",
        "constraints": constraints,
        "sources": sources,
        "policy_id": "policy/default",
        "budget_tokens": 15000,
    }
    run_url = url_join(api_base, url_join(copyhook_prefix, "run"))
    status_url_base = url_join(api_base, url_join(copyhook_prefix, "status"))
    return _exec_run(run_url, status_url_base, payload)


def run_visualgen():
    # Keep VisualGen request minimal and generic; adapt to your service’s accepted fields
    constraints = {
        "brand": brand,
        "brand_id": client_id,
        "size": vg_size,  # e.g., "1200x628"
        "aspect_ratio": vg_aspect,  # e.g., "1.91:1"
        "template": vg_template,
        "count": int(vg_count),
    }
    sources = [{"type": "url", "value": website}] if website.strip() else []
    payload = {
        "project_id": client_id,
        "goal": f"{vg_count} creative variants for {brand}",
        "constraints": constraints,
        "sources": sources,
        "policy_id": "policy/default",
        "budget_tokens": 15000,
    }
    run_url = url_join(api_base, url_join(visualgen_prefix, "run"))
    status_url_base = url_join(api_base, url_join(visualgen_prefix, "status"))
    return _exec_run(run_url, status_url_base, payload)


def _exec_run(run_url: str, status_url_base: str, payload: dict) -> dict:
    # Kick off
    resp = post_json(run_url, payload)
    if resp.get("__error__"):
        return {"status": "failed", "error": resp}

    task_id = resp.get("task_id")
    if not task_id:
        return {
            "status": "failed",
            "error": {"message": "No task_id returned from /run", "raw": resp},
        }

    # Poll
    with st.spinner("Running…"):
        deadline = time.time() + int(poll_seconds)
        while time.time() < deadline:
            time.sleep(1.2)
            st_resp = get_json(url_join(status_url_base, task_id))
            if st_resp.get("__error__"):
                # status endpoint failed—show what we have
                return {"status": "failed", "error": st_resp, "task_id": task_id}
            status = (st_resp.get("status") or "").lower()
            if status in ("finished", "failed"):
                st_resp["task_id"] = task_id
                return st_resp

    # timeout
    return {"status": "timeout", "task_id": task_id}


# ------------------------------
# Handle run
# ------------------------------
if submitted:
    if not api_base or api_base.startswith("https://YOUR_"):
        st.error("Please enter a valid API Base URL in the Setup section.")
    elif not api_key.strip():
        st.error("Please paste your API Key.")
    else:
        if feature.startswith("CopyHook"):
            result = run_copyhook()
        else:
            result = run_visualgen()

        # --------------------------
        # Render results
        # --------------------------
        st.markdown("---")
        st.subheader("Result")

        # Error handling
        if result.get("status") in ("failed", "timeout"):
            st.error(f"Run status: {result.get('status').upper()}")
            st.code(json.dumps(result.get("error", {}), indent=2), language="json")
        else:
            # Tabs: Summary | Artifacts | Trace | Raw JSON
            tabs = st.tabs(["Summary", "Artifacts", "Trace", "Raw JSON"])
            with tabs[0]:
                st.write(f"**Status:** {result.get('status')}")
                st.write(f"**Module:** {result.get('module', 'unknown')}")
                if "score" in result and result["score"] is not None:
                    st.write(f"**Score:** {result['score']}")
                if "task_id" in result:
                    st.write(f"**Task ID:** `{result['task_id']}`")

            # Artifacts tab: show images (VisualGen) or structured JSON (CopyHook)
            with tabs[1]:
                artifacts = result.get("artifacts") or []
                if not artifacts:
                    st.info("No artifacts returned.")
                else:
                    # Try to display images if the artifact looks like one; otherwise show JSON
                    for a in artifacts:
                        atype = (a.get("type") or "").lower()
                        url = a.get("url") or a.get("path") or ""
                        meta = a.get("meta") or {}
                        st.write(f"**Artifact:** {atype or 'unknown'}")
                        if (
                            atype.endswith(".png")
                            or atype in ("image", "png", "jpg", "jpeg")
                            or url.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
                        ):
                            # Display image if accessible by URL; otherwise just show the URL
                            try:
                                st.image(url, caption=url, use_column_width=True)
                            except Exception:
                                st.write(url)
                        elif atype == "copy.json" or atype == "copy" or "variants" in meta:
                            # Likely CopyHook result
                            if "variants" in meta:
                                st.write("**Variants**")
                                for i, v in enumerate(meta["variants"], 1):
                                    st.markdown(f"- **{i}.** {v}")
                            st.code(json.dumps(a, indent=2), language="json")
                        else:
                            st.code(json.dumps(a, indent=2), language="json")

            with tabs[2]:
                st.code(json.dumps(result.get("trace", []), indent=2), language="json")

            with tabs[3]:
                st.code(json.dumps(result, indent=2), language="json")

            # Download entire result as JSON
            st.download_button(
                label="Download result JSON",
                data=json.dumps(result, indent=2),
                file_name="result.json",
                mime="application/json",
            )
