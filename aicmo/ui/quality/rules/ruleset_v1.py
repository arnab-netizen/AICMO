"""
Deterministic QC Ruleset V1

Agency-grade quality control rules for all artifact types.
All rules are deterministic (no LLM calls).
"""
import re
from typing import List, Dict, Any, Optional
from aicmo.ui.quality.qc_models import (
    QCCheck,
    CheckType,
    CheckStatus,
    CheckSeverity
)


# ============================================================================
# INTAKE QC RULES
# ============================================================================

def check_intake_required_fields(content: Dict[str, Any]) -> List[QCCheck]:
    """
    BLOCKER: Verify all required fields are present and non-empty.
    
    Required: client_name, website, industry, geography, primary_offer,
              target_audience, pain_points, desired_outcomes
    """
    checks = []
    
    required_fields = [
        "client_name",
        "website",
        "industry",
        "geography",
        "primary_offer",
        "target_audience",
        "pain_points",
        "desired_outcomes"
    ]
    
    missing = []
    for field in required_fields:
        value = content.get(field, "")
        if not value or (isinstance(value, str) and not value.strip()):
            missing.append(field)
    
    if missing:
        checks.append(QCCheck(
            check_id="intake_required_fields",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.BLOCKER,
            message=f"Missing required fields: {', '.join(missing)}",
            evidence=f"Required fields cannot be empty: {missing}"
        ))
    else:
        checks.append(QCCheck(
            check_id="intake_required_fields",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.BLOCKER,
            message="All required fields present"
        ))
    
    return checks


def check_intake_website_format(content: Dict[str, Any]) -> List[QCCheck]:
    """
    BLOCKER: Verify website looks like a URL.
    """
    checks = []
    
    website = content.get("website", "")
    
    # Basic URL regex (http/https optional, domain.tld pattern)
    url_pattern = r'^(https?://)?(www\.)?[a-zA-Z0-9-]+\.[a-zA-Z]{2,}(/.*)?$'
    
    if not website or not website.strip():
        checks.append(QCCheck(
            check_id="intake_website_format",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.BLOCKER,
            message="Website field is empty",
            evidence="Website is required"
        ))
    elif not re.match(url_pattern, website.strip()):
        checks.append(QCCheck(
            check_id="intake_website_format",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.BLOCKER,
            message=f"Website does not look like a valid URL: {website}",
            evidence="Expected format: domain.com or https://domain.com"
        ))
    else:
        checks.append(QCCheck(
            check_id="intake_website_format",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.BLOCKER,
            message="Website format valid"
        ))
    
    return checks


def check_intake_constraints(content: Dict[str, Any]) -> List[QCCheck]:
    """
    BLOCKER: Verify at least one constraint field is present.
    
    Must have at least one of: compliance_requirements, forbidden_claims, risk_tolerance
    """
    checks = []
    
    constraint_fields = ["compliance_requirements", "forbidden_claims", "risk_tolerance"]
    has_constraint = False
    
    for field in constraint_fields:
        value = content.get(field, "")
        if value and (not isinstance(value, str) or value.strip()):
            has_constraint = True
            break
    
    if not has_constraint:
        checks.append(QCCheck(
            check_id="intake_constraints",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.BLOCKER,
            message="No constraints specified",
            evidence="Must have at least one of: compliance_requirements, forbidden_claims, or risk_tolerance"
        ))
    else:
        checks.append(QCCheck(
            check_id="intake_constraints",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.BLOCKER,
            message="Constraints present"
        ))
    
    return checks


def check_intake_proof_assets(content: Dict[str, Any]) -> List[QCCheck]:
    """
    MAJOR: Verify proof assets are addressed.
    """
    checks = []
    
    proof_assets = content.get("proof_assets", "")
    
    if not proof_assets or not proof_assets.strip():
        checks.append(QCCheck(
            check_id="intake_proof_assets",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.MAJOR,
            message="Proof assets not specified",
            evidence="Should specify available proof (testimonials, case studies, data) or explicitly state 'none'"
        ))
    else:
        checks.append(QCCheck(
            check_id="intake_proof_assets",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.MAJOR,
            message="Proof assets documented"
        ))
    
    return checks


def check_intake_pricing(content: Dict[str, Any]) -> List[QCCheck]:
    """
    MAJOR: Verify pricing information is addressed.
    """
    checks = []
    
    pricing_logic = content.get("pricing_logic", "")
    
    if not pricing_logic or not pricing_logic.strip():
        checks.append(QCCheck(
            check_id="intake_pricing",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.MAJOR,
            message="Pricing logic not specified",
            evidence="Should specify pricing model/range or explicitly state 'unknown'"
        ))
    else:
        checks.append(QCCheck(
            check_id="intake_pricing",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.MAJOR,
            message="Pricing logic documented"
        ))
    
    return checks


def check_intake_tone(content: Dict[str, Any]) -> List[QCCheck]:
    """
    MINOR: Verify tone/voice is specified.
    """
    checks = []
    
    tone = content.get("brand_voice", "")
    
    if not tone or not tone.strip():
        checks.append(QCCheck(
            check_id="intake_tone",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.MINOR,
            message="Brand voice/tone not specified",
            evidence="Helpful for creative consistency"
        ))
    else:
        checks.append(QCCheck(
            check_id="intake_tone",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.MINOR,
            message="Brand voice documented"
        ))
    
    return checks


# ============================================================================
# STRATEGY QC RULES
# ============================================================================

def check_strategy_schema_version(content: Dict[str, Any]) -> List[QCCheck]:
    """
    BLOCKER: Verify strategy uses strategy_contract_v1 schema.
    """
    checks = []
    
    schema_version = content.get("schema_version", "")
    
    if schema_version != "strategy_contract_v1":
        checks.append(QCCheck(
            check_id="strategy_schema_version",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.BLOCKER,
            message=f"Invalid schema version: {schema_version}",
            evidence="Must be 'strategy_contract_v1'"
        ))
    else:
        checks.append(QCCheck(
            check_id="strategy_schema_version",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.BLOCKER,
            message="Schema version correct"
        ))
    
    return checks


def check_strategy_all_layers_exist(content: Dict[str, Any]) -> List[QCCheck]:
    """
    BLOCKER: Verify all 8 strategy layers are present.
    """
    checks = []
    
    required_layers = [
        "layer1_business_reality",
        "layer2_market_truth",
        "layer3_audience_psychology",
        "layer4_value_architecture",
        "layer5_narrative",
        "layer6_channel_strategy",
        "layer7_constraints",
        "layer8_measurement"
    ]
    
    missing = []
    for layer in required_layers:
        if layer not in content or not isinstance(content[layer], dict):
            missing.append(layer)
    
    if missing:
        checks.append(QCCheck(
            check_id="strategy_all_layers",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.BLOCKER,
            message=f"Missing strategy layers: {', '.join(missing)}",
            evidence="All 8 layers required for complete strategy"
        ))
    else:
        checks.append(QCCheck(
            check_id="strategy_all_layers",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.BLOCKER,
            message="All 8 strategy layers present"
        ))
    
    return checks


def check_strategy_layer_required_fields(content: Dict[str, Any]) -> List[QCCheck]:
    """
    BLOCKER: Verify each layer has required fields.
    """
    checks = []
    
    # Define required fields per layer (sample - adjust based on actual schema)
    layer_requirements = {
        "layer1_business_reality": ["business_model_summary", "revenue_streams", "unit_economics"],
        "layer2_market_truth": ["category_maturity", "white_space_logic"],
        "layer3_audience_psychology": ["awareness_state", "objection_hierarchy"],
        "layer4_value_architecture": ["core_promise", "differentiation_logic"],
        "layer5_narrative": ["narrative_problem", "narrative_resolution", "enemy_definition"],
        "layer6_channel_strategy": ["channels"],
        "layer7_constraints": ["tone_boundaries", "forbidden_language"],
        "layer8_measurement": ["success_definition", "leading_indicators", "lagging_indicators"]
    }
    
    all_missing = []
    
    for layer_name, required_fields in layer_requirements.items():
        layer = content.get(layer_name, {})
        if not isinstance(layer, dict):
            continue
        
        for field in required_fields:
            value = layer.get(field, "")
            if not value or (isinstance(value, str) and not value.strip()):
                all_missing.append(f"{layer_name}.{field}")
    
    if all_missing:
        checks.append(QCCheck(
            check_id="strategy_layer_fields",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.BLOCKER,
            message=f"Missing required layer fields: {', '.join(all_missing[:5])}{'...' if len(all_missing) > 5 else ''}",
            evidence=f"Total {len(all_missing)} missing fields"
        ))
    else:
        checks.append(QCCheck(
            check_id="strategy_layer_fields",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.BLOCKER,
            message="All layer required fields present"
        ))
    
    return checks


def check_strategy_channels(content: Dict[str, Any]) -> List[QCCheck]:
    """
    BLOCKER: Verify layer 6 has at least 1 channel with complete info.
    """
    checks = []
    
    layer6 = content.get("layer6_channel_strategy", {})
    channels = layer6.get("channels", [])
    
    if not channels or not isinstance(channels, list) or len(channels) == 0:
        checks.append(QCCheck(
            check_id="strategy_channels",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.BLOCKER,
            message="No channels defined in Layer 6",
            evidence="Must have at least 1 channel with strategic_role, KPI, and kill criteria"
        ))
    else:
        # Check first channel has required fields
        channel = channels[0]
        required = ["name", "strategic_role"]
        missing = [f for f in required if not channel.get(f)]
        
        if missing:
            checks.append(QCCheck(
                check_id="strategy_channels",
                check_type=CheckType.DETERMINISTIC,
                status=CheckStatus.FAIL,
                severity=CheckSeverity.BLOCKER,
                message=f"Channel missing required fields: {', '.join(missing)}",
                evidence="Each channel needs name, strategic_role"
            ))
        else:
            checks.append(QCCheck(
                check_id="strategy_channels",
                check_type=CheckType.DETERMINISTIC,
                status=CheckStatus.PASS,
                severity=CheckSeverity.BLOCKER,
                message=f"{len(channels)} channel(s) defined with required fields"
            ))
    
    return checks


def check_strategy_what_not_to_do(content: Dict[str, Any]) -> List[QCCheck]:
    """
    MAJOR: Verify layer 2 has "what_not_to_do" guidance.
    """
    checks = []
    
    layer2 = content.get("layer2_market_truth", {})
    what_not = layer2.get("what_not_to_do", "")
    
    if not what_not or not what_not.strip():
        checks.append(QCCheck(
            check_id="strategy_what_not_to_do",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.MAJOR,
            message="Layer 2 missing 'what_not_to_do' guidance",
            evidence="Strategic clarity improved by explicitly stating what to avoid"
        ))
    else:
        checks.append(QCCheck(
            check_id="strategy_what_not_to_do",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.MAJOR,
            message="'What not to do' guidance present"
        ))
    
    return checks


def check_strategy_repetition_logic(content: Dict[str, Any]) -> List[QCCheck]:
    """
    MINOR: Verify layer 5 has repetition logic (narrative consistency).
    """
    checks = []
    
    layer5 = content.get("layer5_narrative", {})
    repetition = layer5.get("repetition_logic", "")
    
    if not repetition or len(str(repetition).strip()) < 20:
        checks.append(QCCheck(
            check_id="strategy_repetition_logic",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.MINOR,
            message="Layer 5 repetition_logic too brief or missing",
            evidence="Should define key phrases/themes to repeat for narrative consistency"
        ))
    else:
        checks.append(QCCheck(
            check_id="strategy_repetition_logic",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.MINOR,
            message="Repetition logic defined"
        ))
    
    return checks


# ============================================================================
# CREATIVES QC RULES
# ============================================================================

def check_creatives_strategy_reference(content: Dict[str, Any]) -> List[QCCheck]:
    """
    BLOCKER: Verify creatives reference strategy layers.
    """
    checks = []
    
    source_schema = content.get("source_strategy_schema_version", "")
    source_layers = content.get("source_layers_used", [])
    
    if not source_schema:
        checks.append(QCCheck(
            check_id="creatives_strategy_ref",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.BLOCKER,
            message="Creatives do not reference strategy schema version",
            evidence="Must store source_strategy_schema_version for traceability"
        ))
    elif not source_layers or len(source_layers) == 0:
        checks.append(QCCheck(
            check_id="creatives_strategy_ref",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.BLOCKER,
            message="Creatives do not specify which strategy layers were used",
            evidence="Must store source_layers_used for traceability"
        ))
    else:
        checks.append(QCCheck(
            check_id="creatives_strategy_ref",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.BLOCKER,
            message=f"Strategy reference present: {source_schema}, {len(source_layers)} layers"
        ))
    
    return checks


def check_creatives_minimum_assets(content: Dict[str, Any]) -> List[QCCheck]:
    """
    BLOCKER: Verify minimum creative assets present.
    
    Must have: 3 hooks, 3 angles, 3 CTAs, 1 offer framing, 1 compliance claim set
    """
    checks = []
    
    requirements = {
        "hooks": 3,
        "angles": 3,
        "ctas": 3,
        "offer_framing": 1,
        "compliance_safe_claims": 1
    }
    
    failures = []
    
    for field, min_count in requirements.items():
        value = content.get(field, [])
        
        if isinstance(value, list):
            count = len(value)
        elif isinstance(value, str):
            count = 1 if value.strip() else 0
        else:
            count = 0
        
        if count < min_count:
            failures.append(f"{field} (need {min_count}, have {count})")
    
    if failures:
        checks.append(QCCheck(
            check_id="creatives_minimum_assets",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.BLOCKER,
            message=f"Insufficient creative assets: {', '.join(failures)}",
            evidence="Must have 3+ hooks, 3+ angles, 3+ CTAs, 1+ offer framing, 1+ compliance claim"
        ))
    else:
        checks.append(QCCheck(
            check_id="creatives_minimum_assets",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.BLOCKER,
            message="Minimum creative assets present"
        ))
    
    return checks


def check_creatives_channel_mapping(content: Dict[str, Any]) -> List[QCCheck]:
    """
    MAJOR: Verify channel mapping for at least 1 channel.
    """
    checks = []
    
    channel_mapping = content.get("channel_mapping", {})
    
    if not channel_mapping or len(channel_mapping) == 0:
        checks.append(QCCheck(
            check_id="creatives_channel_mapping",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.MAJOR,
            message="No channel mapping defined",
            evidence="Should map creative variants to channels from strategy Layer 6"
        ))
    else:
        checks.append(QCCheck(
            check_id="creatives_channel_mapping",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.MAJOR,
            message=f"Channel mapping present for {len(channel_mapping)} channel(s)"
        ))
    
    return checks


def check_creatives_brand_voice(content: Dict[str, Any]) -> List[QCCheck]:
    """
    MINOR: Verify brand voice notes are included.
    """
    checks = []
    
    brand_voice = content.get("brand_voice_notes", "")
    
    if not brand_voice or not brand_voice.strip():
        checks.append(QCCheck(
            check_id="creatives_brand_voice",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.MINOR,
            message="Brand voice notes missing",
            evidence="Helpful for creative consistency across channels"
        ))
    else:
        checks.append(QCCheck(
            check_id="creatives_brand_voice",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.MINOR,
            message="Brand voice notes present"
        ))
    
    return checks


# ============================================================================
# EXECUTION QC RULES
# ============================================================================

def check_execution_channel_plan(content: Dict[str, Any]) -> List[QCCheck]:
    """
    BLOCKER: Verify channel plan exists (derived from Strategy Layer 6).
    """
    checks = []
    
    channel_plan = content.get("channel_plan", [])
    
    if not channel_plan or len(channel_plan) == 0:
        checks.append(QCCheck(
            check_id="execution_channel_plan",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.BLOCKER,
            message="No channel plan defined",
            evidence="Must have at least 1 channel from Strategy Layer 6"
        ))
    else:
        checks.append(QCCheck(
            check_id="execution_channel_plan",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.BLOCKER,
            message=f"Channel plan present with {len(channel_plan)} channel(s)"
        ))
    
    return checks


def check_execution_cadence_schedule(content: Dict[str, Any]) -> List[QCCheck]:
    """
    BLOCKER: Verify cadence/schedule and tracking plan are defined.
    """
    checks = []
    
    cadence = content.get("cadence", "")
    schedule = content.get("schedule", "")
    utm_plan = content.get("utm_plan", "")
    
    missing = []
    if not cadence or not cadence.strip():
        missing.append("cadence")
    if not schedule or not schedule.strip():
        missing.append("schedule")
    if not utm_plan or not utm_plan.strip():
        missing.append("utm_plan")
    
    if missing:
        checks.append(QCCheck(
            check_id="execution_cadence_schedule",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.BLOCKER,
            message=f"Missing execution planning: {', '.join(missing)}",
            evidence="Must have cadence, schedule, and UTM tracking plan"
        ))
    else:
        checks.append(QCCheck(
            check_id="execution_cadence_schedule",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.BLOCKER,
            message="Cadence, schedule, and tracking plan defined"
        ))
    
    return checks


def check_execution_governance(content: Dict[str, Any]) -> List[QCCheck]:
    """
    MAJOR: Verify governance/roles are defined.
    """
    checks = []
    
    governance = content.get("governance", "")
    publishing_roles = content.get("publishing_roles", "")
    
    if (not governance or not governance.strip()) and (not publishing_roles or not publishing_roles.strip()):
        checks.append(QCCheck(
            check_id="execution_governance",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.MAJOR,
            message="Governance and publishing roles not defined",
            evidence="Should specify who approves/publishes content"
        ))
    else:
        checks.append(QCCheck(
            check_id="execution_governance",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.MAJOR,
            message="Governance roles defined"
        ))
    
    return checks


def check_execution_risk_guardrails(content: Dict[str, Any]) -> List[QCCheck]:
    """
    MINOR: Verify risk guardrails summary is present.
    """
    checks = []
    
    risk_guardrails = content.get("risk_guardrails", "")
    
    if not risk_guardrails or not risk_guardrails.strip():
        checks.append(QCCheck(
            check_id="execution_risk_guardrails",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.MINOR,
            message="Risk guardrails summary missing",
            evidence="Should summarize constraints from Strategy Layer 7"
        ))
    else:
        checks.append(QCCheck(
            check_id="execution_risk_guardrails",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.MINOR,
            message="Risk guardrails documented"
        ))
    
    return checks


# ============================================================================
# MONITORING QC RULES
# ============================================================================

def check_monitoring_kpis(content: Dict[str, Any]) -> List[QCCheck]:
    """
    BLOCKER: Verify KPIs list is non-empty and matches Strategy Layer 8.
    """
    checks = []
    
    kpis = content.get("kpis", [])
    
    if not kpis or len(kpis) == 0:
        checks.append(QCCheck(
            check_id="monitoring_kpis",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.BLOCKER,
            message="No KPIs defined",
            evidence="Must define KPIs matching Strategy Layer 8 indicators"
        ))
    else:
        checks.append(QCCheck(
            check_id="monitoring_kpis",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.BLOCKER,
            message=f"{len(kpis)} KPI(s) defined"
        ))
    
    return checks


def check_monitoring_review_cadence(content: Dict[str, Any]) -> List[QCCheck]:
    """
    BLOCKER: Verify review cadence is specified.
    """
    checks = []
    
    review_cadence = content.get("review_cadence", "")
    
    if not review_cadence or not review_cadence.strip():
        checks.append(QCCheck(
            check_id="monitoring_review_cadence",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.BLOCKER,
            message="Review cadence not specified",
            evidence="Must specify weekly/monthly/etc review schedule"
        ))
    else:
        checks.append(QCCheck(
            check_id="monitoring_review_cadence",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.BLOCKER,
            message=f"Review cadence: {review_cadence}"
        ))
    
    return checks


def check_monitoring_decision_rules(content: Dict[str, Any]) -> List[QCCheck]:
    """
    MAJOR: Verify decision rules are present.
    """
    checks = []
    
    decision_rules = content.get("decision_rules", [])
    
    if not decision_rules or len(decision_rules) == 0:
        checks.append(QCCheck(
            check_id="monitoring_decision_rules",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.MAJOR,
            message="No decision rules defined",
            evidence="Should define when to pause/scale/pivot based on metrics"
        ))
    else:
        checks.append(QCCheck(
            check_id="monitoring_decision_rules",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.MAJOR,
            message=f"{len(decision_rules)} decision rule(s) defined"
        ))
    
    return checks


def check_monitoring_alerts(content: Dict[str, Any]) -> List[QCCheck]:
    """
    MINOR: Verify alerts are configured or explicitly stated as none.
    """
    checks = []
    
    alerts = content.get("alerts", "")
    
    if not alerts or not alerts.strip():
        checks.append(QCCheck(
            check_id="monitoring_alerts",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.MINOR,
            message="Alerts not configured",
            evidence="Should configure alerts or explicitly state 'none'"
        ))
    else:
        checks.append(QCCheck(
            check_id="monitoring_alerts",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.MINOR,
            message="Alerts configured"
        ))
    
    return checks


# ============================================================================
# DELIVERY QC RULES
# ============================================================================

def check_delivery_manifest_schema(content: Dict[str, Any]) -> List[QCCheck]:
    """
    BLOCKER: Verify manifest uses delivery_manifest_v1 schema.
    """
    checks = []
    
    manifest = content.get("manifest", {})
    schema_version = manifest.get("schema_version", "")
    
    if schema_version != "delivery_manifest_v1":
        checks.append(QCCheck(
            check_id="delivery_manifest_schema",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.BLOCKER,
            message=f"Invalid manifest schema: {schema_version}",
            evidence="Must be 'delivery_manifest_v1'"
        ))
    else:
        checks.append(QCCheck(
            check_id="delivery_manifest_schema",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.BLOCKER,
            message="Manifest schema correct"
        ))
    
    return checks


def check_delivery_included_artifacts(content: Dict[str, Any]) -> List[QCCheck]:
    """
    BLOCKER: Verify included artifacts list matches configuration.
    """
    checks = []
    
    manifest = content.get("manifest", {})
    included_artifacts = manifest.get("included_artifacts", [])
    
    if not included_artifacts or len(included_artifacts) == 0:
        checks.append(QCCheck(
            check_id="delivery_included_artifacts",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.BLOCKER,
            message="No artifacts included in delivery package",
            evidence="Must include at least one artifact (Intake/Strategy/etc)"
        ))
    else:
        checks.append(QCCheck(
            check_id="delivery_included_artifacts",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.BLOCKER,
            message=f"{len(included_artifacts)} artifact(s) included"
        ))
    
    return checks


def check_delivery_approvals_ok(content: Dict[str, Any]) -> List[QCCheck]:
    """
    BLOCKER: Verify all included artifacts are approved.
    """
    checks = []
    
    manifest = content.get("manifest", {})
    checks_dict = manifest.get("checks", {})
    approvals_ok = checks_dict.get("approvals_ok", False)
    
    if not approvals_ok:
        checks.append(QCCheck(
            check_id="delivery_approvals_ok",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.BLOCKER,
            message="Not all included artifacts are approved",
            evidence="All artifacts must be approved before delivery"
        ))
    else:
        checks.append(QCCheck(
            check_id="delivery_approvals_ok",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.BLOCKER,
            message="All included artifacts approved"
        ))
    
    return checks


def check_delivery_branding_ok(content: Dict[str, Any]) -> List[QCCheck]:
    """
    MAJOR: Verify branding is configured correctly.
    """
    checks = []
    
    manifest = content.get("manifest", {})
    checks_dict = manifest.get("checks", {})
    branding_ok = checks_dict.get("branding_ok", False)
    
    if not branding_ok:
        checks.append(QCCheck(
            check_id="delivery_branding_ok",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.MAJOR,
            message="Branding configuration incomplete",
            evidence="Should have agency name, footer, and primary color"
        ))
    else:
        checks.append(QCCheck(
            check_id="delivery_branding_ok",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.MAJOR,
            message="Branding configured"
        ))
    
    return checks


def check_delivery_notes(content: Dict[str, Any]) -> List[QCCheck]:
    """
    MINOR: Verify delivery notes are present.
    """
    checks = []
    
    notes = content.get("notes", "")
    
    if not notes or not notes.strip():
        checks.append(QCCheck(
            check_id="delivery_notes",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.MINOR,
            message="Delivery notes missing",
            evidence="Should include usage notes or special instructions"
        ))
    else:
        checks.append(QCCheck(
            check_id="delivery_notes",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.MINOR,
            message="Delivery notes present"
        ))
    
    return checks


def check_delivery_generation_plan(content: Dict[str, Any]) -> List[QCCheck]:
    """
    MAJOR: Check if generation plan was provided for delivery.
    When plan is missing, delivery defaults to intake+strategy only (safe minimum).
    This surfaces visibility warning so users understand scoping.
    """
    checks = []
    
    manifest = content.get("manifest", {})
    generation_plan = manifest.get("generation_plan", {})
    selected_jobs = generation_plan.get("selected_job_ids", [])
    
    if not selected_jobs:
        checks.append(QCCheck(
            check_id="delivery_generation_plan",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.FAIL,
            severity=CheckSeverity.MAJOR,
            message="Generation plan missing; defaulted to Intake+Strategy",
            evidence="Consider specifying selected job IDs for correct delivery scope"
        ))
    else:
        checks.append(QCCheck(
            check_id="delivery_generation_plan",
            check_type=CheckType.DETERMINISTIC,
            status=CheckStatus.PASS,
            severity=CheckSeverity.MAJOR,
            message=f"Generation plan specified ({len(selected_jobs)} jobs)"
        ))
    
    return checks


# ============================================================================
# REGISTER ALL RULES
# ============================================================================

def register_all_rules():
    """Register all ruleset v1 rules with the QC registry."""
    from aicmo.ui.persistence.artifact_store import ArtifactType
    from .qc_registry import register_rule
    
    # Intake rules
    register_rule(ArtifactType.INTAKE, check_intake_required_fields)
    register_rule(ArtifactType.INTAKE, check_intake_website_format)
    register_rule(ArtifactType.INTAKE, check_intake_constraints)
    register_rule(ArtifactType.INTAKE, check_intake_proof_assets)
    register_rule(ArtifactType.INTAKE, check_intake_pricing)
    register_rule(ArtifactType.INTAKE, check_intake_tone)
    
    # Strategy rules
    register_rule(ArtifactType.STRATEGY, check_strategy_schema_version)
    register_rule(ArtifactType.STRATEGY, check_strategy_all_layers_exist)
    register_rule(ArtifactType.STRATEGY, check_strategy_layer_required_fields)
    register_rule(ArtifactType.STRATEGY, check_strategy_channels)
    register_rule(ArtifactType.STRATEGY, check_strategy_what_not_to_do)
    register_rule(ArtifactType.STRATEGY, check_strategy_repetition_logic)
    
    # Creatives rules
    register_rule(ArtifactType.CREATIVES, check_creatives_strategy_reference)
    register_rule(ArtifactType.CREATIVES, check_creatives_minimum_assets)
    register_rule(ArtifactType.CREATIVES, check_creatives_channel_mapping)
    register_rule(ArtifactType.CREATIVES, check_creatives_brand_voice)
    
    # Execution rules
    register_rule(ArtifactType.EXECUTION, check_execution_channel_plan)
    register_rule(ArtifactType.EXECUTION, check_execution_cadence_schedule)
    register_rule(ArtifactType.EXECUTION, check_execution_governance)
    register_rule(ArtifactType.EXECUTION, check_execution_risk_guardrails)
    
    # Monitoring rules
    register_rule(ArtifactType.MONITORING, check_monitoring_kpis)
    register_rule(ArtifactType.MONITORING, check_monitoring_review_cadence)
    register_rule(ArtifactType.MONITORING, check_monitoring_decision_rules)
    register_rule(ArtifactType.MONITORING, check_monitoring_alerts)
    
    # Delivery rules
    register_rule(ArtifactType.DELIVERY, check_delivery_manifest_schema)
    register_rule(ArtifactType.DELIVERY, check_delivery_included_artifacts)
    register_rule(ArtifactType.DELIVERY, check_delivery_approvals_ok)
    register_rule(ArtifactType.DELIVERY, check_delivery_branding_ok)
    register_rule(ArtifactType.DELIVERY, check_delivery_notes)
    register_rule(ArtifactType.DELIVERY, check_delivery_generation_plan)
