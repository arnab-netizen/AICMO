"""
Campaign Operations Streamlit UI - Dashboard implementation.

Integrated into aicmo_operator.py tab.
Provides operator command center for campaign management.
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Optional

from aicmo.campaign_ops.service import CampaignOpsService
from aicmo.campaign_ops.schemas import CampaignCreate
from aicmo.campaign_ops.wiring import get_session_for_campaign_ops


def render_campaign_ops_dashboard():
    """Main Campaign Ops dashboard renderer."""
    
    session = get_session_for_campaign_ops()
    if not session:
        st.error("❌ Database connection failed. Campaign Ops unavailable.")
        return
    
    service = CampaignOpsService(session)
    
    st.markdown("## 📋 Campaign Operations - Operator Command Center")
    st.markdown("""
    **Operator Dashboard**: Manage campaigns, view tasks, log metrics, and track execution.
    
    Everything you need to run campaigns like an agency with an operator in the loop.
    No autonomous posting—you control every action.
    """)
    
    # Main navigation
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Campaigns",
        "Today's Tasks",
        "Calendar",
        "Metrics",
        "Reports",
        "Settings",
    ])
    
    # ========================================================================
    # Tab 1: Campaigns
    # ========================================================================
    with tab1:
        st.subheader("📊 Campaign List")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            status_filter = st.selectbox(
                "Filter by status",
                ["All", "PLANNED", "ACTIVE", "PAUSED", "COMPLETED"],
            )
        
        with col2:
            if st.button("➕ New Campaign"):
                st.session_state.show_create_campaign = True
        
        # List campaigns
        status = None if status_filter == "All" else status_filter
        campaigns = service.list_campaigns(status=status)
        
        if campaigns:
            for campaign in campaigns:
                with st.container(border=True):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**{campaign.name}**")
                        st.caption(f"📱 Platforms: {', '.join(campaign.platforms)}")
                    
                    with col2:
                        st.write(f"🎯 {campaign.objective[:60]}...")
                        st.caption(f"Client: {campaign.client_name}")
                    
                    with col3:
                        status_color = {
                            "PLANNED": "🔵",
                            "ACTIVE": "🟢",
                            "PAUSED": "🟡",
                            "COMPLETED": "⚫",
                        }
                        st.write(f"{status_color.get(campaign.status, '')} {campaign.status}")
                        
                        if st.button("View", key=f"view_{campaign.id}"):
                            st.session_state.selected_campaign_id = campaign.id
        else:
            st.info("No campaigns found.")
        
        # Create campaign form
        if st.session_state.get("show_create_campaign"):
            st.divider()
            st.subheader("Create New Campaign")
            
            with st.form("create_campaign_form"):
                name = st.text_input("Campaign Name *", placeholder="Q1 2025 B2B Outreach")
                client_name = st.text_input("Client Name *", placeholder="Acme Corp")
                venture_name = st.text_input("Venture/Division", placeholder="Sales Dev")
                
                objective = st.text_area(
                    "Campaign Objective *",
                    placeholder="Generate qualified leads in finance vertical, focus on VP titles",
                )
                
                platforms = st.multiselect(
                    "Platforms",
                    ["linkedin", "instagram", "twitter", "email"],
                    default=["linkedin"],
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("Start Date", datetime.today())
                
                with col2:
                    end_date = st.date_input("End Date", datetime.today() + timedelta(days=30))
                
                primary_cta = st.text_input(
                    "Primary CTA *",
                    placeholder="Reply with 'audit' for free assessment",
                )
                
                cadence = {}
                st.write("**Posts per week (cadence)**:")
                col1, col2, col3, col4 = st.columns(4)
                for platform, col in zip(platforms, [col1, col2, col3, col4]):
                    with col:
                        cadence[platform] = st.number_input(
                            f"{platform.capitalize()}",
                            min_value=0,
                            max_value=7,
                            value=3,
                            key=f"cadence_{platform}",
                        )
                
                if st.form_submit_button("Create Campaign"):
                    try:
                        campaign = service.create_campaign(
                            CampaignCreate(
                                name=name,
                                client_name=client_name,
                                venture_name=venture_name,
                                objective=objective,
                                platforms=platforms,
                                start_date=datetime.combine(start_date, datetime.min.time()),
                                end_date=datetime.combine(end_date, datetime.min.time()),
                                cadence=cadence,
                                primary_cta=primary_cta,
                            )
                        )
                        st.success(f"✅ Campaign '{campaign.name}' created!")
                        st.session_state.show_create_campaign = False
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Failed to create campaign: {str(e)}")
    
    # ========================================================================
    # Tab 2: Today's Tasks
    # ========================================================================
    with tab2:
        st.subheader("📌 Today's Tasks")
        
        campaigns = service.list_campaigns(status="ACTIVE")
        
        if not campaigns:
            st.info("No active campaigns. Create one first!")
        else:
            selected_campaign = st.selectbox(
                "Select campaign",
                campaigns,
                format_func=lambda c: c.name,
            )
            
            if selected_campaign:
                today_tasks = service.get_today_tasks(selected_campaign.id)
                
                if today_tasks:
                    st.write(f"**{len(today_tasks)} tasks today**")
                    
                    for task in today_tasks:
                        _render_task_card(service, task)
                else:
                    st.info("No tasks for today.")
    
    # ========================================================================
    # Tab 3: Calendar
    # ========================================================================
    with tab3:
        st.subheader("📅 Campaign Calendar")
        
        campaigns = service.list_campaigns()
        if not campaigns:
            st.info("No campaigns yet.")
        else:
            selected_campaign = st.selectbox(
                "Select campaign",
                campaigns,
                format_func=lambda c: c.name,
                key="calendar_campaign",
            )
            
            if st.button("Generate Calendar (14 days)"):
                try:
                    items = service.generate_calendar(selected_campaign.id, days_ahead=14)
                    st.success(f"✅ Generated {len(items)} calendar items")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed: {e}")
    
    # ========================================================================
    # Tab 4: Metrics
    # ========================================================================
    with tab4:
        st.subheader("📊 Log Metrics")
        
        campaigns = service.list_campaigns(status="ACTIVE")
        if not campaigns:
            st.info("No active campaigns.")
        else:
            selected_campaign = st.selectbox(
                "Select campaign",
                campaigns,
                format_func=lambda c: c.name,
                key="metrics_campaign",
            )
            
            with st.form("log_metric_form"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    platform = st.selectbox(
                        "Platform",
                        selected_campaign.platforms,
                    )
                
                with col2:
                    date = st.date_input("Date", datetime.today())
                
                with col3:
                    metric_name = st.text_input("Metric", placeholder="impressions")
                
                metric_value = st.number_input("Value", min_value=0.0, step=0.1)
                notes = st.text_area("Notes", placeholder="Optional context")
                
                if st.form_submit_button("Log Metric"):
                    try:
                        from aicmo.campaign_ops.schemas import MetricEntryCreate
                        from aicmo.campaign_ops import repo
                        
                        repo.create_metric_entry(
                            session,
                            campaign_id=selected_campaign.id,
                            platform=platform,
                            date=datetime.combine(date, datetime.min.time()),
                            metric_name=metric_name,
                            metric_value=metric_value,
                            notes=notes,
                        )
                        st.success("✅ Metric logged")
                    except Exception as e:
                        st.error(f"❌ Failed: {e}")
    
    # ========================================================================
    # Tab 5: Reports
    # ========================================================================
    with tab5:
        st.subheader("📈 Weekly Reports")
        
        campaigns = service.list_campaigns()
        if not campaigns:
            st.info("No campaigns yet.")
        else:
            selected_campaign = st.selectbox(
                "Select campaign",
                campaigns,
                format_func=lambda c: c.name,
                key="report_campaign",
            )
            
            if st.button("Generate Weekly Summary"):
                try:
                    summary = service.generate_weekly_summary(selected_campaign.id)
                    
                    st.markdown(f"""
### Week of {summary.week_start.strftime('%B %d, %Y')}

**Tasks**:
- Planned: {summary.tasks_planned}
- Completed: {summary.tasks_completed}
- Overdue: {summary.tasks_overdue}
- Completion Rate: {(summary.tasks_completed / summary.tasks_planned * 100) if summary.tasks_planned > 0 else 0:.1f}%

**Top Platform**: {summary.top_platform or 'N/A'}

**Metrics**:
{_format_metrics_for_display(summary.metrics_summary)}

---
{summary.notes}
                    """)
                except Exception as e:
                    st.error(f"❌ Failed: {e}")
    
    # ========================================================================
    # Tab 6: Settings
    # ========================================================================
    with tab6:
        st.subheader("⚙️ Campaign Ops Settings")
        
        st.markdown("""
### Overview

**Campaign Operations** is the operator command center for AICMO.

- ✅ Create campaigns with objectives, platforms, cadence
- ✅ Generate planning, calendar, and task lists
- ✅ Provide WHERE+HOW SOP instructions per platform
- ✅ Track task completion with proof
- ✅ Log metrics manually
- ✅ Generate weekly reports
- ❌ NO autonomous posting (operators execute manually)

### AOL Integration

Campaign Ops can optionally integrate with AOL (Autonomy Orchestration Layer) for:
- Automatic task status updates (CAMPAIGN_TICK)
- Overdue task escalation (ESCALATE_OVERDUE_TASKS)
- Weekly summary generation (WEEKLY_CAMPAIGN_SUMMARY)

Enable in `.env`:
```
AICMO_CAMPAIGN_OPS_ENABLED=true
```

### Database

Campaign tables:
- `campaign_ops_campaigns` - Campaign metadata
- `campaign_ops_plans` - Strategy/angles
- `campaign_ops_calendar_items` - Scheduled posts
- `campaign_ops_operator_tasks` - Operator task items
- `campaign_ops_metric_entries` - Manual metrics
- `campaign_ops_audit_log` - Accountability log

All data persists to PostgreSQL (production) or SQLite (local).
        """)


def _render_task_card(service, task):
    """Render a single task card."""
    with st.container(border=True):
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            st.write(f"**{task.title}**")
            st.caption(f"📱 {task.platform}")
        
        with col2:
            st.code(task.copy_text or "No copy provided", language="text")
        
        with col3:
            status_emoji = {"PENDING": "⏳", "DUE": "🔴", "DONE": "✅", "BLOCKED": "🚫"}
            st.write(f"{status_emoji.get(task.status, '❓')} {task.status}")
            
            if st.button("Mark Done", key=f"done_{task.id}"):
                st.session_state.show_completion_form = task.id
        
        # Show instructions
        with st.expander("📋 Instructions"):
            st.markdown(task.instructions_text)
        
        # Completion form
        if st.session_state.get("show_completion_form") == task.id:
            st.divider()
            with st.form(f"complete_task_{task.id}"):
                proof_type = st.radio(
                    "Proof type",
                    ["URL", "TEXT", "UPLOAD"],
                )
                proof_value = st.text_area("Proof (paste URL, text, or filename)")
                
                if st.form_submit_button("Complete Task"):
                    try:
                        service.mark_task_complete(
                            task.id,
                            proof_type=proof_type,
                            proof_value=proof_value,
                        )
                        st.success("✅ Task completed!")
                        st.session_state.show_completion_form = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Failed: {e}")


def _format_metrics_for_display(metrics_summary: dict) -> str:
    """Format metrics for Streamlit display."""
    lines = []
    for platform, metrics_dict in metrics_summary.items():
        lines.append(f"**{platform.capitalize()}**:")
        for metric_name, value in metrics_dict.items():
            lines.append(f"  - {metric_name}: {value}")
    return "\n".join(lines) if lines else "(No metrics recorded)"
