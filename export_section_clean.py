#!/usr/bin/env python3
"""
Clean Export Section Implementation for streamlit_app.py

This file contains the corrected Export section that follows Streamlit's
widget lifecycle rules. Copy-paste this to replace lines ~1555-1950.

Key principles:
1. State initialization at top (always runs)
2. Button handler only mutates state
3. Download rendering at top-level (always runs, conditional on state)
"""

# ===========================================================================
# EXPORT SECTION START (replaces ~line 1555 onwards)
# ===========================================================================

# Check if report exists
if not st.session_state.generated_report:
    st.info("No report available. Generate and refine one first.")
else:
    st.markdown("#### Export Final Report")
    fmt = st.selectbox(
        "Format",
        ["pdf", "pptx", "zip", "json"],
        index=0,
        key="export_format_select"
    )

    # STEP 2.2: Export button handler (ONLY MUTATES STATE)
    st.markdown('<div data-testid="e2e-run-export">', unsafe_allow_html=True)
    if st.button("Generate export file", type="primary", key="generate_export_button"):
        if e2e_mode:
            st.session_state.e2e_export_state = "RUNNING"
            st.session_state.e2e_export_last_error = ""
        
        try:
            output_to_export = st.session_state.generated_report.copy()
            
            # Inject violation if mode enabled
            violation_mode = st.session_state.get("e2e_violation_mode", False)
            if e2e_mode and violation_mode:
                if 'sections' in output_to_export and output_to_export['sections']:
                    first_key = list(output_to_export['sections'].keys())[0]
                    content = output_to_export['sections'][first_key]
                    del output_to_export['sections'][first_key]
                    output_to_export['sections'][f'TODO: {first_key}'] = content
            
            # E2E path
            if e2e_mode:
                try:
                    from aicmo.validation.export_gate import process_export_with_gate
                    from aicmo.delivery.gate import DeliveryBlockedError
                    from aicmo.validation.runtime_paths import get_runtime_paths
                    import io
                    from reportlab.lib.pagesizes import letter
                    from reportlab.pdfgen import canvas
                    
                    # Generate PDF
                    buffer = io.BytesIO()
                    c = canvas.Canvas(buffer, pagesize=letter)
                    c.drawString(100, 750, "AICMO E2E Test Export")
                    c.drawString(100, 730, f"Brand: {st.session_state.current_brief.get('brand', {}).get('brand_name', 'Test')}")
                    y = 680
                    for title, content in output_to_export.get('sections', {}).items():
                        c.drawString(100, y, f"Section: {title}")
                        y -= 40
                    c.save()
                    file_bytes = buffer.getvalue()
                    
                    brand_name = st.session_state.current_brief.get("brand", {}).get("brand_name", "test")
                    file_name = f"{brand_name}.{fmt}"
                    
                    # Process through gate
                    file_bytes, validation_report = process_export_with_gate(
                        brief=st.session_state.current_brief,
                        output=output_to_export,
                        file_bytes=file_bytes,
                        format_=fmt,
                        filename=file_name,
                    )
                    
                    # Store paths as serializable dict
                    paths = get_runtime_paths()
                    st.session_state.e2e_export_state = "PASS"
                    st.session_state.e2e_export_run_id = paths.run_id
                    st.session_state.e2e_export_last_error = ""
                    st.session_state.e2e_export_paths = {
                        "manifest_path": str(paths.manifest_path),
                        "validation_path": str(paths.validation_path),
                        "section_map_path": str(paths.section_map_path),
                        "downloads_dir": str(paths.downloads_dir)
                    }
                    st.success(f"✅ Export validated (run_id: {paths.run_id})")
                    
                except DeliveryBlockedError as e:
                    paths = get_runtime_paths()
                    st.session_state.e2e_export_state = "FAIL"
                    st.session_state.e2e_export_run_id = paths.run_id
                    st.session_state.e2e_export_last_error = str(e)[:200]
                    st.session_state.e2e_export_paths = {
                        "manifest_path": str(paths.manifest_path),
                        "validation_path": str(paths.validation_path),
                        "section_map_path": str(paths.section_map_path),
                        "downloads_dir": str(paths.downloads_dir)
                    }
                    st.error(f"🚫 Delivery blocked: {e}")
                    
                except Exception as e:
                    st.session_state.e2e_export_state = "ERROR"
                    st.session_state.e2e_export_last_error = str(e)[:200]
                    st.error(f"❌ Export error: {e}")
            else:
                # Non-E2E: use API
                file_bytes = aicmo_export(
                    api_base=api_base,
                    brief=st.session_state.current_brief,
                    output=output_to_export,
                    format_=fmt,
                    timeout=int(timeout),
                )
                
                # Regular download for non-E2E
                brand_name = st.session_state.current_brief.get("brand", {}).get("brand_name", "report")
                file_name = f"{brand_name}.{fmt}"
                mime_map = {"pdf": "application/pdf", "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation", "zip": "application/zip", "json": "application/json"}
                st.download_button("Download report", file_bytes, file_name=file_name, mime=mime_map.get(fmt, "application/octet-stream"), key="download_report_button")
                st.success("Export ready.")
                
        except Exception as exc:
            st.error(f"Export failed: {exc}")
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close e2e-run-export div
    
    # STEP 3: TOP-LEVEL DOWNLOADS (always executes when state matches)
    if e2e_mode:
        export_state = st.session_state.get("e2e_export_state", "IDLE")
        paths_dict = st.session_state.get("e2e_export_paths")
        
        if export_state == "PASS" and paths_dict:
            st.markdown("---")
            st.markdown("### 📦 Export Artifacts")
            st.markdown('<div data-testid="e2e-downloads-ready" style="display:none;">READY</div>', unsafe_allow_html=True)
            
            from pathlib import Path
            import json
            
            manifest_path = Path(paths_dict["manifest_path"])
            validation_path = Path(paths_dict["validation_path"])
            section_map_path = Path(paths_dict["section_map_path"])
            downloads_dir = Path(paths_dict["downloads_dir"])
            
            # Metadata files
            st.markdown("#### Metadata Files")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown('<div data-testid="e2e-download-manifest">', unsafe_allow_html=True)
                manifest_bytes = manifest_path.read_bytes()
                st.download_button("📋 Manifest JSON", manifest_bytes, file_name="manifest.json", mime="application/json", key="dl-manifest")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div data-testid="e2e-download-validation">', unsafe_allow_html=True)
                validation_bytes = validation_path.read_bytes()
                st.download_button("✅ Validation JSON", validation_bytes, file_name="validation.json", mime="application/json", key="dl-validation")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col3:
                st.markdown('<div data-testid="e2e-download-section-map">', unsafe_allow_html=True)
                section_map_bytes = section_map_path.read_bytes()
                st.download_button("🗺️ Section Map JSON", section_map_bytes, file_name="section_map.json", mime="application/json", key="dl-section-map")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Deliverables
            st.markdown("#### Deliverables")
            manifest = json.loads(manifest_bytes)
            
            if manifest.get('artifacts'):
                for artifact in manifest['artifacts']:
                    artifact_id = artifact['artifact_id']
                    filename = artifact['filename']
                    filepath = downloads_dir / filename
                    
                    if filepath.exists():
                        format_str = artifact.get('format', '')
                        mime = {'pdf': 'application/pdf', 'json': 'application/json'}.get(format_str, 'application/octet-stream')
                        
                        st.markdown(f'<div data-testid="e2e-download-{artifact_id}">', unsafe_allow_html=True)
                        artifact_bytes = filepath.read_bytes()
                        st.download_button(f"📄 {filename}", artifact_bytes, file_name=filename, mime=mime, key=f"dl-{artifact_id}")
                        st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("No deliverable artifacts")
                
        elif export_state in ["FAIL", "ERROR"] and paths_dict:
            st.markdown("---")
            st.markdown('<div data-testid="e2e-downloads-blocked">', unsafe_allow_html=True)
            st.warning("📛 **Downloads Blocked**: Validation failed")
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Still allow validation download for debugging
            from pathlib import Path
            validation_path = Path(paths_dict["validation_path"])
            if validation_path.exists():
                st.markdown("#### Validation Report (debugging)")
                st.markdown('<div data-testid="e2e-download-validation">', unsafe_allow_html=True)
                validation_bytes = validation_path.read_bytes()
                st.download_button("⚠️ Download Validation JSON", validation_bytes, file_name="validation.json", mime="application/json", key="dl-validation-fail")
                st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### Creatives / Assets Bundle")
    st.info("ZIP format includes strategy documents, creatives, persona cards, and assets.")

# ===========================================================================
# EXPORT SECTION END
# ===========================================================================
