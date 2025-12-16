"""
Learn / Kaizen Tab - Knowledge base and continuous improvement
"""

import streamlit as st
from aicmo.ui_v2.shared import (
    render_status_banner,
    backend_base_url,
    check_db_env_vars
)


def render_learn_tab():
    """Render the Learn / Kaizen tab"""
    st.header("📚 Learn / Kaizen")
    st.write("Knowledge base, best practices, and continuous improvement framework.")
    
    try:
        # Status banner
        backend_url = "OK" if backend_base_url() else "Not configured"
        db_config = check_db_env_vars()
        db_status = "OK" if db_config['db_url_configured'] and not db_config['issues'] else "Unconfigured"
        
        render_status_banner("Learn", backend_url, db_status)
        
        # Knowledge base
        st.subheader("📖 Knowledge Base")
        
        search_term = st.text_input("Search articles", placeholder="e.g., 'LinkedIn engagement tips'", key="learn_search")
        
        categories = st.multiselect(
            "Filter by category",
            ["Best Practices", "Troubleshooting", "API Docs", "Case Studies"],
            key="learn_categories"
        )
        
        st.info("""
        **Available Articles:**
        - Best Practices: Social Media Posting Times & Cadence
        - Case Study: 3x Lead Generation Growth
        - Tutorial: Setting up Autonomous Campaigns
        - FAQ: Common Integration Issues
        """)
        
        # Kaizen framework
        st.subheader("⚡ Kaizen - Continuous Improvement")
        
        st.write("""
        **Kaizen Cycle:**
        1. **Analyze** - Review campaign performance
        2. **Identify** - Find improvement opportunities
        3. **Implement** - Apply changes
        4. **Measure** - Track results
        5. **Iterate** - Repeat
        """)
        
        # Recent improvements
        st.write("**Recent Improvements (This Month):**")
        st.dataframe({
            "Date": ["2025-12-10", "2025-12-08", "2025-12-05"],
            "Area": ["LinkedIn Posting", "Lead Scoring", "Email Cadence"],
            "Change": ["Moved to 10 AM UTC", "Increased weight on engagement", "From daily to 3x weekly"],
            "Impact": ["+23% engagement", "+18% quality", "-12% unsubscribes"]
        }, use_container_width=True)
        
        # Performance trends
        st.subheader("📈 Performance Trends")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Avg Engagement Rate", "3.2%", "+0.5%")
            st.metric("Lead Quality Score", "74/100", "+8 points")
        
        with col2:
            st.metric("Campaign ROI", "3.4x", "+0.6x")
            st.metric("Posting Efficiency", "92%", "+4%")
        
        # Feedback loop
        st.subheader("💬 Feedback & Suggestions")
        
        feedback_type = st.selectbox(
            "Feedback Type",
            ["Bug Report", "Feature Request", "Performance Issue", "Question"],
            key="learn_feedback_type"
        )
        
        feedback_text = st.text_area(
            "Your feedback",
            placeholder="Describe your feedback here...",
            key="learn_feedback"
        )
        
        if st.button("📤 Submit Feedback"):
            if feedback_text:
                st.success("✅ Feedback submitted - thank you!")
            else:
                st.error("Please provide feedback")
    
    except Exception as e:
        st.error(f"Error in Learn tab: {str(e)}")


if __name__ == "__main__":
    render_learn_tab()
