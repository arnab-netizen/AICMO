"""
Proof File Utilities – Helper functions for proof file generation and management.

Integrates with operator_qc.py to provide consistent proof file handling across
the system.
"""

import datetime
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Try to import quality gates
try:
    from backend.quality_gates import is_report_learnable, sanitize_final_report_text
except Exception:
    is_report_learnable = None
    sanitize_final_report_text = None


class ProofFileManager:
    """Manage proof file generation and storage."""

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize proof file manager.

        Args:
            base_path: Directory to store proof files. Defaults to .aicmo/proof/operator/
        """
        if base_path is None:
            base_path = Path.cwd() / ".aicmo" / "proof" / "operator"

        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        report_markdown: str,
        brief_dict: Dict[str, Any],
        package_key: str,
        quality_results: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Generate a comprehensive proof file.

        Args:
            report_markdown: The final report markdown
            brief_dict: Brief metadata dictionary
            package_key: WOW package key (e.g., "launch_gtm_pack")
            quality_results: Optional quality gate results

        Returns:
            Path to generated proof file
        """
        # Generate timestamp and filename
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        report_id = f"{package_key}_{timestamp}"
        proof_file = self.base_path / f"{report_id}.md"

        # Build quality results if not provided
        if quality_results is None and is_report_learnable:
            is_learnable, rejection_reasons = is_report_learnable(
                report_markdown, brief_dict.get("brand_name", "")
            )
            quality_results = {
                "is_learnable": is_learnable,
                "rejection_reasons": rejection_reasons,
            }

        # Extract brief metadata
        brand_name = brief_dict.get("brand_name", "N/A")
        industry = brief_dict.get("industry", "N/A")
        geography = brief_dict.get("geography", "N/A")

        # Sanitize report
        sanitized = (
            sanitize_final_report_text(report_markdown)
            if sanitize_final_report_text
            else report_markdown
        )

        # Extract placeholders used
        placeholder_pattern = r"{{\s*([a-zA-Z0-9_]+)\s*}}"
        placeholders_found = set(re.findall(placeholder_pattern, report_markdown))

        # Build proof file content
        proof_content = self._build_proof_markdown(
            report_id=report_id,
            now=now,
            package_key=package_key,
            brand_name=brand_name,
            industry=industry,
            geography=geography,
            report_markdown=report_markdown,
            sanitized=sanitized,
            brief_dict=brief_dict,
            quality_results=quality_results,
            placeholders_found=placeholders_found,
        )

        # Write proof file
        proof_file.write_text(proof_content, encoding="utf-8")
        return proof_file

    def _build_proof_markdown(
        self,
        report_id: str,
        now: datetime.datetime,
        package_key: str,
        brand_name: str,
        industry: str,
        geography: str,
        report_markdown: str,
        sanitized: str,
        brief_dict: Dict[str, Any],
        quality_results: Optional[Dict[str, Any]],
        placeholders_found: set,
    ) -> str:
        """Build the full proof markdown content."""
        lines = [
            "# AICMO Proof File Report",
            "",
            f"**Report ID:** {report_id}",
            f"**Generated:** {now.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Package:** {package_key}",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
            f"- **Brand:** {brand_name}",
            f"- **Industry:** {industry}",
            f"- **Geography:** {geography}",
            f"- **Report Length:** {len(report_markdown):,} characters",
            f"- **Learnable:** {'✅ Yes' if quality_results and quality_results.get('is_learnable') else '❌ No'}",
            "",
            "---",
            "",
            "## Brief Metadata",
            "",
            "```json",
            json.dumps(brief_dict, indent=2, ensure_ascii=False),
            "```",
            "",
            "---",
            "",
            "## Quality Gate Results",
            "",
        ]

        if quality_results:
            lines.append("### Checks")
            is_learnable = quality_results.get("is_learnable", False)
            lines.append(
                f"**Learnability:** {'✅ Eligible' if is_learnable else '❌ Not eligible'}"
            )

            rejection_reasons = quality_results.get("rejection_reasons", [])
            if rejection_reasons:
                lines.append("\n**Rejection Reasons:**")
                for reason in rejection_reasons:
                    lines.append(f"- ❌ {reason}")
            else:
                lines.append("\n✅ All checks passed")
        else:
            lines.append("⚠️ No quality results available.")

        lines.extend(
            [
                "",
                "---",
                "",
                "## Placeholder Usage",
                "",
                f"**Placeholders detected in raw report:** {len(placeholders_found)}",
                "",
            ]
        )

        if placeholders_found:
            lines.append("| Placeholder | Status |")
            lines.append("|---|---|")
            for ph in sorted(placeholders_found):
                lines.append(f"| `{{{{{ph}}}}}` | Should have been filled |")
        else:
            lines.append("✅ No unfilled placeholders detected.")

        lines.extend(
            [
                "",
                "---",
                "",
                "## Sanitization Report",
                "",
                f"**Original length:** {len(report_markdown):,} chars",
                f"**After sanitization:** {len(sanitized):,} chars",
                f"**Removed:** {len(report_markdown) - len(sanitized):,} chars",
                "",
                "---",
                "",
                "## Final Report (Sanitized)",
                "",
                sanitized,
                "",
                "---",
                "",
                "## System Metadata",
                "",
                "- **Proof File Version:** 1.0",
                f"- **Generated At:** {datetime.datetime.now().isoformat()}",
                "",
            ]
        )

        return "\n".join(lines)

    def list_all(self) -> List[Tuple[Path, datetime.datetime]]:
        """List all proof files with timestamps."""
        files = []
        for pf in self.base_path.glob("*.md"):
            try:
                stat = pf.stat()
                mtime = datetime.datetime.fromtimestamp(stat.st_mtime)
                files.append((pf, mtime))
            except Exception:
                pass
        return sorted(files, key=lambda x: x[1], reverse=True)

    def get_latest(self) -> Optional[Tuple[Path, str]]:
        """Get the latest proof file content."""
        files = self.list_all()
        if not files:
            return None
        latest_path, _ = files[0]
        content = latest_path.read_text(encoding="utf-8")
        return latest_path, content

    def get_by_id(self, report_id: str) -> Optional[Tuple[Path, str]]:
        """Get a proof file by report ID."""
        proof_file = self.base_path / f"{report_id}.md"
        if not proof_file.exists():
            return None
        content = proof_file.read_text(encoding="utf-8")
        return proof_file, content


# Global instance
_default_manager: Optional[ProofFileManager] = None


def get_proof_manager() -> ProofFileManager:
    """Get the default proof file manager instance."""
    global _default_manager
    if _default_manager is None:
        _default_manager = ProofFileManager()
    return _default_manager


def generate_proof_file(
    report_markdown: str,
    brief_dict: Dict[str, Any],
    package_key: str,
    quality_results: Optional[Dict[str, Any]] = None,
) -> Path:
    """
    Generate a proof file using the default manager.

    Convenience function for use in Streamlit pages.
    """
    manager = get_proof_manager()
    return manager.generate(report_markdown, brief_dict, package_key, quality_results)
