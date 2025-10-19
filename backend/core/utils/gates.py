from typing import Sequence, Dict


# Lightweight stubs; can be replaced with real libs later.
def readability_score(text: str) -> float:
    words = max(1, len(text.split()))
    sentences = max(1, text.count(".") + text.count("!") + text.count("?"))
    syll = sum(max(1, sum(ch in "aeiouy" for ch in w.lower())) for w in text.split())
    return round(206.835 - 1.015 * (words / sentences) - 84.6 * (syll / words), 2)


def platform_limit_ok(
    line: str, google_max: int = 90, linkedin_max: int = 150, x_max: int = 280
) -> Dict[str, bool]:
    return {
        "google": len(line) <= google_max,
        "linkedin": len(line) <= linkedin_max,
        "x": len(line) <= x_max,
    }


def dedup_jaccard_ok(variants: Sequence[str], max_sim: float = 0.8) -> bool:
    toks = [set(v.lower().split()) for v in variants]
    for i in range(len(toks)):
        for j in range(i + 1, len(toks)):
            inter = len(toks[i] & toks[j])
            union = len(toks[i] | toks[j]) or 1
            sim = inter / union
            if sim > (1.0 - max_sim):  # ~0.2 threshold
                return False
    return True


def ocr_legibility_stub(_: bytes) -> float:
    # Replace with real OCR if you like; keep 0.0–1.0
    return 0.95


def contrast_ratio_stub() -> float:
    return 5.0  # > 4.5 passes WCAG AA for text


def file_budget_ok(size_bytes: int, max_bytes: int = 310_000) -> bool:
    return size_bytes <= max_bytes
