"""
Autonomy (AOL) Tab - AI agent settings and autonomous operation
"""

import streamlit as st
from aicmo.ui_v2.shared import (
    render_status_banner,
    backend_base_url,
    http_get_json,
    http_post_json,
    check_db_env_vars
)


def render_autonomy_tab():
    """Render the Autonomy tab"""
    st.header("🤖 Autonomy (AOL)")
    st.write("Configure AI Agent Operation Logic for autonomous campaign management.")
    
    try:
        # Status banner
        backend_url = "OK" if backend_base_url() else "Not configured"
        db_config = check_db_env_vars()
        db_status = "OK" if db_config['db_url_configured'] and not db_config['issues'] else "Unconfigured"
        
        render_status_banner("Autonomy", backend_url, db_status)
        
        # Agent status
        st.subheader("🤖 AI Agent Status")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Agent Status", "READY")
        with col2:
            st.metric("Campaigns Managed", "3")
        with col3:
            st.metric("Posts This Week", "47")
        
        # Autonomy settings
        st.subheader("⚙️ Autonomy Settings")
        
        autonomy_enabled = st.toggle(
            "Enable Autonomous Operation",
            value=False,
            key="autonomy_enabled"
        )
        
        if autonomy_enabled:
            st.warning("⚠️ Autonomous mode enabled - agent will post without approval")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Agent Behavior:**")
            
            auto_posting = st.toggle(
                "Auto-post content",
                value=False,
                key="auto_posting"
            )
            
            auto_engagement = st.toggle(
                "Auto-respond to comments",
                value=False,
                key="auto_engagement"
            )
            
            auto_adjust = st.toggle(
                "Auto-adjust budget",
                value=False,
                key="auto_adjust"
            )
        
        with col2:
            st.write("**Performance Thresholds:**")
            
            min_engagement_rate = st.slider(
                "Min Engagement Rate (%)",
                min_value=0.0,
                max_value=10.0,
                value=2.0,
                key="min_engagement"
            )
            
            max_daily_posts = st.number_input(
                "Max Daily Posts",
                min_value=1,
                max_value=20,
                value=5,
                key="max_daily_posts"
            )
            
            budget_limit = st.number_input(
                "Daily Budget Limit ($)",
                min_value=50,
                max_value=5000,
                value=500,
                key="budget_limit"
            )
        
        # AI model selection
        st.subheader("🧠 AI Model Configuration")
        
        model_choice = st.selectbox(
            "Content Generation Model",
            ["GPT-4", "Claude 3", "Mixtral", "Custom"],
            key="model_choice"
        )
        
        tone = st.selectbox(
            "Content Tone",
            ["Professional", "Casual", "Technical", "Storytelling"],
            key="content_tone"
        )
        
        creativity = st.slider(
            "Creativity Level",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            key="creativity_level"
        )
        
        # Campaign autonomy rules
        st.subheader("📋 Campaign Rules")
        
        st.write("Define what the agent can and cannot do per campaign:")
        
        rule_1 = st.toggle(
            "Can modify post copy (within 20% edit distance)",
            value=True,
            key="rule_modify"
        )
        
        rule_2 = st.toggle(
            "Can skip posting if engagement predicted < threshold",
            value=True,
            key="rule_skip"
        )
        
        rule_3 = st.toggle(
            "Can increase posting frequency if trending",
            value=False,
            key="rule_frequency"
        )
        
        # Save settings
        if st.button("💾 Save Settings"):
            st.success("✅ Autonomy settings saved")
            st.json({
                "enabled": autonomy_enabled,
                "auto_posting": auto_posting,
                "auto_engagement": auto_engagement,
                "model": model_choice,
                "tone": tone,
                "creativity": creativity
            })
    
    except Exception as e:
        st.error(f"Error in Autonomy tab: {str(e)}")


if __name__ == "__main__":
    render_autonomy_tab()
