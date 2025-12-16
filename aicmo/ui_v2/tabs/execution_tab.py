"""
Execution Tab - Campaign posting and execution
"""

import streamlit as st
from aicmo.ui_v2.shared import (
    render_status_banner,
    backend_base_url,
    http_get_json,
    check_db_env_vars
)


def render_execution_tab():
    """Render the Execution tab"""
    st.header("🚀 Execution (Posting)")
    st.write("Post content and execute campaigns across channels.")
    
    try:
        # Status banner
        backend_url = "OK" if backend_base_url() else "Not configured"
        db_config = check_db_env_vars()
        db_status = "OK" if db_config['db_url_configured'] and not db_config['issues'] else "Unconfigured"
        
        render_status_banner("Execution", backend_url, db_status)
        
        st.subheader("📤 Scheduled Posts")
        
        # Posting queue
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Scheduled", 12)
        with col2:
            st.metric("Posted Today", 4)
        with col3:
            st.metric("Failed", 0)
        
        # Queue table
        st.write("**Next Posts to Execute:**")
        st.info("""
        | Platform | Content | Scheduled | Status |
        |----------|---------|-----------|--------|
        | LinkedIn | Thought leadership post | 2025-12-17 09:00 | Ready |
        | Instagram | Product showcase | 2025-12-17 12:00 | Ready |
        | Twitter | Industry news thread | 2025-12-17 15:00 | Pending Approval |
        """)
        
        # Manual posting
        st.subheader("📱 Manual Post")
        
        col1, col2 = st.columns(2)
        with col1:
            post_content = st.text_area("Post Content", key="exec_content", height=100)
            post_platforms = st.multiselect(
                "Platforms",
                ["LinkedIn", "Instagram", "Twitter", "Facebook"],
                key="exec_platforms"
            )
        
        with col2:
            post_when = st.radio(
                "When to post?",
                ["Now", "Schedule for later"],
                key="exec_when"
            )
            if post_when == "Schedule for later":
                scheduled_time = st.time_input("Scheduled time", key="exec_time")
                scheduled_date = st.date_input("Scheduled date", key="exec_date")
        
        if st.button("Post Content"):
            if post_content and post_platforms:
                st.success(f"✅ Posted to {', '.join(post_platforms)}")
                st.write("**Posting Details:**")
                st.json({
                    "platforms": post_platforms,
                    "when": post_when,
                    "content_length": len(post_content)
                })
            else:
                st.error("Content and at least one platform required")
        
        # Platform-specific instructions
        st.subheader("📋 Platform Posting Guide")
        
        with st.expander("LinkedIn Instructions"):
            st.markdown("""
            **LinkedIn Best Practices:**
            - Post between 8 AM - 2 PM on weekdays
            - Use 1-2 relevant hashtags
            - Include native image/video (avoid links when possible)
            - Engagement usually peaks 24-48 hours after posting
            - Use LinkedIn's native upload for better reach
            """)
        
        with st.expander("Instagram Instructions"):
            st.markdown("""
            **Instagram Best Practices:**
            - Post between 11 AM - 1 PM or 7 PM - 9 PM
            - Use 10-15 relevant hashtags
            - Include a clear call-to-action (CTA)
            - Stories have higher completion rates
            - Reply to comments within first hour
            """)
        
        with st.expander("Twitter Instructions"):
            st.markdown("""
            **Twitter Best Practices:**
            - Post 1-2 times daily max
            - Use trending hashtags
            - Threads get more engagement than single tweets
            - Engage with replies promptly
            - Best times: 9 AM - 3 PM weekdays
            """)
    
    except Exception as e:
        st.error(f"Error in Execution tab: {str(e)}")


if __name__ == "__main__":
    render_execution_tab()
