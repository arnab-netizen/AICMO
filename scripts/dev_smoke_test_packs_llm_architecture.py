"""
AICMO Pack LLM Architecture Smoke Test
======================================

Purpose: Verify all packs generate successfully and track actual LLM service usage.

This script:
1. Runs every pack end-to-end in stub mode (safe for dev)
2. Uses monkeypatching to track when ResearchService and CreativeService methods are called
3. Reports which packs actually use research, strategy polish, and calendar enhancement

Usage:
    python scripts/dev_smoke_test_packs_llm_architecture.py

Expected Results:
    - All packs generate without errors
    - Packs with requires_research=True show Rsch=Y
    - Packs with strategy sections show Pol=Y (polish_section called)
    - Packs with quick_social calendar show Cal=Y (enhance_calendar_posts called)
"""

import os
import sys
import asyncio
from typing import Dict
from dataclasses import dataclass
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

# Force stub mode for safe dev testing
os.environ.setdefault("AICMO_STUB_MODE", "1")
os.environ.setdefault("AICMO_USE_LLM", "1")

# Import after env vars set and path configured
from backend.main import api_aicmo_generate_report
from aicmo.presets.package_presets import PACKAGE_PRESETS
from backend.services.research_service import ResearchService
from backend.services.creative_service import CreativeService


@dataclass
class UsageTracker:
    """Track which LLM services were actually called during pack generation."""

    research_called: bool = False
    polish_called: bool = False
    calendar_enhance_called: bool = False


def make_generic_payload(pack_key: str) -> Dict:
    """
    Create a realistic payload that works for all pack types.

    Using a B2B SaaS brand so it's neutral enough for:
    - Social packs (Instagram/LinkedIn)
    - Strategy packs (campaign planning)
    - Launch packs (product positioning)
    - Turnaround packs (brand reset)
    - Retention packs (CRM/lifecycle)
    - Audit packs (performance review)
    """
    return {
        "pack_key": pack_key,
        "stage": "draft",
        "client_brief": {
            "brand_name": "SmokeTest Marketing Platform",
            "industry": "B2B SaaS",
            "product_service": "Marketing automation platform for startups",
            "primary_goal": "Generate qualified demo bookings",
            "primary_customer": "B2B startup founders and marketing leads",
            "geography": "Global (US, EU, APAC)",
            "brand_tone": "authoritative, helpful, data-driven",
            "timeline": "90 days",
        },
        "services": {},
        "wow_enabled": True,
        "wow_package_key": pack_key,
        "use_learning": False,
    }


async def run_for_pack(pack_key: str, tracker: UsageTracker) -> Dict:
    """
    Generate report for one pack and track LLM service usage via monkeypatching.

    Args:
        pack_key: Pack identifier from PACKAGE_PRESETS
        tracker: UsageTracker instance to record service calls

    Returns:
        Dict with pack_key, section count, usage flags, and status
    """
    # Store original methods and __init__
    orig_fetch = ResearchService.fetch_comprehensive_research
    orig_polish = CreativeService.polish_section
    orig_enhance = CreativeService.enhance_calendar_posts
    orig_init = CreativeService.__init__

    # Monkeypatch to track calls (non-invasive)
    def patched_fetch(self, brief, *args, **kwargs):
        tracker.research_called = True
        return orig_fetch(self, brief, *args, **kwargs)

    def patched_polish(
        self, content, brief, research_data=None, section_type=None, *args, **kwargs
    ):
        tracker.polish_called = True
        # In stub mode, just return content unchanged to avoid OpenAI API call
        if os.getenv("AICMO_STUB_MODE") == "1":
            return content
        return orig_polish(self, content, brief, research_data, section_type, *args, **kwargs)

    def patched_enhance(self, posts, brief, research_data=None, *args, **kwargs):
        tracker.calendar_enhance_called = True
        # In stub mode, just return posts unchanged to avoid OpenAI API call
        if os.getenv("AICMO_STUB_MODE") == "1":
            return posts
        return orig_enhance(self, posts, brief, research_data, *args, **kwargs)

    def patched_init(self, client=None, config=None):
        """Force enabled=True and set dummy client so is_enabled() returns True."""
        orig_init(self, client, config)
        self.enabled = True  # Override to force code path execution
        if self.client is None:
            self.client = "stub_client"  # Dummy value so is_enabled() returns True

    # Apply patches
    ResearchService.fetch_comprehensive_research = patched_fetch
    CreativeService.polish_section = patched_polish
    CreativeService.enhance_calendar_posts = patched_enhance
    CreativeService.__init__ = patched_init

    try:
        payload = make_generic_payload(pack_key)

        # Generate report (api_aicmo_generate_report is the Streamlit-compatible entry point)
        result = await api_aicmo_generate_report(payload)

        # Count sections (result has report_markdown and extra_sections)
        section_count = len(result.get("extra_sections", {}))

        return {
            "pack_key": pack_key,
            "sections": section_count,
            "research_used": tracker.research_called,
            "polish_used": tracker.polish_called,
            "calendar_enhance_used": tracker.calendar_enhance_called,
            "status": "OK",
        }
    except Exception as e:
        return {
            "pack_key": pack_key,
            "sections": 0,
            "research_used": tracker.research_called,
            "polish_used": tracker.polish_called,
            "calendar_enhance_used": tracker.calendar_enhance_called,
            "status": f"ERROR: {str(e)[:60]}",
        }
    finally:
        # Restore originals (critical for isolation between packs)
        ResearchService.fetch_comprehensive_research = orig_fetch
        CreativeService.polish_section = orig_polish
        CreativeService.enhance_calendar_posts = orig_enhance
        CreativeService.__init__ = orig_init


async def main():
    """Run smoke test for all packs and print usage matrix."""
    print("=" * 80)
    print("AICMO PACK LLM ARCHITECTURE SMOKE TEST")
    print("=" * 80)
    print("Environment:")
    print(f"  AICMO_STUB_MODE: {os.getenv('AICMO_STUB_MODE', 'not set')}")
    print(f"  AICMO_USE_LLM: {os.getenv('AICMO_USE_LLM', 'not set')}")
    print(f"  OPENAI_API_KEY: {'set' if os.getenv('OPENAI_API_KEY') else 'not set'}")
    print(f"  PERPLEXITY_API_KEY: {'set' if os.getenv('PERPLEXITY_API_KEY') else 'not set'}")
    print("=" * 80)
    print()

    rows = []
    pack_count = len(PACKAGE_PRESETS)

    for idx, pack_key in enumerate(PACKAGE_PRESETS.keys(), 1):
        print(f"[{idx}/{pack_count}] Testing {pack_key}...", end=" ", flush=True)
        tracker = UsageTracker()
        info = await run_for_pack(pack_key, tracker)
        rows.append(info)

        # Print inline status
        if info["status"] == "OK":
            print(f"✓ ({info['sections']} sections)")
        else:
            print(f"✗ {info['status']}")

    print()
    print("=" * 80)
    print("RESULTS MATRIX")
    print("=" * 80)
    print(f"{'Pack':40s} | {'Secs':4s} | Rsch | Pol | Cal | Status")
    print("-" * 80)

    for r in rows:
        print(
            f"{r['pack_key']:40s} | "
            f"{r['sections']:4d} | "
            f"{'Y' if r['research_used'] else '-':4s} | "
            f"{'Y' if r['polish_used'] else '-':3s} | "
            f"{'Y' if r['calendar_enhance_used'] else '-':3s} | "
            f"{r['status']}"
        )

    print("=" * 80)
    print()
    print("Legend:")
    print("  Rsch = ResearchService.fetch_comprehensive_research() called")
    print("  Pol  = CreativeService.polish_section() called")
    print("  Cal  = CreativeService.enhance_calendar_posts() called")
    print()
    print("Expected behavior:")
    print("  - All packs should show status=OK")
    print("  - Packs with requires_research=True should show Rsch=Y")
    print("  - Packs with campaign_objective section should show Pol=Y (STEP 3)")
    print("  - Packs with detailed_30_day_calendar should show Cal=Y (STEP 4)")
    print()

    # Summary stats
    ok_count = sum(1 for r in rows if r["status"] == "OK")
    error_count = len(rows) - ok_count
    rsch_count = sum(1 for r in rows if r["research_used"])
    pol_count = sum(1 for r in rows if r["polish_used"])
    cal_count = sum(1 for r in rows if r["calendar_enhance_used"])

    print("Summary:")
    print(f"  Total packs: {len(rows)}")
    print(f"  Success: {ok_count}")
    print(f"  Errors: {error_count}")
    print(f"  Research used: {rsch_count}/{len(rows)}")
    print(f"  Polish used: {pol_count}/{len(rows)}")
    print(f"  Calendar enhancement used: {cal_count}/{len(rows)}")
    print()

    if error_count > 0:
        print("⚠️  Some packs failed. Review error messages above.")
        sys.exit(1)
    else:
        print("✅ All packs generated successfully!")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
