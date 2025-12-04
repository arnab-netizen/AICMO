#!/usr/bin/env python3
"""
Diagnose what content is being generated for failing sections.
"""
import os

os.environ["OPENAI_API_KEY"] = "sk-test-fake"
os.environ["AICMO_STUB_MODE"] = "0"

import asyncio
from backend.main import GenerateRequest, aicmo_generate
from aicmo.io.client_reports import (
    BrandBrief,
    AudienceBrief,
    GoalBrief,
    ClientInputBrief,
)


async def main():
    brief = ClientInputBrief(
        brand=BrandBrief(
            brand_name="TestBrand",
            industry="B2B SaaS",
            product_service="Marketing automation platform",
            primary_goal="awareness",
            primary_customer="Marketing Directors",
        ),
        audience=AudienceBrief(
            primary_customer="Marketing directors at mid-market companies",
            pain_points="Manual campaign management, lack of attribution",
        ),
        goal=GoalBrief(
            primary_goal="Generate 100 qualified demo requests",
            success_metrics=["Demo conversion rate", "Sales-qualified leads"],
        ),
    )

    req = GenerateRequest(
        brief=brief,
        package_preset="strategy_campaign_standard",
        wow_package_key="strategy_campaign_standard",
        wow_enabled=False,  # Just get sections, not WOW
        include_agency_grade=False,
        skip_benchmark_enforcement=True,  # Skip enforcement to get raw output
    )

    # Temporarily modify generate_sections to skip enforcement
    import backend.main

    original_is_stub = backend.utils.config.is_stub_mode

    try:
        # Force non-stub mode
        backend.utils.config.is_stub_mode = lambda: False

        output = await aicmo_generate(req)

        # Check failing sections
        failing = [
            "messaging_framework",
            "detailed_30_day_calendar",
            "ad_concepts",
            "execution_roadmap",
            "final_summary",
        ]

        for section_id in failing:
            content = output.extra_sections.get(section_id, "")
            print(f"\n{'='*80}")
            print(f"SECTION: {section_id}")
            print(f"{'='*80}")
            print(f"Length: {len(content)} chars")
            print(f"Words: {len(content.split())}")

            # Check for required headings
            if "messaging_framework" == section_id:
                print(f"Has 'Core Message': {'Core Message' in content}")
                print(f"Has 'Key Themes': {'Key Themes' in content}")
            elif "detailed_30_day_calendar" == section_id:
                print(f"Has 'Phase 1': {'Phase 1' in content}")
                print(f"Has 'Phase 2': {'Phase 2' in content}")
                print(f"Has 'Phase 3': {'Phase 3' in content}")
                print(f"Has table marker '|': {'|' in content}")
            elif "ad_concepts" == section_id:
                print(f"Has 'Ad Concepts': {'Ad Concepts' in content}")
                print(f"Has 'Messaging': {'Messaging' in content}")
            elif "execution_roadmap" == section_id:
                print(f"Has 'Phase 1': {'Phase 1' in content}")
                print(f"Has 'Phase 2': {'Phase 2' in content}")
                print(f"Has 'Key Milestones': {'Key Milestones' in content}")
                print(f"Has table marker '|': {'|' in content}")
            elif "final_summary" == section_id:
                print(f"Has 'Key Takeaways': {'Key Takeaways' in content}")

            print(f"\nFirst 500 chars:\n{content[:500]}")

    finally:
        backend.utils.config.is_stub_mode = original_is_stub


if __name__ == "__main__":
    asyncio.run(main())
