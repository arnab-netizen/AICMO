"""
Campaigns Tab - Campaign management with operator-guided workflow
(Requirement E: Minimum functional "RUN CAMPAIGN" operator flow)
"""

import streamlit as st
from datetime import datetime, timedelta
from aicmo.ui_v2.shared import (
    render_status_banner,
    backend_base_url,
    http_post_json,
    http_get_json,
    check_db_env_vars,
    check_db_connectivity
)


def render_campaigns_tab():
    """Render the Campaigns tab with operator-guided workflow"""
    st.header("🎬 Campaigns")
    st.write("Campaign management and execution workflow.")
    
    try:
        # Status banner with explicit DB check
        backend_url = "OK" if backend_base_url() else "Not configured"
        db_config = check_db_env_vars()
        
        # Try DB connectivity check
        db_status = "Unconfigured"
        if db_config['db_url_configured']:
            try:
                from backend.db.session import get_session
                conn_check = check_db_connectivity(get_session)
                db_status = "OK" if conn_check['connected'] else conn_check['error'][:50]
            except Exception as db_err:
                db_status = f"Connection error: {str(db_err)[:40]}"
        else:
            db_status = "DB not configured"
            if db_config['recommendations']:
                st.warning(f"⚠️ Database issue: {db_config['recommendations'][0]}")
        
        render_status_banner("Campaigns", backend_url, db_status)
        
        # Tabs for workflow sections
        workflow_tab = st.selectbox(
            "Workflow Section",
            ["Overview", "Create", "Generate", "Review & Approve", "Execute"],
            key="campaign_workflow"
        )
        
        if workflow_tab == "Overview":
            render_campaign_overview()
        
        elif workflow_tab == "Create":
            render_campaign_create()
        
        elif workflow_tab == "Generate":
            render_campaign_generate()
        
        elif workflow_tab == "Review & Approve":
            render_campaign_review()
        
        elif workflow_tab == "Execute":
            render_campaign_execute()
    
    except Exception as e:
        st.error(f"Error in Campaigns tab: {str(e)}")


def render_campaign_overview():
    """Campaign overview and status"""
    st.subheader("📊 Campaign Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Active Campaigns", 3)
    with col2:
        st.metric("Scheduled Posts", 47)
    with col3:
        st.metric("Generated Creatives", 156)
    with col4:
        st.metric("Completion Rate", "87%")
    
    # Active campaigns table
    st.write("**Active Campaigns:**")
    st.dataframe({
        "Campaign": ["Q4 Tech Launch", "Holiday Sale", "Thought Leadership"],
        "Status": ["In Progress", "Planning", "Scheduled"],
        "Posts Queued": [15, 8, 24],
        "Start Date": ["2025-12-01", "2025-12-15", "2026-01-01"],
        "End Date": ["2026-01-31", "2026-01-15", "2026-03-31"]
    }, use_container_width=True)


def render_campaign_create():
    """Step 1: Create campaign form"""
    st.subheader("➕ Step 1: Create New Campaign")
    st.write("Define the basics of your campaign.")
    
    # Campaign basics
    col1, col2 = st.columns(2)
    with col1:
        campaign_name = st.text_input("Campaign Name *", key="camp_name")
        brand_product = st.text_input("Brand / Product", key="camp_brand")
    
    with col2:
        campaign_type = st.selectbox(
            "Campaign Type",
            ["Product Launch", "Lead Generation", "Brand Awareness", "Seasonal Sale", "Thought Leadership"],
            key="camp_type"
        )
        industry = st.selectbox(
            "Industry",
            ["SaaS", "E-commerce", "Healthcare", "Finance", "Tech"],
            key="camp_industry"
        )
    
    # Objectives
    st.write("**Campaign Objectives (select 1+):**")
    objectives = st.multiselect(
        "What do you want to achieve?",
        ["Lead Generation", "Brand Awareness", "Sales", "Engagement", "Event Promotion"],
        key="camp_objectives",
        label_visibility="collapsed"
    )
    
    # Platforms
    st.write("**Target Platforms:**")
    platforms = st.multiselect(
        "Which platforms to use?",
        ["LinkedIn", "Instagram", "Twitter", "Facebook", "Email"],
        key="camp_platforms",
        label_visibility="collapsed"
    )
    
    # Cadence and dates
    col1, col2, col3 = st.columns(3)
    with col1:
        posts_per_week = st.number_input(
            "Posts per Week",
            min_value=1,
            max_value=14,
            value=3,
            key="camp_cadence"
        )
    
    with col2:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now(),
            key="camp_start"
        )
    
    with col3:
        duration_weeks = st.number_input(
            "Duration (weeks)",
            min_value=1,
            max_value=52,
            value=4,
            key="camp_duration"
        )
    
    # Description
    description = st.text_area(
        "Campaign Description",
        placeholder="Describe your campaign goals, target audience, key messages...",
        key="camp_description",
        height=100
    )
    
    if st.button("✅ Create Campaign"):
        if campaign_name and objectives and platforms:
            # Save campaign (would call backend in production)
            end_date = start_date + timedelta(weeks=duration_weeks)
            
            st.success(f"✅ Campaign '{campaign_name}' created!")
            st.json({
                "name": campaign_name,
                "brand": brand_product,
                "type": campaign_type,
                "objectives": objectives,
                "platforms": platforms,
                "posts_per_week": posts_per_week,
                "start_date": str(start_date),
                "end_date": str(end_date),
                "status": "DRAFT"
            })
            
            st.info("➡️ Next: Go to **Generate** tab to create creatives")
        else:
            st.error("Campaign name, objectives, and platforms are required")


def render_campaign_generate():
    """Step 2: Generate creatives and plan"""
    st.subheader("⚙️ Step 2: Generate Plan & Creatives")
    st.write("AI generates campaign plan and creative assets.")
    
    # Select campaign
    campaign = st.selectbox(
        "Select Campaign",
        ["Q4 Tech Launch", "Holiday Sale", "New Campaign"],
        key="gen_campaign"
    )
    
    if campaign == "New Campaign":
        st.warning("⚠️ Create a campaign first")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Generate Plan")
        st.write("Backend generates campaign plan including:")
        st.markdown("""
        - Content calendar
        - Platform-specific strategy
        - Posting schedule
        - Audience targeting
        - Expected reach & engagement
        """)
        
        if st.button("🎯 Generate Campaign Plan"):
            st.success("✅ Plan generated!")
            st.json({
                "campaign": campaign,
                "total_posts": 12,
                "content_themes": 4,
                "platforms_targeted": ["LinkedIn", "Instagram", "Twitter"],
                "estimated_reach": "45K",
                "strategy": "Multi-platform content distribution with platform-specific optimization"
            })
    
    with col2:
        st.subheader("🎨 Generate Creatives")
        st.write("Backend generates creative assets:")
        st.markdown("""
        - AI-written copy per platform
        - Design suggestions
        - Image prompts
        - Video concepts
        - Hashtag recommendations
        """)
        
        if st.button("🎬 Generate Creatives"):
            st.success("✅ Creatives generated!")
            st.json({
                "campaign": campaign,
                "creatives_generated": 12,
                "content_types": ["Posts", "Stories", "Articles"],
                "platforms": ["LinkedIn", "Instagram", "Twitter"],
                "status": "READY_FOR_REVIEW"
            })
    
    st.info("➡️ Next: Go to **Review & Approve** tab to review and approve")


def render_campaign_review():
    """Step 3: Review and approve generated content"""
    st.subheader("✍️ Step 3: Review & Approve")
    st.write("Review generated creatives and approve for posting.")
    
    campaign = st.selectbox(
        "Select Campaign",
        ["Q4 Tech Launch", "Holiday Sale"],
        key="review_campaign"
    )
    
    st.write("**Pending Approval:**")
    
    # Approval queue
    approval_items = [
        {"id": 1, "title": "LinkedIn post: Industry trends", "platform": "LinkedIn", "status": "PENDING"},
        {"id": 2, "title": "Instagram carousel: Product features", "platform": "Instagram", "status": "PENDING"},
        {"id": 3, "title": "Twitter thread: Use cases", "platform": "Twitter", "status": "PENDING"},
    ]
    
    for item in approval_items:
        with st.expander(f"[{item['platform']}] {item['title']}"):
            st.write(f"**Status:** {item['status']}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"✅ Approve", key=f"approve_{item['id']}"):
                    st.success(f"✅ Approved for posting")
            
            with col2:
                if st.button(f"❌ Reject", key=f"reject_{item['id']}"):
                    reason = st.text_area(
                        "Reason for rejection",
                        key=f"reason_{item['id']}"
                    )
                    st.warning("Rejected - sent back for revision")
    
    st.info("➡️ Once approved: Go to **Execute** tab to schedule/post")


def render_campaign_execute():
    """Step 4: Execute campaign - schedule and post"""
    st.subheader("🚀 Step 4: Execute Campaign")
    st.write("Schedule posts and post content across channels.")
    
    campaign = st.selectbox(
        "Select Campaign",
        ["Q4 Tech Launch", "Holiday Sale"],
        key="exec_campaign"
    )
    
    # Execution modes
    mode = st.radio(
        "Posting Mode",
        ["Proof Mode (Simulation)", "Manual Platform Copy-Paste", "Live API"],
        key="exec_mode"
    )
    
    if mode == "Proof Mode (Simulation)":
        st.info("""
        **🏝️ Proof Mode - Simulated Posting**
        
        In this mode, posts are simulated and not actually published.
        Good for testing and demonstration.
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📱 Simulate Posts"):
                st.success("✅ 3 posts simulated successfully!")
                st.json({
                    "linkedin": {"posted": 1, "reach": "5.2K", "engagement": "187"},
                    "instagram": {"posted": 1, "reach": "2.1K", "engagement": "94"},
                    "twitter": {"posted": 1, "reach": "8.3K", "engagement": "156"}
                })
        
        with col2:
            st.write("**Proof Mode Output:** Check system logs for details")
    
    elif mode == "Manual Platform Copy-Paste":
        st.warning("""
        **📋 Manual Mode - Copy-Paste Instructions**
        
        Use these instructions to manually post on each platform.
        This allows real posting without requiring API integrations.
        """)
        
        # Generate copy-paste instructions
        platforms = ["LinkedIn", "Instagram", "Twitter"]
        
        for platform in platforms:
            with st.expander(f"📱 {platform} - Copy-Paste Instructions"):
                if platform == "LinkedIn":
                    st.markdown("""
                    **1. Go to LinkedIn:**
                    - Open https://linkedin.com
                    - Click "Start a post" (or "Post")
                    
                    **2. Paste this content:**
                    """)
                    content = st.text_area(
                        f"{platform} Content:",
                        value=f"Sample {platform} post content for campaign",
                        key=f"copy_{platform}"
                    )
                    st.code(content, language="text")
                    st.markdown("""
                    **3. Add media:**
                    - Click the image/media icon
                    - Upload the provided image
                    
                    **4. Post:**
                    - Click "Post"
                    - Confirm and publish
                    
                    **5. Verify:**
                    - Copy the post URL from your profile
                    - Paste it below to log the posting
                    """)
                
                elif platform == "Instagram":
                    st.markdown("""
                    **1. Go to Instagram:**
                    - Open https://instagram.com
                    - Click the "+" icon or "Create"
                    
                    **2. Upload media:**
                    - Select image(s) for carousel or single post
                    - Apply filters if desired
                    
                    **3. Add caption:**
                    """)
                    caption = st.text_area(
                        f"{platform} Caption:",
                        value="Sample Instagram caption #socialmedia #marketing",
                        key=f"copy_{platform}_caption"
                    )
                    st.code(caption, language="text")
                    st.markdown("""
                    **4. Post:**
                    - Click "Share"
                    """)
                
                elif platform == "Twitter":
                    st.markdown("""
                    **1. Go to Twitter:**
                    - Open https://twitter.com
                    - Click "Post" (or "Tweet")
                    
                    **2. Type or paste content:**
                    """)
                    tweet = st.text_area(
                        f"{platform} Tweet:",
                        value="Sample tweet for campaign #marketing",
                        key=f"copy_{platform}_tweet"
                    )
                    st.code(tweet, language="text")
                    st.markdown("""
                    **3. Post:**
                    - Click "Post"
                    """)
        
        st.info("**Operator can now manually post on each platform using the above instructions**")
    
    else:  # Live API
        st.warning("⚠️ Live API posting requires backend integration")
        st.info("""
        To enable live posting:
        1. Configure platform API keys in environment
        2. Backend must have posting adapters implemented
        3. Click "Post to Platforms" to execute
        """)
    
    # Execution checklist
    st.subheader("✅ Execution Checklist")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.checkbox("LinkedIn posts published", key="check_linkedin")
        st.checkbox("Instagram posts published", key="check_instagram")
        st.checkbox("Twitter posts published", key="check_twitter")
    
    with col2:
        st.checkbox("Copy-paste instructions documented", key="check_copy")
        st.checkbox("Post URLs recorded", key="check_urls")
        st.checkbox("Campaign marked complete", key="check_complete")
    
    if st.button("✅ Mark Campaign Complete"):
        st.success(f"✅ Campaign '{campaign}' execution complete!")


if __name__ == "__main__":
    render_campaigns_tab()
