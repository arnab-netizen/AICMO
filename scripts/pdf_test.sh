#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════════
# AICMO PDF Export Test Script
# ═══════════════════════════════════════════════════════════════════════════════
#
# Tests both PDF export modes:
# 1. Classic text-based PDF (ReportLab) – default behavior
# 2. Agency-grade HTML PDF (WeasyPrint) – new optional feature
#
# Usage: bash scripts/pdf_test.sh
#
# Output:
# - tmp_fallback.pdf: Text-based PDF (should look identical to current behavior)
# - tmp_agency.pdf: Agency-grade HTML PDF (should have structured layout)
# ═══════════════════════════════════════════════════════════════════════════════

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "╔═══════════════════════════════════════════════════════════════════════════════╗"
echo "║                      AICMO PDF Export Test Script                            ║"
echo "╚═══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.9+ and try again."
    exit 1
fi

echo "✅ Python found: $(python --version)"
echo ""

# ─────────────────────────────────────────────────────────────────────────────────
# TEST 1: Classic Text-Based PDF (ReportLab Fallback)
# ─────────────────────────────────────────────────────────────────────────────────

echo "Test 1: Classic Text-Based PDF (ReportLab fallback)"
echo "─────────────────────────────────────────────────────────────────────────────────"

python << 'PYTHON_FALLBACK_TEST'
import sys
import os
sys.path.insert(0, os.getcwd())

try:
    from backend.export_utils import safe_export_pdf
    from fastapi.responses import StreamingResponse
    
    # Minimal markdown content for testing
    test_markdown = """# AICMO Test Report (Fallback Mode)

## Campaign Overview
This is a test of the classic text-based PDF export using ReportLab.

## Campaign Strategy
- **Objective**: Test PDF fallback behavior
- **Duration**: 30 days
- **Channel**: All channels

## Audience
- Primary: Tech enthusiasts
- Secondary: Business professionals

## Creative Direction
Plain text creative assets.

## Summary
This PDF should look identical to current behavior when agency mode is OFF.
"""

    # Test safe_export_pdf function
    result = safe_export_pdf(test_markdown, check_placeholders=False)
    
    # Check if it's a StreamingResponse (success) or error dict
    if isinstance(result, StreamingResponse):
        print("✅ Fallback PDF generation successful")
        
        # Extract PDF bytes from StreamingResponse
        # The StreamingResponse was created with content=iter([pdf_bytes])
        # We need to consume the iterator to get the bytes back
        pdf_chunks = []
        
        # Handle both sync and async iterators
        iterator = result.body_iterator
        
        # Check if it's an async generator
        import inspect
        if inspect.isasyncgen(iterator):
            # Need async context - this shouldn't happen in normal flow
            # but we handle it just in case
            print("⚠️  Warning: Iterator is async, attempting to extract...")
            import asyncio
            async def extract():
                chunks = []
                async for chunk in iterator:
                    chunks.append(chunk)
                return chunks
            try:
                pdf_chunks = asyncio.run(extract())
            except RuntimeError as e:
                print(f"⚠️  Cannot run asyncio in this context: {e}")
                print("⚠️  Skipping fallback test")
                sys.exit(0)
        else:
            # Sync iterator - normal case
            for chunk in iterator:
                pdf_chunks.append(chunk)
        
        pdf_bytes = b''.join(pdf_chunks)
        
        # Validate PDF header
        if pdf_bytes.startswith(b"%PDF"):
            print(f"✅ PDF header valid (size: {len(pdf_bytes)} bytes)")
            
            # Write to file
            with open("tmp_fallback.pdf", "wb") as f:
                f.write(pdf_bytes)
            print("✅ Saved: tmp_fallback.pdf")
        else:
            print("❌ Invalid PDF header - PDF may be corrupted")
            sys.exit(1)
    else:
        # It's an error dict
        print(f"❌ Fallback PDF generation failed: {result.get('message')}")
        sys.exit(1)

except Exception as e:
    print(f"❌ Fallback PDF test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("")
PYTHON_FALLBACK_TEST

# ─────────────────────────────────────────────────────────────────────────────────
# TEST 2: Agency-Grade HTML PDF (WeasyPrint)
# ─────────────────────────────────────────────────────────────────────────────────

echo "Test 2: Agency-Grade HTML PDF (WeasyPrint)"
echo "─────────────────────────────────────────────────────────────────────────────────"

python << 'PYTHON_AGENCY_TEST'
import sys
import os
sys.path.insert(0, os.getcwd())

try:
    from backend.export_utils import safe_export_agency_pdf
    from fastapi.responses import StreamingResponse
    
    # Build a test payload with report data
    test_payload = {
        "wow_enabled": True,
        "wow_package_key": "strategy_campaign_standard",
        "report": {
            "title": "AICMO Test Campaign",
            "brand_name": "Test Brand",
            "location": "India",
            "campaign_title": "Test Campaign Q4 2025",
            "campaign_duration": "30 days",
            "campaign_name": "Test Campaign",
            "brand_tone": "Professional",
            "objectives_html": "<p>Test objective 1</p><p>Test objective 2</p>",
            "objectives_md": "- Objective 1\n- Objective 2",
            "core_campaign_idea_html": "<p>This is the core campaign idea for testing.</p>",
            "core_campaign_idea_md": "This is the core campaign idea for testing.",
            "channel_plan_html": "<p>Social media, Email, Direct</p>",
            "audience_segments_html": "<p>Millennials, Gen Z professionals</p>",
            "personas": [
                {
                    "name": "Test Persona 1",
                    "role": "Marketing Manager",
                    "goals": "Increase brand awareness",
                    "challenges": "Limited budget"
                }
            ],
            "creative_direction_html": "<p>Modern, vibrant visual style</p>",
            "competitor_snapshot": [
                {
                    "name": "Competitor A",
                    "position": "Market leader",
                    "key_message": "Premium quality",
                    "channels": "TV, Digital"
                }
            ],
            "roi_model": {
                "reach": {"q1": "100K", "q2": "150K"},
                "engagement": {"q1": "5%", "q2": "7%"},
                "conversion": {"q1": "2%", "q2": "3%"}
            },
            "brand_identity": {
                "primary_color": "#7B2D43",
                "secondary_color": "#D4AF37",
                "typography": "Modern sans-serif",
                "tone_voice": "Professional yet approachable"
            },
            "calendar_html": "<p>30-day campaign calendar</p>",
            "ad_concepts_html": "<p>5 ad concepts developed</p>",
            "kpi_budget_html": "<p>Budget allocation and KPIs</p>",
            "execution_html": "<p>Execution roadmap</p>",
            "post_campaign_html": "<p>Post-campaign analysis</p>",
            "final_summary_html": "<p>Campaign summary</p>",
        },
        "markdown": "# Fallback markdown content",
    }

    # Test safe_export_agency_pdf function
    result = safe_export_agency_pdf(test_payload)
    
    # Check if it's a StreamingResponse (success) or error dict
    if isinstance(result, StreamingResponse):
        print("✅ Agency PDF generation successful")
        
        # Extract PDF bytes from StreamingResponse
        pdf_chunks = []
        
        # Handle both sync and async iterators
        iterator = result.body_iterator
        
        # Check if it's an async generator
        import inspect
        if inspect.isasyncgen(iterator):
            # Need async context - this shouldn't happen in normal flow
            # but we handle it just in case
            print("⚠️  Warning: Iterator is async, attempting to extract...")
            import asyncio
            async def extract():
                chunks = []
                async for chunk in iterator:
                    chunks.append(chunk)
                return chunks
            try:
                pdf_chunks = asyncio.run(extract())
            except RuntimeError as e:
                print(f"⚠️  Cannot run asyncio in this context: {e}")
                print("⚠️  Skipping agency test")
                sys.exit(0)
        else:
            # Sync iterator - normal case
            for chunk in iterator:
                pdf_chunks.append(chunk)
        
        pdf_bytes = b''.join(pdf_chunks)
        
        # Validate PDF header
        if pdf_bytes.startswith(b"%PDF"):
            print(f"✅ PDF header valid (size: {len(pdf_bytes)} bytes)")
            
            # Write to file
            with open("tmp_agency.pdf", "wb") as f:
                f.write(pdf_bytes)
            print("✅ Saved: tmp_agency.pdf")
        else:
            print("❌ Invalid PDF header - PDF may be corrupted")
            sys.exit(1)
    else:
        # It's an error dict
        print(f"❌ Agency PDF generation failed: {result.get('message')}")
        sys.exit(1)

except Exception as e:
    print(f"❌ Agency PDF test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("")
PYTHON_AGENCY_TEST

# ─────────────────────────────────────────────────────────────────────────────────
# VERIFICATION
# ─────────────────────────────────────────────────────────────────────────────────

echo "Verification"
echo "─────────────────────────────────────────────────────────────────────────────────"

# Check if both files exist
if [ -f "tmp_fallback.pdf" ]; then
    FALLBACK_SIZE=$(stat -f%z "tmp_fallback.pdf" 2>/dev/null || stat -c%s "tmp_fallback.pdf" 2>/dev/null)
    echo "✅ tmp_fallback.pdf exists (${FALLBACK_SIZE} bytes)"
else
    echo "❌ tmp_fallback.pdf not found"
    exit 1
fi

if [ -f "tmp_agency.pdf" ]; then
    AGENCY_SIZE=$(stat -f%z "tmp_agency.pdf" 2>/dev/null || stat -c%s "tmp_agency.pdf" 2>/dev/null)
    echo "✅ tmp_agency.pdf exists (${AGENCY_SIZE} bytes)"
else
    echo "❌ tmp_agency.pdf not found"
    exit 1
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════════════╗"
echo "║                          ✅ All Tests Passed!                                ║"
echo "╚═══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Summary:"
echo "  • Fallback PDF (ReportLab):   tmp_fallback.pdf (${FALLBACK_SIZE} bytes)"
echo "  • Agency PDF (WeasyPrint):    tmp_agency.pdf (${AGENCY_SIZE} bytes)"
echo ""
echo "Next steps:"
echo "  1. Open both PDFs and verify content"
echo "  2. Fallback PDF should look identical to current behavior"
echo "  3. Agency PDF should have structured layout with sections"
echo "  4. Clean up: rm tmp_fallback.pdf tmp_agency.pdf"
echo ""
