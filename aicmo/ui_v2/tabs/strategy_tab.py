"""
Strategy Tab - Campaign strategy and planning
"""

import streamlit as st
from aicmo.ui_v2.shared import (
    render_status_banner,
    backend_base_url,
    http_get_json,
    check_db_env_vars
)


def render_strategy_tab():
    """Render the Strategy tab"""
    st.header("📊 Strategy")
    st.write("Define and manage campaign strategies.")
    
    try:
        # Status banner
        backend_url = "OK" if backend_base_url() else "Not configured"
        db_config = check_db_env_vars()
        db_status = "OK" if db_config['db_url_configured'] and not db_config['issues'] else "Unconfigured"
        
        render_status_banner("Strategy", backend_url, db_status)
        
        # Strategy form
        st.subheader("🎯 New Strategy")
        
        strategy_name = st.text_input("Strategy Name", key="strategy_name")
        
        col1, col2 = st.columns(2)
        with col1:
            industry = st.selectbox(
                "Industry",
                ["SaaS", "E-commerce", "Healthcare", "Finance", "Other"],
                key="strategy_industry"
            )
            budget = st.number_input("Monthly Budget ($)", min_value=1000, step=1000, key="strategy_budget")
        
        with col2:
            duration = st.selectbox(
                "Duration",
                ["3 months", "6 months", "12 months"],
                key="strategy_duration"
            )
            objectives = st.multiselect(
                "Objectives",
                ["Lead Generation", "Brand Awareness", "Sales", "Engagement"],
                key="strategy_objectives"
            )
        
        channels = st.multiselect(
            "Marketing Channels",
            ["LinkedIn", "Instagram", "Twitter", "Email", "Web"],
            key="strategy_channels"
        )
        
        if st.button("Create Strategy"):
            if strategy_name and objectives:
                st.success(f"✅ Strategy '{strategy_name}' created")
                st.json({
                    "name": strategy_name,
                    "industry": industry,
                    "budget": budget,
                    "duration": duration,
                    "objectives": objectives,
                    "channels": channels
                })
            else:
                st.error("Strategy name and objectives required")
        
        # Display strategies
        st.subheader("📋 Active Strategies")
        st.info("Backend would display active strategies here")
    
    except Exception as e:
        st.error(f"Error in Strategy tab: {str(e)}")


if __name__ == "__main__":
    render_strategy_tab()
