"""Offline builder: CSV + red flags -> data/products.json. Run by the developer, not the app."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pandas as pd

from matching import load_red_flags, match_ingredients, normalize_text
from scoring import calculate_score, get_risk_level, normalize_to_ten


ROOT = Path(__file__).resolve().parent
FOODS_CSV = ROOT / "data" / "packaged_foods_india.csv"
REDFLAGS_CSV = ROOT / "data" / "redflag_ingredients.csv"
OUTPUT_JSON = ROOT / "data" / "products.json"

NUTRIENT_COLUMNS = [
    "Sugar_g",
    "Sodium_mg",
    "Total_Fat_g",
    "Saturated_Fat_g",
    "Trans_Fat_g",
    "Proteins_g",
    "Calories_kcal",
    "Carbohydrates_g",
]


def _to_number(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    if text == "" or text.lower() in {"nan", "none", "null"}:
        return None
    try:
        number = float(text)
    except (TypeError, ValueError):
        return None
    if pd.isna(number):
        return None
    return number


def build_product_record(row: dict, red_flags: list[dict]) -> dict:
    ingredients_raw = row.get("Ingredients")
    if ingredients_raw is not None and not isinstance(ingredients_raw, str):
        if pd.isna(ingredients_raw):
            ingredients_raw = ""
        else:
            ingredients_raw = str(ingredients_raw)

    normalized = normalize_text(ingredients_raw)
    matches = match_ingredients(normalized or ingredients_raw, red_flags)
    raw_score = calculate_score(matches)

    record = {
        "product_id": str(row.get("S.No") or "").strip(),
        "name": str(row.get("Item name") or "").strip(),
        "brand": str(row.get("Brand_Name") or "").strip(),
        "category": str(row.get("Category") or "").strip(),
        "sub_category": str(row.get("Sub_Category") or "").strip(),
        "ingredients_raw": ingredients_raw or "",
        "matched_ingredients": matches,
        "healthscore": normalize_to_ten(raw_score),
        "risk_level": get_risk_level(raw_score),
        "raw_score": raw_score,
        "Serving_Size_g": _to_number(row.get("Serving_Size_g")),
    }
    for column in NUTRIENT_COLUMNS:
        record[column] = _to_number(row.get(column))
    return record


def main() -> None:
    if not FOODS_CSV.exists():
        raise FileNotFoundError(f"Missing source file: {FOODS_CSV}")
    if not REDFLAGS_CSV.exists():
        raise FileNotFoundError(f"Missing source file: {REDFLAGS_CSV}")

    foods = pd.read_csv(FOODS_CSV, encoding="utf-8-sig")
    red_flags = load_red_flags(REDFLAGS_CSV)
    products = [build_product_record(row, red_flags) for row in foods.to_dict(orient="records")]

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as file:
        json.dump(products, file, indent=2, ensure_ascii=False)

    counts = Counter(product["risk_level"] for product in products)
    print(f"Wrote {len(products)} products to {OUTPUT_JSON}")
    print("Risk level distribution:")
    for level in ("Low", "Moderate", "High"):
        print(f"  {level}: {counts.get(level, 0)}")
    print(f"Red-flag ingredients loaded: {len(red_flags)}")


if __name__ == "__main__":
    main()
