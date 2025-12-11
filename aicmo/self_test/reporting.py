"""
Self-Test Engine Reporting

Generate human-readable health reports in Markdown and HTML.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from aicmo.self_test.models import FeatureCategory, SelfTestResult, TestStatus


class ReportGenerator:
    """Generate self-test reports in Markdown and HTML."""

    def __init__(self, output_dir: str = "/workspaces/AICMO/self_test_artifacts"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_markdown_report(self, result: SelfTestResult) -> str:
        """Generate a Markdown report."""
        lines = []

        # Header
        lines.append("# AICMO System Health Report\n")
        lines.append(f"**Generated:** {result.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        if result.deterministic_mode:
            lines.append("**Mode:** Deterministic ✅ (stub outputs, fixed seeds)\n")

        # Summary
        lines.append("## Summary\n")
        lines.append(f"- **Features Tested:** {result.total_features}")
        lines.append(f"- **Passed:** {result.passed_features} ✅")
        lines.append(f"- **Failed:** {result.failed_features} ❌")
        lines.append(f"- **Skipped:** {result.skipped_features} ⏭️")
        lines.append(f"- **Status:** {'🟢 HEALTHY' if result.failed_features == 0 else '🔴 ISSUES DETECTED'}\n")

        # Performance & Flakiness (3.0)
        lines.append("## Performance & Flakiness\n")
        lines.append("**Feature Runtimes:**\n")
        for feature in sorted(result.features, key=lambda f: f.runtime_seconds or 0, reverse=True):
            if feature.runtime_seconds is not None:
                runtime_str = f"{feature.runtime_seconds:.3f}s"
                lines.append(f"- {feature.name}: {runtime_str}")
        lines.append("")
        
        # Flakiness check results
        if result.flakiness_check_results:
            lines.append("**Flakiness Detected:** ⚠️\n")
            for feature_name, signatures in result.flakiness_check_results.items():
                lines.append(f"- **{feature_name}**: Inconsistent across runs")
                lines.append(f"  - Variations: {len(set(signatures))} different outputs")
            lines.append("")
        else:
            lines.append("**Flakiness Check:** No inconsistencies detected ✅\n")

        # Benchmark Coverage (2.0)
        if result.coverage_info:
            lines.append("## Benchmark Coverage\n")
            coverage = result.coverage_info
            
            # Global coverage summary
            lines.append(f"**Global Coverage Summary**\n")
            lines.append(f"- **Total Benchmarks:** {coverage.total_benchmarks}")
            lines.append(f"- **Mapped Benchmarks:** {coverage.mapped_benchmarks}")
            lines.append(f"- **Enforced Benchmarks:** {coverage.enforced_benchmarks}")
            lines.append(f"- **Unenforced Benchmarks:** {coverage.unenforced_benchmarks}")
            lines.append(f"- **Unmapped Benchmarks:** {coverage.unmapped_benchmarks}\n")
            
            # Calculate coverage percentage
            if coverage.mapped_benchmarks > 0:
                enforcement_pct = (coverage.enforced_benchmarks / coverage.mapped_benchmarks) * 100
                lines.append(f"**Enforcement Rate:** {enforcement_pct:.1f}% ({coverage.enforced_benchmarks}/{coverage.mapped_benchmarks})\n")
            
            # Per-feature coverage
            enforced_features = [f for f in result.features if f.benchmark_coverage and f.benchmark_coverage.benchmarks_enforced]
            if enforced_features:
                lines.append("**Benchmark Coverage by Feature**\n")
                lines.append("| Feature | Mapped | Enforced | Unenforced |")
                lines.append("|---------|--------|----------|------------|")
                for feature in sorted(enforced_features, key=lambda f: f.name):
                    cov = feature.benchmark_coverage
                    lines.append(f"| {feature.name} | {len(cov.benchmarks_mapped)} | {len(cov.benchmarks_enforced)} | {len(cov.benchmarks_unenforced)} |")
                lines.append("")
            
            # Notes about coverage gaps
            if coverage.notes:
                lines.append("**Coverage Notes**\n")
                for note in coverage.notes:
                    lines.append(f"- {note}")
                lines.append("")
            
            # Explicit statement about unenforced benchmarks
            if coverage.unenforced_benchmarks > 0:
                lines.append("⚠️ **Note:** Some benchmarks are mapped to features but not actively enforced in validators.\n")

        # Layout Checks (2.0)
        layout_features = [f for f in result.features if f.layout_checks]
        if layout_features:
            lines.append("## Layout Checks\n")
            lines.append("Validation of client-facing output structure and organization:\n")
            
            # HTML Layout Check Summary
            html_features = [f for f in layout_features if f.layout_checks.html_valid is not None]
            if html_features:
                lines.append("### HTML Summary Validation\n")
                for feature in html_features:
                    lc = feature.layout_checks
                    status_icon = "✅" if lc.html_valid else "❌"
                    lines.append(f"**{status_icon} {feature.name}**\n")
                    
                    if lc.html_details:
                        details = lc.html_details
                        if details.get("total_headings_found"):
                            lines.append(f"- **Headings Found:** {details.get('total_headings_found')}")
                        if details.get("has_overview"):
                            lines.append(f"- **Has Overview Section:** {details.get('has_overview')}")
                        if details.get("has_deliverables"):
                            lines.append(f"- **Has Deliverables Section:** {details.get('has_deliverables')}")
                        if details.get("heading_order_ok"):
                            lines.append(f"- **Heading Order Valid:** {details.get('heading_order_ok')}")
                        
                        if details.get("missing_sections"):
                            lines.append(f"- **Missing Sections:** {', '.join(details.get('missing_sections', []))}")
                    
                    lines.append("")
            
            # PPTX Layout Check Summary
            pptx_features = [f for f in layout_features if f.layout_checks.pptx_valid is not None]
            if pptx_features:
                lines.append("### PPTX Deck Validation\n")
                for feature in pptx_features:
                    lc = feature.layout_checks
                    status_icon = "✅" if lc.pptx_valid else "❌"
                    lines.append(f"**{status_icon} {feature.name}**\n")
                    
                    if lc.pptx_slide_count > 0:
                        lines.append(f"- **Total Slides:** {lc.pptx_slide_count}")
                    
                    if lc.pptx_details:
                        details = lc.pptx_details
                        if details.get("min_slides_required"):
                            lines.append(f"- **Minimum Required:** {details.get('min_slides_required')} slides")
                        if details.get("required_titles_present"):
                            lines.append(f"- **Required Titles Found:** {', '.join(details.get('required_titles_present', []))}")
                        
                        if details.get("missing_titles"):
                            lines.append(f"- **Missing Titles:** {', '.join(details.get('missing_titles', []))}")
                    
                    lines.append("")
            
            # PDF Layout Check Summary
            pdf_features = [f for f in layout_features if f.layout_checks.pdf_valid is not None]
            if pdf_features:
                lines.append("### PDF Validation\n")
                for feature in pdf_features:
                    lc = feature.layout_checks
                    
                    # Special handling for "not implemented" case
                    if lc.pdf_details and lc.pdf_details.get("reason") == "PDF layout check not implemented":
                        lines.append(f"**⚠️ {feature.name}**\n")
                        lines.append(f"- **Status:** PDF layout check not implemented\n")
                        if lc.pdf_details.get("message"):
                            lines.append(f"- **Note:** {lc.pdf_details.get('message')}\n")
                    else:
                        status_icon = "✅" if lc.pdf_valid else "❌"
                        lines.append(f"**{status_icon} {feature.name}**\n")
                        
                        if lc.pdf_page_count > 0:
                            lines.append(f"- **Total Pages:** {lc.pdf_page_count}")
                        
                        if lc.pdf_details:
                            details = lc.pdf_details
                            if "has_title_on_first_page" in details:
                                lines.append(f"- **Title on First Page:** {details.get('has_title_on_first_page')}")
                        
                        lines.append("")
            
            lines.append("\n")

        # Content Quality & Genericity (2.0)
        quality_features = [f for f in result.features if f.quality_checks]
        if quality_features:
            lines.append("## Content Quality & Genericity\n")
            lines.append("Assessment of content originality, diversity, and placeholder detection:\n")
            
            for feature in quality_features:
                qc = feature.quality_checks
                
                # Status based on severity
                if qc.placeholders_found:
                    status_icon = "❌"
                    status_text = "CRITICAL - Contains Placeholders"
                elif qc.warnings:
                    status_icon = "⚠️"
                    status_text = "ISSUES FOUND"
                else:
                    status_icon = "✅"
                    status_text = "PASS"
                
                lines.append(f"**{status_icon} {feature.name}**\n")
                
                # Key metrics
                lines.append(f"- **Genericity Score:** {qc.genericity_score:.2f}/1.0 (lower = less generic)")
                lines.append(f"- **Lexical Diversity:** {qc.details.get('unique_tokens', 0)}/{qc.details.get('total_tokens', 0)} unique words")
                lines.append(f"- **Quality Assessment:** {qc.overall_quality_assessment}")
                lines.append(f"- **Status:** {status_text}")
                
                if qc.placeholders_found:
                    lines.append(f"- **⚠️ Placeholders Found:** {', '.join(qc.placeholders_found[:3])}" + 
                               (f" (+{len(qc.placeholders_found)-3} more)" if len(qc.placeholders_found) > 3 else ""))
                
                if qc.repeated_phrases:
                    lines.append(f"- **Repeated Phrases:** {', '.join(qc.repeated_phrases[:2])}")
                
                if qc.generic_phrases_found:
                    lines.append(f"- **Generic Phrases Found:** {len(qc.generic_phrases_found)} instances")
                
                if qc.warnings:
                    lines.append("- **Warnings:**")
                    for warning in qc.warnings[:3]:  # Limit to 3 warnings for brevity
                        lines.append(f"  - {warning}")
                
                lines.append("")

        # External Integrations Health Matrix (4.0)
        if result.external_services:
            lines.append("## External Integrations Health Matrix\n")
            lines.append("Status of external services and APIs:\n")
            lines.append("| Service | Configured | Status | Criticality |")
            lines.append("|---------|-----------|--------|-------------|")
            
            for service in result.external_services:
                configured_str = "✅" if service.configured else "❌"
                status_str = service.status_display
                critical_str = service.criticality_display
                lines.append(f"| {service.name} | {configured_str} | {status_str} | {critical_str} |")
            
            lines.append("")
            
            # Summary stats
            configured = sum(1 for s in result.external_services if s.configured)
            reachable = sum(1 for s in result.external_services if s.reachable is True)
            critical = sum(1 for s in result.external_services if s.critical)
            
            lines.append(f"**Summary:** {configured}/{len(result.external_services)} configured, "
                        f"{reachable} reachable, {critical} critical\n")
            
            # Warn about unconfigured critical services
            unconfigured_critical = [s for s in result.external_services if s.critical and not s.configured]
            if unconfigured_critical:
                lines.append("⚠️ **Warning:** The following CRITICAL services are not configured:\n")
                for service in unconfigured_critical:
                    lines.append(f"- **{service.name}** - Set `{service.details.get('env_vars_present', 'API_KEY')}` to enable")
                lines.append("")

        # Semantic Alignment vs Brief (2.0)
        semantic_features = [f for f in result.features if f.semantic_alignment]
        if semantic_features:
            lines.append("## Semantic Alignment vs Brief\n")
            lines.append("Verification that output aligns with ClientInputBrief:\n")
            
            for feature in semantic_features:
                sem = feature.semantic_alignment
                
                # Status based on mismatches
                if not sem.is_valid:
                    status_icon = "❌"
                    status_text = "CRITICAL MISMATCH"
                elif sem.mismatched_fields:
                    status_icon = "⚠️"
                    status_text = "MISMATCHES FOUND"
                elif sem.partial_matches:
                    status_icon = "⚠️"
                    status_text = "PARTIAL ALIGNMENT"
                else:
                    status_icon = "✅"
                    status_text = "ALIGNED"
                
                lines.append(f"**{status_icon} {feature.name}**\n")
                lines.append(f"- **Status:** {status_text}")
                
                if sem.mismatched_fields:
                    lines.append("- **Mismatches:**")
                    for mismatch in sem.mismatched_fields[:3]:
                        lines.append(f"  - {mismatch}")
                
                if sem.partial_matches:
                    lines.append("- **Partial Matches:**")
                    for partial in sem.partial_matches[:3]:
                        lines.append(f"  - {partial}")
                
                if sem.notes:
                    lines.append("- **Notes:**")
                    for note in sem.notes[:2]:
                        lines.append(f"  - {note}")
                
                lines.append("")

        # Security & Privacy Scan (5.0)
        security_features = [f for f in result.features if f.security_scan_result]
        if security_features:
            lines.append("## Security & Privacy Scan\n")
            lines.append("Pattern-based scanning for secrets, environment variables, and prompt injection markers:\n")
            
            for feature in security_features:
                sec = feature.security_scan_result
                
                # Determine overall status
                has_issues = (sec.has_secret_like_patterns or 
                             sec.has_env_like_patterns or 
                             sec.has_prompt_injection_markers)
                
                status_icon = "⚠️" if has_issues else "✅"
                lines.append(f"**{status_icon} {feature.name}**\n")
                
                # Show boolean flags
                secret_icon = "🚨" if sec.has_secret_like_patterns else "✅"
                env_icon = "🚨" if sec.has_env_like_patterns else "✅"
                injection_icon = "🚨" if sec.has_prompt_injection_markers else "✅"
                
                lines.append(f"- **Secret-like patterns:** {secret_icon} {'FOUND' if sec.has_secret_like_patterns else 'None'}")
                lines.append(f"- **Env placeholders:** {env_icon} {'FOUND' if sec.has_env_like_patterns else 'None'}")
                lines.append(f"- **Injection markers:** {injection_icon} {'FOUND' if sec.has_prompt_injection_markers else 'None'}")
                
                # Show suspicious snippets if any
                if sec.suspicious_snippets:
                    lines.append("- **Suspicious Snippets:**")
                    for snippet in sec.suspicious_snippets[:3]:
                        # Truncate snippet for readability
                        snippet_preview = snippet[:80] if len(snippet) <= 80 else snippet[:77] + "..."
                        lines.append(f"  - `{snippet_preview}`")
                
                lines.append("")

        # Format & Word Counts (2.0)
        format_features = [f for f in result.features if f.format_checks]
        if format_features:
            lines.append("## Format & Word Counts\n")
            lines.append("Validation of text length and word-count requirements:\n")
            
            for feature in format_features:
                fc = feature.format_checks
                status_icon = "✅" if fc.is_valid else "⚠️"
                lines.append(f"**{status_icon} {feature.name}**\n")
                
                # Summary metrics
                total_checked = len(fc.metrics)
                too_short_count = len(fc.too_short_fields)
                too_long_count = len(fc.too_long_fields)
                
                lines.append(f"- **Fields Checked:** {total_checked}")
                lines.append(f"- **Validation Status:** {'PASS' if fc.is_valid else 'ISSUES FOUND'}")
                
                if too_short_count > 0:
                    lines.append(f"- **Too Short ({too_short_count}):** {', '.join(fc.too_short_fields)}")
                if too_long_count > 0:
                    lines.append(f"- **Too Long ({too_long_count}):** {', '.join(fc.too_long_fields)}")
                
                # Detailed metrics for problematic fields
                if fc.metrics:
                    problem_fields = fc.too_short_fields + fc.too_long_fields
                    if problem_fields:
                        lines.append("- **Details:**")
                        for field_name in problem_fields[:5]:  # Limit to 5 for brevity
                            if field_name in fc.metrics:
                                metric = fc.metrics[field_name]
                                min_req = metric.get("min_required", "?")
                                max_allow = metric.get("max_allowed", "?")
                                actual = metric.get("word_count", "?")
                                lines.append(f"  - {field_name}: {actual} words (min: {min_req}, max: {max_allow})")
                
                lines.append("")

        # Critical Failures
        if result.critical_failures:
            lines.append("## ⚠️ Critical Failures\n")
            for failure in result.critical_failures:
                lines.append(f"- {failure}\n")
            lines.append("")

        # Full Project Rehearsal (2.0)
        if result.project_rehearsals:
            lines.append("## Full Project Rehearsal\n")
            lines.append("End-to-end simulation of complete project flows from brief through final artifacts:\n")
            
            for rehearsal in result.project_rehearsals:
                status_icon = "✅" if rehearsal.passed else "❌"
                lines.append(f"### {status_icon} {rehearsal.project_name}\n")
                lines.append(f"- **Brief:** {rehearsal.brief_name}")
                lines.append(f"- **Overall Status:** {'PASS' if rehearsal.passed else 'FAIL'}")
                lines.append(f"- **Success Rate:** {rehearsal.success_rate:.1f}% ({rehearsal.passed_steps}/{rehearsal.total_steps} steps)")
                lines.append(f"- **Duration:** {rehearsal.overall_duration_ms / 1000:.2f}s")
                lines.append("")
                
                # Step details
                if rehearsal.steps:
                    lines.append("#### Execution Steps\n")
                    for step in rehearsal.steps:
                        step_icon = self._status_icon(step.status)
                        lines.append(f"- {step_icon} **{step.name}** ({step.duration_ms:.0f}ms)")
                        if step.errors:
                            lines.append(f"  - Errors: {', '.join(step.errors[:2])}")
                        if step.warnings:
                            lines.append(f"  - Warnings: {', '.join(step.warnings[:2])}")
                        if step.metrics:
                            metric_str = ", ".join(f"{k}={v}" for k, v in list(step.metrics.items())[:2])
                            lines.append(f"  - Metrics: {metric_str}")
                    lines.append("")
                
                # Artifacts
                if rehearsal.artifacts_generated:
                    lines.append("#### Generated Artifacts\n")
                    for artifact in rehearsal.artifacts_generated:
                        lines.append(f"- {artifact}")
                    lines.append("")
                
                # Critical errors
                if rehearsal.critical_errors:
                    lines.append("#### Critical Errors\n")
                    for error in rehearsal.critical_errors:
                        lines.append(f"- ⚠️  {error}")
                    lines.append("")

        # Feature Details by Category
        lines.append("## Feature Testing Results\n")

        categories = [cat for cat in FeatureCategory]
        for category in categories:
            category_features = [f for f in result.features if f.category == category]
            if not category_features:
                continue

            lines.append(f"### {category.value.title()} Features\n")

            for feature in sorted(category_features, key=lambda f: f.name):
                status_icon = self._status_icon(feature.status)
                critical_badge = "🔴 **CRITICAL**" if feature.critical else ""
                lines.append(f"#### {status_icon} {feature.name} {critical_badge}\n")

                if feature.description:
                    lines.append(f"*{feature.description}*\n")

                if feature.total_scenarios > 0:
                    lines.append(f"- **Scenarios:** {feature.scenarios_passed}/{feature.total_scenarios} passed")
                    if feature.scenarios_failed > 0:
                        lines.append(f"  - Failed: {feature.scenarios_failed}")
                    if feature.scenarios_skipped > 0:
                        lines.append(f"  - Skipped: {feature.scenarios_skipped}")
                    lines.append("")

                if feature.errors:
                    lines.append("**Errors:**")
                    for error in feature.errors[:3]:  # Limit to 3 errors per feature
                        lines.append(f"- {error}")
                    if len(feature.errors) > 3:
                        lines.append(f"- ... and {len(feature.errors) - 3} more")
                    lines.append("")

                if feature.warnings:
                    lines.append("**Warnings:**")
                    for warning in feature.warnings[:2]:  # Limit to 2 warnings
                        lines.append(f"- {warning}")
                    if len(feature.warnings) > 2:
                        lines.append(f"- ... and {len(feature.warnings) - 2} more")
                    lines.append("")

            lines.append("")

        # Generators Detail
        if result.generators:
            lines.append("## Generator Details\n")
            for gen in sorted(result.generators, key=lambda g: g.name):
                lines.append(f"### {gen.name}\n")
                lines.append(f"- **Module:** {gen.module_path}")
                lines.append(f"- **Status:** {self._status_icon(gen.status)} {gen.status.value.upper()}")
                lines.append(f"- **Scenarios Passed:** {gen.scenarios_passed}")
                lines.append(f"- **Scenarios Failed:** {gen.scenarios_failed}")
                lines.append(f"- **Scenarios Skipped:** {gen.scenarios_skipped}")

                if gen.errors:
                    lines.append(f"- **Errors:**")
                    for error in gen.errors[:3]:
                        lines.append(f"  - {error}")

                lines.append("")

        # Gateways Detail
        if result.gateways:
            lines.append("## Gateway/Adapter Status\n")
            for gw in sorted(result.gateways, key=lambda g: g.name):
                status_icon = self._status_icon(gw.status)
                lines.append(f"### {status_icon} {gw.name}\n")
                lines.append(f"- **Provider:** {gw.provider}")
                lines.append(f"- **Configured:** {'Yes' if gw.is_configured else 'No'}")
                if gw.details:
                    lines.append(f"- **Details:** {gw.details}")
                if gw.error_message:
                    lines.append(f"- **Error:** {gw.error_message}")
                lines.append("")

        # Packagers Detail
        if result.packagers:
            lines.append("## Packager Functions\n")
            for pkg in sorted(result.packagers, key=lambda p: p.name):
                status_icon = self._status_icon(pkg.status)
                lines.append(f"### {status_icon} {pkg.name}\n")
                lines.append(f"- **Module:** {pkg.module_path}")
                lines.append(f"- **Status:** {pkg.status.value.upper()}")
                if pkg.output_file:
                    lines.append(f"- **Output:** {pkg.output_file}")
                if pkg.file_size:
                    lines.append(f"- **Size:** {pkg.file_size:,} bytes")
                if pkg.error_message:
                    lines.append(f"- **Error:** {pkg.error_message}")
                lines.append("")

        # Recommendations
        if result.failed_features > 0:
            lines.append("## Recommendations\n")
            lines.append("1. **Review Failed Features:** Check the errors above for details")
            lines.append("2. **Check Dependencies:** Ensure all required packages are installed")
            lines.append("3. **Verify Configuration:** Check API keys and service configurations")
            lines.append("4. **Review Logs:** Check application logs for more details\n")

        return "\n".join(lines)

    def generate_html_report(self, result: SelfTestResult) -> str:
        """Generate an HTML report."""
        markdown = self.generate_markdown_report(result)

        # Simple HTML conversion (in production, use markdown library)
        html_lines = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            "<title>AICMO System Health Report</title>",
            "<style>",
            "body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; color: #333; }",
            "h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }",
            "h2 { color: #34495e; margin-top: 30px; border-left: 4px solid #3498db; padding-left: 10px; }",
            "h3 { color: #555; }",
            "h4 { color: #666; }",
            ".summary { background: #ecf0f1; padding: 15px; border-radius: 5px; margin: 15px 0; }",
            ".passed { color: #27ae60; font-weight: bold; }",
            ".failed { color: #e74c3c; font-weight: bold; }",
            ".skipped { color: #f39c12; font-weight: bold; }",
            ".error { color: #c0392b; background: #fadbd8; padding: 5px; border-left: 3px solid #c0392b; margin: 5px 0; }",
            ".warning { color: #d68910; background: #fef5e7; padding: 5px; border-left: 3px solid #f39c12; margin: 5px 0; }",
            ".code { background: #f4f4f4; padding: 2px 6px; font-family: monospace; border-radius: 3px; }",
            ".timestamp { color: #7f8c8d; font-size: 0.9em; }",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>AICMO System Health Report</h1>",
            f'<p class="timestamp">Generated: {result.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")}</p>',
            '<div class="summary">',
            f"<p><strong>Features Tested:</strong> {result.total_features}</p>",
            f'<p><strong class="passed">✅ Passed:</strong> {result.passed_features}</p>',
            f'<p><strong class="failed">❌ Failed:</strong> {result.failed_features}</p>',
            f'<p><strong class="skipped">⏭️ Skipped:</strong> {result.skipped_features}</p>',
            f'<p><strong>Status:</strong> {"🟢 HEALTHY" if result.failed_features == 0 else "🔴 ISSUES DETECTED"}</p>',
            "</div>",
            markdown.replace("\n", "<br>"),  # Simplified conversion
            "</body>",
            "</html>",
        ]

        return "\n".join(html_lines)

    def save_reports(self, result: SelfTestResult) -> tuple[str, Optional[str]]:
        """
        Save reports to files.

        Returns:
            Tuple of (markdown_path, html_path)
        """
        # Save Markdown
        md_path = self.output_dir / "AICMO_SELF_TEST_REPORT.md"
        md_content = self.generate_markdown_report(result)
        md_path.write_text(md_content)

        # Save HTML
        html_path = self.output_dir / "AICMO_SELF_TEST_REPORT.html"
        html_content = self.generate_html_report(result)
        html_path.write_text(html_content)

        return str(md_path), str(html_path)

    @staticmethod
    def _status_icon(status: TestStatus) -> str:
        """Get icon for test status."""
        if status == TestStatus.PASS:
            return "✅"
        elif status == TestStatus.FAIL:
            return "❌"
        elif status == TestStatus.SKIP:
            return "⏭️"
        elif status == TestStatus.PARTIAL:
            return "⚠️"
        else:
            return "❓"
