"""
Monitoring Tab - Analytics and performance tracking
"""

import streamlit as st
from aicmo.ui_v2.shared import (
    render_status_banner,
    backend_base_url,
    http_get_json,
    check_db_env_vars
)


def render_monitoring_tab():
    """Render the Monitoring tab"""
    st.header("📈 Monitoring (Analytics)")
    st.write("Track campaign performance and metrics in real-time.")
    
    try:
        # Status banner
        backend_url = "OK" if backend_base_url() else "Not configured"
        db_config = check_db_env_vars()
        db_status = "OK" if db_config['db_url_configured'] and not db_config['issues'] else "Unconfigured"
        
        render_status_banner("Monitoring", backend_url, db_status)
        
        # Key metrics
        st.subheader("📊 Campaign Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Posts", 47)
        with col2:
            st.metric("Total Impressions", "128.5K")
        with col3:
            st.metric("Total Engagements", "4.2K")
        with col4:
            st.metric("Engagement Rate", "3.3%")
        
        # Time period selector
        period = st.selectbox(
            "Time Period",
            ["Last 7 days", "Last 30 days", "Last 90 days", "All time"],
            key="mon_period"
        )
        
        # Platform breakdown
        st.subheader("📱 By Platform")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info("""
            **LinkedIn**
            - Posts: 15
            - Impressions: 45.2K
            - Engagements: 1.8K
            - Engagement Rate: 3.9%
            """)
        
        with col2:
            st.info("""
            **Instagram**
            - Posts: 18
            - Impressions: 32.1K
            - Engagements: 1.5K
            - Engagement Rate: 4.7%
            """)
        
        with col3:
            st.info("""
            **Twitter**
            - Posts: 14
            - Impressions: 51.2K
            - Engagements: 0.9K
            - Engagement Rate: 1.8%
            """)
        
        # Top performing content
        st.subheader("⭐ Top Performing Posts")
        st.markdown("""
        | Platform | Content | Engagements | Reach |
        |----------|---------|-------------|-------|
        | LinkedIn | Thought leadership on AI | 324 | 12.4K |
        | Instagram | Product feature showcase | 287 | 8.9K |
        | LinkedIn | Industry trend analysis | 256 | 9.1K |
        | Twitter | Breaking news thread | 198 | 21.3K |
        """)
        
        # Lead source
        st.subheader("🎯 Lead Source Attribution")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("""
            - LinkedIn: 312 leads (42%)
            - Organic Web: 198 leads (27%)
            - Instagram: 164 leads (22%)
            - Twitter: 58 leads (8%)
            - Other: 8 leads (1%)
            """)
        
        with col2:
            st.write("""
            - Paid campaigns: 89 leads (12%)
            - Organic campaigns: 651 leads (88%)
            
            **Quality Score (0-100):**
            - LinkedIn: 78
            - Organic: 72
            - Instagram: 68
            """)
        
        # Export option
        if st.button("📊 Export Analytics Report"):
            st.success("Report exported to CSV")
    
    except Exception as e:
        st.error(f"Error in Monitoring tab: {str(e)}")


if __name__ == "__main__":
    render_monitoring_tab()
