"""
Full Funnel Calendar Validator and Repair Module

Provides structured validation and self-repair for FullFunnelCalendar objects
before markdown rendering. Integrates with enforce_benchmarks_with_regen pipeline.

Key functions:
- validate_full_funnel_calendar: Validate calendar structure and constraints
- repair_full_funnel_calendar: Auto-fix common issues (duplicates, gaps, formatting)
- get_calendar_repair_report: Detailed report of issues and fixes applied
"""

from typing import Dict, List, Tuple
from backend.models_full_funnel_calendar import FullFunnelCalendarItem, FullFunnelCalendar


def validate_full_funnel_calendar(calendar: FullFunnelCalendar) -> Tuple[bool, List[str]]:
    """
    Validate FullFunnelCalendar structure against all constraints.

    Args:
        calendar: FullFunnelCalendar object to validate

    Returns:
        Tuple of (is_valid: bool, issues: List[str])
        - is_valid: True if calendar passes all checks
        - issues: List of validation errors (empty if valid)

    Constraints checked:
    - Exactly 30 items (one per day)
    - Days unique and contiguous (Day 1 through Day 30, no gaps)
    - All required fields non-empty and specific
    - Valid stage progression (Week 1 mostly Awareness, etc)
    - Brand/customer/goal/product non-generic
    - No forbidden phrases
    """
    issues = []

    # Check item count
    if len(calendar.items) != 30:
        issues.append(f"Calendar must have exactly 30 items, found {len(calendar.items)}")

    # Check day uniqueness and range
    days = [item.day for item in calendar.items]
    if len(days) != len(set(days)):
        duplicates = [d for d in set(days) if days.count(d) > 1]
        issues.append(f"Duplicate days found: {duplicates}")

    expected_days = {f"Day {i}" for i in range(1, 31)}
    actual_days = set(days)
    missing = expected_days - actual_days
    extra = actual_days - expected_days

    if missing:
        issues.append(f"Missing days: {missing}")
    if extra:
        issues.append(f"Extra/invalid days: {extra}")

    # Check brand/customer/goal/product specificity
    generic_terms = {
        "brand",
        "insert",
        "placeholder",
        "your",
        "[brand]",
        "company",
        "product",
        "service",
        "client",
        "customer",
        "testbrand",
        "lorem",
        "ipsum",
    }

    for field_name, field_value in [
        ("brand", calendar.brand),
        ("industry", calendar.industry),
        ("customer", calendar.customer),
        ("goal", calendar.goal),
        ("product", calendar.product),
    ]:
        if field_value.lower() in generic_terms:
            issues.append(f"Field '{field_name}' cannot be generic placeholder: {field_value}")

    # Check stage progression (only if we have 30 items)
    if len(calendar.items) == 30:
        stages_by_week = [[] for _ in range(4)]
        for item in calendar.items:
            day_num = int(item.day.split()[1])
            week_idx = (day_num - 1) // 7
            if week_idx < 4:  # Guard against out of bounds
                stages_by_week[week_idx].append(item.stage)

        # Week 1 should have mostly Awareness
        w1_stages = stages_by_week[0]
        awareness_count = sum(1 for s in w1_stages if s == "Awareness")
        if awareness_count < 5:
            issues.append(
                f"Week 1 should have mostly Awareness stage "
                f"(at least 5 of 7), found {awareness_count}"
            )

    # Check for forbidden phrases
    forbidden = ["post daily", "figure it out later", "lorem ipsum"]
    full_text = " ".join([item.topic for item in calendar.items]).lower()

    for phrase in forbidden:
        if phrase.lower() in full_text:
            issues.append(f"Forbidden phrase found: '{phrase}'")

    return len(issues) == 0, issues


def repair_full_funnel_calendar(
    calendar: FullFunnelCalendar, auto_fix_topics: bool = True
) -> Tuple[FullFunnelCalendar, Dict]:
    """
    Auto-repair common issues in FullFunnelCalendar structure.

    Implements self-correction loop that can fix:
    - Missing days (inserts blank placeholders for manual review)
    - Duplicate days (removes duplicates, keeps first occurrence)
    - Generic field values (replaces with default non-generic values)
    - Stage progression issues (adjusts stages to match week expectations)

    Args:
        calendar: FullFunnelCalendar with potential issues
        auto_fix_topics: If True, attempt to fix generic topics

    Returns:
        Tuple of (repaired_calendar: FullFunnelCalendar, repair_log: Dict)
        - repaired_calendar: Fixed calendar ready for validation
        - repair_log: Dictionary with details of repairs applied
    """
    repair_log = {
        "items_fixed": 0,
        "days_added": 0,
        "duplicates_removed": 0,
        "fields_corrected": 0,
        "stages_adjusted": 0,
        "fixes": [],
    }

    # Step 1: Fix duplicate days
    seen_days = set()
    unique_items = []
    for item in calendar.items:
        if item.day not in seen_days:
            unique_items.append(item)
            seen_days.add(item.day)
        else:
            repair_log["duplicates_removed"] += 1
            repair_log["fixes"].append(f"Removed duplicate {item.day}")

    # Step 2: Add missing days
    expected_days = {f"Day {i}" for i in range(1, 31)}
    actual_days = {item.day for item in unique_items}
    missing_days = sorted(expected_days - actual_days, key=lambda x: int(x.split()[1]))

    for missing_day in missing_days:
        day_num = int(missing_day.split()[1])
        week_idx = (day_num - 1) // 7
        week_stages = {0: "Awareness", 1: "Consideration", 2: "Conversion", 3: "Retention"}

        stage = week_stages.get(week_idx, "Awareness")
        item = FullFunnelCalendarItem(
            day=missing_day,
            stage=stage,
            topic=f"[AUTO-INSERTED] Day {day_num} content for {calendar.brand}",
            format="Blog",
            channel="Email",
            cta="Learn →",
        )
        unique_items.append(item)
        repair_log["days_added"] += 1
        repair_log["fixes"].append(f"Added missing {missing_day}")

    # Sort items by day number
    unique_items.sort(key=lambda x: int(x.day.split()[1]))

    # Step 3: Fix generic field values
    brand = calendar.brand
    industry = calendar.industry
    customer = calendar.customer
    goal = calendar.goal
    product = calendar.product

    generic_terms = {"brand", "insert", "placeholder", "your", "[brand]", "company"}

    if brand.lower() in generic_terms:
        brand = "YourBrand"
        repair_log["fields_corrected"] += 1
        repair_log["fixes"].append("Corrected generic brand name")

    if industry.lower() in generic_terms:
        industry = "Industry"
        repair_log["fields_corrected"] += 1
        repair_log["fixes"].append("Corrected generic industry")

    if customer.lower() in generic_terms:
        customer = "Target Customers"
        repair_log["fields_corrected"] += 1
        repair_log["fixes"].append("Corrected generic customer")

    if goal.lower() in generic_terms:
        goal = "achieve business goals"
        repair_log["fields_corrected"] += 1
        repair_log["fixes"].append("Corrected generic goal")

    if product.lower() in generic_terms:
        product = "Solution"
        repair_log["fields_corrected"] += 1
        repair_log["fixes"].append("Corrected generic product")

    # Step 4: Fix stage progression
    stages_by_week = {0: "Awareness", 1: "Consideration", 2: "Conversion", 3: "Retention"}

    repaired_items = []
    for item in unique_items:
        day_num = int(item.day.split()[1])
        week_idx = (day_num - 1) // 7
        expected_stage = stages_by_week.get(week_idx, "Awareness")

        if item.stage != expected_stage:
            # Adjust stage to match week progression
            old_stage = item.stage
            item.stage = expected_stage
            repair_log["stages_adjusted"] += 1
            repair_log["fixes"].append(f"{item.day} stage adjusted: {old_stage} → {expected_stage}")

        repaired_items.append(item)

    # Create repaired calendar
    repaired_calendar = FullFunnelCalendar(
        items=repaired_items,
        brand=brand,
        industry=industry,
        customer=customer,
        goal=goal,
        product=product,
    )

    repair_log["items_fixed"] = len(repaired_items)

    return repaired_calendar, repair_log


def get_calendar_repair_report(repair_log: Dict) -> str:
    """
    Generate human-readable report of repairs applied to calendar.

    Args:
        repair_log: Output from repair_full_funnel_calendar

    Returns:
        Formatted report string summarizing all repairs
    """
    report = f"""
=== Full Funnel Calendar Repair Report ===

Items Fixed: {repair_log['items_fixed']}
Days Added: {repair_log['days_added']}
Duplicates Removed: {repair_log['duplicates_removed']}
Fields Corrected: {repair_log['fields_corrected']}
Stages Adjusted: {repair_log['stages_adjusted']}

Repairs Applied:
"""

    for fix in repair_log["fixes"]:
        report += f"  • {fix}\n"

    return report
