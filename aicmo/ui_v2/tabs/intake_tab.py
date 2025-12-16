"""
Intake Tab - Lead and prospect intake management
"""

import streamlit as st
from aicmo.ui_v2.shared import (
    render_status_banner,
    backend_base_url,
    http_get_json,
    check_db_env_vars
)


def render_intake_tab():
    """Render the Intake tab"""
    st.header("📥 Intake")
    st.write("Manage lead and prospect intake workflows.")
    
    try:
        # Status banner
        backend_url = "OK" if backend_base_url() else "Not configured"
        db_config = check_db_env_vars()
        db_status = "OK" if db_config['db_url_configured'] and not db_config['issues'] else "Unconfigured"
        
        render_status_banner("Intake", backend_url, db_status)
        
        # Intake form
        st.subheader("➕ New Lead Intake")
        col1, col2 = st.columns(2)
        
        with col1:
            lead_name = st.text_input("Lead Name", key="intake_name")
            lead_email = st.text_input("Email", key="intake_email")
        
        with col2:
            lead_company = st.text_input("Company", key="intake_company")
            lead_phone = st.text_input("Phone (optional)", key="intake_phone")
        
        intake_notes = st.text_area("Notes", key="intake_notes")
        
        if st.button("Submit Lead"):
            if lead_name and lead_email:
                st.success(f"✅ Lead '{lead_name}' would be submitted to backend at {backend_base_url() or '(not configured)'}")
                # In production: call http_post_json("/leads", {...})
            else:
                st.error("Name and email required")
        
        # Display existing leads (stub)
        st.subheader("📋 Recent Intakes")
        st.info("Backend integration would show recent leads here")
    
    except Exception as e:
        st.error(f"Error in Intake tab: {str(e)}")


if __name__ == "__main__":
    render_intake_tab()
