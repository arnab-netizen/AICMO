"""
Visual Concept Generator for platform-aware creative directions.

This module generates structured visual concepts that can be used to guide
asset creation or embedded into LLM prompts for more specific creative output.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List


@dataclass
class VisualConcept:
    """
    Structured description of a creative asset.

    This is intended to be embedded into LLM prompts or exported into
    front-end tools. Keep it JSON-serialisable.
    """

    shot_type: str
    setting: str
    subjects: List[str]
    mood: str
    color_palette: str
    motion: str
    on_screen_text: str
    aspect_ratio: str
    platform_notes: str

    def to_prompt_snippet(self) -> str:
        """
        Convert this concept into a compact, human-readable description
        suitable for feeding into an LLM prompt.
        """
        subjects_str = ", ".join(self.subjects)
        return (
            f"Shot type: {self.shot_type}. Setting: {self.setting}. "
            f"Subjects: {subjects_str}. Mood: {self.mood}. "
            f"Colour palette: {self.color_palette}. Motion: {self.motion}. "
            f"On-screen text: {self.on_screen_text}. "
            f"Aspect ratio: {self.aspect_ratio}. "
            f"Platform notes: {self.platform_notes}."
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _base_aspect_ratio_for_platform(platform: str) -> str:
    platform = platform.lower()
    if platform in ("instagram_reel", "reel", "tiktok", "stories", "story"):
        return "9:16"
    if platform in ("instagram_post", "feed", "facebook", "linkedin"):
        return "1:1 or 4:5"
    if platform in ("youtube", "youtube_short"):
        return "9:16 for short, 16:9 for long-form"
    return "flexible"


def generate_visual_concept(
    *,
    platform: str,
    theme: str,
    creative_territory_id: str,
    brand_name: str,
    industry: str,
) -> VisualConcept:
    """
    Deterministic, non-LLM helper that returns a reasonable visual concept
    based on high-level inputs. LLMs can then elaborate on this.

    This function is intentionally simple and rule-based so that it can be
    safely called inside existing generators without introducing new
    external dependencies.
    """
    pl = platform.lower()
    territory = creative_territory_id

    # Defaults
    shot_type = "medium shot"
    setting = "indoors"
    subjects: List[str] = ["product"]
    mood = "warm and welcoming"
    color_palette = "brand colours with soft ambient tones"
    motion = "slow, steady camera movement"
    on_screen_text = ""
    aspect_ratio = _base_aspect_ratio_for_platform(pl)
    platform_notes = ""

    brand_lower = brand_name.strip().lower()

    # Starbucks-specific heuristics
    if "starbucks" in brand_lower:
        color_palette = "Starbucks green, warm neutrals, natural textures (wood, stone)"
        if territory == "rituals_and_moments":
            shot_type = "hand-held close-up"
            setting = "cafe interior near window light"
            subjects = ["cup with visible logo", "guest hands", "table surface"]
            mood = "calm, cosy, everyday comfort"
            motion = "subtle hand movements, steam rising, shallow depth of field"
            on_screen_text = "First sip of the day."
        elif territory == "behind_the_bar":
            shot_type = "POV and close-ups of barista actions"
            setting = "behind the bar, espresso machine area"
            subjects = ["barista hands", "espresso machine", "milk pitcher", "cups"]
            mood = "craft-driven, energetic but precise"
            motion = "quick cuts between grind, pour, steam, serve"
            on_screen_text = "Handcrafted for you."
        elif territory == "seasonal_magic":
            shot_type = "hero product close-up"
            setting = "seasonal decor area (holiday props, lights, or summer elements)"
            subjects = ["seasonal drink", "seasonal props", "subtle branding"]
            mood = "festive, joyful, slightly cinematic"
            motion = "slow push-in or rotating product shot"
            on_screen_text = "Tastes like the season."
        elif territory == "third_place_culture":
            shot_type = "wide to medium shots"
            setting = "seating area with multiple guests"
            subjects = ["group of friends", "laptops/books", "cups on table"]
            mood = "social, relaxed, inclusive"
            motion = "gentle pans across the table or room"
            on_screen_text = "Your third place."
        elif territory == "responsibility_and_sourcing":
            shot_type = "documentary-style close-ups"
            setting = "coffee farm visuals or sustainability touchpoints in store"
            subjects = ["beans", "farmer hands", "reusable cups", "recycling stations"]
            mood = "thoughtful, optimistic, grounded"
            motion = "slower cuts, focus on details and textures"
            on_screen_text = "From farm to your cup."

    # Platform-specific notes
    if "reel" in pl or "tiktok" in pl or "short" in pl:
        platform_notes = (
            "Hook in first 2 seconds. Use bold on-screen text and clear focal subject. "
            "Optimised for vertical viewing with sound off but sound-on friendly."
        )
    elif "instagram" in pl or "facebook" in pl:
        platform_notes = "Optimised for feed scrolling. Strong first frame and readable text."
    elif "linkedin" in pl:
        platform_notes = "Slightly more professional framing, but still human and warm."

    return VisualConcept(
        shot_type=shot_type,
        setting=setting,
        subjects=subjects,
        mood=mood,
        color_palette=color_palette,
        motion=motion,
        on_screen_text=on_screen_text,
        aspect_ratio=aspect_ratio,
        platform_notes=platform_notes,
    )
