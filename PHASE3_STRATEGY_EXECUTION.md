# Phase 3 Execution: Strategy Contract Replacement

## CRITICAL: This is the biggest error in the system

**Current State:** Strategy tab has some implementation but NOT the 8-layer contract
**Required State:** Strategy MUST be exactly the 8 layers specified

---

## Step-by-Step Implementation

### Step 1: Locate Current Strategy Tab
- Find `render_strategy_tab()` in operator_v2.py
- Document current schema for comparison

### Step 2: Design New 8-Layer UI Structure
Each layer needs its own expander with specific fields

### Step 3: Replace Strategy Tab Renderer
Complete rewrite of `render_strategy_tab()` with:

**Layer 1: Business Reality Alignment**
```python
with st.expander("📊 Layer 1: Business Reality Alignment", expanded=True):
    business_model_summary = st.text_area("Business Model Summary*", ...)
    revenue_streams = st.text_area("Revenue Streams*", ...)
    unit_economics = st.text_area("Unit Economics (CAC/LTV)*", ...)
    pricing_logic = st.text_area("Pricing Logic*", ...)
    growth_constraint = st.text_input("Primary Growth Constraint*", ...)
    bottleneck = st.selectbox("REAL Bottleneck*", ["Demand", "Awareness", "Trust", "Conversion", "Retention"])
    risk_tolerance = st.select_slider("Risk Tolerance", ["Conservative", "Moderate", "Aggressive"])
    regulatory_constraints = st.text_area("Regulatory/Brand Constraints", ...)
```

**Layer 2: Market & Competitive Truth**
```python
with st.expander("🎯 Layer 2: Market & Competitive Truth"):
    category_maturity = st.selectbox("Category Maturity", ["Emerging", "Growing", "Mature", "Declining"])
    competitive_vectors = st.multiselect("Competitive Vectors", ["Price", "Speed", "Trust", "Brand", "Distribution"])
    white_space_logic = st.text_area("White-Space Logic*", ...)
    what_not_to_do = st.text_area("Explicit: What NOT to Do*", ...)
```

**Layer 3: Audience Decision Psychology**
```python
with st.expander("🧠 Layer 3: Audience Decision Psychology"):
    awareness_state = st.selectbox("Awareness State", ["Unaware", "Problem Aware", "Solution Aware", "Product Aware", "Most Aware"])
    pain_intensity = st.select_slider("Pain Intensity", ["1 - Mild", "2", "3", "4", "5 - Severe"])
    objection_hierarchy = st.text_area("Objection Hierarchy*", ...)
    trust_transfer_mechanism = st.text_area("Trust Transfer Mechanism*", ...)
```

**Layer 4: Value Proposition Architecture**
```python
with st.expander("💎 Layer 4: Value Proposition Architecture"):
    core_promise = st.text_input("Core Promise (single sentence)*", ...)
    proof_stack_social = st.text_area("Proof Stack - Social", ...)
    proof_stack_authority = st.text_area("Proof Stack - Authority", ...)
    proof_stack_mechanism = st.text_area("Proof Stack - Mechanism", ...)
    sacrifice_framing = st.text_area("Sacrifice Framing*", ...)
    differentiation_logic = st.radio("Differentiation Logic", ["Structural", "Cosmetic"])
```

**Layer 5: Strategic Narrative**
```python
with st.expander("📖 Layer 5: Strategic Narrative"):
    narrative_problem = st.text_area("Problem*", ...)
    narrative_tension = st.text_area("Tension*", ...)
    narrative_resolution = st.text_area("Resolution*", ...)
    enemy_definition = st.text_area("Enemy Definition (belief/system, not competitor)*", ...)
    repetition_logic = st.text_area("Repetition Logic*", ...)
```

**Layer 6: Channel Strategy**
```python
with st.expander("📡 Layer 6: Channel Strategy"):
    st.write("Define strategy for each channel:")
    
    # Dynamic channel inputs (could be N channels)
    num_channels = st.number_input("Number of Channels", 1, 10, 3)
    
    channels = []
    for i in range(num_channels):
        with st.container():
            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                channel_name = st.text_input(f"Channel {i+1} Name", key=f"ch_name_{i}")
                strategic_role = st.selectbox(f"Strategic Role", ["Discovery", "Trust", "Conversion", "Retention"], key=f"ch_role_{i}")
            with col2:
                allowed_content_types = st.text_input(f"Allowed Content Types", key=f"ch_content_{i}")
                kpi = st.text_input(f"KPI", key=f"ch_kpi_{i}")
            kill_criteria = st.text_input(f"Kill Criteria", key=f"ch_kill_{i}")
            
            if channel_name:
                channels.append({
                    "name": channel_name,
                    "strategic_role": strategic_role,
                    "allowed_content_types": allowed_content_types,
                    "kpi": kpi,
                    "kill_criteria": kill_criteria
                })
```

**Layer 7: Execution Constraints**
```python
with st.expander("⚖️ Layer 7: Execution Constraints"):
    tone_boundaries = st.text_area("Tone Boundaries*", ...)
    forbidden_language = st.text_area("Forbidden Language*", ...)
    claim_boundaries = st.text_area("Claim Boundaries*", ...)
    visual_constraints = st.text_area("Visual Constraints", ...)
    compliance_rules = st.text_area("Compliance Rules*", ...)
```

**Layer 8: Measurement & Learning Loop**
```python
with st.expander("📈 Layer 8: Measurement & Learning Loop"):
    success_definition = st.text_area("Success Definition*", ...)
    leading_indicators = st.text_area("Leading Indicators*", ...)
    lagging_indicators = st.text_area("Lagging Indicators*", ...)
    review_cadence = st.selectbox("Review Cadence", ["Daily", "Weekly", "Bi-weekly", "Monthly"])
    decision_rules = st.text_area("Decision Rules (If X → do Y)*", ...)
```

### Step 4: Update Validation Function

In `artifact_store.py`, update `validate_strategy_contract()`:

```python
def validate_strategy_contract(content: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
    """
    Validate 8-layer strategy contract schema.
    
    Returns: (ok: bool, errors: List[str], warnings: List[str])
    """
    errors = []
    warnings = []
    
    # Layer 1: Business Reality Alignment
    if "layer1_business_reality" not in content:
        errors.append("Missing Layer 1: Business Reality Alignment")
    else:
        l1 = content["layer1_business_reality"]
        required_l1 = ["business_model_summary", "revenue_streams", "unit_economics", 
                       "pricing_logic", "growth_constraint", "bottleneck"]
        for field in required_l1:
            if not l1.get(field):
                errors.append(f"Layer 1 missing required field: {field}")
    
    # Layer 2: Market & Competitive Truth
    if "layer2_market_truth" not in content:
        errors.append("Missing Layer 2: Market & Competitive Truth")
    else:
        l2 = content["layer2_market_truth"]
        required_l2 = ["category_maturity", "white_space_logic", "what_not_to_do"]
        for field in required_l2:
            if not l2.get(field):
                errors.append(f"Layer 2 missing required field: {field}")
    
    # Layer 3: Audience Decision Psychology
    if "layer3_audience_psychology" not in content:
        errors.append("Missing Layer 3: Audience Decision Psychology")
    else:
        l3 = content["layer3_audience_psychology"]
        required_l3 = ["awareness_state", "objection_hierarchy", "trust_transfer_mechanism"]
        for field in required_l3:
            if not l3.get(field):
                errors.append(f"Layer 3 missing required field: {field}")
    
    # Layer 4: Value Proposition Architecture
    if "layer4_value_architecture" not in content:
        errors.append("Missing Layer 4: Value Proposition Architecture")
    else:
        l4 = content["layer4_value_architecture"]
        required_l4 = ["core_promise", "sacrifice_framing", "differentiation_logic"]
        for field in required_l4:
            if not l4.get(field):
                errors.append(f"Layer 4 missing required field: {field}")
    
    # Layer 5: Strategic Narrative
    if "layer5_narrative" not in content:
        errors.append("Missing Layer 5: Strategic Narrative")
    else:
        l5 = content["layer5_narrative"]
        required_l5 = ["narrative_problem", "narrative_tension", "narrative_resolution", 
                       "enemy_definition", "repetition_logic"]
        for field in required_l5:
            if not l5.get(field):
                errors.append(f"Layer 5 missing required field: {field}")
    
    # Layer 6: Channel Strategy
    if "layer6_channel_strategy" not in content:
        errors.append("Missing Layer 6: Channel Strategy")
    else:
        l6 = content["layer6_channel_strategy"]
        if "channels" not in l6 or not l6["channels"]:
            errors.append("Layer 6 must define at least one channel")
        else:
            for idx, channel in enumerate(l6["channels"]):
                if not channel.get("name"):
                    errors.append(f"Layer 6 channel {idx+1} missing name")
                if not channel.get("strategic_role"):
                    errors.append(f"Layer 6 channel {idx+1} missing strategic_role")
    
    # Layer 7: Execution Constraints
    if "layer7_constraints" not in content:
        errors.append("Missing Layer 7: Execution Constraints")
    else:
        l7 = content["layer7_constraints"]
        required_l7 = ["tone_boundaries", "forbidden_language", "claim_boundaries", "compliance_rules"]
        for field in required_l7:
            if not l7.get(field):
                errors.append(f"Layer 7 missing required field: {field}")
    
    # Layer 8: Measurement & Learning Loop
    if "layer8_measurement" not in content:
        errors.append("Missing Layer 8: Measurement & Learning Loop")
    else:
        l8 = content["layer8_measurement"]
        required_l8 = ["success_definition", "leading_indicators", "lagging_indicators", 
                       "review_cadence", "decision_rules"]
        for field in required_l8:
            if not l8.get(field):
                errors.append(f"Layer 8 missing required field: {field}")
    
    return (len(errors) == 0, errors, warnings)
```

### Step 5: Save Draft Button

```python
if st.button("💾 Save Strategy Draft", use_container_width=True, type="primary"):
    strategy_content = {
        "layer1_business_reality": {
            "business_model_summary": business_model_summary,
            "revenue_streams": revenue_streams,
            "unit_economics": unit_economics,
            "pricing_logic": pricing_logic,
            "growth_constraint": growth_constraint,
            "bottleneck": bottleneck,
            "risk_tolerance": risk_tolerance,
            "regulatory_constraints": regulatory_constraints
        },
        "layer2_market_truth": {
            "category_maturity": category_maturity,
            "competitive_vectors": competitive_vectors,
            "white_space_logic": white_space_logic,
            "what_not_to_do": what_not_to_do
        },
        "layer3_audience_psychology": {
            "awareness_state": awareness_state,
            "pain_intensity": pain_intensity,
            "objection_hierarchy": objection_hierarchy,
            "trust_transfer_mechanism": trust_transfer_mechanism
        },
        "layer4_value_architecture": {
            "core_promise": core_promise,
            "proof_stack": {
                "social": proof_stack_social,
                "authority": proof_stack_authority,
                "mechanism": proof_stack_mechanism
            },
            "sacrifice_framing": sacrifice_framing,
            "differentiation_logic": differentiation_logic
        },
        "layer5_narrative": {
            "narrative_spine": {
                "problem": narrative_problem,
                "tension": narrative_tension,
                "resolution": narrative_resolution
            },
            "enemy_definition": enemy_definition,
            "repetition_logic": repetition_logic
        },
        "layer6_channel_strategy": {
            "channels": channels
        },
        "layer7_constraints": {
            "tone_boundaries": tone_boundaries,
            "forbidden_language": forbidden_language,
            "claim_boundaries": claim_boundaries,
            "visual_constraints": visual_constraints,
            "compliance_rules": compliance_rules
        },
        "layer8_measurement": {
            "success_definition": success_definition,
            "leading_indicators": leading_indicators,
            "lagging_indicators": lagging_indicators,
            "review_cadence": review_cadence,
            "decision_rules": decision_rules
        }
    }
    
    # Create/update artifact
    try:
        intake_artifact = store.get_artifact(ArtifactType.INTAKE)
        
        if not strategy_artifact:
            strategy_artifact = store.create_artifact(
                artifact_type=ArtifactType.STRATEGY,
                client_id=intake_artifact.client_id,
                engagement_id=intake_artifact.engagement_id,
                content=strategy_content,
                source_artifacts=[intake_artifact]
            )
            st.success("✅ Strategy draft created!")
        else:
            store.update_artifact(
                strategy_artifact,
                content=strategy_content,
                increment_version=True
            )
            st.success(f"✅ Strategy updated to v{strategy_artifact.version + 1}!")
        
        st.rerun()
    
    except Exception as e:
        st.error(f"❌ Save failed: {str(e)}")
```

---

## Estimated Lines: ~600-800 for Strategy tab alone

This is the foundation. Once this is done, downstream tabs can be fixed.
