#!/usr/bin/env python3
"""
Debug script to validate Quick Social sections and see exact failures.
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.models import GenerateRequest, ClientBrief, BrandContext, GoalContext, AudienceContext
from backend.validators.report_gate import validate_report_sections


def main():
    # Create a realistic brief for Quick Social
    brief = ClientBrief(
        brand=BrandContext(
            brand_name="Debug Café",
            industry="Food & Beverage",
            location="Indiranagar, Bangalore",
            product_service="Artisan coffee, breakfast items, remote work-friendly space",
            brand_story="A cozy neighborhood café focused on quality coffee and community",
        ),
        goal=GoalContext(
            primary_goal="Increase daily footfall and Instagram visibility",
            secondary_goal="Build a loyal regular customer base",
            timeline="3 months",
        ),
        audience=AudienceContext(
            primary_customer="Students and remote workers",
            secondary_customer="Young professionals seeking quality coffee",
        ),
    )

    # Create request
    req = GenerateRequest(
        brief=brief,
        package_preset="Quick Social Pack (Basic)",
        wow_package_key="quick_social_basic",
    )

    # Import after setting up path
    from backend.main import generate_sections_for_pack

    print("=" * 80)
    print("GENERATING QUICK SOCIAL SECTIONS")
    print("=" * 80)

    try:
        # Generate all sections
        sections = generate_sections_for_pack(req)

        print(f"\n✅ Generated {len(sections)} sections\n")

        # Validate against benchmarks
        print("=" * 80)
        print("VALIDATING AGAINST BENCHMARKS")
        print("=" * 80)

        # Build sections list for validation
        sections_list = [
            {"id": section_id, "content": content}
            for section_id, content in sections.items()
            if content
        ]

        result = validate_report_sections(pack_key="quick_social_basic", sections=sections_list)

        print(f"\nValidation Status: {result.status}")
        print(f"Total Sections: {result.total_sections}")
        print(f"Passing Sections: {result.passing_sections}")
        print(f"Failing Sections: {result.failing_sections}")

        if result.failing_sections > 0:
            print("\n" + "=" * 80)
            print("DETAILED FAILURES")
            print("=" * 80)

            for section_result in result.section_results:
                if section_result.issues:
                    section_id = section_result.section_id
                    print(f"\n❌ {section_id}")
                    print(f"   Status: {section_result.status}")

                    # Get section content
                    content = sections.get(section_id, "")
                    word_count = len(content.split())
                    line_count = len([line for line in content.split("\n") if line.strip()])
                    heading_count = len(
                        [line for line in content.split("\n") if line.strip().startswith("#")]
                    )
                    bullet_count = len(
                        [line for line in content.split("\n") if line.strip().startswith("-")]
                    )

                    print(
                        f"   Actual: {word_count} words, {heading_count} headings, {bullet_count} bullets, {line_count} lines"
                    )

                    for issue in section_result.issues:
                        print(f"   - {issue.code}: {issue.message}")

                    # Show first 300 chars of content
                    print("\n   Content preview:")
                    preview = content[:300].replace("\n", "\n   ")
                    print(f"   {preview}...")
                    print()
        else:
            print("\n✅ ALL SECTIONS PASSED!")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0 if result.failing_sections == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
