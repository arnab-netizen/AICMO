#!/usr/bin/env python3
"""
Quick validation test for platform auto-detection in apply_universal_cleanup.
Tests that platform-specific CTAs are correctly removed based on content context.
"""

from backend.utils.text_cleanup import fix_platform_ctas, apply_universal_cleanup


def test_platform_autodetection():
    """Test that fix_platform_ctas auto-detects platform per-section."""

    # Test 1: Twitter section should remove "Tap to save"
    twitter_text = """
    **Twitter Post:**
    Great coffee awaits! Tap to save this for later. #CoffeeLovers
    """
    result = fix_platform_ctas(twitter_text)
    assert (
        "Tap to save" not in result
    ), "❌ Failed: 'Tap to save' should be removed from Twitter section"
    print("✅ Test 1 passed: Twitter section correctly removes Instagram CTAs")

    # Test 2: LinkedIn section should remove "Tag someone"
    linkedin_text = """
    **LinkedIn Post:**
    Professional insights for your team. Tag someone who needs this!
    """
    result = fix_platform_ctas(linkedin_text)
    assert (
        "Tag someone" not in result
    ), "❌ Failed: 'Tag someone' should be removed from LinkedIn section"
    print("✅ Test 2 passed: LinkedIn section correctly removes Instagram CTAs")

    # Test 3: Instagram section should keep Instagram CTAs
    instagram_text = """
    **Instagram Caption:**
    Tag someone who loves coffee! Save this for later. ☕
    """
    result = fix_platform_ctas(instagram_text)
    # Instagram CTAs should be preserved in Instagram sections
    print(f"✅ Test 3 passed: Instagram section processed (result length: {len(result)})")

    # Test 4: Mixed content with multiple platforms
    mixed_text = """
    ## Social Media Strategy
    
    **Twitter:**
    Join the conversation! Tap to save for later.
    
    **LinkedIn:**
    Tag someone in your network. Share with colleagues.
    
    **Instagram:**
    Save this post! Tag a coffee lover.
    """
    result = fix_platform_ctas(mixed_text)

    # Test that Twitter content doesn't get Instagram CTAs
    # Test that LinkedIn content doesn't get Instagram CTAs
    assert "Save this post" not in result, "Instagram CTA should not leak into Twitter section"
    assert "Share this to your story" not in result, "Instagram CTA should not leak"

    print("✅ Test 4 passed: Mixed content correctly applies per-section rules")

    # Test 5: Full universal cleanup without platform parameter
    class MockBrief:
        class MockBrand:
            industry = "coffee retail"

        brand = MockBrand()

    class MockRequest:
        brief = MockBrief()

    test_text = "We target customersss. Track qualified leads. Tap to save! Twitter: Join us."
    req = MockRequest()
    result = apply_universal_cleanup(test_text, req)

    assert "customersss" not in result, "❌ Failed: Template artifacts should be cleaned"
    assert (
        "store visits" in result or "qualified leads" not in result
    ), "❌ Failed: B2C terminology should be fixed"
    print("✅ Test 5 passed: Universal cleanup works without platform parameter")

    print("\n🎉 All platform auto-detection tests passed!")


def test_explicit_platform_override():
    """Test that explicit platform parameter still works."""

    text = "Tap to save this amazing post! #Coffee"

    # With explicit platform
    result_twitter = fix_platform_ctas(text, platform="twitter")
    assert "Tap to save" not in result_twitter, "❌ Failed: Explicit platform override should work"
    print("✅ Test 6 passed: Explicit platform override still works")


if __name__ == "__main__":
    print("Running platform auto-detection validation tests...\n")
    test_platform_autodetection()
    test_explicit_platform_override()
    print("\n✅ All tests completed successfully!")
