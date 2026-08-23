# Sugarcoated

Sugarcoated is a local analyzer for Indian packaged-food labels. It flags red-flag ingredients (added sugars, trans-fat sources, refined flours, and similar), turns those hits into a 0–10 healthscore, and shows how one serving sits against everyday sugar, sodium, and fat limits — plus simple diet-profile checks (vegan, gluten-free, diabetic-friendly, low sodium) and same-category alternatives. It exists because front-of-pack marketing is easier to read than a comma-separated ingredient list, and because most of this dataset is biscuits, namkeen, and drinks that hide sugar and fat under technical names.

## Architecture

There are two layers, on purpose:

1. **Offline pipeline** (`sugarcoated/build_dataset.py`) — run by a developer when the CSVs change. It reads `sugarcoated/data/packaged_foods_india.csv` and `sugarcoated/data/redflag_ingredients.csv`, calls the same matching and scoring modules the app uses, and writes `sugarcoated/data/products.json`. That file is the catalog the UI searches and the pool for alternatives. Precomputing 852 products keeps the app snappy and keeps matching deterministic for the catalog.
2. **Runtime app** (`sugarcoated/app.py` + shared modules) — Streamlit only. No Flask, no browser localStorage, no live network calls. Lookups read local JSON/CSV. When you search a product or paste ingredients, matching and scoring run once, the result is cached in Streamlit session state, and the three tabs read that cache.

Splitting them avoids re-scoring the whole catalog on every page load, while still using one matching implementation for both batch and live paste.

## Files

| File | Owns |
| --- | --- |
| `sugarcoated/matching.py` | The only ingredient matcher: comma tokens, word-boundary exact match, then RapidFuzz, then overlap cleanup. |
| `sugarcoated/scoring.py` | Severity points, raw score, Low/Moderate/High buckets, 0–10 healthscore. |
| `sugarcoated/build_dataset.py` | One-shot CSV → `data/products.json`, plus a printed risk-level summary. |
| `sugarcoated/alternates.py` | One generic same-`sub_category` top-N finder used by every tab. |
| `sugarcoated/macro_insights.py` | Mifflin-St Jeor targets, % of daily limit, protein/fat efficiency, efficiency alternatives. |
| `sugarcoated/diet_profiles.py` | Vegan / gluten-free / diabetic-friendly / low-sodium checks with reasons. |
| `sugarcoated/app.py` | Streamlit UI: intake, search vs paste, three tabs. |
| `sugarcoated/data/packaged_foods_india.csv` | Source product + nutrition table (untouched by the app). |
| `sugarcoated/data/redflag_ingredients.csv` | Source red-flag dictionary (untouched by the app). |
| `sugarcoated/data/products.json` | Generated catalog. Regenerate; do not hand-edit as source of truth. |
| `sugarcoated/requirements.txt` | `streamlit`, `pandas`, `rapidfuzz`. |

## How to run

From the `sugarcoated` directory:

```bash
pip install -r requirements.txt
python build_dataset.py
streamlit run app.py
```

Re-run `python build_dataset.py` whenever either source CSV changes.

## Input modes

- **Search existing product** — type a name or brand. RapidFuzz ranks catalog rows so a misspelling can still surface the right pack. You pick from the ranked list.
- **Paste custom ingredients** — paste the ingredient line from a pack that is not in the 852-row catalog. A **sub-category is required** because alternatives are “other products in the same sub-category.” Without it, the Healthscore and Dietician tabs would have nothing to compare against. Nutrition fields are optional; if you skip them, the Macros tab says so instead of showing empty numbers.

## Scoring methodology

Each matched red flag adds points:

| Severity | Points |
| --- | ---: |
| High | 5 |
| Medium | 3 |
| Low | 1 |

The **raw score** is the sum of those points. Internal buckets (same as the original project):

- **Low** — 0–4 points
- **Moderate** — 5–9 points
- **High** — 10+ points

The user-facing **healthscore** is that raw total scaled onto 0–10, inverted (10 = cleanest). The scale saturates at 25 raw points — five high-severity flags — anything harsher still maps to 0. Fuzzy matches are shown as `original token → matched name (confidence%)`; they are never silent corrections.

## Nutrient limit sources

Applied **per serving as stored in the dataset** (or as you typed), not as a full-day diet:

- **Free sugars** — WHO adult guidance of 25 g/day (about 5% of a 2000 kcal diet). If you enter weight, height, age, and gender, sugar and saturated-fat caps are scaled by estimated Mifflin-St Jeor calories vs 2000 kcal.
- **Sodium** — ICMR-NIN population guidance of 2000 mg/day. This cap is **not** scaled with BMR.
- **Saturated fat** — 22 g/day as a simple 10%-of-2000-kcal stand-in.
- **Trans fat** — flagged as present vs absent on the panel, in the spirit of FSSAI limits on industrially produced trans fat, not as a percentage of a daily allowance.

These are **population-level guidelines applied to a single serving**. They are not personalized medical thresholds. **Sugarcoated is not medical advice** and is not a diagnosis, allergen lab, or substitute for a clinician or the legal label.

## Scope and limitations

- **No OpenFoodFacts (or other) live integration.** The catalog is a static local extract of **852** Indian packaged foods.
- **No OCR.** You search or paste text; the app does not read photos of packs.
- **Fuzzy matching at 85 is a heuristic.** OCR typos in the source data (for example salt spelling variants) may still miss or over-match.
- **BMR is Mifflin-St Jeor**, a standard estimate, not a clinical calculation. Incomplete intake falls back to population RDAs instead of guessing.
- Diet-profile keyword lists are small and English-label oriented; they will miss unnamed derivatives and non-listed allergens.

## Credits

Built by **Rihana Shaik** and **Jack** as a two-person hackathon project. Dataset: [Indian Packaged Foods Nutritional Dataset 2026](https://www.kaggle.com/datasets/lalit7881/indian-packaged-foods-nutritional-dataset-2026) on Kaggle.
