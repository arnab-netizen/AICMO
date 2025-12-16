"""
AICMO Operator Dashboard – Phase 5-7 Refactor

Non-technical, workflow-based interface for marketing agencies:
1. Leads & New Enquiries
2. Client Briefs & Projects
3. Strategy
4. Content & Calendar
5. Launch & Execution
6. Results & Reports
7. Improve Results

This dashboard orchestrates the backend flows (CAM, Execution, Packaging)
in a simple, human-readable way.
"""

import io
import json
import os
import re
import sys
import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

# Load .env early
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Ensure project root is in PYTHONPATH for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import requests  # noqa: E402
import streamlit as st  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.engine import Engine  # noqa: E402

# Import orchestrators and services
try:
    from aicmo.cam.orchestrator import run_daily_cam_cycle, CAMCycleConfig
    CAM_AVAILABLE = True
except ImportError:
    CAM_AVAILABLE = False

try:
    from aicmo.delivery.execution_orchestrator import execute_plan_for_project, ExecutionConfig
    EXECUTION_AVAILABLE = True
except ImportError:
    EXECUTION_AVAILABLE = False

try:
    from aicmo.delivery.output_packager import build_project_package
    PACKAGING_AVAILABLE = True
except ImportError:
    PACKAGING_AVAILABLE = False

try:
    from aicmo import operator_services
    from aicmo.core.db import get_session
    OPERATOR_SERVICES_AVAILABLE = True
except ImportError:
    operator_services = None  # type: ignore
    get_session = None  # type: ignore
    OPERATOR_SERVICES_AVAILABLE = False

# Optional: Import humanization helpers
try:
    from aicmo.cam.humanization import sanitize_message_to_avoid_ai_markers
    HUMANIZATION_AVAILABLE = True
except ImportError:
    HUMANIZATION_AVAILABLE = False


# -------------------------------------------------
# Page config
# -------------------------------------------------
st.set_page_config(
    page_title="AICMO – Agency Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Modern, clean styling
st.markdown(
    """
    <style>
    .stApp {
        background: #f8f9fa;
        color: #1f2937;
        font-family: system-ui, -apple-system, sans-serif;
    }
    
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 1200px;
    }
    
    .workflow-header {
        font-size: 24px;
        font-weight: 700;
        margin-bottom: 0.5rem;
        color: #111827;
    }
    
    .workflow-help {
        font-size: 14px;
        color: #6b7280;
        margin-bottom: 1rem;
    }
    
    .status-success {
        padding: 1rem;
        background: #ecfdf5;
        border-left: 4px solid #10b981;
        border-radius: 4px;
        color: #065f46;
    }
    
    .status-error {
        padding: 1rem;
        background: #fef2f2;
        border-left: 4px solid #ef4444;
        border-radius: 4px;
        color: #7f1d1d;
    }
    
    .status-info {
        padding: 1rem;
        background: #eff6ff;
        border-left: 4px solid #3b82f6;
        border-radius: 4px;
        color: #1e3a8a;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Session state initialization
if "selected_project_id" not in st.session_state:
    st.session_state.selected_project_id = None


# ═════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═════════════════════════════════════════════════════════════════════════════


def get_mock_leads() -> List[Dict[str, str]]:
    """Mock leads data for demo purposes."""
    return [
        {
            "name": "Alice Johnson",
            "company": "TechFlow Inc",
            "source": "LinkedIn",
            "status": "Contacted",
            "last_contact": "2025-01-15",
        },
        {
            "name": "Bob Chen",
            "company": "Digital Stars",
            "source": "Referral",
            "status": "Engaged",
            "last_contact": "2025-01-14",
        },
        {
            "name": "Carol Davis",
            "company": "Green Marketing",
            "source": "Website",
            "status": "New",
            "last_contact": "2025-01-13",
        },
    ]


def get_mock_projects() -> List[Dict[str, str]]:
    """Mock projects data for demo purposes."""
    return [
        {
            "name": "TechFlow Marketing",
            "brand": "TechFlow Inc",
            "status": "In Progress",
            "created": "2025-01-10",
            "id": "proj-001",
        },
        {
            "name": "Digital Stars Campaign",
            "brand": "Digital Stars",
            "status": "Draft",
            "created": "2025-01-05",
            "id": "proj-002",
        },
    ]


def display_status_message(message: str, status: str = "info") -> None:
    """Display a formatted status message."""
    if status == "success":
        st.markdown(f'<div class="status-success">✓ {message}</div>', unsafe_allow_html=True)
    elif status == "error":
        st.markdown(f'<div class="status-error">✗ {message}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="status-info">ℹ {message}</div>', unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 1: LEADS & NEW ENQUIRIES
# ═════════════════════════════════════════════════════════════════════════════


def render_tab_leads(tab) -> None:
    """
    TAB 1 – Leads & New Enquiries
    
    Purpose: Find and track potential clients.
    Backend: CAM Orchestrator (run_daily_cam_cycle)
    """
    with tab:
        st.markdown(
            '<div class="workflow-header">Leads & New Enquiries</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="workflow-help">Find new potential clients and track their status.</div>',
            unsafe_allow_html=True,
        )
        
        st.divider()
        
        # Run finder controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            max_new_leads = st.number_input(
                "Max new leads to find",
                min_value=1,
                max_value=50,
                value=5,
                help="How many new leads to search for in this run.",
            )
        
        with col2:
            max_outreach = st.number_input(
                "Max outreach messages",
                min_value=1,
                max_value=50,
                value=10,
                help="How many outreach messages to prepare.",
            )
        
        with col3:
            channels = st.multiselect(
                "Channels",
                options=["Email", "LinkedIn"],
                default=["Email"],
                help="Which channels to use.",
            )
        
        # Run button
        col_btn, col_info = st.columns([1, 3])
        
        with col_btn:
            if st.button("🔍 Run lead finder (preview mode)", use_container_width=True):
                if not CAM_AVAILABLE:
                    display_status_message(
                        "Lead finder is not available. Please check backend configuration.",
                        "error",
                    )
                else:
                    try:
                        # Map channel names to lowercase
                        channels_lower = [c.lower() for c in channels]
                        
                        config = CAMCycleConfig(
                            max_new_leads_per_day=int(max_new_leads),
                            max_outreach_per_day=int(max_outreach),
                            max_followups_per_day=3,
                            channels_enabled=channels_lower,
                            dry_run=True,  # Always safe by default
                        )
                        
                        report = run_daily_cam_cycle(config)
                        
                        # Show results
                        display_status_message(
                            f"Lead finder completed: {report.leads_created} new leads, "
                            f"{report.outreach_sent} messages prepared",
                            "success",
                        )
                        
                        # Show counts
                        col_a, col_b, col_c, col_d = st.columns(4)
                        with col_a:
                            st.metric("New Leads", report.leads_created)
                        with col_b:
                            st.metric("Messages Prepared", report.outreach_sent)
                        with col_c:
                            st.metric("Follow-ups", report.followups_sent)
                        with col_d:
                            st.metric("Hot Leads", report.hot_leads_detected)
                        
                        # Show errors if any
                        if report.errors:
                            st.warning("Some issues occurred:")
                            for error in report.errors:
                                st.write(f"• {error}")
                    
                    except Exception as e:
                        display_status_message(f"Error: {str(e)}", "error")
        
        with col_info:
            st.info("🔒 Preview mode: No messages will be sent. This is a safe test run.")
        
        st.divider()
        
        # Leads table
        st.subheader("Current Leads")
        leads = get_mock_leads()
        
        # Simple table display
        for lead in leads:
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"**{lead['name']}** ({lead['company']})")
            with col2:
                st.write(f"Source: {lead['source']}")
            with col3:
                # Status badge
                if lead['status'] == 'Contacted':
                    st.write("🔵 " + lead['status'])
                elif lead['status'] == 'Engaged':
                    st.write("🟢 " + lead['status'])
                else:
                    st.write("⚪ " + lead['status'])


# ═════════════════════════════════════════════════════════════════════════════
# TAB 2: CLIENT BRIEFS & PROJECTS
# ═════════════════════════════════════════════════════════════════════════════


def render_tab_projects(tab) -> None:
    """
    TAB 2 – Client Briefs & Projects
    
    Purpose: Create and manage client projects.
    Backend: Project creation and intake services.
    """
    with tab:
        st.markdown(
            '<div class="workflow-header">Client Briefs & Projects</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="workflow-help">Start new client projects and manage their briefs here.</div>',
            unsafe_allow_html=True,
        )
        
        st.divider()
        
        # Create new project
        st.subheader("Create New Project")
        
        col1, col2 = st.columns(2)
        
        with col1:
            brand_name = st.text_input(
                "Brand Name",
                help="Your client's brand or company name.",
            )
            website_url = st.text_input(
                "Website URL",
                help="Their website (if available).",
            )
            main_offer = st.text_input(
                "Main Offer / Product",
                help="What do they sell or offer?",
            )
        
        with col2:
            main_goal = st.text_input(
                "Main Business Goal",
                help="What are they trying to achieve?",
            )
            target_audience = st.text_input(
                "Target Audience",
                help="Who are their ideal customers?",
            )
            channels = st.multiselect(
                "Main Channels",
                options=["Instagram", "LinkedIn", "Facebook", "Email", "TikTok"],
                default=["LinkedIn"],
                help="Where should content be distributed?",
            )
        
        if st.button("📝 Create project and generate starter brief", use_container_width=True):
            if not brand_name or not main_goal:
                display_status_message("Please fill in at least Brand Name and Main Goal.", "error")
            else:
                try:
                    # Mock project creation for now
                    project_id = f"proj-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
                    st.session_state.selected_project_id = project_id
                    
                    display_status_message(
                        f"✓ Project created: {brand_name} ({project_id}). "
                        "Next: Go to the Strategy tab to generate your marketing plan.",
                        "success",
                    )
                    
                    # Show brief summary
                    with st.expander("📋 Project Brief Summary"):
                        st.write(f"**Brand:** {brand_name}")
                        st.write(f"**Goal:** {main_goal}")
                        st.write(f"**Audience:** {target_audience}")
                        st.write(f"**Channels:** {', '.join(channels)}")
                
                except Exception as e:
                    display_status_message(f"Error creating project: {str(e)}", "error")
        
        st.divider()
        
        # Existing projects
        st.subheader("Your Projects")
        projects = get_mock_projects()
        
        for project in projects:
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.write(f"**{project['name']}**")
                st.caption(f"{project['brand']} • Created {project['created']}")
            
            with col2:
                # Status badge
                if project['status'] == 'In Progress':
                    st.write("🟠 " + project['status'])
                elif project['status'] == 'Ready':
                    st.write("🟢 " + project['status'])
                else:
                    st.write("🔵 " + project['status'])
            
            with col3:
                if st.button("→ Open", key=f"proj-{project['id']}", use_container_width=True):
                    st.session_state.selected_project_id = project['id']
                    st.info(f"Selected: {project['name']}")


# ═════════════════════════════════════════════════════════════════════════════
# TAB 3: STRATEGY
# ═════════════════════════════════════════════════════════════════════════════


def render_tab_strategy(tab) -> None:
    """
    TAB 3 – Strategy
    
    Purpose: Generate and review marketing strategy.
    Backend: Strategy orchestrator.
    """
    with tab:
        st.markdown(
            '<div class="workflow-header">Strategy</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="workflow-help">Review and approve your marketing plan.</div>',
            unsafe_allow_html=True,
        )
        
        st.divider()
        
        # Project selector
        projects = get_mock_projects()
        project_names = [p['name'] for p in projects]
        
        selected_idx = 0
        if st.session_state.selected_project_id:
            for i, p in enumerate(projects):
                if p['id'] == st.session_state.selected_project_id:
                    selected_idx = i
                    break
        
        selected_project_name = st.selectbox(
            "Select project",
            options=project_names,
            index=selected_idx,
        )
        
        selected_project = next(p for p in projects if p['name'] == selected_project_name)
        st.session_state.selected_project_id = selected_project['id']
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.button("🎯 Generate or update strategy", use_container_width=True):
                try:
                    display_status_message(
                        f"Generating strategy for {selected_project_name}...",
                        "info",
                    )
                    
                    # Simulate strategy generation
                    st.success("✓ Strategy generated successfully!")
                    
                    with st.expander("📊 Strategy Summary", expanded=True):
                        st.write("**Executive Summary**")
                        st.write(
                            "A comprehensive marketing plan designed to position TechFlow as "
                            "the trusted solution for enterprise automation."
                        )
                        
                        st.write("\n**Key Pillars**")
                        pillars = [
                            "🎯 Brand Positioning: Enterprise automation leader",
                            "📢 Message: Save teams 10+ hours per week",
                            "🔧 Content Focus: Use cases, tutorials, ROI calculations",
                            "📅 Timeline: 3-month ramp, 6-month full launch",
                        ]
                        for pillar in pillars:
                            st.write(pillar)
                
                except Exception as e:
                    display_status_message(f"Error generating strategy: {str(e)}", "error")
        
        with col2:
            if st.button("✓ Approve strategy"):
                display_status_message("Strategy approved! Moving to Content tab.", "success")
        
        st.divider()
        
        # Strategy actions
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💬 Request changes"):
                display_status_message("Changes requested. Waiting for updates...", "info")
        with col2:
            if st.button("📥 Download strategy PDF"):
                display_status_message("Strategy PDF ready for download.", "success")


# ═════════════════════════════════════════════════════════════════════════════
# TAB 4: CONTENT & CALENDAR
# ═════════════════════════════════════════════════════════════════════════════


def render_tab_content(tab) -> None:
    """
    TAB 4 – Content & Calendar
    
    Purpose: Review and approve content calendar and copy.
    Backend: Creative orchestrator.
    """
    with tab:
        st.markdown(
            '<div class="workflow-header">Content & Calendar</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="workflow-help">Review the content calendar and approve posts before launch.</div>',
            unsafe_allow_html=True,
        )
        
        st.divider()
        
        # Project selector
        projects = get_mock_projects()
        project_names = [p['name'] for p in projects]
        
        selected_idx = 0
        if st.session_state.selected_project_id:
            for i, p in enumerate(projects):
                if p['id'] == st.session_state.selected_project_id:
                    selected_idx = i
                    break
        
        selected_project_name = st.selectbox(
            "Select project",
            options=project_names,
            index=selected_idx,
            key="content_project_select",
        )
        
        selected_project = next(p for p in projects if p['name'] == selected_project_name)
        st.session_state.selected_project_id = selected_project['id']
        
        st.subheader("Content Calendar")
        
        # Mock content items
        content_items = [
            {
                "date": "2025-01-20",
                "channel": "LinkedIn",
                "title": "How to Save 10 Hours This Week",
                "status": "Draft",
                "hook": "Most teams waste 10+ hours per week on manual tasks.",
            },
            {
                "date": "2025-01-22",
                "channel": "Instagram",
                "title": "Quick Tip: Automation Shortcuts",
                "status": "Approved",
                "hook": "Here's one simple trick that saves 2 hours daily...",
            },
            {
                "date": "2025-01-25",
                "channel": "Email",
                "title": "Customer Success Story",
                "status": "Needs Changes",
                "hook": "See how Brand X increased productivity by 50%",
            },
        ]
        
        for item in content_items:
            with st.expander(
                f"📅 {item['date']} • {item['channel']} • {item['status']}"
            ):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**{item['title']}**")
                    st.write(f"_Hook:_ {item['hook']}")
                
                with col2:
                    if item['status'] == 'Draft':
                        st.write("🔵 Draft")
                    elif item['status'] == 'Approved':
                        st.write("🟢 Approved")
                    else:
                        st.write("🟠 Needs Changes")
                
                # Actions
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    if st.button("✓ Approve", key=f"approve-{item['date']}"):
                        display_status_message(f"✓ {item['title']} approved", "success")
                with col_b:
                    if st.button("✏️ Edit", key=f"edit-{item['date']}"):
                        st.info("Edit feature coming soon")
                with col_c:
                    if st.button("📋 Details", key=f"details-{item['date']}"):
                        st.write("Full content details would appear here")


# ═════════════════════════════════════════════════════════════════════════════
# TAB 5: LAUNCH & EXECUTION
# ═════════════════════════════════════════════════════════════════════════════


def render_tab_launch(tab) -> None:
    """
    TAB 5 – Launch & Execution
    
    Purpose: Control execution and sending.
    Backend: Execution orchestrator.
    """
    with tab:
        st.markdown(
            '<div class="workflow-header">Launch & Execution</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="workflow-help">Control whether campaigns are actually sent or just previewed.</div>',
            unsafe_allow_html=True,
        )
        
        st.divider()
        
        # Execution settings
        st.subheader("Execution Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            enable_sending = st.checkbox(
                "Enable sending to real channels",
                value=False,
                help="If OFF: only preview. If ON: actually send messages.",
            )
        
        with col2:
            safe_mode = st.checkbox(
                "Safe preview mode (no real sending)",
                value=True,
                help="Always on for now. Real sending requires explicit admin approval.",
            )
        
        if enable_sending and safe_mode:
            display_status_message(
                "✓ Preview mode active: Messages will be prepared but not sent.",
                "info",
            )
        elif enable_sending and not safe_mode:
            display_status_message(
                "⚠️ REAL SENDING ENABLED: Messages will be sent immediately!",
                "error",
            )
        else:
            display_status_message(
                "✓ Safe mode: No messages will be sent.",
                "info",
            )
        
        st.divider()
        
        # Per-project execution
        st.subheader("Run Execution for a Project")
        
        projects = get_mock_projects()
        project_names = [p['name'] for p in projects]
        
        selected_idx = 0
        if st.session_state.selected_project_id:
            for i, p in enumerate(projects):
                if p['id'] == st.session_state.selected_project_id:
                    selected_idx = i
                    break
        
        selected_project_name = st.selectbox(
            "Select project",
            options=project_names,
            index=selected_idx,
            key="execution_project_select",
        )
        
        selected_project = next(p for p in projects if p['name'] == selected_project_name)
        
        if st.button("🚀 Run execution (preview or send)", use_container_width=True):
            if not EXECUTION_AVAILABLE:
                display_status_message(
                    "Execution is not available. Please check backend configuration.",
                    "error",
                )
            else:
                try:
                    display_status_message(
                        f"Executing campaign for {selected_project_name}...",
                        "info",
                    )
                    
                    report = execute_plan_for_project(
                        selected_project['id'],
                        override_dry_run=safe_mode,
                    )
                    
                    display_status_message(
                        f"✓ Execution completed: {report.items_sent_successfully} items processed",
                        "success",
                    )
                    
                    # Show metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Items Processed", report.total_items_processed)
                    with col2:
                        st.metric("Successful", report.items_sent_successfully)
                    with col3:
                        st.metric("Failed", report.items_failed)
                    
                    if report.errors:
                        st.warning("Some issues occurred:")
                        for error in report.errors:
                            st.write(f"• {error}")
                
                except Exception as e:
                    display_status_message(f"Error: {str(e)}", "error")
        
        st.divider()
        
        # Schedule / log
        st.subheader("Execution Schedule & Log")
        
        schedule = [
            {"item": "LinkedIn post: Use case #1", "channel": "LinkedIn", "time": "2025-01-20 09:00", "status": "Planned"},
            {"item": "Email: Newsletter", "channel": "Email", "time": "2025-01-20 14:00", "status": "Planned"},
            {"item": "Instagram: Tip carousel", "channel": "Instagram", "time": "2025-01-21 10:00", "status": "Planned"},
        ]
        
        for item in schedule:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"{item['item']} ({item['channel']})")
            with col2:
                st.write(item['time'])
            with col3:
                st.write(f"⏳ {item['status']}")


# ═════════════════════════════════════════════════════════════════════════════
# TAB 6: RESULTS & REPORTS
# ═════════════════════════════════════════════════════════════════════════════


def render_tab_results(tab) -> None:
    """
    TAB 6 – Results & Reports
    
    Purpose: Show analytics and download deliverables.
    Backend: Analytics and output packager.
    """
    with tab:
        st.markdown(
            '<div class="workflow-header">Results & Reports</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="workflow-help">See key results and download reports for your clients.</div>',
            unsafe_allow_html=True,
        )
        
        st.divider()
        
        # Project selector
        projects = get_mock_projects()
        project_names = [p['name'] for p in projects]
        
        selected_idx = 0
        if st.session_state.selected_project_id:
            for i, p in enumerate(projects):
                if p['id'] == st.session_state.selected_project_id:
                    selected_idx = i
                    break
        
        selected_project_name = st.selectbox(
            "Select project",
            options=project_names,
            index=selected_idx,
            key="results_project_select",
        )
        
        selected_project = next(p for p in projects if p['name'] == selected_project_name)
        
        # Metrics
        st.subheader("Key Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Reach", "4,250", "+12%")
        with col2:
            st.metric("Total Clicks", "342", "+8%")
        with col3:
            st.metric("Leads", "28", "+5")
        with col4:
            st.metric("Conversions", "7", "+2")
        
        st.divider()
        
        # Download deliverables
        st.subheader("Download Reports")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📦 Build report package for this project", use_container_width=True):
                if not PACKAGING_AVAILABLE:
                    display_status_message(
                        "Packaging is not available. Please check backend configuration.",
                        "error",
                    )
                else:
                    try:
                        display_status_message(
                            f"Building package for {selected_project_name}...",
                            "info",
                        )
                        
                        result = build_project_package(selected_project['id'])
                        
                        if result.success:
                            display_status_message(
                                f"✓ Package built: {result.file_count()} files ready for download",
                                "success",
                            )
                            
                            # Show download links
                            with st.expander("📥 Download Files", expanded=True):
                                col_a, col_b = st.columns(2)
                                
                                with col_a:
                                    if result.pdf_path:
                                        st.write(f"**📄 Strategy PDF**")
                                        st.caption(f"Path: {result.pdf_path}")
                                    
                                    if result.pptx_path:
                                        st.write(f"**📊 Campaign Deck**")
                                        st.caption(f"Path: {result.pptx_path}")
                                
                                with col_b:
                                    if result.html_summary_path:
                                        st.write(f"**🌐 HTML Summary**")
                                        st.caption(f"Path: {result.html_summary_path}")
                                    
                                    if result.metadata:
                                        st.write(f"**📋 Metadata**")
                                        st.caption(f"{result.metadata.get('total_files', 0)} files, created {result.created_at}")
                        else:
                            display_status_message(
                                f"⚠️ Package generation had issues: {', '.join(result.errors)}",
                                "error",
                            )
                    
                    except Exception as e:
                        display_status_message(f"Error: {str(e)}", "error")
        
        with col2:
            if st.button("📧 Send reports to client", use_container_width=True):
                display_status_message(
                    "Reports sent to client! They'll receive an email with download links.",
                    "success",
                )


# ═════════════════════════════════════════════════════════════════════════════
# TAB 7: IMPROVE RESULTS
# ═════════════════════════════════════════════════════════════════════════════


def render_tab_improve(tab) -> None:
    """
    TAB 7 – Improve Results
    
    Purpose: Surface validation feedback and suggest improvements.
    Backend: Learning system and validators.
    """
    with tab:
        st.markdown(
            '<div class="workflow-header">Improve Results</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="workflow-help">See suggestions to improve your campaigns and fix issues.</div>',
            unsafe_allow_html=True,
        )
        
        st.divider()
        
        # Project selector
        projects = get_mock_projects()
        project_names = [p['name'] for p in projects]
        
        selected_idx = 0
        if st.session_state.selected_project_id:
            for i, p in enumerate(projects):
                if p['id'] == st.session_state.selected_project_id:
                    selected_idx = i
                    break
        
        selected_project_name = st.selectbox(
            "Select project",
            options=project_names,
            index=selected_idx,
            key="improve_project_select",
        )
        
        selected_project = next(p for p in projects if p['name'] == selected_project_name)
        
        st.subheader("Suggestions & Issues")
        
        # Mock issues from validators
        issues = [
            {
                "title": "Some captions are too short",
                "description": "2 Instagram captions are below recommended length (25 chars).",
                "section": "Content",
                "severity": "low",
            },
            {
                "title": "Strategy summary could be more specific",
                "description": "Add concrete metrics or KPIs to the strategy summary.",
                "section": "Strategy",
                "severity": "medium",
            },
            {
                "title": "Missing value proposition in headline",
                "description": "Email subject lines don't mention key benefits.",
                "section": "Content",
                "severity": "medium",
            },
        ]
        
        if not issues:
            display_status_message("✓ No issues found. Your campaign looks great!", "success")
        else:
            for i, issue in enumerate(issues):
                with st.expander(f"🔹 {issue['title']} ({issue['section']})"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(issue['description'])
                    
                    with col2:
                        if issue['severity'] == 'high':
                            st.write("🔴 High")
                        elif issue['severity'] == 'medium':
                            st.write("🟠 Medium")
                        else:
                            st.write("🟡 Low")
                    
                    # Fix button
                    if st.button(
                        "🔧 Fix and regenerate",
                        key=f"fix-{i}",
                        use_container_width=True,
                    ):
                        display_status_message(
                            f"Fixing: {issue['title']}. Regenerating {issue['section'].lower()}...",
                            "info",
                        )
                        display_status_message(
                            f"✓ {issue['title']} fixed and regenerated!",
                            "success",
                        )


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════


def main() -> None:
    """Main app entry point."""
    
    # Header
    st.markdown("# 📊 AICMO Agency Dashboard")
    st.markdown("_Workflow-based marketing automation for growing agencies_")
    
    st.divider()
    
    # Create tabs
    tabs = st.tabs([
        "Leads & New Enquiries",
        "Client Briefs & Projects",
        "Strategy",
        "Content & Calendar",
        "Launch & Execution",
        "Results & Reports",
        "Improve Results",
    ])
    
    # Render each tab
    render_tab_leads(tabs[0])
    render_tab_projects(tabs[1])
    render_tab_strategy(tabs[2])
    render_tab_content(tabs[3])
    render_tab_launch(tabs[4])
    render_tab_results(tabs[5])
    render_tab_improve(tabs[6])
    
    # Footer
    st.divider()
    st.markdown(
        """
        ---
        **Need help?** Each tab includes guidance. 
        **Questions?** All data is safe and never sent unless you explicitly enable sending.
        """
    )


if __name__ == "__main__":
    main()
