"""
4-Layer Generation Pipeline for AICMO Pack Outputs

This module implements a progressive, non-blocking quality improvement pipeline:

Layer 1: Raw Draft Generator (UNBLOCKED)
  - Generates first-pass section content with correct structure
  - Never fails; returns raw text or empty string
  
Layer 2: Humanizer / Enhancement Pass (FALLBACK-SAFE)
  - Makes draft more human-like, specific, and compelling
  - On any error → silently returns raw_text (never blocks)
  
Layer 3: Soft Validators (NON-BLOCKING)
  - Scores and flags issues (quality, genericity, warnings)
  - Returns tuple: (text, quality_score, genericity_score, warnings)
  - Never raises HTTPException; all errors logged internally
  
Layer 4: Section-Level Rewriter (OPTIONAL, NON-BLOCKING)
  - Improves weak sections (quality_score < 60)
  - Max 1 rewrite attempt per section
  - On any error → returns previous version (never blocks)

Key Principles:
✅ Never blocks users (all errors handled gracefully)
✅ Backward compatible (all public APIs unchanged)
✅ Progressive enhancement (each layer improves previous output)
✅ Non-blocking validation (quality scored, not enforced)
✅ Safe social calendar (per-day fallback micro-passes)
✅ Comprehensive logging (warnings for low quality, debug for details)
"""

from backend.layers.layer1_raw_draft import generate_raw_section
from backend.layers.layer2_humanizer import enhance_section_humanizer
from backend.layers.layer3_soft_validators import run_soft_validators
from backend.layers.layer4_section_rewriter import rewrite_low_quality_section

__all__ = [
    "generate_raw_section",
    "enhance_section_humanizer",
    "run_soft_validators",
    "rewrite_low_quality_section",
]
