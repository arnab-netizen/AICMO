#!/usr/bin/env python3
"""
Quick test of the humanization wrapper.
"""

import sys

# Add workspace to path
sys.path.insert(0, "/workspaces/AICMO")

from backend.humanization_wrapper import HumanizationWrapper


def test_humanization():
    """Test basic humanization functionality."""

    wrapper = HumanizationWrapper()

    # Sample AI-generated text (typical AICMO output)
    ai_text = """
Here are some ways to improve your marketing strategy. In conclusion, you should focus on these key areas:
    
1. Brand positioning - Overall, this is critical.
2. Audience segmentation - In summary, divide your audience strategically.
3. Channel optimization - To summarize, choose platforms wisely.

This section will explore the messaging pyramid. Here are some key takeaways you should remember.
"""

    print("=" * 70)
    print("HUMANIZATION WRAPPER TEST")
    print("=" * 70)
    print("\n📝 ORIGINAL (AI-like) TEXT:")
    print("-" * 70)
    print(ai_text)

    print("\n🔄 PROCESSING...")
    print("-" * 70)

    # Apply humanization
    humanized = wrapper.process_text(
        ai_text,
        brand_voice="Professional, conversational, direct",
        extra_context="B2B SaaS marketing strategy",
    )

    print("\n✨ HUMANIZED TEXT:")
    print("-" * 70)
    print(humanized)

    print("\n✅ TEST COMPLETE")
    print("=" * 70)
    print("\nNote: Without OPENAI_API_KEY set, this falls back to heuristic cleanup.")
    print("With OpenAI configured, output will be fully humanized with:")
    print("  • Layer 1: Boilerplate removal (LLM)")
    print("  • Layer 2: Variation injection (heuristics)")
    print("  • Layer 3: Persona rewrite (LLM)")


if __name__ == "__main__":
    test_humanization()
