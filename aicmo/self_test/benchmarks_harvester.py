"""
Benchmarks Harvester

Discovers and maps benchmarks from aicmo/learning/benchmarks/ to features.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkInfo:
    """Information about a discovered benchmark."""

    file_path: str
    """Full file path to benchmark JSON"""

    name: str
    """Benchmark name (from filename or metadata)"""

    target_feature: Optional[str] = None
    """Feature this benchmark targets (if detectable)"""

    metadata: Dict[str, any] = field(default_factory=dict)
    """Additional metadata from the benchmark JSON"""

    enforced_by: Optional[str] = None
    """Validator or function that enforces this benchmark"""


def discover_all_benchmarks(base_path: str = "/workspaces/AICMO") -> List[BenchmarkInfo]:
    """
    Discover all benchmark JSON files.

    Args:
        base_path: Root path to search from

    Returns:
        List of BenchmarkInfo for all discovered benchmarks
    """
    benchmarks = []
    benchmarks_dir = Path(base_path) / "aicmo" / "learning" / "benchmarks"

    if not benchmarks_dir.exists():
        logger.debug(f"Benchmarks directory not found: {benchmarks_dir}")
        return benchmarks

    for json_file in sorted(benchmarks_dir.glob("*.json")):
        try:
            with open(json_file, "r") as f:
                data = json.load(f)

            # Extract metadata
            name = json_file.stem
            target_feature = None
            metadata = {}

            # Try to infer target feature from filename or metadata
            if "target_feature" in data:
                target_feature = data["target_feature"]
            elif "feature" in data:
                target_feature = data["feature"]
            else:
                # Try to infer from filename
                target_feature = _infer_feature_from_name(name)

            # Store metadata
            if isinstance(data, dict):
                metadata = {k: v for k, v in data.items() if k not in ["target_feature", "feature"]}

            benchmark = BenchmarkInfo(
                file_path=str(json_file),
                name=name,
                target_feature=target_feature,
                metadata=metadata,
            )
            benchmarks.append(benchmark)
            logger.debug(f"Discovered benchmark: {name} → {target_feature or 'unmapped'}")

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse benchmark JSON {json_file}: {e}")
        except Exception as e:
            logger.warning(f"Error loading benchmark {json_file}: {e}")

    return benchmarks


def map_benchmarks_to_features(
    benchmarks: List[BenchmarkInfo],
    known_features: Optional[Set[str]] = None,
) -> Dict[str, List[BenchmarkInfo]]:
    """
    Map benchmarks to features.

    Args:
        benchmarks: List of discovered benchmarks
        known_features: Set of known feature names (optional, for validation)

    Returns:
        Dictionary mapping feature names to their benchmarks.
        Includes key "__unmapped__" for benchmarks that couldn't be mapped.
    """
    mapping = {}
    unmapped = []

    for benchmark in benchmarks:
        if benchmark.target_feature:
            if benchmark.target_feature not in mapping:
                mapping[benchmark.target_feature] = []
            mapping[benchmark.target_feature].append(benchmark)
        else:
            unmapped.append(benchmark)

    if unmapped:
        mapping["__unmapped__"] = unmapped

    return mapping


def find_benchmark_validators(base_path: str = "/workspaces/AICMO") -> Dict[str, str]:
    """
    Find which validators enforce which benchmarks.

    Scans quality/validators.py and similar for functions/methods that reference
    benchmark files.

    Args:
        base_path: Root path to search from

    Returns:
        Dictionary mapping benchmark names to validator names
    """
    validators_file = Path(base_path) / "aicmo" / "quality" / "validators.py"
    mapping = {}

    if not validators_file.exists():
        logger.debug("Validators file not found")
        return mapping

    try:
        with open(validators_file, "r") as f:
            content = f.read()

        # Look for patterns like validate_report, validate_strategy, etc.
        # This is heuristic-based; it finds functions that might enforce benchmarks

        import re

        # Find function definitions
        func_pattern = r"def\s+(\w+)\s*\([^)]*\)"
        functions = re.findall(func_pattern, content)

        # Common naming patterns for validators
        for func_name in functions:
            if "validate" in func_name.lower():
                # Try to map to benchmarks based on naming
                if "report" in func_name.lower():
                    mapping.setdefault("report", func_name)
                if "strategy" in func_name.lower():
                    mapping.setdefault("strategy", func_name)
                if "calendar" in func_name.lower():
                    mapping.setdefault("calendar", func_name)
                if "persona" in func_name.lower():
                    mapping.setdefault("persona", func_name)

    except Exception as e:
        logger.debug(f"Error scanning validators: {e}")

    return mapping


def _infer_feature_from_name(name: str) -> Optional[str]:
    """
    Attempt to infer target feature from benchmark filename.

    Args:
        name: Benchmark filename (without .json)

    Returns:
        Inferred feature name or None
    """
    name_lower = name.lower()

    # Direct matches
    feature_keywords = {
        "persona": "persona_generator",
        "calendar": "social_calendar_generator",
        "social": "social_calendar_generator",
        "situation": "situation_analysis_generator",
        "analysis": "situation_analysis_generator",
        "messaging": "messaging_pillars_generator",
        "pillars": "messaging_pillars_generator",
        "swot": "swot_generator",
        "pptx": "generate_full_deck_pptx",
        "deck": "generate_full_deck_pptx",
        "html": "generate_html_summary",
        "summary": "generate_html_summary",
    }

    for keyword, feature in feature_keywords.items():
        if keyword in name_lower:
            return feature

    return None


def summarize_benchmark_coverage(
    benchmarks: List[BenchmarkInfo],
    enforced_benchmarks: Set[str],
) -> Dict[str, any]:
    """
    Create a coverage summary of benchmark enforcement.

    Args:
        benchmarks: All discovered benchmarks
        enforced_benchmarks: Set of benchmark names that are actually enforced

    Returns:
        Dictionary with coverage metrics
    """
    total = len(benchmarks)
    mapped = sum(1 for b in benchmarks if b.target_feature)
    unmapped = total - mapped
    enforced = len([b for b in benchmarks if b.name in enforced_benchmarks])

    return {
        "total_benchmarks": total,
        "mapped_benchmarks": mapped,
        "unmapped_benchmarks": unmapped,
        "enforced_benchmarks": enforced,
        "unenforced_benchmarks": mapped - enforced,
        "coverage_percent": round((enforced / mapped * 100) if mapped > 0 else 0, 1),
    }
