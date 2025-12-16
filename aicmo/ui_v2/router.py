"""
Router for AICMO UI V2
Coordinates all 11 tabs with clean routing logic.
"""

import streamlit as st
import os
from aicmo.ui_v2.tabs.intake_tab import render_intake_tab
from aicmo.ui_v2.tabs.strategy_tab import render_strategy_tab
from aicmo.ui_v2.tabs.creatives_tab import render_creatives_tab
from aicmo.ui_v2.tabs.execution_tab import render_execution_tab
from aicmo.ui_v2.tabs.monitoring_tab import render_monitoring_tab
from aicmo.ui_v2.tabs.leadgen_tab import render_leadgen_tab
from aicmo.ui_v2.tabs.campaigns_tab import render_campaigns_tab
from aicmo.ui_v2.tabs.aol_autonomy_tab import render_autonomy_tab
from aicmo.ui_v2.tabs.delivery_tab import render_delivery_tab
from aicmo.ui_v2.tabs.learn_kaizen_tab import render_learn_tab
from aicmo.ui_v2.tabs.system_diag_tab import render_system_diag_tab


# Tab configuration - 11 top-level tabs
TABS = {
    "📥 Intake": ("Intake", render_intake_tab),
    "📊 Strategy": ("Strategy", render_strategy_tab),
    "🎨 Creatives": ("Creatives", render_creatives_tab),
    "🚀 Execution": ("Execution", render_execution_tab),
    "📈 Monitoring": ("Monitoring", render_monitoring_tab),
    "🎯 Lead Gen": ("Lead Gen", render_leadgen_tab),
    "🎬 Campaigns": ("Campaigns", render_campaigns_tab),
    "🤖 Autonomy": ("Autonomy", render_autonomy_tab),
    "📦 Delivery": ("Delivery", render_delivery_tab),
    "📚 Learn": ("Learn", render_learn_tab),
    "🔧 System": ("System", render_system_diag_tab),
}


def render_header():
    """Render dashboard header with watermark and build info"""
    dashboard_build = os.getenv("DASHBOARD_BUILD", "OPERATOR_V2_DEV")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.title("🎯 AICMO Operator Dashboard V2")
    
    with col2:
        st.write("")  # Spacing
    
    with col3:
        st.markdown(f"""
        <div style='text-align: right; font-size: 12px; color: #888;'>
        <b>Build:</b> {dashboard_build}<br/>
        <b>Status:</b> ✅ LIVE
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()


def route_to_tab(selected_tab: str):
    """Route to the appropriate tab renderer"""
    if selected_tab in TABS:
        tab_name, tab_render = TABS[selected_tab]
        try:
            tab_render()
        except Exception as e:
            st.error(f"Error rendering {tab_name} tab: {str(e)}")
            st.exception(e)
    else:
        st.error(f"Tab not found: {selected_tab}")


def render_router():
    """Main router - displays tab selector and routes to tabs"""
    
    render_header()
    
    # Print build marker to stderr for verification
    dashboard_build = os.getenv("DASHBOARD_BUILD", "OPERATOR_V2_DEV")
    print(f"[STREAMLIT] DASHBOARD_BUILD={dashboard_build}", flush=True)
    
    # Create tabs
    tab_names = list(TABS.keys())
    tabs = st.tabs(tab_names)
    
    # Route each tab
    for i, (tab_name, tab_object) in enumerate(zip(tab_names, tabs)):
        with tab_object:
            route_to_tab(tab_name)


if __name__ == "__main__":
    render_router()
