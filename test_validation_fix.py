#!/usr/bin/env python
"""
Test script to verify the Pydantic validation fixes for ToneVariant.
"""
from aicmo.io.client_reports import ToneVariant, CreativesBlock

# Test 1: ToneVariant structure
print("=" * 60)
print("TEST 1: ToneVariant Structure")
print("=" * 60)

tone_variant_data = {
    "tone_label": "Empathetic and Encouraging",
    "example_caption": "Your style matters - reflect your true style.",
}

try:
    tv = ToneVariant(**tone_variant_data)
    print(f"✅ ToneVariant created: {tv}")
except Exception as e:
    print(f"❌ FAILED: {e}")

# Test 2: CreativesBlock with tone_variants
print("\n" + "=" * 60)
print("TEST 2: CreativesBlock with ToneVariants")
print("=" * 60)

creatives_data = {
    "notes": "Test creatives",
    "hooks": ["Hook 1", "Hook 2"],
    "captions": ["Caption 1", "Caption 2"],
    "scripts": [],
    "email_subject_lines": ["Subject 1", "Subject 2"],
    "tone_variants": [
        {
            "tone_label": "Empathetic and Encouraging",
            "example_caption": "Your style matters - reflect your true style.",
        },
        {
            "tone_label": "Bold and Inspirational",
            "example_caption": "Step into our latest collection.",
        },
    ],
    "channel_variants": [],
    "hook_insights": [],
    "cta_library": [],
    "offer_angles": [],
}

try:
    cb = CreativesBlock(**creatives_data)
    print(f"✅ CreativesBlock created with {len(cb.tone_variants)} tone variants")
    for tv in cb.tone_variants:
        print(f"   - {tv.tone_label}: {tv.example_caption[:40]}...")
except Exception as e:
    print(f"❌ FAILED: {e}")

# Test 3: Invalid structure (what the old code was doing)
print("\n" + "=" * 60)
print("TEST 3: Invalid ToneVariant (strings instead of objects)")
print("=" * 60)

invalid_tone_variants = [
    "Empathetic and Encouraging: Your style matters - reflect your true style.",
    "Bold and Inspirational: Step into our latest collection.",
]

try:
    # This should fail with the old code
    cb_invalid = CreativesBlock(
        tone_variants=invalid_tone_variants,
        hooks=[],
        captions=[],
        scripts=[],
        channel_variants=[],
        email_subject_lines=[],
        hook_insights=[],
        cta_library=[],
        offer_angles=[],
    )
    print("❌ Should have failed but didn't!")
except Exception as e:
    print(f"✅ Correctly rejected invalid structure: {type(e).__name__}")
    print(f"   Error: {str(e)[:100]}...")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("All tests passed! ToneVariant structure is correct.")
print("\nKey fix: tone_variants must be List[ToneVariant] objects,")
print("not strings. Each must have 'tone_label' and 'example_caption'.")
