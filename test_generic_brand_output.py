#!/usr/bin/env python3
"""
Quick test to generate a Quick Social Pack for a generic brand (not Starbucks)
to verify it's truly client-ready and brand-agnostic.
"""

from aicmo.io.client_reports import (
    BrandBrief,
    ClientInputBrief,
    AudienceBrief,
    GoalBrief,
    VoiceBrief,
    ProductServiceBrief,
    AssetsConstraintsBrief,
    OperationsBrief,
    StrategyExtrasBrief,
)
from backend.main import (
    GenerateRequest,
    _gen_overview,
    _gen_messaging_framework,
    _gen_final_summary,
)
from backend.views import MarketingPlanView, CampaignBlueprintView

# Create a generic tech startup brief
brand = BrandBrief(
    brand_name="TechFlow Solutions",
    industry="Software & Technology",
    product_service="Cloud-based project management software",
    primary_goal="Increase trial signups and product awareness",
    primary_customer="tech-savvy project managers and startups",
    location="Austin, TX, USA",
    timeline="90 days",
    brand_tone="professional, innovative, approachable",
).with_safe_defaults()

brief = ClientInputBrief(
    brand=brand,
    audience=AudienceBrief(primary_customer="project managers at tech startups"),
    goal=GoalBrief(primary_goal="Increase trial signups by 40%"),
    voice=VoiceBrief(brand_tone="innovative"),
    product_service=ProductServiceBrief(product_service="Project management software"),
    assets_constraints=AssetsConstraintsBrief(),
    operations=OperationsBrief(),
    strategy_extras=StrategyExtrasBrief(),
)

req = GenerateRequest(brief=brief, wow_package_key="quick_social_basic")

# Create minimal views for generators that need them
mp = MarketingPlanView()
cb = CampaignBlueprintView()

print("=" * 80)
print("QUICK SOCIAL PACK - GENERIC BRAND TEST")
print("Brand: TechFlow Solutions (NOT Starbucks)")
print("=" * 80)

print("\n" + "=" * 80)
print("1. BRAND & CONTEXT SNAPSHOT")
print("=" * 80)
overview = _gen_overview(req, mp, cb, pack_key="quick_social_basic")
print(overview[:500] + "...")

print("\n" + "=" * 80)
print("2. MESSAGING FRAMEWORK")
print("=" * 80)
messaging = _gen_messaging_framework(req, mp, pack_key="quick_social_basic")
print(messaging[:500] + "...")

print("\n" + "=" * 80)
print("3. FINAL SUMMARY & NEXT STEPS")
print("=" * 80)
summary = _gen_final_summary(req, pack_key="quick_social_basic")
print(summary)

print("\n" + "=" * 80)
print("VERIFICATION CHECKS")
print("=" * 80)

# Check for hard-coded brands
checks = {
    "No 'Starbucks'": "starbucks" not in overview.lower()
    and "starbucks" not in messaging.lower()
    and "starbucks" not in summary.lower(),
    "Uses 'TechFlow Solutions'": "TechFlow Solutions" in overview
    and "TechFlow Solutions" in messaging
    and "TechFlow Solutions" in summary,
    "Uses brief industry": "Software & Technology" in overview or "technology" in overview.lower(),
    "Uses brief goal": "trial signup" in overview.lower()
    or "trial signup" in summary.lower()
    or "awareness" in overview.lower(),
    "No awkward 'Operating in'": "Operating in the" not in overview,
    "Brand-first phrasing": "TechFlow Solutions operates" in overview
    or "TechFlow Solutions is" in overview,
}

for check_name, passed in checks.items():
    status = "✅" if passed else "❌"
    print(f"{status} {check_name}")

if all(checks.values()):
    print("\n🎉 SUCCESS: Content is brand-agnostic and client-ready!")
else:
    print("\n❌ FAIL: Some checks failed - needs more fixes")
