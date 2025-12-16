"""
Creatives Tab - Content and creative asset management
"""

import streamlit as st
from aicmo.ui_v2.shared import (
    render_status_banner,
    backend_base_url,
    http_get_json,
    check_db_env_vars
)


def render_creatives_tab():
    """Render the Creatives tab"""
    st.header("🎨 Creatives")
    st.write("Manage marketing creatives and content assets.")
    
    try:
        # Status banner
        backend_url = "OK" if backend_base_url() else "Not configured"
        db_config = check_db_env_vars()
        db_status = "OK" if db_config['db_url_configured'] and not db_config['issues'] else "Unconfigured"
        
        render_status_banner("Creatives", backend_url, db_status)
        
        # Creative form
        st.subheader("✏️ New Creative")
        
        creative_type = st.selectbox(
            "Creative Type",
            ["Image", "Video", "Copy", "Design", "Social Post"],
            key="creative_type"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Title", key="creative_title")
            platform = st.selectbox(
                "Platform",
                ["LinkedIn", "Instagram", "Twitter", "Facebook", "Web"],
                key="creative_platform"
            )
        
        with col2:
            status = st.selectbox(
                "Status",
                ["Draft", "Review", "Approved", "Scheduled"],
                key="creative_status"
            )
            file_upload = st.file_uploader("Upload File (optional)", key="creative_file")
        
        description = st.text_area("Description", key="creative_description")
        
        if st.button("Save Creative"):
            if title:
                st.success(f"✅ Creative '{title}' saved")
                st.json({
                    "type": creative_type,
                    "title": title,
                    "platform": platform,
                    "status": status,
                    "uploaded": file_upload is not None
                })
            else:
                st.error("Title required")
        
        # Display creatives library
        st.subheader("🎬 Creative Library")
        st.info("Backend would display creative assets here")
    
    except Exception as e:
        st.error(f"Error in Creatives tab: {str(e)}")


if __name__ == "__main__":
    render_creatives_tab()
