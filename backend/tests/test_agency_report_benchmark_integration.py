import json
from pathlib import Path

import pytest

from benchmark_utils import run_strategy_campaign_for_benchmark

BENCHMARKS_DIR = Path(__file__).resolve().parent.parent.parent / "learning" / "benchmarks"


def _load_luxotica_constraints():
    path = BENCHMARKS_DIR / "agency_report_automotive_luxotica.json"
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.integration
def test_strategy_campaign_luxotica_benchmark_passes_quality_and_terms():
    data = _load_luxotica_constraints()
    result = run_strategy_campaign_for_benchmark("agency_report_automotive_luxotica.json")

    assert result.get("status") == "success", f"Generation failed: {result}"

    text = result.get("report_markdown") or ""
    text_lower = text.lower()

    for term in data["required_terms"]:
        assert term.lower() in text_lower, f"Missing required term: {term}"

    for term in data["forbidden_terms"]:
        assert term.lower() not in text_lower, f"Forbidden term leaked into report: {term}"

    brand = data["brand_name"]
    assert text.count(brand) >= data.get("min_brand_mentions", 1), "Brand not mentioned enough"
