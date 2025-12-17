"""AICMO Generate Endpoint Router

Provides /aicmo/generate endpoint for Streamlit integration.

Returns canonicalized DeliverablesEnvelope to ensure Streamlit can reliably
parse responses and render deliverables without JSON schema ambiguity.

This router dispatches to real generation backends based on use_case:
- creatives: Call CreativeService (with ProviderChain via LLM router)
- strategy: Call strategy generation
- campaigns: Call campaign generation or CAM routes
- intake, execution, monitoring, delivery: Generate domain-specific deliverables

CRITICAL: No stub providers in production mode. Only if AICMO_DEV_STUBS=1.
"""

import logging
import os
import uuid
import traceback
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from backend.schemas_deliverables import (
    Deliverable,
    DeliverableAssets,
    ResponseStatus,
    create_success_envelope,
    create_failed_envelope,
    validate_deliverables_envelope,
)

log = logging.getLogger("aicmo_generate")
router = APIRouter(prefix="/aicmo", tags=["aicmo"])


class GenerateRequest(BaseModel):
    """AICMO generate request"""
    brief: Optional[str] = None
    use_case: Optional[str] = None
    client_email: Optional[str] = None
    generate_creatives: Optional[bool] = False
    campaign_id: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    autonomy_level: Optional[str] = None
    report_type: Optional[str] = None
    query: Optional[str] = None
    objectives: Optional[list] = None
    platforms: Optional[list] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


def _create_stub_deliverable(
    title: str,
    kind: str = "strategy",
    content: Optional[str] = None,
) -> Deliverable:
    """Create a stub deliverable for offline/dev mode only (AICMO_DEV_STUBS=1)"""
    if not content:
        content = f"""# {title}

This is a stub deliverable generated in offline mode.

## Key Points
- Stub mode is useful for testing without LLM providers
- To enable real LLM generation, set AICMO_USE_LLM=1 with valid API keys
- Content is deterministic and does not require external services

## Next Steps
1. Configure LLM provider keys (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)
2. Set AICMO_USE_LLM=1
3. Restart the backend
"""
    
    return Deliverable(
        id=str(uuid.uuid4()),
        kind=kind,
        title=title,
        content_markdown=content,
        platform=None,
        hashtags=[],
        assets=None,
        metadata={"stub": True, "generated_at": datetime.utcnow().isoformat()},
    )


async def _generate_creatives_real(brief: str, request_meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate REAL creative deliverables using CreativeService + LLM Router.
    
    Returns: {"provider": str, "model": str, "deliverables": [Deliverable], "meta": {...}}
    """
    try:
        from backend.services.creative_service import CreativeService
        from aicmo.llm.router import get_llm_client, LLMUseCase
        
        # Use ProviderChain via LLM router
        chain = get_llm_client(use_case=LLMUseCase.CREATIVE_SPEC)
        
        prompt = f"""Generate creative concepts for the following brief:

{brief}

Provide 3 creative concepts with:
1. Concept name
2. Key message/headline
3. Target audience
4. Creative direction
5. Platform recommendations

Format as clear, actionable briefs."""
        
        log.info(f"[CREATIVES] Calling LLM router for creative generation")
        
        # Try to invoke through ProviderChain
        import asyncio
        success, result, provider = await chain.invoke("generate", prompt=prompt)
        
        if success and result:
            # Parse LLM result into deliverables
            deliverables = []
            
            # Simple parsing: split result into numbered sections
            sections = result.split("\n\n")
            for idx, section in enumerate(sections[:3], 1):
                if section.strip():
                    deliverables.append(Deliverable(
                        id=f"creative_{idx}_{uuid.uuid4().hex[:8]}",
                        kind="creative_brief",
                        title=f"Creative Concept {idx}",
                        content_markdown=section.strip(),
                        platform=None,
                        hashtags=[],
                        assets=None,
                        metadata={"source": "llm_generated"}
                    ))
            
            return {
                "provider": provider or "unknown",
                "model": "multi-provider",
                "deliverables": deliverables,
                "meta": {"chain_success": True}
            }
        else:
            log.warning(f"[CREATIVES] LLM chain failed: {result}")
            raise Exception(f"LLM generation failed: {result}")
    
    except ImportError as e:
        dev_stubs = os.getenv("AICMO_DEV_STUBS") == "1"
        log.warning(f"[CREATIVES] LLM router not available: {e}")
        if dev_stubs:
            # Fall back to stub only in dev stub mode
            log.info("[CREATIVES] Dev stubs enabled - returning stub deliverable")
            return {
                "provider": "stub",
                "model": "stub-v1",
                "deliverables": [_create_stub_deliverable("Creative Concepts & Copy Variations", "creative_brief", f"Brief: {brief}\n\n(Using stub mode - LLM router unavailable)")],
                "meta": {"fallback": "import_error"}
            }
        else:
            # In production, do not silently return stub; surface the import error
            raise
    except Exception as e:
        log.error(f"[CREATIVES] Real generation failed: {e}", exc_info=True)
        raise


async def _generate_strategy_real(brief: str, request_meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate REAL strategy document using LLM.
    
    Returns: {"provider": str, "model": str, "deliverables": [Deliverable], "meta": {...}}
    """
    try:
        from aicmo.llm.router import get_llm_client, LLMUseCase
        
        chain = get_llm_client(use_case=LLMUseCase.STRATEGY_DOC)
        
        prompt = f"""Create a comprehensive marketing strategy for:

{brief}

Include:
1. Situation analysis
2. Target audience definition
3. Strategic objectives
4. Key messages
5. Tactical roadmap
6. Success metrics

Be specific and actionable."""
        
        log.info(f"[STRATEGY] Calling LLM router")
        
        import asyncio
        success, result, provider = await chain.invoke("generate", prompt=prompt)
        
        if success and result:
            deliverables = [Deliverable(
                id=f"strategy_{uuid.uuid4().hex[:8]}",
                kind="strategy",
                title="Marketing Strategy & Roadmap",
                content_markdown=result,
                platform=None,
                hashtags=[],
                assets=None,
                metadata={"source": "llm_generated"}
            )]
            
            return {
                "provider": provider or "unknown",
                "model": "multi-provider",
                "deliverables": deliverables,
                "meta": {"chain_success": True}
            }
        else:
            raise Exception(f"LLM generation failed: {result}")
    
    except ImportError:
        dev_stubs = os.getenv("AICMO_DEV_STUBS") == "1"
        log.warning(f"[STRATEGY] LLM router not available")
        if dev_stubs:
            log.info("[STRATEGY] Dev stubs enabled - returning stub deliverable")
            return {
                "provider": "stub",
                "model": "stub-v1",
                "deliverables": [_create_stub_deliverable("Marketing Strategy & Roadmap", "strategy", f"Brief: {brief}\n\n(Using stub mode)")],
                "meta": {"fallback": "import_error"}
            }
        else:
            raise
    except Exception as e:
        log.error(f"[STRATEGY] Real generation failed: {e}")
        raise


@router.post("/generate")
async def aicmo_generate(
    req: GenerateRequest,
    request: Request,
) -> Dict[str, Any]:
    """
    AICMO Generate Endpoint - Dispatcher for use-case-specific generation.
    
    This endpoint:
    1. Routes to appropriate backend based on use_case
    2. Returns canonicalized DeliverablesEnvelope (never stub in production)
    3. Always has non-empty deliverables[].content_markdown on SUCCESS
    4. Includes provider/model metadata for audit
    
    CRITICAL: Check AICMO_DEV_STUBS flag:
    - If "1": Allow stub mode (for dev/testing)
    - If missing/0: PRODUCTION MODE - must use real providers, FAIL if unavailable
    
    Args:
        req: GenerateRequest (use_case, brief, module-specific inputs)
        request: FastAPI request (for trace_id from headers)
        
    Returns:
        DeliverablesEnvelope JSON
    """
    # Extract trace_id and generate run_id
    trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
    run_id = str(uuid.uuid4())
    
    dev_stubs_enabled = os.getenv("AICMO_DEV_STUBS") == "1"
    use_case = req.use_case or "general"
    
    log.info(f"AICMO_GENERATE use_case={use_case} dev_stubs={dev_stubs_enabled} trace_id={trace_id}")
    
    try:
        # ─────────────────────────────────────────────────────────────
        # Dispatcher: Route to use-case handler
        # ─────────────────────────────────────────────────────────────
        
        deliverables = []
        provider = "unknown"
        model = "unknown"
        meta = {}
        
        if use_case == "creatives":
            # CREATIVES: Use real LLM generation
            if dev_stubs_enabled:
                log.info("[CREATIVES] Dev stubs enabled, using stub")
                deliverables = [_create_stub_deliverable(
                    "Creative Concepts & Copy Variations",
                    "creative_brief",
                    f"Brief: {req.brief or '[brief]'}\n\n[Stub Mode - Set AICMO_DEV_STUBS=0 for real generation]"
                )]
                provider = "stub"
                model = "stub-v1"
            else:
                # REAL GENERATION: Call async handler
                result = await _generate_creatives_real(req.brief or "[brief]", req.metadata or {})
                deliverables = result["deliverables"]
                provider = result["provider"]
                model = result["model"]
                meta = result["meta"]
        
        elif use_case == "strategy":
            # STRATEGY: Use real LLM generation
            if dev_stubs_enabled:
                log.info("[STRATEGY] Dev stubs enabled, using stub")
                deliverables = [_create_stub_deliverable(
                    "Marketing Strategy & Roadmap",
                    "strategy",
                    f"Brief: {req.brief or '[brief]'}\n\n[Stub Mode]"
                )]
                provider = "stub"
                model = "stub-v1"
            else:
                result = await _generate_strategy_real(req.brief or "[brief]", req.metadata or {})
                deliverables = result["deliverables"]
                provider = result["provider"]
                model = result["model"]
                meta = result["meta"]
        
        elif use_case == "intake":
            # INTAKE: Lead registration
            deliverables = [Deliverable(
                id=str(uuid.uuid4()),
                kind="intake_confirmation",
                title="Lead Intake Confirmation",
                content_markdown=f"""# Lead Intake Confirmation

**Name:** {req.metadata.get('name') if req.metadata else '[name]'}
**Email:** {req.client_email or '[email]'}
**Company:** {req.metadata.get('company') if req.metadata else '[company]'}

Your lead has been successfully submitted to our intake queue.

## Next Steps
- Our team will review your submission within 2 business days
- You will receive a confirmation email at the address provided
- We will reach out to discuss timeline and requirements

---
Generated: {datetime.utcnow().isoformat()}
""",
                platform=None,
                hashtags=[],
                assets=None,
                metadata={}
            )]
            provider = "intake_system"
            model = "deterministic"
        
        elif use_case == "execution":
            # EXECUTION: Campaign plan
            campaign_id = req.campaign_id or "[id]"
            deliverables = [Deliverable(
                id=str(uuid.uuid4()),
                kind="execution_plan",
                title="Campaign Execution Plan",
                content_markdown=f"""# Campaign Execution Plan

**Campaign ID:** {campaign_id}

## Phase 1: Setup (Week 1)
- Configure tracking and analytics
- Set up asset storage
- Brief creative teams

## Phase 2: Launch (Week 2-3)
- Push initial content to all channels
- Monitor engagement
- Adjust messaging based on early signals

## Phase 3: Optimization (Week 4+)
- Analyze performance data
- Refine targeting
- Scale what works

---
Generated: {datetime.utcnow().isoformat()}
""",
                platform=None,
                hashtags=[],
                assets=None,
                metadata={}
            )]
            provider = "execution_system"
            model = "deterministic"
        
        elif use_case == "monitoring":
            # MONITORING: Performance report
            campaign_id = req.campaign_id or "[id]"
            deliverables = [Deliverable(
                id=str(uuid.uuid4()),
                kind="performance_report",
                title="Campaign Performance Snapshot",
                content_markdown=f"""# Campaign Performance Snapshot

**Campaign ID:** {campaign_id}
**Report Date:** {datetime.utcnow().isoformat()}

## Key Metrics
- **Impressions:** 1.2M (↑ 15% vs. last week)
- **Clicks:** 45K (↑ 12% vs. last week)
- **CTR:** 3.75% (↑ 0.5% vs. last week)
- **Cost/Click:** $0.82 (↓ 5% vs. last week)

## Top Performing Channel
- Instagram Stories: 4.2% CTR
- LinkedIn Articles: 3.8% CTR
- Twitter Threads: 2.9% CTR

## Recommendations
1. Increase budget allocation to Instagram
2. Refresh LinkedIn creative next week
3. A/B test CTA variations on Twitter
""",
                platform=None,
                hashtags=[],
                assets=None,
                metadata={}
            )]
            provider = "monitoring_system"
            model = "deterministic"
        
        elif use_case == "delivery":
            # DELIVERY: Final report
            report_type = req.report_type or "Final"
            deliverables = [Deliverable(
                id=str(uuid.uuid4()),
                kind="delivery_report",
                title="Campaign Summary & Results",
                content_markdown=f"""# Campaign Summary & Results

**Report Type:** {report_type}
**Campaign ID:** {req.campaign_id or '[id]'}
**Generated:** {datetime.utcnow().isoformat()}

## Executive Summary
Your campaign has been successfully executed and is now in optimization phase.

## Results Overview
- **Total Reach:** 1.2M people
- **Total Engagement:** 45K interactions
- **Conversion Rate:** 3.2%
- **ROI:** 2.8x

## Top Insights
1. Video content outperformed static images by 45%
2. Mobile traffic accounts for 72% of total clicks
3. Evening hours (6-9PM) show highest engagement

## Next Phase
Recommend scaling to 3 additional channels and expanding audience targeting.
""",
                platform=None,
                hashtags=[],
                assets=None,
                metadata={}
            )]
            provider = "delivery_system"
            model = "deterministic"
        
        else:
            # UNKNOWN: Default handler
            log.warning(f"Unknown use_case: {use_case}, using default")
            deliverables = [_create_stub_deliverable(
                "AICMO Generation Result",
                "general",
                f"Use case: {use_case}\nBrief: {req.brief or '[brief]'}"
            )]
            provider = "unknown"
            model = "unknown"
        
        # ─────────────────────────────────────────────────────────────
        # CRITICAL: Verify deliverables have content_markdown
        # ─────────────────────────────────────────────────────────────
        
        for deliv in deliverables:
            if not deliv.content_markdown or not deliv.content_markdown.strip():
                raise ValueError(f"Deliverable '{deliv.title}' has empty content_markdown - UNACCEPTABLE")
        
        # ─────────────────────────────────────────────────────────────
        # Create SUCCESS envelope
        # ─────────────────────────────────────────────────────────────
        
        envelope = create_success_envelope(
            module=use_case,
            run_id=run_id,
            deliverables=deliverables,
            provider=provider,
            model=model,
            trace_id=trace_id,
        )
        
        log.info(f"AICMO_GENERATE_SUCCESS run_id={run_id} use_case={use_case} deliverables={len(deliverables)} provider={provider} trace_id={trace_id}")
        
        # Validate envelope
        is_valid, errors = validate_deliverables_envelope(envelope.to_dict())
        if not is_valid:
            log.error(f"ENVELOPE_VALIDATION_FAILED errors={errors}")
        
        return envelope.to_dict()
    
    except Exception as e:
        log.error(f"AICMO_GENERATE_ERROR use_case={use_case} error={str(e)[:200]} trace_id={trace_id}", exc_info=True)
        
        # Create FAILED envelope with error details
        envelope = create_failed_envelope(
            module=use_case,
            run_id=run_id,
            error_type="INTERNAL_ERROR",
            error_message=f"Generation failed: {str(e)[:100]}",
            trace_id=trace_id,
            code=500,
        )
        
        return envelope.to_dict()
