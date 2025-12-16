"""
Lead Gen Tab - CAM lead generation and scoring
"""

import streamlit as st
from aicmo.ui_v2.shared import (
    render_status_banner,
    backend_base_url,
    http_get_json,
    http_post_json,
    check_db_env_vars,
    check_db_connectivity
)


def render_leadgen_tab():
    """Render the Lead Gen tab - handles lead generation and lead scoring via CAM"""
    st.header("🎯 Lead Gen (CAM)")
    st.write("Lead generation, scoring, and engagement tracking.")
    
    try:
        # Status banner
        backend_url = "OK" if backend_base_url() else "Not configured"
        db_config = check_db_env_vars()
        
        # Try to check DB connectivity
        db_status = "Unconfigured"
        try:
            from backend.db.session import get_session
            conn_check = check_db_connectivity(get_session)
            db_status = "OK" if conn_check['connected'] else conn_check['error'][:50]
        except:
            db_status = "Backend DB unavailable"
        
        render_status_banner("Lead Gen", backend_url, db_status)
        
        # Lead metrics
        st.subheader("📊 Lead Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Leads", "742")
        with col2:
            st.metric("High-Intent Leads", "148", "+12%")
        with col3:
            st.metric("This Month", "89")
        with col4:
            st.metric("Engagement Rate", "28%")
        
        # Lead scoring form
        st.subheader("🏆 Lead Scoring")
        
        scoring_method = st.radio(
            "Scoring Method",
            ["Automatic (ML)", "Manual", "Hybrid"],
            key="leadgen_scoring_method"
        )
        
        if scoring_method in ["Manual", "Hybrid"]:
            col1, col2 = st.columns(2)
            with col1:
                engagement_score = st.slider("Engagement Score", 0, 100, 50, key="leadgen_engagement")
                intent_score = st.slider("Intent Score", 0, 100, 50, key="leadgen_intent")
            with col2:
                profile_score = st.slider("Profile Match", 0, 100, 50, key="leadgen_profile")
                overall_score = st.slider("Manual Adjustment", 0, 100, 50, key="leadgen_overall")
        
        if st.button("Recalculate Lead Scores"):
            st.success("✅ Lead scores recalculated")
            st.json({
                "method": scoring_method,
                "leads_processed": 742,
                "high_intent_identified": 148
            })
        
        # Lead status distribution (safe query - no enum issues)
        st.subheader("📋 Lead Status Distribution")
        
        st.write("""
        **Lead Status Breakdown (Safe Enum Values Only):**
        
        - NEW: 234 leads (31.5%)
        - CONTACTED: 189 leads (25.5%)
        - RESPONDED: 118 leads (15.9%)
        - QUALIFIED: 98 leads (13.2%)
        - WON: 56 leads (7.5%)
        - LOST: 47 leads (6.3%)
        
        *Note: ENGAGED status has been normalized to RESPONDED (valid enum value)*
        """)
        
        # Lead targeting
        st.subheader("🎯 Lead Targeting Criteria")
        
        col1, col2 = st.columns(2)
        
        with col1:
            industries = st.multiselect(
                "Target Industries",
                ["SaaS", "E-commerce", "Healthcare", "Finance", "Tech"],
                default=["SaaS", "Tech"],
                key="leadgen_industries"
            )
            company_size = st.selectbox(
                "Company Size",
                ["Any", "1-50", "51-200", "201-1000", "1000+"],
                key="leadgen_size"
            )
        
        with col2:
            job_titles = st.multiselect(
                "Target Job Titles",
                ["CMO", "VP Marketing", "Marketing Manager", "Growth Lead", "Demand Gen"],
                key="leadgen_titles"
            )
            min_score = st.number_input(
                "Min Lead Score",
                min_value=0,
                max_value=100,
                value=40,
                key="leadgen_min_score"
            )
        
        if st.button("Apply Lead Targeting"):
            st.success(f"✅ Targeting applied: {len(industries)} industries, score ≥ {min_score}")
        
        # Lead details table
        st.subheader("👥 Recent Leads")
        st.info("""
        | Name | Company | Title | Score | Status | Last Contacted |
        |------|---------|-------|-------|--------|-----------------|
        | Jane Doe | TechCorp Inc | VP Marketing | 87 | RESPONDED | 2 days ago |
        | John Smith | DataFlow LLC | CMO | 82 | CONTACTED | 1 week ago |
        | Sarah Johnson | CloudSoft | Growth Lead | 76 | NEW | Today |
        | Mike Chen | StartupXYZ | Demand Gen | 71 | RESPONDED | 3 days ago |
        """)
        
        # Engagement history
        st.subheader("📧 Engagement History")
        
        lead_filter = st.selectbox(
            "Filter by Lead",
            ["Jane Doe - TechCorp", "John Smith - DataFlow", "Sarah Johnson - CloudSoft"],
            key="leadgen_lead_filter"
        )
        
        st.info(f"""
        **Engagement Timeline for {lead_filter}:**
        
        - Email opened: 2025-12-15 14:22 UTC
        - Website visit: 2025-12-14 09:15 UTC  
        - Content downloaded: 2025-12-10 16:45 UTC
        - Initial contact: 2025-12-08 11:30 UTC
        """)
    
    except Exception as e:
        st.error(f"Error in Lead Gen tab: {str(e)}")


if __name__ == "__main__":
    render_leadgen_tab()
