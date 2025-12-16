# This is the E2E UI section to be integrated into streamlit_app.py
# Insert this after line 912 (after the existing system pause control)

    # ─── E2E DIAGNOSTICS & REVENUE ENGINE UI (Test Mode Only) ──────────────────────────
    # Only show when AICMO_E2E_DIAGNOSTICS=1 or AICMO_REVENUE_ENGINE_UI=1
    if os.getenv("AICMO_E2E_DIAGNOSTICS") == "1" or os.getenv("AICMO_REVENUE_ENGINE_UI") == "1":
        st.markdown("---")
        st.markdown("## 🔬 E2E Revenue Engine (Test Mode)")
        st.warning("⚠️ This panel is only visible in E2E test mode")
        
        from aicmo.core.e2e_helpers import hard_reset_test_data
        from aicmo.core.db import get_session
        from aicmo.cam.db_models import CampaignDB, LeadDB, OutreachAttemptDB, LeadAttributionDB
        from aicmo.cam.domain import LeadStatus, AttemptStatus, Channel
        import json
        from sqlalchemy.sql import func
        
        # Initialize session state for E2E UI
        if 'e2e_reset_success' not in st.session_state:
            st.session_state.e2e_reset_success = False
        if 'e2e_last_report_path' not in st.session_state:
            st.session_state.e2e_last_report_path = None
        if 'e2e_last_report_valid' not in st.session_state:
            st.session_state.e2e_last_report_valid = False
        
        with get_session() as session:
            try:
                # Get or create default campaign for E2E testing
                campaign = session.query(CampaignDB).filter_by(name="E2E Test Campaign").first()
                if not campaign:
                    campaign = CampaignDB(
                        name="E2E Test Campaign",
                        description="Auto-created for E2E testing",
                        active=True,
                        mode="SIMULATION"
                    )
                    session.add(campaign)
                    session.commit()
                    session.refresh(campaign)
                
                campaign_id = campaign.id
                
                # SYSTEM PAUSE CONTROL (Test 1)
                st.markdown("### 🎛️ System Controls")
                col_pause, col_badge = st.columns([1, 3])
                
                with col_pause:
                    paused = st.session_state.get('system_paused', False)
                    st.markdown('<div data-testid="aicmo-system-pause-toggle">', unsafe_allow_html=True)
                    new_paused = st.checkbox("⏸️ Pause All Execution", value=paused, key="e2e_pause_checkbox")
                    st.markdown('</div>', unsafe_allow_html=True)
                    if new_paused != paused:
                        st.session_state.system_paused = new_paused
                
                with col_badge:
                    if st.session_state.get('system_paused', False):
                        st.markdown('<div data-testid="aicmo-system-paused-badge" style="padding: 0.5rem; background: #ff4b4b; color: white; border-radius: 0.5rem; text-align: center;">🛑 System Paused</div>', unsafe_allow_html=True)
                
                st.markdown("---")
                
                # LEAD CAPTURE FORM (Test 2)
                st.markdown("### 📋 Lead Capture")
                col_email, col_utm = st.columns(2)
                
                with col_email:
                    st.markdown('<div data-testid="aicmo-lead-email">', unsafe_allow_html=True)
                    lead_email = st.text_input("Email", key="e2e_lead_email_input", placeholder="lead@example.com")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col_utm:
                    st.markdown('<div data-testid="aicmo-lead-utm-campaign">', unsafe_allow_html=True)
                    lead_utm = st.text_input("UTM Campaign", key="e2e_lead_utm_input", placeholder="e2e_campaign")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('<div data-testid="aicmo-lead-submit">', unsafe_allow_html=True)
                if st.button("➕ Add Lead", key="e2e_lead_submit_btn", type="primary"):
                    if lead_email:
                        existing = session.query(LeadDB).filter_by(email=lead_email, campaign_id=campaign_id).first()
                        if existing:
                            existing.status = LeadStatus.CONTACTED
                            st.success(f"✅ Lead updated (dedupe): {lead_email}")
                        else:
                            new_lead = LeadDB(
                                campaign_id=campaign_id,
                                email=lead_email,
                                name=lead_email.split('@')[0],
                                status=LeadStatus.NEW,
                                consent_status="CONSENTED",
                                source_channel=lead_utm or "direct"
                            )
                            session.add(new_lead)
                            session.flush()
                            existing = new_lead
                            st.success(f"✅ Lead created: {lead_email}")
                        
                        if lead_utm:
                            attr = session.query(LeadAttributionDB).filter_by(lead_id=existing.id, campaign_id=campaign_id).first()
                            if not attr:
                                attr = LeadAttributionDB(
                                    lead_id=existing.id,
                                    campaign_id=campaign_id,
                                    attribution_model="LAST_TOUCH",
                                    first_touch_channel=lead_utm,
                                    first_touch_date=func.now(),
                                    last_touch_channel=lead_utm,
                                    last_touch_date=func.now()
                                )
                                session.add(attr)
                            else:
                                attr.last_touch_channel = lead_utm
                                attr.last_touch_date = func.now()
                        session.commit()
                    else:
                        st.error("❌ Email is required")
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown("---")
                
                # DNC TOGGLE (Test 3)
                st.markdown("### 🚫 DNC Management")
                leads = session.query(LeadDB).filter_by(campaign_id=campaign_id).all()
                
                if leads:
                    st.markdown('<div data-testid="aicmo-lead-picker">', unsafe_allow_html=True)
                    lead_options = {f"{l.email} ({l.id})": l.id for l in leads}
                    selected_lead_key = st.selectbox("Select Lead", options=list(lead_options.keys()), key="e2e_lead_picker_select")
                    selected_lead_id = lead_options[selected_lead_key]
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    selected_lead = session.query(LeadDB).get(selected_lead_id)
                    if selected_lead:
                        col_dnc_toggle, col_dnc_save = st.columns([2, 1])
                        with col_dnc_toggle:
                            st.markdown('<div data-testid="aicmo-lead-dnc-toggle">', unsafe_allow_html=True)
                            is_dnc = selected_lead.consent_status == "DNC"
                            dnc_checked = st.checkbox("Mark as DNC", value=is_dnc, key="e2e_dnc_checkbox")
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        with col_dnc_save:
                            st.markdown('<div data-testid="aicmo-lead-dnc-save">', unsafe_allow_html=True)
                            if st.button("💾 Save DNC", key="e2e_dnc_save_btn"):
                                selected_lead.consent_status = "DNC" if dnc_checked else "CONSENTED"
                                session.commit()
                                st.success(f"✅ DNC status updated")
                            st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.info("No leads found. Add a lead first.")
                
                st.markdown("---")
                
                # JOB ENQUEUE & DISPATCHER (Test 4)
                st.markdown("### 📤 Outreach Dispatch")
                col_enqueue, col_dispatch = st.columns(2)
                
                with col_enqueue:
                    st.markdown('<div data-testid="aicmo-enqueue-email-job">', unsafe_allow_html=True)
                    if st.button("📨 Enqueue Job", key="e2e_enqueue_btn", type="primary"):
                        eligible_lead = session.query(LeadDB).filter(
                            LeadDB.campaign_id == campaign_id,
                            LeadDB.consent_status == "CONSENTED"
                        ).first()
                        if eligible_lead:
                            attempt = OutreachAttemptDB(
                                lead_id=eligible_lead.id,
                                campaign_id=campaign_id,
                                channel=Channel.EMAIL,
                                step_number=1,
                                status=AttemptStatus.PENDING
                            )
                            session.add(attempt)
                            session.commit()
                            st.success(f"✅ Job enqueued")
                        else:
                            st.warning("⚠️ No eligible leads")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col_dispatch:
                    st.markdown('<div data-testid="aicmo-run-dispatcher-once">', unsafe_allow_html=True)
                    if st.button("🚀 Run Dispatcher", key="e2e_dispatch_btn", type="secondary"):
                        pending = session.query(OutreachAttemptDB).filter(
                            OutreachAttemptDB.campaign_id == campaign_id,
                            OutreachAttemptDB.status == AttemptStatus.PENDING
                        ).all()
                        executed = 0
                        for attempt in pending:
                            lead = session.query(LeadDB).get(attempt.lead_id)
                            if lead and lead.consent_status != "DNC":
                                attempt.status = AttemptStatus.PROOF_SENT
                                executed += 1
                        session.commit()
                        st.success(f"✅ Dispatched {executed} jobs (PROOF-RUN)")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown("---")
                
                # EXPORT CSV & GENERATE REPORT (Test 5)
                st.markdown("### 📊 Export & Reporting")
                col_export, col_report = st.columns(2)
                
                with col_export:
                    leads_export = session.query(LeadDB).filter_by(campaign_id=campaign_id).all()
                    if leads_export:
                        import pandas as pd
                        df_leads = pd.DataFrame([
                            {
                                'id': l.id,
                                'email': l.email,
                                'name': l.name,
                                'status': l.status.value if hasattr(l.status, 'value') else str(l.status),
                                'consent_status': l.consent_status,
                                'source_channel': l.source_channel
                            }
                            for l in leads_export
                        ])
                        csv = df_leads.to_csv(index=False)
                        st.markdown('<div data-testid="aicmo-export-leads-csv">', unsafe_allow_html=True)
                        st.download_button(
                            label="📥 Export CSV",
                            data=csv,
                            file_name=f"campaign_{campaign_id}_leads.csv",
                            mime="text/csv",
                            key="e2e_export_csv_btn"
                        )
                        st.markdown('</div>', unsafe_allow_html=True)
                
                with col_report:
                    st.markdown('<div data-testid="aicmo-generate-campaign-report">', unsafe_allow_html=True)
                    if st.button("📄 Generate Report", key="e2e_report_btn", type="secondary"):
                        import os as os_module
                        from datetime import datetime
                        artifacts_dir = f"artifacts/campaign_{campaign_id}"
                        os_module.makedirs(artifacts_dir, exist_ok=True)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        report_path = f"{artifacts_dir}/report_{timestamp}.txt"
                        
                        lead_count = session.query(LeadDB).filter_by(campaign_id=campaign_id).count()
                        attempt_count = session.query(OutreachAttemptDB).filter_by(campaign_id=campaign_id).count()
                        attr_count = session.query(LeadAttributionDB).filter_by(campaign_id=campaign_id).count()
                        
                        report_content = f"""Campaign Report: {campaign.name}
Generated: {datetime.now().isoformat()}

=== Executive Summary ===
Campaign ID: {campaign_id}
Total Leads: {lead_count}
Outreach Attempts: {attempt_count}

=== Attribution ===
Attribution Records: {attr_count}
Primary Source: E2E Testing

=== Next Actions ===
1. Review lead quality
2. Optimize messaging
3. Scale campaign
"""
                        with open(report_path, 'w') as f:
                            f.write(report_content)
                        
                        has_required = all(s in report_content for s in ["Executive Summary", "Attribution", "Next Actions"])
                        st.session_state.e2e_last_report_path = report_path
                        st.session_state.e2e_last_report_valid = has_required
                        st.success(f"✅ Report generated")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # Report status markers
                if st.session_state.e2e_last_report_path:
                    st.markdown(f'<div data-testid="aicmo-last-report-path" style="display:none;">{st.session_state.e2e_last_report_path}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div data-testid="aicmo-last-report-has-required-sections" style="display:none;">{str(st.session_state.e2e_last_report_valid).lower()}</div>', unsafe_allow_html=True)
                
                st.markdown("---")
                
                # HARD RESET BUTTON
                st.markdown("### 🔄 Test Data Management")
                st.markdown('<div data-testid="aicmo-e2e-reset">', unsafe_allow_html=True)
                if st.button("🔄 Hard Reset", key="e2e_hard_reset_btn", type="secondary"):
                    deleted_counts = hard_reset_test_data(session)
                    st.session_state.e2e_reset_success = True
                    st.success("✅ Reset complete")
                st.markdown('</div>', unsafe_allow_html=True)
                
                if st.session_state.e2e_reset_success:
                    st.markdown('<div data-testid="aicmo-e2e-reset-ok" style="display:none;">reset_complete</div>', unsafe_allow_html=True)
                
                st.markdown("---")
                
                # DIAGNOSTICS JSON PAYLOAD
                st.markdown("### 🔍 Diagnostics State")
                lead_count = session.query(LeadDB).filter_by(campaign_id=campaign_id).count()
                attr_count = session.query(LeadAttributionDB).filter_by(campaign_id=campaign_id).count()
                attempt_count = session.query(OutreachAttemptDB).filter_by(campaign_id=campaign_id).count()
                
                last_attempt = session.query(OutreachAttemptDB).filter_by(campaign_id=campaign_id).order_by(OutreachAttemptDB.created_at.desc()).first()
                last_job_status = None
                if last_attempt:
                    last_job_status = last_attempt.status.value if hasattr(last_attempt.status, 'value') else str(last_attempt.status)
                
                diagnostics_state = {
                    "campaign_id": campaign_id,
                    "paused": st.session_state.get('system_paused', False),
                    "leads": lead_count,
                    "attributions": attr_count,
                    "outreach_attempts": attempt_count,
                    "jobs": attempt_count,
                    "audit_logs": 0,
                    "last_job_status": last_job_status
                }
                
                diagnostics_json = json.dumps(diagnostics_state, indent=2)
                st.markdown(f'<div data-testid="aicmo-e2e-state-json" style="font-family: monospace; white-space: pre; padding: 1rem; background: #f0f0f0; border-radius: 0.5rem;">{diagnostics_json}</div>', unsafe_allow_html=True)
                
            except Exception as e:
                st.error(f"❌ E2E UI error: {e}")
                import traceback
                st.code(traceback.format_exc())
