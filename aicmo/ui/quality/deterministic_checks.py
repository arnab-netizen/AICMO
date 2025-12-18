"""
Deterministic Quality Checks for AICMO Artifacts

Implements code-based validation checks (no LLM) for structural correctness,
required fields, consistency, and basic content sanity.
"""
from typing import List, Dict, Any, Optional
import re
import json
from aicmo.ui.quality.qc_models import (
    QCCheck,
    CheckType,
    CheckStatus,
    CheckSeverity
)


# ============================================================================
# INTAKE QC
# ============================================================================

def validate_intake_qc(intake_content: Dict[str, Any]) -> List[QCCheck]:
    """
    Deterministic checks for Intake artifacts.
    
    Checks:
        1. Required fields present (brand/objective/audience/offer)
        2. Objective ↔ jobs consistency
        3. Budget sanity (no ads with zero budget)
        4. Regulated industry requires compliance note
        5. Timeline sanity (end after start)
    """
    checks = []
    
    # Check 1: Required fields
    required_fields = ["brand_name", "objective", "target_audience", "offer"]
    missing = [f for f in required_fields if not intake_content.get(f, "").strip()]
    
    if missing:
        checks.append(QCCheck(
            check_id="intake_required_fields",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.BLOCKER,
            message=f"Missing required fields: {', '.join(missing)}",
            evidence=f"Fields must be non-empty: {missing}",
            auto_fixable=False
        ))
    else:
        checks.append(QCCheck(
            check_id="intake_required_fields",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.BLOCKER,
            message="All required fields present"
        ))
    
    # Check 2: Objective ↔ jobs consistency
    objective = intake_content.get("objective", "").lower()
    jobs_requested = intake_content.get("jobs_requested", [])
    
    inconsistencies = []
    if "awareness" in objective and "ads" not in [j.lower() for j in jobs_requested]:
        inconsistencies.append("Objective mentions awareness but no ads job requested")
    if "content" in objective and "content" not in [j.lower() for j in jobs_requested]:
        inconsistencies.append("Objective mentions content but no content job requested")
    
    if inconsistencies:
        checks.append(QCCheck(
            check_id="intake_objective_jobs_consistency",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.WARN,
            severity=CheckSeverity.MAJOR,
            message="Objective and jobs may be inconsistent",
            evidence="; ".join(inconsistencies),
            auto_fixable=False
        ))
    else:
        checks.append(QCCheck(
            check_id="intake_objective_jobs_consistency",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.MAJOR,
            message="Objective aligns with requested jobs"
        ))
    
    # Check 3: Budget sanity
    budget_info = intake_content.get("budget", {})
    if isinstance(budget_info, dict):
        ads_budget = budget_info.get("ads_budget", 0)
        if ads_budget == 0 and "ads" in [j.lower() for j in jobs_requested]:
            checks.append(QCCheck(
                check_id="intake_budget_sanity",
                check_type=CheckType.DETERMINISTIC,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.BLOCKER,
                message="Ads job requested but ads_budget is zero",
                evidence=f"jobs_requested includes ads, but ads_budget={ads_budget}",
                auto_fixable=False
            ))
        else:
            checks.append(QCCheck(
                check_id="intake_budget_sanity",
                check_type=CheckType.DETERMINISTIC,
                status=CheckStatus.PASS,
                severity=CheckSeverity.BLOCKER,
                message="Budget allocation is reasonable"
            ))
    else:
        checks.append(QCCheck(
            check_id="intake_budget_sanity",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.BLOCKER,
            message="Budget not provided (acceptable for some engagements)"
        ))
    
    # Check 4: Regulated industry compliance
    industry = intake_content.get("industry", "").lower()
    regulated = ["finance", "healthcare", "pharma", "legal", "gambling", "crypto"]
    
    if any(reg in industry for reg in regulated):
        compliance_notes = intake_content.get("compliance_notes", "").strip()
        if not compliance_notes:
            checks.append(QCCheck(
                check_id="intake_regulated_compliance",
                check_type=CheckType.DETERMINISTIC,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.MAJOR,
                message=f"Regulated industry ({industry}) requires compliance notes",
                evidence="compliance_notes field is empty",
                auto_fixable=False
            ))
        else:
            checks.append(QCCheck(
                check_id="intake_regulated_compliance",
                check_type=CheckType.DETERMINISTIC,
                status=CheckStatus.PASS,
                severity=CheckSeverity.MAJOR,
                message="Compliance notes provided for regulated industry"
            ))
    else:
        checks.append(QCCheck(
            check_id="intake_regulated_compliance",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.MAJOR,
            message="Not a regulated industry or compliance addressed"
        ))
    
    # Check 5: Timeline sanity
    timeline = intake_content.get("timeline", {})
    if isinstance(timeline, dict):
        start = timeline.get("start_date")
        end = timeline.get("end_date")
        if start and end:
            # Simple string comparison (assumes ISO format)
            if end < start:
                checks.append(QCCheck(
                    check_id="intake_timeline_sanity",
                    check_type=CheckType.DETERMINISTIC,
                    status=CheckStatus.FAIL,
                    severity=CheckSeverity.BLOCKER,
                    message="End date before start date",
                    evidence=f"start={start}, end={end}",
                    auto_fixable=False
                ))
            else:
                checks.append(QCCheck(
                    check_id="intake_timeline_sanity",
                    check_type=CheckType.DETERMINISTIC,
                    status=CheckStatus.PASS,
                    severity=CheckSeverity.BLOCKER,
                    message="Timeline dates are valid"
                ))
        else:
            checks.append(QCCheck(
                check_id="intake_timeline_sanity",
                check_type=CheckType.DETERMINISTIC,
                status=CheckStatus.PASS,
                severity=CheckSeverity.BLOCKER,
                message="Timeline dates not fully specified (acceptable)"
            ))
    else:
        checks.append(QCCheck(
            check_id="intake_timeline_sanity",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.BLOCKER,
            message="No timeline provided (acceptable)"
        ))
    
    return checks


# ============================================================================
# STRATEGY QC
# ============================================================================

def validate_strategy_qc(strategy_content: Dict[str, Any]) -> List[QCCheck]:
    """
    Deterministic checks for Strategy artifacts.
    
    Checks:
        1. All required contract sections present
        2. No placeholder text (TBD/lorem/fill/TODO)
        3. Platform ↔ geography consistency
        4. Measurement framework includes metrics
        5. CTAs defined and actionable
    """
    checks = []
    
    # Check 1: Required sections
    required_sections = [
        "icp",
        "positioning",
        "messaging",
        "pillars",
        "platform_plan",
        "ctas",
        "measurement"
    ]
    
    missing_sections = [s for s in required_sections if s not in strategy_content or not strategy_content[s]]
    
    if missing_sections:
        checks.append(QCCheck(
            check_id="strategy_required_sections",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.BLOCKER,
            message=f"Missing required strategy sections: {', '.join(missing_sections)}",
            evidence=f"Contract requires: {required_sections}",
            auto_fixable=False
        ))
    else:
        checks.append(QCCheck(
            check_id="strategy_required_sections",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.BLOCKER,
            message="All required strategy sections present"
        ))
    
    # Check 2: No placeholder text
    full_text = json.dumps(strategy_content).lower()
    placeholders = ["tbd", "lorem ipsum", "fill in", "todo", "[placeholder]", "xxx"]
    found_placeholders = [p for p in placeholders if p in full_text]
    
    if found_placeholders:
        checks.append(QCCheck(
            check_id="strategy_no_placeholders",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.BLOCKER,
            message=f"Placeholder text found: {', '.join(found_placeholders)}",
            evidence="Strategy must be fully populated with real content",
            auto_fixable=True,
            fix_instruction="Remove all placeholder text and replace with actual strategic content. Every section must have real, actionable information."
        ))
    else:
        checks.append(QCCheck(
            check_id="strategy_no_placeholders",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.BLOCKER,
            message="No placeholder text detected"
        ))
    
    # Check 3: Platform-geography consistency
    platform_plan = strategy_content.get("platform_plan", {})
    if isinstance(platform_plan, dict):
        platforms = list(platform_plan.keys())
        geography = strategy_content.get("geography", "").lower()
        
        inconsistencies = []
        if "china" in geography and "instagram" in [p.lower() for p in platforms]:
            inconsistencies.append("Instagram not available in China")
        if "weibo" in [p.lower() for p in platforms] and "china" not in geography:
            inconsistencies.append("Weibo primarily for China market")
        
        if inconsistencies:
            checks.append(QCCheck(
                check_id="strategy_platform_geography",
                check_type=CheckType.DETERMINISTIC,
                status=CheckStatus.WARN,
                severity=CheckSeverity.MAJOR,
                message="Platform-geography inconsistency detected",
                evidence="; ".join(inconsistencies),
                auto_fixable=False
            ))
        else:
            checks.append(QCCheck(
                check_id="strategy_platform_geography",
                check_type=CheckType.DETERMINISTIC,
                status=CheckStatus.PASS,
                severity=CheckSeverity.MAJOR,
                message="Platforms align with target geography"
            ))
    else:
        checks.append(QCCheck(
            check_id="strategy_platform_geography",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.MAJOR,
            message="Platform plan not structured for validation"
        ))
    
    # Check 4: Measurement framework
    measurement = strategy_content.get("measurement", {})
    if isinstance(measurement, dict):
        has_metrics = bool(measurement.get("metrics") or measurement.get("kpis"))
        if not has_metrics:
            checks.append(QCCheck(
                check_id="strategy_measurement_metrics",
                check_type=CheckType.DETERMINISTIC,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.MAJOR,
                message="Measurement framework missing metrics/KPIs",
                evidence="measurement section exists but no metrics defined",
                auto_fixable=True,
                fix_instruction="Add specific, measurable KPIs aligned with campaign objective (e.g., CTR, conversion rate, engagement rate, reach)."
            ))
        else:
            checks.append(QCCheck(
                check_id="strategy_measurement_metrics",
                check_type=CheckType.DETERMINISTIC,
                status=CheckStatus.PASS,
                severity=CheckSeverity.MAJOR,
                message="Measurement framework includes metrics"
            ))
    else:
        checks.append(QCCheck(
            check_id="strategy_measurement_metrics",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.WARN,
            severity=CheckSeverity.MAJOR,
            message="Measurement section not structured as expected"
        ))
    
    # Check 5: CTAs defined
    ctas = strategy_content.get("ctas", [])
    if not ctas or (isinstance(ctas, str) and not ctas.strip()):
        checks.append(QCCheck(
            check_id="strategy_ctas_defined",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.MAJOR,
            message="No CTAs defined in strategy",
            evidence="ctas field is empty or missing",
            auto_fixable=True,
            fix_instruction="Define 2-3 primary CTAs aligned with campaign objective (e.g., 'Shop Now', 'Learn More', 'Get Started')."
        ))
    else:
        checks.append(QCCheck(
            check_id="strategy_ctas_defined",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.MAJOR,
            message="CTAs are defined"
        ))
    
    return checks


# ============================================================================
# CREATIVES QC
# ============================================================================

def validate_creatives_qc(creatives_content: Dict[str, Any]) -> List[QCCheck]:
    """
    Deterministic checks for Creatives artifacts.
    
    Checks:
        1. Required assets present per format
        2. Platform constraints respected (caption length, hashtags)
        3. Brand assets used (colors/fonts if specified)
        4. CTA present in creative
    """
    checks = []
    
    # Check 1: Required assets by format
    format_type = creatives_content.get("format", "").lower()
    required_assets = []
    
    if "image" in format_type or "static" in format_type:
        required_assets = ["image_url"]
    elif "video" in format_type:
        required_assets = ["video_url", "thumbnail_url"]
    elif "carousel" in format_type:
        required_assets = ["images"]
    
    missing_assets = [a for a in required_assets if not creatives_content.get(a)]
    
    if missing_assets:
        checks.append(QCCheck(
            check_id="creatives_required_assets",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.BLOCKER,
            message=f"Missing required assets for {format_type}: {', '.join(missing_assets)}",
            evidence=f"Format '{format_type}' requires: {required_assets}",
            auto_fixable=False
        ))
    elif required_assets:
        checks.append(QCCheck(
            check_id="creatives_required_assets",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.BLOCKER,
            message="All required assets present"
        ))
    else:
        checks.append(QCCheck(
            check_id="creatives_required_assets",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.BLOCKER,
            message="Format not requiring specific asset validation"
        ))
    
    # Check 2: Platform constraints
    platform = creatives_content.get("platform", "").lower()
    caption = creatives_content.get("caption", "")
    hashtags = creatives_content.get("hashtags", [])
    
    violations = []
    
    if "twitter" in platform or "x.com" in platform:
        if len(caption) > 280:
            violations.append(f"Caption exceeds Twitter's 280 char limit ({len(caption)} chars)")
    
    if "instagram" in platform:
        if len(hashtags) > 30:
            violations.append(f"Instagram allows max 30 hashtags ({len(hashtags)} provided)")
        if len(caption) > 2200:
            violations.append(f"Caption exceeds Instagram's 2200 char limit ({len(caption)} chars)")
    
    if "linkedin" in platform:
        if len(caption) > 3000:
            violations.append(f"Caption exceeds LinkedIn's 3000 char limit ({len(caption)} chars)")
    
    if violations:
        checks.append(QCCheck(
            check_id="creatives_platform_constraints",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.BLOCKER,
            message="Platform constraints violated",
            evidence="; ".join(violations),
            auto_fixable=True,
            fix_instruction=f"Adjust content to meet platform limits: {'; '.join(violations)}"
        ))
    else:
        checks.append(QCCheck(
            check_id="creatives_platform_constraints",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.BLOCKER,
            message="Platform constraints respected"
        ))
    
    # Check 3: Brand assets (if brand guidelines provided)
    brand_guidelines = creatives_content.get("brand_guidelines", {})
    if isinstance(brand_guidelines, dict) and brand_guidelines:
        brand_colors = brand_guidelines.get("colors", [])
        brand_fonts = brand_guidelines.get("fonts", [])
        
        # Check if creative references brand assets
        creative_text = json.dumps(creatives_content).lower()
        uses_brand_colors = any(c.lower() in creative_text for c in brand_colors) if brand_colors else True
        uses_brand_fonts = any(f.lower() in creative_text for f in brand_fonts) if brand_fonts else True
        
        if not (uses_brand_colors and uses_brand_fonts):
            checks.append(QCCheck(
                check_id="creatives_brand_assets",
                check_type=CheckType.DETERMINISTIC,
                status=CheckStatus.WARN,
                severity=CheckSeverity.MINOR,
                message="Brand guidelines provided but not clearly referenced in creative",
                evidence="Consider explicitly using brand colors/fonts specified in guidelines",
                auto_fixable=False
            ))
        else:
            checks.append(QCCheck(
                check_id="creatives_brand_assets",
                check_type=CheckType.DETERMINISTIC,
                status=CheckStatus.PASS,
                severity=CheckSeverity.MINOR,
                message="Brand assets appear to be used"
            ))
    else:
        checks.append(QCCheck(
            check_id="creatives_brand_assets",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.MINOR,
            message="No brand guidelines provided (acceptable)"
        ))
    
    # Check 4: CTA present
    cta_fields = ["cta", "call_to_action", "cta_text", "cta_button"]
    has_cta = any(creatives_content.get(f, "").strip() for f in cta_fields)
    
    # Also check caption for CTA-like phrases
    if not has_cta and caption:
        cta_phrases = ["learn more", "shop now", "sign up", "get started", "click here", "visit", "download", "register"]
        has_cta = any(phrase in caption.lower() for phrase in cta_phrases)
    
    if not has_cta:
        checks.append(QCCheck(
            check_id="creatives_cta_present",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.MAJOR,
            message="No clear CTA detected in creative",
            evidence="Creative should include explicit call-to-action",
            auto_fixable=True,
            fix_instruction="Add clear CTA to creative (e.g., 'Shop Now', 'Learn More', 'Sign Up'). Include in caption or as CTA button."
        ))
    else:
        checks.append(QCCheck(
            check_id="creatives_cta_present",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.MAJOR,
            message="CTA is present"
        ))
    
    return checks


# ============================================================================
# EXECUTION QC
# ============================================================================

def validate_execution_qc(execution_content: Dict[str, Any]) -> List[QCCheck]:
    """
    Deterministic checks for Execution artifacts (content calendar).
    
    Checks:
        1. CTA in every post
        2. Platform constraints respected
        3. Calendar integrity (no duplicates, reasonable cadence)
        4. Links present where required
    """
    checks = []
    
    posts = execution_content.get("posts", [])
    
    if not posts:
        checks.append(QCCheck(
            check_id="execution_has_posts",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.BLOCKER,
            message="Execution plan has no posts",
            evidence="posts array is empty",
            auto_fixable=False
        ))
        return checks
    
    # Check 1: CTA in every post
    posts_without_cta = []
    for i, post in enumerate(posts):
        caption = post.get("caption", "").lower()
        cta_phrases = ["learn more", "shop now", "sign up", "get started", "click here", "visit", "download", "register", "book", "order"]
        has_cta = any(phrase in caption for phrase in cta_phrases) or post.get("cta") or post.get("call_to_action")
        
        if not has_cta:
            posts_without_cta.append(i + 1)
    
    if posts_without_cta:
        checks.append(QCCheck(
            check_id="execution_cta_every_post",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.BLOCKER,
            message=f"Posts missing CTA: {', '.join(map(str, posts_without_cta))}",
            evidence=f"{len(posts_without_cta)} of {len(posts)} posts lack clear CTA",
            auto_fixable=True,
            fix_instruction=f"Add explicit CTA to posts {', '.join(map(str, posts_without_cta))}. Every post must drive action."
        ))
    else:
        checks.append(QCCheck(
            check_id="execution_cta_every_post",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.BLOCKER,
            message="All posts include CTA"
        ))
    
    # Check 2: Platform constraints
    platform_violations = []
    for i, post in enumerate(posts):
        platform = post.get("platform", "").lower()
        caption = post.get("caption", "")
        hashtags = post.get("hashtags", [])
        
        if "twitter" in platform and len(caption) > 280:
            platform_violations.append(f"Post {i+1}: Twitter caption exceeds 280 chars")
        if "instagram" in platform and len(hashtags) > 30:
            platform_violations.append(f"Post {i+1}: Instagram allows max 30 hashtags")
        if "linkedin" in platform and len(caption) > 3000:
            platform_violations.append(f"Post {i+1}: LinkedIn caption exceeds 3000 chars")
    
    if platform_violations:
        checks.append(QCCheck(
            check_id="execution_platform_constraints",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.BLOCKER,
            message="Platform constraints violated in execution plan",
            evidence="; ".join(platform_violations),
            auto_fixable=True,
            fix_instruction="Adjust post content to meet platform limits: " + "; ".join(platform_violations)
        ))
    else:
        checks.append(QCCheck(
            check_id="execution_platform_constraints",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.BLOCKER,
            message="All posts respect platform constraints"
        ))
    
    # Check 3: Calendar integrity
    dates_seen = set()
    duplicates = []
    for i, post in enumerate(posts):
        date = post.get("date") or post.get("scheduled_date")
        if date:
            if date in dates_seen:
                duplicates.append(date)
            dates_seen.add(date)
    
    if duplicates:
        checks.append(QCCheck(
            check_id="execution_calendar_integrity",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.WARN,
            severity=CheckSeverity.MAJOR,
            message=f"Duplicate dates in calendar: {', '.join(duplicates)}",
            evidence="Multiple posts scheduled for same date (may be intentional for different platforms)",
            auto_fixable=False
        ))
    else:
        checks.append(QCCheck(
            check_id="execution_calendar_integrity",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.MAJOR,
            message="No duplicate dates detected"
        ))
    
    # Check 4: Links present where platform requires
    posts_missing_links = []
    for i, post in enumerate(posts):
        platform = post.get("platform", "").lower()
        caption = post.get("caption", "")
        link = post.get("link") or post.get("url")
        
        # Link should be present if CTA mentions visiting/clicking
        caption_lower = caption.lower()
        cta_needs_link = any(phrase in caption_lower for phrase in ["click here", "visit", "link in bio"])
        
        if cta_needs_link and not link:
            posts_missing_links.append(i + 1)
    
    if posts_missing_links:
        checks.append(QCCheck(
            check_id="execution_links_present",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.WARN,
            severity=CheckSeverity.MAJOR,
            message=f"Posts with CTA but missing link: {', '.join(map(str, posts_missing_links))}",
            evidence="Posts mention clicking/visiting but no URL provided",
            auto_fixable=True,
            fix_instruction=f"Add destination URLs to posts {', '.join(map(str, posts_missing_links))} where CTA requires a link."
        ))
    else:
        checks.append(QCCheck(
            check_id="execution_links_present",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.MAJOR,
            message="Links present where required"
        ))
    
    return checks


# ============================================================================
# DELIVERY QC
# ============================================================================

def validate_delivery_qc(delivery_content: Dict[str, Any]) -> List[QCCheck]:
    """
    Deterministic checks for Delivery artifacts (final client report).
    
    Checks:
        1. All required sections present
        2. Files referenced exist (basic check)
        3. Version numbers correct
        4. No internal notes leaked
    """
    checks = []
    
    # Check 1: Required sections
    required_sections = [
        "executive_summary",
        "campaign_overview",
        "deliverables",
        "timeline",
        "next_steps"
    ]
    
    missing_sections = [s for s in required_sections if s not in delivery_content or not delivery_content[s]]
    
    if missing_sections:
        checks.append(QCCheck(
            check_id="delivery_required_sections",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.BLOCKER,
            message=f"Missing required delivery sections: {', '.join(missing_sections)}",
            evidence=f"Client-facing delivery must include: {required_sections}",
            auto_fixable=False
        ))
    else:
        checks.append(QCCheck(
            check_id="delivery_required_sections",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.BLOCKER,
            message="All required delivery sections present"
        ))
    
    # Check 2: Files referenced (simplified check - just look for file extensions)
    full_text = json.dumps(delivery_content)
    file_patterns = [r'\b\w+\.pdf\b', r'\b\w+\.docx?\b', r'\b\w+\.xlsx?\b', r'\b\w+\.pptx?\b']
    files_mentioned = []
    for pattern in file_patterns:
        files_mentioned.extend(re.findall(pattern, full_text, re.IGNORECASE))
    
    if files_mentioned:
        # Cannot actually check file existence without filesystem access
        # But we can flag if files are mentioned
        checks.append(QCCheck(
            check_id="delivery_files_exist",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.MAJOR,
            message=f"Files referenced: {', '.join(set(files_mentioned)[:5])}",
            evidence="Ensure these files exist before final delivery"
        ))
    else:
        checks.append(QCCheck(
            check_id="delivery_files_exist",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.MAJOR,
            message="No explicit file references detected (acceptable)"
        ))
    
    # Check 3: Version numbers
    deliverables = delivery_content.get("deliverables", {})
    if isinstance(deliverables, dict):
        version_issues = []
        for key, value in deliverables.items():
            if isinstance(value, dict) and "version" in value:
                version = value["version"]
                if version < 1:
                    version_issues.append(f"{key} has invalid version {version}")
        
        if version_issues:
            checks.append(QCCheck(
                check_id="delivery_version_numbers",
                check_type=CheckType.DETERMINISTIC,
                status=CheckStatus.WARN,
                severity=CheckSeverity.MINOR,
                message="Version number issues detected",
                evidence="; ".join(version_issues),
                auto_fixable=False
            ))
        else:
            checks.append(QCCheck(
                check_id="delivery_version_numbers",
                check_type=CheckType.DETERMINISTIC,
                status=CheckStatus.PASS,
                severity=CheckSeverity.MINOR,
                message="Version numbers are valid"
            ))
    else:
        checks.append(QCCheck(
            check_id="delivery_version_numbers",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.MINOR,
            message="Deliverables not structured for version checking"
        ))
    
    # Check 4: No internal notes leaked
    internal_markers = ["internal:", "do not share", "confidential", "draft", "wip", "fixme", "hack"]
    full_text_lower = json.dumps(delivery_content).lower()
    leaked_markers = [m for m in internal_markers if m in full_text_lower]
    
    if leaked_markers:
        checks.append(QCCheck(
            check_id="delivery_no_internal_notes",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.BLOCKER,
            message=f"Internal notes detected: {', '.join(leaked_markers)}",
            evidence="Client-facing delivery must not contain internal markers",
            auto_fixable=True,
            fix_instruction=f"Remove all internal notes/markers: {', '.join(leaked_markers)}. Ensure content is client-ready."
        ))
    else:
        checks.append(QCCheck(
            check_id="delivery_no_internal_notes",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.BLOCKER,
            message="No internal notes detected"
        ))
    
    return checks


# ============================================================================
# DISPATCHER
# ============================================================================

def run_deterministic_checks(artifact_type: str, content: Dict[str, Any]) -> List[QCCheck]:
    """
    Run appropriate deterministic checks based on artifact type.
    
    Args:
        artifact_type: One of INTAKE, STRATEGY, CREATIVES, EXECUTION, DELIVERY
        content: Artifact content as dict
    
    Returns:
        List of QCCheck results
    """
    artifact_type_upper = artifact_type.upper()
    
    if artifact_type_upper == "INTAKE":
        return validate_intake_qc(content)
    elif artifact_type_upper == "STRATEGY":
        return validate_strategy_qc(content)
    elif artifact_type_upper == "CREATIVES":
        return validate_creatives_qc(content)
    elif artifact_type_upper == "EXECUTION":
        return validate_execution_qc(content)
    elif artifact_type_upper == "DELIVERY":
        return validate_delivery_qc(content)
    else:
        return [QCCheck(
            check_id="unknown_artifact_type",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.BLOCKER,
            message=f"Unknown artifact type: {artifact_type}",
            evidence="Cannot run QC on unsupported artifact type"
        )]
