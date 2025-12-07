import json
import asyncio
from pathlib import Path
from typing import Any, Dict

from backend.main import api_aicmo_generate_report

BENCHMARKS_DIR = Path(__file__).resolve().parent.parent.parent / "learning" / "benchmarks"


def load_benchmark(name: str) -> Dict[str, Any]:
    path = BENCHMARKS_DIR / name
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def run_strategy_campaign_for_benchmark(benchmark_name: str) -> Dict[str, Any]:
    data = load_benchmark(benchmark_name)

    brief = {
        "brand_name": data.get("brand_name", "Test Brand"),
        "industry": data.get("industry", "Automotive"),
        "product_service": data.get("brief", {}).get(
            "product_service", "Luxury automotive dealership"
        ),
        "geography": data.get("brief", {}).get("geography", "Kolkata"),
        "primary_goal": data.get("brief", {}).get(
            "primary_goal", "Increase qualified leads and showroom visits"
        ),
        # Provide explicit fields used by AgencyReport planning/validation
        "target_audience": data.get("brief", {}).get(
            "target_audience", "Affluent car buyers in Kolkata"
        ),
        "positioning_summary": data.get("brief", {}).get(
            "positioning_summary",
            "Boutique luxury dealership focused on curated premium vehicles and concierge service.",
        ),
        "raw_brief_text": (
            f"{data.get('brand_name', 'Test Brand')} is a luxury car dealership in Kolkata. "
            "Target audience: affluent car buyers in Kolkata. "
            "Primary goal: increase qualified leads and showroom visits. "
            "Positioning Summary: boutique dealership with curated premium vehicles and concierge service. "
            "Strategy: dominate local luxury search, build showroom experiences, leverage owner social proof."
        ),
        "notes": data.get(
            "notes",
            "Benchmark run for Strategy+Campaign automotive dealership.",
        ),
    }

    payload = {
        "stage": "final",
        "client_brief": brief,
        "services": {
            "include_agency_grade": False,
            "marketing_plan": True,
            "campaign_blueprint": True,
            "social_calendar": True,
            "performance_review": False,
        },
        "package_name": "Strategy + Campaign Pack (Standard)",
        "wow_enabled": True,
        "wow_package_key": "strategy_campaign_standard",
        "refinement_mode": {
            "name": "Balanced",
            "passes": 1,
            "max_tokens": 4000,
            "temperature": 0.7,
        },
        "feedback": "",
        "previous_draft": "",
        "learn_items": [],
        "use_learning": False,
        "industry_key": None,
    }

    # Call the internal async API handler synchronously
    return asyncio.run(api_aicmo_generate_report(payload))
