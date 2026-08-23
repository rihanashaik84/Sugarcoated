"""Diet-profile checks with visible reasons, not just pass/fail."""

from __future__ import annotations

import re

from matching import normalize_text


VEGAN_EXCLUDE_KEYWORDS = [
    "milk solids",
    "whey",
    "ghee",
    "gelatin",
    "honey",
    "egg",
    "casein",
]

GLUTEN_KEYWORDS = [
    "wheat",
    "maida",
    "gluten",
    "barley",
    "malt",
]


def _keyword_hits(ingredients_text, keywords: list[str]) -> list[str]:
    text = normalize_text(ingredients_text)
    if not text:
        return []
    hits = []
    for keyword in keywords:
        pattern = r"(?<![A-Z0-9])" + re.escape(normalize_text(keyword)) + r"(?![A-Z0-9])"
        if re.search(pattern, text):
            hits.append(keyword)
    return hits


def check_vegan(ingredients_text) -> tuple[bool, list[str]]:
    if ingredients_text is None or str(ingredients_text).strip() == "":
        return False, ["No ingredient list was provided, so vegan status cannot be checked."]
    hits = _keyword_hits(ingredients_text, VEGAN_EXCLUDE_KEYWORDS)
    if hits:
        return False, [f"Contains non-vegan keyword: {item}" for item in hits]
    return True, ["No listed animal-derived keywords were found in the ingredient text."]


def check_gluten_free(ingredients_text) -> tuple[bool, list[str]]:
    if ingredients_text is None or str(ingredients_text).strip() == "":
        return False, ["No ingredient list was provided, so gluten status cannot be checked."]
    hits = _keyword_hits(ingredients_text, GLUTEN_KEYWORDS)
    if hits:
        return False, [f"Contains gluten-related keyword: {item}" for item in hits]
    return True, ["No listed gluten keywords were found in the ingredient text."]


def check_diabetic_friendly(sugar_g, threshold: float = 5) -> tuple[bool, str]:
    if sugar_g is None:
        return False, "Sugar per serving is missing, so this diabetic-friendly check cannot run."
    try:
        value = float(sugar_g)
    except (TypeError, ValueError):
        return False, "Sugar per serving is not a number, so this check cannot run."
    if value <= threshold:
        return True, f"Sugar is {value} g per serving, at or below the {threshold} g project threshold."
    return False, f"Sugar is {value} g per serving, above the {threshold} g project threshold."


def check_low_sodium(sodium_mg, per_100g: bool = True, threshold: float = 140) -> tuple[bool, str]:
    if sodium_mg is None:
        return False, "Sodium is missing, so this low-sodium check cannot run."
    try:
        value = float(sodium_mg)
    except (TypeError, ValueError):
        return False, "Sodium is not a number, so this check cannot run."
    basis = "per 100 g" if per_100g else "per serving"
    if value <= threshold:
        return True, f"Sodium is {value} mg {basis}, at or below the {threshold} mg 'low sodium' threshold."
    return False, f"Sodium is {value} mg {basis}, above the {threshold} mg 'low sodium' threshold."


def _to_float(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def check_profile(profile_name: str, product: dict) -> dict:
    """Return a consistent {passes, reasons} shape for any profile."""
    if not isinstance(product, dict):
        return {"passes": False, "reasons": ["No product record was provided."]}

    name = (profile_name or "").strip().lower().replace(" ", "_").replace("-", "_")
    ingredients = product.get("ingredients_raw")
    sugar = _to_float(product.get("Sugar_g"))
    sodium = _to_float(product.get("Sodium_mg"))

    if name in {"vegan"}:
        passes, reasons = check_vegan(ingredients)
        return {"passes": passes, "reasons": reasons}
    if name in {"gluten_free", "glutenfree"}:
        passes, reasons = check_gluten_free(ingredients)
        return {"passes": passes, "reasons": reasons}
    if name in {"diabetic_friendly", "diabetic"}:
        passes, reason = check_diabetic_friendly(sugar)
        return {"passes": passes, "reasons": [reason]}
    if name in {"low_sodium", "lowsodium"}:
        passes, reason = check_low_sodium(sodium, per_100g=True)
        return {"passes": passes, "reasons": [reason]}

    return {
        "passes": False,
        "reasons": [
            f"Unknown diet profile '{profile_name}'. Choose vegan, gluten_free, diabetic_friendly, or low_sodium."
        ],
    }
