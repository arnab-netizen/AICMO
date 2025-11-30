"""
Benchmark configuration loader for AICMO section quality validation.

Loads JSON-based benchmark files that define quality criteria (word counts,
required phrases, forbidden patterns, etc.) for each section in a pack.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

BENCHMARKS_DIR = Path(__file__).resolve().parents[2] / "learning" / "benchmarks"


class BenchmarkNotFoundError(Exception):
    """Raised when no benchmark file can be found for a given pack."""

    pass


@lru_cache(maxsize=32)
def load_benchmarks_for_pack(pack_key: str) -> Dict[str, Any]:
    """
    Load the benchmark config for a pack.

    Filename convention: section_benchmarks.<pack_key_suffix>.json

    Example:
      pack_key = "quick_social_basic"
      file     = "section_benchmarks.quick_social.json"

    Args:
        pack_key: Internal pack key (e.g., "quick_social_basic")

    Returns:
        Dict containing benchmark configuration with "pack_key", "strict", and "sections" keys

    Raises:
        BenchmarkNotFoundError: If no benchmark file found for this pack
    """
    # Basic heuristic: take first 2 segments of pack_key
    # Adjust if your naming pattern is different.
    key_parts = pack_key.split("_")
    if len(key_parts) >= 2:
        suffix = "_".join(key_parts[:2])
    else:
        suffix = pack_key

    candidate_name = f"section_benchmarks.{suffix}.json"
    candidate_path = BENCHMARKS_DIR / candidate_name

    if not candidate_path.exists():
        raise BenchmarkNotFoundError(
            f"No benchmark file found for pack_key={pack_key} at {candidate_path}"
        )

    with candidate_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if data.get("pack_key") and data["pack_key"] != pack_key:
        # Not fatal – but useful to catch misalignment early.
        # You can choose to raise instead if you want strict behaviour.
        pass

    return data


def get_section_benchmark(pack_key: str, section_id: str) -> Optional[Dict[str, Any]]:
    """
    Return benchmark config for a specific section or None if not defined.

    Args:
        pack_key: Pack identifier
        section_id: Section identifier (must match SECTION_GENERATORS key)

    Returns:
        Section benchmark dict or None if section not benchmarked
    """
    config = load_benchmarks_for_pack(pack_key)
    sections = config.get("sections", {})
    return sections.get(section_id)


def is_strict_pack(pack_key: str) -> bool:
    """
    Return whether strict mode is enabled for this pack.

    In strict mode, sections without benchmarks cause validation failures.
    In non-strict mode, unbenchmarked sections generate warnings only.

    Args:
        pack_key: Pack identifier

    Returns:
        True if strict mode enabled, False otherwise
    """
    try:
        config = load_benchmarks_for_pack(pack_key)
        return bool(config.get("strict", False))
    except BenchmarkNotFoundError:
        return False
