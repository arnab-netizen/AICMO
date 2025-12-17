"""DEPRECATED_STREAMLIT_ENTRYPOINT

This file is a deprecated Streamlit dashboard from early development.

**Production deployment must use: streamlit_pages/aicmo_operator.py**

Rationale:
- This is a simple example dashboard
- aicmo_operator.py (109 KB) is the production operator UI
- RUNBOOK_RENDER_STREAMLIT.md:33 specifies: streamlit_pages/aicmo_operator.py

If imported or run directly, raises RuntimeError to prevent accidental deployment.
"""

import sys

"""Thin wrapper entrypoint for Streamlit UI.

This file delegates to `operator_v2.py` which hosts the canonical
dashboard UI. Keep this file minimal so deployment tools can run either
`streamlit run operator_v2.py` or `streamlit run app.py` interchangeably.
"""
from operator_v2 import main as operator_v2_main


if __name__ == "__main__":
    operator_v2_main()


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
                    for a in artifacts:
                        atype = (a.get("type") or "").lower()
                        url = (a.get("url") or a.get("path") or "").strip()
                        meta = a.get("meta") or {}
                        b64 = a.get("base64")

                        st.write(f"**Artifact:** {atype or 'unknown'}")

                        # Heuristic: decide if this is an image
                        is_img = (
                            atype in ("image", "png", "jpg", "jpeg", "webp")
                            or url.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
                            or (
                                isinstance(meta, dict)
                                and meta.get("format", "").lower() in ("png", "jpg", "jpeg", "webp")
                            )
                            or bool(b64)
                        )

                        if is_img:
                            try:
                                if b64:
                                    import base64

                                    st.image(
                                        base64.b64decode(b64),
                                        caption=meta.get("caption") or "image",
                                        use_column_width=True,
                                    )
                                elif url.startswith("data:image/"):
                                    import base64

                                    header, data = url.split(",", 1)
                                    st.image(
                                        base64.b64decode(data),
                                        caption=url[:32] + "…",
                                        use_column_width=True,
                                    )
                                elif url:
                                    # Public (or signed) URL — let Streamlit fetch it directly
                                    st.image(url, caption=url, use_column_width=True)
                                else:
                                    st.info("Image artifact without url/base64.")
                            except Exception as e:
                                st.warning(f"Could not render image: {e}")
                                st.code(json.dumps(a, indent=2), language="json")
                        elif atype in ("copy.json", "copy") or ("variants" in (meta or {})):
                            # Likely CopyHook structured artifact
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
