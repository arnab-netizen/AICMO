"""
Creative Territories Engine for brand-aware content generation.

This module provides structured creative territories that help guide content creation
to be more specific, brand-aware, and strategically aligned. It's intentionally
lightweight and framework-agnostic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class CreativeTerritory:
    """
    A simple, serialisable representation of a creative territory.

    This is intentionally lightweight and framework-agnostic so it can be
    passed into LLM prompts or stored in JSON without extra dependencies.
    """

    id: str
    label: str
    summary: str
    example_angles: List[str]


def _starbucks_territories() -> List[CreativeTerritory]:
    return [
        CreativeTerritory(
            id="rituals_and_moments",
            label="Daily Rituals & Micro-Moments",
            summary=(
                "Everyday coffee rituals: first sip of the morning, study sessions, "
                "remote work days, post-work catch-ups. Focus on how Starbucks fits "
                "into the rhythm of a guest's day as their 'third place'."
            ),
            example_angles=[
                "Monday reset with your first latte of the week.",
                "Your 4 PM focus break with a caramel macchiato.",
                "Late-evening wind-down with friends over frappuccinos.",
            ],
        ),
        CreativeTerritory(
            id="behind_the_bar",
            label="Behind the Bar & Craft",
            summary=(
                "Baristas, handcrafted beverages, origin stories, and preparation "
                "shots. Show the craft behind each cup and the people who make it."
            ),
            example_angles=[
                "Three steps your latte goes through before it reaches your hands.",
                "Barista POV: writing your name on the cup.",
                "Grind, steam, pour – close-ups of the espresso ritual.",
            ],
        ),
        CreativeTerritory(
            id="seasonal_magic",
            label="Seasonal Magic & Limited Flavours",
            summary=(
                "Seasonal beverages and limited-time offerings as emotional markers "
                "for time of year (holidays, winter, summer cold brews, etc.)."
            ),
            example_angles=[
                "The first sip that makes it feel like December.",
                "Pumpkin spice season – the unofficial start of cosy weather.",
                "Iced cold brew to survive long summer afternoons.",
            ],
        ),
        CreativeTerritory(
            id="third_place_culture",
            label="Third Place Culture & Community",
            summary=(
                "Starbucks as a welcoming 'third place' between home and work. "
                "Tables, corners, ambient music, regulars, and community stories."
            ),
            example_angles=[
                "Today's office: your corner table by the window.",
                "Meet the regular who has a favourite seat and a favourite drink.",
                "One table, four cups, zero rush.",
            ],
        ),
        CreativeTerritory(
            id="responsibility_and_sourcing",
            label="Responsibility, Sourcing & Sustainability",
            summary=(
                "Ethical sourcing, farmer stories, reusables, recycling, and "
                "Starbucks' sustainability commitments made tangible for guests."
            ),
            example_angles=[
                "What happens before your coffee reaches your cup.",
                "Bring-your-own-cup moments and small daily choices.",
                "From farm to cup: spotlight on bean origins.",
            ],
        ),
    ]


def _generic_food_beverage_territories() -> List[CreativeTerritory]:
    return [
        CreativeTerritory(
            id="product_focus",
            label="Product Hero & Taste",
            summary="Showcase hero products, flavours, ingredients, and taste cues.",
            example_angles=[
                "Close-ups of textures, toppings, and steam.",
                "Before/after shots (plain vs plated/served).",
            ],
        ),
        CreativeTerritory(
            id="people_and_places",
            label="People & Places",
            summary="Guests, staff, interiors, and the atmosphere of the venue.",
            example_angles=[
                "Candid guest moments (laughter, conversations).",
                "Staff portraits and micro-stories.",
            ],
        ),
        CreativeTerritory(
            id="process_and_craft",
            label="Process & Craft",
            summary="How things are made, from raw ingredient to final dish/drink.",
            example_angles=[
                "Step-by-step preparation sequences.",
                "Tools of the trade (equipment, utensils, bar).",
            ],
        ),
    ]


def get_creative_territories_for_brief(brief: Dict[str, Any]) -> List[CreativeTerritory]:
    """
    Entry point used by generators.

    `brief` is expected to be a lightweight dict extracted from the full
    BrandBrief / client_brief structure, e.g.:

        {
            "brand_name": "Starbucks",
            "industry": "Coffeehouse / Beverage Retail",
            "geography": "Global",
        }

    The function is deliberately defensive: if keys are missing, it falls
    back to generic territories rather than raising.
    """
    brand_name = (brief.get("brand_name") or brief.get("brand") or "").strip().lower()
    industry = (brief.get("industry") or "").strip().lower()

    # Brand-specific overrides first.
    if "starbucks" in brand_name:
        return _starbucks_territories()

    # Industry-based defaults.
    if any(k in industry for k in ("coffee", "cafe", "coffeehouse", "beverage")):
        return _generic_food_beverage_territories()

    # Fallback – very generic creative lenses.
    return [
        CreativeTerritory(
            id="brand_story",
            label="Brand Story & Origin",
            summary="Founding story, mission, values, and what makes the brand distinct.",
            example_angles=[
                "Why this brand exists and who it serves.",
                "A moment that captures the brand's purpose.",
            ],
        ),
        CreativeTerritory(
            id="customer_moments",
            label="Customer Moments",
            summary="Real-life situations where the product/service appears naturally.",
            example_angles=[
                "Before/after using the product.",
                "Day-in-the-life scenes around usage.",
            ],
        ),
    ]
