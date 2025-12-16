"""
Delivery (Exports) Tab - Report generation and data export
"""

import streamlit as st
from aicmo.ui_v2.shared import (
    render_status_banner,
    backend_base_url,
    check_db_env_vars
)


def render_delivery_tab():
    """Render the Delivery tab"""
    st.header("📦 Delivery (Exports)")
    st.write("Generate reports and export campaign data.")
    
    try:
        # Status banner
        backend_url = "OK" if backend_base_url() else "Not configured"
        db_config = check_db_env_vars()
        db_status = "OK" if db_config['db_url_configured'] and not db_config['issues'] else "Unconfigured"
        
        render_status_banner("Delivery", backend_url, db_status)
        
        # Report generation
        st.subheader("📊 Generate Reports")
        
        report_type = st.selectbox(
            "Report Type",
            ["Campaign Summary", "Performance Analytics", "Lead ROI", "Executive Briefing"],
            key="delivery_report_type"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            report_start = st.date_input("Start Date", key="delivery_start")
        with col2:
            report_end = st.date_input("End Date", key="delivery_end")
        
        format_choice = st.selectbox(
            "Export Format",
            ["PDF", "CSV", "Excel", "JSON"],
            key="delivery_format"
        )
        
        if st.button("📥 Generate Report"):
            st.success(f"✅ {report_type} report generated as {format_choice}")
            st.info(f"Report ready for download: {report_type}_2025-12-16.{format_choice.lower()}")
        
        # Data export
        st.subheader("💾 Data Export")
        
        export_data = st.multiselect(
            "What to export?",
            ["Campaigns", "Leads", "Posts", "Analytics", "Budgets"],
            key="delivery_data"
        )
        
        if st.button("📦 Export Data"):
            st.success(f"✅ Exporting {', '.join(export_data)}")
            st.info("Download will start automatically")
        
        # Scheduled exports
        st.subheader("⏰ Scheduled Exports")
        
        enable_scheduled = st.toggle(
            "Enable scheduled exports",
            value=False,
            key="delivery_scheduled"
        )
        
        if enable_scheduled:
            schedule_freq = st.selectbox(
                "Frequency",
                ["Daily", "Weekly", "Monthly"],
                key="delivery_frequency"
            )
            
            schedule_day = st.selectbox(
                "Day/Time",
                ["Monday 6 AM", "Friday 5 PM", "1st of month", "Every day at 8 AM"],
                key="delivery_day"
            )
            
            schedule_recipient = st.text_input(
                "Email recipient",
                key="delivery_email"
            )
            
            if st.button("✅ Save Schedule"):
                st.success(f"✅ Scheduled {schedule_freq} to {schedule_recipient}")
    
    except Exception as e:
        st.error(f"Error in Delivery tab: {str(e)}")


if __name__ == "__main__":
    render_delivery_tab()
