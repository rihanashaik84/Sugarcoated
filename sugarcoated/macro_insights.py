"""Daily-limit percentages, BMR targets, and protein/fat efficiency."""

from __future__ import annotations

from alternates import find_alternates


# Population fallbacks used when intake data is incomplete.
WHO_SUGAR_G = 25.0
ICMR_NIN_SODIUM_MG = 2000.0
SATURATED_FAT_G = 22.0
REFERENCE_KCAL = 2000.0


def calculate_bmr_targets(weight_kg, height_cm, age, gender):
    """
    Mifflin-St Jeor BMR. Returns None if any input is missing so the caller
    can fall back to standard population RDAs.
    """
    if weight_kg is None or height_cm is None or age is None or gender is None:
        return None
    if str(gender).strip() == "" or str(weight_kg) == "" or str(height_cm) == "" or str(age) == "":
        return None

    try:
        weight = float(weight_kg)
        height = float(height_cm)
        years = float(age)
    except (TypeError, ValueError):
        return None

    if weight <= 0 or height <= 0 or years <= 0:
        return None

    sex = str(gender).strip().lower()
    if sex in {"male", "m", "man"}:
        bmr = 10 * weight + 6.25 * height - 5 * years + 5
    elif sex in {"female", "f", "woman"}:
        bmr = 10 * weight + 6.25 * height - 5 * years - 161
    else:
        return None

    return {
        "calorie_target": round(bmr, 0),
        "protein_target_g": round(weight * 1.5, 1),
    }


def percent_of_daily_limit(nutrient_value, limit):
    if nutrient_value is None or limit is None:
        return None
    try:
        value = float(nutrient_value)
        cap = float(limit)
    except (TypeError, ValueError):
        return None
    if cap == 0:
        return None
    return round((value / cap) * 100.0, 1)


def efficiency_ratio(numerator, denominator):
    if denominator is None or numerator is None:
        return None
    try:
        top = float(numerator)
        bottom = float(denominator)
    except (TypeError, ValueError):
        return None
    if bottom == 0:
        return None
    return top / bottom


def daily_limits_for_intake(bmr_targets: dict | None) -> dict:
    """
    Sugar and saturated fat scale with estimated calories vs a 2000 kcal
    reference. Sodium stays at the ICMR-NIN 2000 mg/day population cap.
    """
    sugar = WHO_SUGAR_G
    sodium = ICMR_NIN_SODIUM_MG
    sat_fat = SATURATED_FAT_G
    source = "population"

    if bmr_targets and bmr_targets.get("calorie_target"):
        calories = float(bmr_targets["calorie_target"])
        if calories > 0:
            scale = calories / REFERENCE_KCAL
            sugar = round(WHO_SUGAR_G * scale, 1)
            sat_fat = round(SATURATED_FAT_G * scale, 1)
            source = "bmr_adjusted"

    return {
        "sugar_g": sugar,
        "sodium_mg": sodium,
        "saturated_fat_g": sat_fat,
        "source": source,
    }


def find_better_efficiency_alternative(product, all_products, ratio_field_pair):
    """Same sub_category, exclude zero-denominator products, sort by ratio desc."""
    if not ratio_field_pair or len(ratio_field_pair) != 2:
        return []
    num_field, den_field = ratio_field_pair

    def has_denominator(candidate):
        ratio = efficiency_ratio(candidate.get(num_field), candidate.get(den_field))
        return ratio is not None

    def sort_key(candidate):
        ratio = efficiency_ratio(candidate.get(num_field), candidate.get(den_field))
        return ratio if ratio is not None else float("-inf")

    return find_alternates(
        product,
        all_products,
        sort_key_fn=sort_key,
        filter_fn=has_denominator,
        top_n=3,
    )
