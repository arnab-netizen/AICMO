"""
Self-Test Engine Snapshots

Save and compare snapshots for regression detection.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from aicmo.self_test.models import SnapshotDiffResult


class SnapshotManager:
    """Manage test snapshots for regression detection."""

    def __init__(self, snapshots_dir: str = "/workspaces/AICMO/self_test_artifacts/snapshots"):
        self.snapshots_dir = Path(snapshots_dir)
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

    def _get_snapshot_path(self, feature_name: str, scenario_name: str) -> Path:
        """Get the path for a snapshot file."""
        feature_dir = self.snapshots_dir / feature_name
        feature_dir.mkdir(parents=True, exist_ok=True)
        return feature_dir / f"{scenario_name}.json"

    def save_snapshot(
        self,
        feature_name: str,
        scenario_name: str,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Save a snapshot for a feature/scenario combination.

        Args:
            feature_name: Generator, packager, or other feature name
            scenario_name: Test scenario name
            payload: The output to snapshot
            metadata: Optional metadata (timestamp, version, etc)

        Returns:
            Path to saved snapshot file
        """
        snapshot_path = self._get_snapshot_path(feature_name, scenario_name)

        snapshot_data = {
            "feature": feature_name,
            "scenario": scenario_name,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
            "payload": payload,
        }

        with open(snapshot_path, "w") as f:
            json.dump(snapshot_data, f, indent=2, default=str)

        return snapshot_path

    def load_snapshot(self, feature_name: str, scenario_name: str) -> Optional[Dict[str, Any]]:
        """
        Load an existing snapshot.

        Args:
            feature_name: Generator, packager, or other feature name
            scenario_name: Test scenario name

        Returns:
            Snapshot data or None if not found
        """
        snapshot_path = self._get_snapshot_path(feature_name, scenario_name)

        if not snapshot_path.exists():
            return None

        with open(snapshot_path, "r") as f:
            return json.load(f)

    def compare_with_snapshot(
        self,
        feature_name: str,
        scenario_name: str,
        new_payload: Dict[str, Any],
        strict: bool = False,
    ) -> SnapshotDiffResult:
        """
        Compare current output with saved snapshot.

        Args:
            feature_name: Generator, packager, or other feature name
            scenario_name: Test scenario name
            new_payload: New output to compare
            strict: If True, any difference is "severe". If False, do soft comparison.

        Returns:
            SnapshotDiffResult with diff information
        """
        old_snapshot = self.load_snapshot(feature_name, scenario_name)

        if old_snapshot is None:
            return SnapshotDiffResult(
                has_diff=False,
                severity="none",
                message="No existing snapshot (first run)",
            )

        old_payload = old_snapshot.get("payload", {})

        # Soft comparison: detect structural changes but allow minor value changes
        added_keys = set(new_payload.keys()) - set(old_payload.keys())
        removed_keys = set(old_payload.keys()) - set(new_payload.keys())
        changed_keys = []
        length_diffs = {}

        for key in set(old_payload.keys()) & set(new_payload.keys()):
            old_val = old_payload[key]
            new_val = new_payload[key]

            # Track length changes for list/string fields
            if isinstance(old_val, (list, str, dict)):
                old_len = len(old_val) if hasattr(old_val, "__len__") else 0
                new_len = len(new_val) if hasattr(new_val, "__len__") else 0
                if old_len != new_len:
                    length_diffs[key] = (old_len, new_len)

            # Check if values differ
            if old_val != new_val:
                changed_keys.append(key)

        # Determine severity
        has_diff = bool(added_keys or removed_keys or changed_keys or length_diffs)

        if not has_diff:
            severity = "none"
        elif strict:
            severity = "severe"
        else:
            # Soft severity: removed keys are more concerning than added
            if removed_keys:
                severity = "moderate"
            elif changed_keys and not length_diffs:
                severity = "minor"
            else:
                severity = "moderate"

        message = ""
        if added_keys:
            message += f"Added keys: {sorted(added_keys)}. "
        if removed_keys:
            message += f"Removed keys: {sorted(removed_keys)}. "
        if changed_keys:
            message += f"Changed keys: {sorted(changed_keys)}. "
        if length_diffs:
            message += f"Length changes: {length_diffs}. "

        return SnapshotDiffResult(
            has_diff=has_diff,
            severity=severity,
            added_keys=sorted(list(added_keys)),
            removed_keys=sorted(list(removed_keys)),
            changed_keys=sorted(changed_keys),
            length_diffs=length_diffs,
            message=message.strip(),
        )

    def get_snapshot_stats(self) -> Dict[str, int]:
        """Get statistics about snapshots."""
        stats = {"total_snapshots": 0, "features": set()}

        for feature_dir in self.snapshots_dir.iterdir():
            if feature_dir.is_dir():
                stats["features"].add(feature_dir.name)
                stats["total_snapshots"] += len(list(feature_dir.glob("*.json")))

        stats["features"] = len(stats["features"])
        return stats
