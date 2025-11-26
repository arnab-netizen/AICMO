from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).parent.parent
PROOF_ROOT = PROJECT_ROOT / ".aicmo" / "proof"


def save_proof_file(
    report_markdown: str,
    brief: Dict[str, Any],
    package_key: str,
    kind: str = "client_report",
) -> Path:
    """
    Save a 'flight recorder' proof file for the generated report.

    Returns the path to the markdown file.
    """
    ts = _dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    dir_path = PROOF_ROOT / ts
    dir_path.mkdir(parents=True, exist_ok=True)

    md = []
    md.append(f"# AICMO Proof File – {package_key}")
    md.append("")
    md.append(f"- Timestamp (UTC): `{ts}`")
    md.append(f"- Package: `{package_key}`")
    md.append(f"- Kind: `{kind}`")
    md.append("")
    md.append("## Brief Snapshot")
    md.append("```json")
    md.append(json.dumps(brief, indent=2, ensure_ascii=False))
    md.append("```")
    md.append("")
    md.append("## Final Report (Sanitized)")
    md.append("")
    md.append(report_markdown)

    file_path = dir_path / f"{package_key}.md"
    file_path.write_text("\n".join(md), encoding="utf-8")
    return file_path
