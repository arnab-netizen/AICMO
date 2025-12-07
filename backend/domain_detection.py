from __future__ import annotations

from enum import Enum
from typing import List


class PackDomain(str, Enum):
    AUTOMOTIVE_DEALERSHIP = "automotive_dealership"
    SAAS = "saas"
    ECOMMERCE = "ecommerce"
    GENERIC = "generic"


AUTOMOTIVE_BANNED_TERMS: List[str] = [
    "ProductHunt",
    "G2",
    "MRR",
    "ARR",
    "SaaS",
    "trial",
    "activation",
    "onboarding",
    "churn",
    "monthly recurring",
    "subscription plan",
]


def infer_domain_from_input(user_input: str) -> PackDomain:
    text = (user_input or "").lower()
    automotive_markers = [
        "car",
        "cars",
        "automobile",
        "automotive",
        "showroom",
        "dealership",
        "test drive",
        "luxury car",
    ]
    saas_markers = [
        "mrr",
        "arr",
        "saas",
        "subscription",
        "trial",
        "producthunt",
        "g2",
    ]

    if any(m in text for m in automotive_markers):
        return PackDomain.AUTOMOTIVE_DEALERSHIP
    if any(m in text for m in saas_markers):
        return PackDomain.SAAS
    return PackDomain.GENERIC
