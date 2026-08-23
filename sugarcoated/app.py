from __future__ import annotations

import json
from pathlib import Path

import streamlit as st
from rapidfuzz import fuzz, process

from alternates import find_alternates
from diet_profiles import check_profile
from macro_insights import (
    calculate_bmr_targets,
    daily_limits_for_intake,
    efficiency_ratio,
    find_better_efficiency_alternative,
    percent_of_daily_limit,
)
from matching import load_red_flags, match_ingredients
from scoring import calculate_score, get_risk_level, normalize_to_ten

st.markdown("""
<style>
    .stApp {
        background-color: #f7f5f0;
        color: #1a1a1a;
    }
    h1 { font-size: 2.1rem !important; font-weight: 700 !important; color: #1a1a1a !important; }
    h2 { font-size: 1.4rem !important; font-weight: 600 !important; color: #1a1a1a !important; }
    h3 { font-size: 1.1rem !important; font-weight: 600 !important; color: #1a1a1a !important; }
    p, label, .stMarkdown, span { color: #1a1a1a !important; }

    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        color: #1a1a1a !important;
        background-color: #ffffff !important;
        border: 1px solid #ccc !important;
        border-radius: 8px !important;
    }

    .stButton button {
        background-color: #1d9e75 !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 0.5rem 1.2rem !important;
        font-weight: 600 !important;
    }
    .stButton button:hover { background-color: #0f6e56 !important; }

    div[data-testid="stMetricValue"] { color: #1d9e75 !important; font-weight: 700 !important; }

    .stTabs [data-baseweb="tab"] {
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: #1a1a1a !important;
    }
    .stTabs [aria-selected="true"] {
        color: #1d9e75 !important;
        border-bottom: 3px solid #1d9e75 !important;
    }

    div[data-testid="stExpander"] {
        background-color: #ffffff !important;
        border-radius: 8px !important;
        border: 1px solid #e0e0e0 !important;
    }

    .card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 1.2rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main, .block-container {
        background-color: #f7f5f0 !important;
    }
    body { background-color: #f7f5f0 !important; }
</style>
""", unsafe_allow_html=True)

ROOT = Path(__file__).resolve().parent
PRODUCTS_PATH = ROOT / "data" / "products.json"
REDFLAGS_PATH = ROOT / "data" / "redflag_ingredients.csv"

PROFILE_OPTIONS = {
    "Vegan": "vegan",
    "Gluten-free": "gluten_free",
    "Diabetic-friendly": "diabetic_friendly",
    "Low sodium": "low_sodium",
}

NUTRIENT_FIELDS = [
    "Sugar_g",
    "Sodium_mg",
    "Total_Fat_g",
    "Saturated_Fat_g",
    "Trans_Fat_g",
    "Proteins_g",
    "Calories_kcal",
    "Carbohydrates_g",
]


def _to_float(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@st.cache_data(show_spinner=False)
def load_products() -> list[dict]:
    if not PRODUCTS_PATH.exists():
        raise FileNotFoundError(
            "data/products.json is missing. Run `python build_dataset.py` once, then reload."
        )
    with open(PRODUCTS_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list) or not data:
        raise ValueError("data/products.json is empty or not a list of products.")
    return data


@st.cache_data(show_spinner=False)
def load_flags() -> list[dict]:
    if not REDFLAGS_PATH.exists():
        raise FileNotFoundError("data/redflag_ingredients.csv is missing.")
    flags = load_red_flags(REDFLAGS_PATH)
    if not flags:
        raise ValueError("redflag_ingredients.csv loaded zero ingredients.")
    return flags


def unique_subcategories(products: list[dict]) -> list[str]:
    values = sorted({(p.get("sub_category") or "").strip() for p in products if (p.get("sub_category") or "").strip()})
    return values


def search_products(query: str, products: list[dict], limit: int = 12) -> list[tuple[float, dict]]:
    query = (query or "").strip()
    if not query:
        return []
    corpus = []
    index = []
    for product in products:
        label = f"{product.get('name') or ''} {product.get('brand') or ''}".strip()
        corpus.append(label)
        index.append(product)
    results = process.extract(query, corpus, scorer=fuzz.WRatio, limit=limit)
    ranked = []
    for _label, score, idx in results:
        if score >= 55:
            ranked.append((score, index[idx]))
    return ranked


def analyze_record(base: dict, ingredients_text: str, red_flags: list[dict]) -> dict:
    matches = match_ingredients(ingredients_text, red_flags)
    raw_score = calculate_score(matches)
    record = dict(base)
    record["ingredients_raw"] = ingredients_text
    record["matched_ingredients"] = matches
    record["raw_score"] = raw_score
    record["healthscore"] = normalize_to_ten(raw_score)
    record["risk_level"] = get_risk_level(raw_score)
    return record


def nutrition_present(record: dict) -> bool:
    return any(_to_float(record.get(field)) is not None for field in ("Sugar_g", "Sodium_mg", "Saturated_Fat_g", "Proteins_g", "Total_Fat_g", "Trans_Fat_g"))


def format_match_line(match: dict) -> str:
    original = (match.get("original_text") or "").strip()
    name = (match.get("ingredient_name") or "").strip()
    confidence = match.get("confidence")
    match_type = match.get("match_type")
    if match_type == "fuzzy":
        return f"{original} → {name} ({confidence}% match)"
    return name or original


def render_intake_form():
    if st.session_state.get("intake_done"):
        with st.expander("Your intake details (saved for this session)", expanded=False):
            data = st.session_state.intake_data or {}
            if data.get("skipped"):
                st.info("You skipped intake. Macro percentages use standard population daily limits.")
            else:
                st.write(
                    f"Weight: {data.get('weight_kg') or '—'} kg · "
                    f"Height: {data.get('height_cm') or '—'} cm · "
                    f"Age: {data.get('age') or '—'} · "
                    f"Gender: {data.get('gender') or '—'} · "
                    f"Diet: {data.get('diet_pref_label') or '—'}"
                )
            if st.button("Clear intake and enter again"):
                st.session_state.intake_done = False
                st.session_state.intake_data = None
                st.rerun()
        return

    st.subheader("Optional intake")
    st.caption("Used only to scale sugar and saturated-fat daily limits from estimated calories. Skip if you would rather use population guidelines.")
    with st.form("intake_form"):
        col1, col2, col3, col4 = st.columns(4)
        weight = col1.number_input("Weight (kg)", min_value=0.0, max_value=400.0, value=0.0, step=0.1)
        height = col2.number_input("Height (cm)", min_value=0.0, max_value=250.0, value=0.0, step=0.1)
        age = col3.number_input("Age", min_value=0, max_value=120, value=0, step=1)
        gender = col4.selectbox("Gender", ["", "Female", "Male"])
        diet_label = st.selectbox("Diet preference (optional)", ["", *PROFILE_OPTIONS.keys()])
        save = st.form_submit_button("Save intake")
        skip = st.form_submit_button("Skip — use population defaults")

    if skip:
        st.session_state.intake_data = {"skipped": True, "diet_pref": None, "diet_pref_label": None}
        st.session_state.intake_done = True
        st.rerun()

    if save:
        weight_v = weight if weight else None
        height_v = height if height else None
        age_v = age if age else None
        gender_v = gender or None
        st.session_state.intake_data = {
            "skipped": False,
            "weight_kg": weight_v,
            "height_cm": height_v,
            "age": age_v,
            "gender": gender_v,
            "diet_pref": PROFILE_OPTIONS.get(diet_label) if diet_label else None,
            "diet_pref_label": diet_label or None,
        }
        st.session_state.intake_done = True
        st.rerun()


def healthscore_tab(record: dict, products: list[dict]):
    score = record.get("healthscore")
    risk = record.get("risk_level")
    st.metric("Healthscore", f"{score}/10" if score is not None else "Unavailable", help="10 is cleanest. 0 is saturated with red-flag severity points.")
    st.write(f"Internal risk bucket (raw severity points): **{risk}**")
    st.caption("Low = 0–4 points, Moderate = 5–9, High = 10+. The /10 number is a scaled inverse of those points.")

    matches = record.get("matched_ingredients") or []
    if not matches:
        st.success("No red-flag ingredients matched this list.")
    else:
        st.markdown("**Matched ingredients**")
        rows = []
        for match in matches:
            rows.append(
                {
                    "Shown as": format_match_line(match),
                    "Category": match.get("category") or "—",
                    "Severity": match.get("severity") or "—",
                    "Match": match.get("match_type") or "—",
                    "Confidence": match.get("confidence"),
                }
            )
        st.dataframe(rows, hide_index=True, use_container_width=True)

    if not record.get("sub_category"):
        st.warning("No sub-category is set, so same-category alternatives cannot be suggested.")
        return

    if not (record.get("ingredients_raw") or "").strip():
        st.info("Enter ingredients above to see alternates.")
    return

    alts = find_alternates(
        record,
        products,
        sort_key_fn=lambda p: _to_float(p.get("healthscore")) or 0.0,
        top_n=3,
    )
    
    st.markdown("**Better healthscore in the same sub-category**")
    if not alts:
        st.info(f"No other catalog products found in sub-category “{record.get('sub_category')}”.")
        return
    for alt in alts:
        st.write(
            f"- {alt.get('name')} ({alt.get('brand')}) — {alt.get('healthscore')}/10, {alt.get('risk_level')}"
        )


def macros_tab(record: dict, products: list[dict], intake_data: dict | None):
    if record.get("source") == "custom" and not nutrition_present(record):
        st.warning(
            "This is a custom ingredient paste with no nutrition fields filled in. "
            "The Macros tab needs sugar, sodium, fat, or protein numbers. "
            "Open “Add nutrition info” on the input form, or search a catalog product instead."
        )
        return

    bmr = None
    if intake_data and not intake_data.get("skipped"):
        bmr = calculate_bmr_targets(
            intake_data.get("weight_kg"),
            intake_data.get("height_cm"),
            intake_data.get("age"),
            intake_data.get("gender"),
        )

    limits = daily_limits_for_intake(bmr)
    if limits["source"] == "bmr_adjusted":
        st.info(
            f"Using BMR-adjusted daily limits from Mifflin-St Jeor "
            f"(~{int(bmr['calorie_target'])} kcal estimate; protein target {bmr['protein_target_g']} g). "
            "Sodium stays at the ICMR-NIN 2000 mg/day cap. This is not medical advice."
        )
    else:
        if intake_data and not intake_data.get("skipped") and bmr is None:
            st.warning(
                "Intake was saved but weight, height, age, and gender were not all filled, "
                "so BMR could not be calculated. Falling back to population daily limits."
            )
        else:
            st.info(
                "Using population daily limits: WHO 25 g free sugar, ICMR-NIN 2000 mg sodium, "
                "22 g saturated fat. Applied per serving as printed — not a personal medical threshold."
            )

    sugar = _to_float(record.get("Sugar_g"))
    sodium = _to_float(record.get("Sodium_mg"))
    sat = _to_float(record.get("Saturated_Fat_g"))
    trans = _to_float(record.get("Trans_Fat_g"))
    protein = _to_float(record.get("Proteins_g"))
    fat = _to_float(record.get("Total_Fat_g"))

    c1, c2, c3 = st.columns(3)
    sugar_pct = percent_of_daily_limit(sugar, limits["sugar_g"])
    sodium_pct = percent_of_daily_limit(sodium, limits["sodium_mg"])
    sat_pct = percent_of_daily_limit(sat, limits["saturated_fat_g"])

    if sugar is None:
        c1.error("Sugar (g) is missing for this product.")
    else:
        c1.metric("Sugar vs daily limit", f"{sugar_pct}%" if sugar_pct is not None else "—", f"{sugar} g / {limits['sugar_g']} g")

    if sodium is None:
        c2.error("Sodium (mg) is missing for this product.")
    else:
        c2.metric("Sodium vs daily limit", f"{sodium_pct}%" if sodium_pct is not None else "—", f"{sodium} mg / {limits['sodium_mg']} mg")

    if sat is None:
        c3.error("Saturated fat (g) is missing for this product.")
    else:
        c3.metric("Saturated fat vs daily limit", f"{sat_pct}%" if sat_pct is not None else "—", f"{sat} g / {limits['saturated_fat_g']} g")

    st.markdown("**Trans fat**")
    if trans is None:
        st.warning("Trans fat is not in this record, so presence cannot be judged.")
    elif trans > 0:
        st.error(f"Trans fat is present on the label: {trans} g per serving.")
    else:
        st.success("Trans fat is listed as 0 g (absent on the nutrition panel).")

    st.markdown("**Protein per gram of fat (same sub-category)**")
    ratio = efficiency_ratio(protein, fat)
    if protein is None or fat is None:
        st.warning("Protein and/or total fat is missing, so an efficiency ratio cannot be calculated.")
        return
    if ratio is None:
        st.warning("Total fat is 0, so protein/fat efficiency is undefined (division by zero avoided).")
        return

    st.write(f"This product: **{ratio:.2f}** g protein per g fat ({protein} g protein / {fat} g fat).")
    alts = find_better_efficiency_alternative(record, products, ("Proteins_g", "Total_Fat_g"))
    if not alts:
        st.info("No same-category catalog products with a usable fat value were found for comparison.")
        return
    st.caption("Alternatives sorted by protein/fat, highest first.")
    for alt in alts:
        alt_ratio = efficiency_ratio(alt.get("Proteins_g"), alt.get("Total_Fat_g"))
        label = f"{alt_ratio:.2f}" if alt_ratio is not None else "n/a"
        st.write(f"- {alt.get('name')} ({alt.get('brand')}) — {label} g protein / g fat")


def dietician_tab(record: dict, products: list[dict], intake_data: dict | None):
    default_key = None
    if intake_data:
        saved = intake_data.get("diet_pref")
        for label, key in PROFILE_OPTIONS.items():
            if key == saved:
                default_key = label
                break
    labels = list(PROFILE_OPTIONS.keys())
    index = labels.index(default_key) if default_key in labels else 0
    chosen_label = st.selectbox("Diet profile", labels, index=index)
    profile_key = PROFILE_OPTIONS[chosen_label]

    result = check_profile(profile_key, record)
    if result["passes"]:
        st.success(f"Passes {chosen_label}.")
    else:
        st.error(f"Does not pass {chosen_label}.")

    for reason in result.get("reasons") or ["No reason was returned."]:
        st.write(f"- {reason}")

    if result["passes"]:
        return

    def passes_profile(product: dict) -> bool:
        return bool(check_profile(profile_key, product).get("passes"))

    if not (record.get("ingredients_raw") or "").strip():
        st.info("Enter ingredients above to see alternates.")
        return
    
    alts = find_alternates(
        record,
        products,
        sort_key_fn=lambda p: _to_float(p.get("healthscore")) or 0.0,
        filter_fn=passes_profile,
        top_n=3,
    )
    st.markdown(f"**Same sub-category alternatives that pass {chosen_label}**")
    if not alts:
        st.info(
            f"No catalog products in “{record.get('sub_category') or 'unknown'}” passed this profile. "
            "That can happen when the category is small or the rule is strict."
        )
        return
    for alt in alts:
        st.write(f"- {alt.get('name')} ({alt.get('brand')}) — {alt.get('healthscore')}/10")


def main():
    st.set_page_config(page_title="Sugarcoated", page_icon="🍬", layout="wide")
    st.markdown(
        """
        <style>
        .stApp { background: #f7f1e8; }
        h1, h2, h3 { font-family: Georgia, serif; color: #4a2c12; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("Sugarcoated")
    st.caption("Ingredient-level risk flags for Indian packaged foods. Not medical advice.")

    if "intake_done" not in st.session_state:
        st.session_state.intake_done = False
    if "intake_data" not in st.session_state:
        st.session_state.intake_data = None
    if "current_product_record" not in st.session_state:
        st.session_state.current_product_record = None

    try:
        products = load_products()
        red_flags = load_flags()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        st.error(str(exc))
        st.stop()

    render_intake_form()
    if not st.session_state.intake_done:
        st.stop()

    st.subheader("Look up a product")
    mode = st.radio("Input mode", ["Search existing product", "Paste custom ingredients"], horizontal=True)

    if mode == "Search existing product":
        query = st.text_input("Product name or brand", placeholder="e.g. hide n seek, britania, amul")
        if query.strip():
            hits = search_products(query, products)
            if not hits:
                st.error("No catalog products matched that search. Try another spelling, or paste ingredients instead.")
            else:
                labels = [f"{p.get('name')} — {p.get('brand')} ({int(score)}% name/brand match)" for score, p in hits]
                choice = st.selectbox("Pick a product", labels)
                if st.button("Analyze selected product", type="primary"):
                    selected = hits[labels.index(choice)][1]
                    ingredients = selected.get("ingredients_raw") or ""
                    if not str(ingredients).strip():
                        st.error("This catalog row has no ingredient text, so it cannot be analyzed.")
                    else:
                        st.session_state.current_product_record = analyze_record(
                            {**selected, "source": "catalog"},
                            ingredients,
                            red_flags,
                        )
                        st.rerun()
    else:
        ingredients = st.text_area("Ingredient list", height=140, placeholder="Sugar, refined palm oil, milk solids, ...")
        subcats = unique_subcategories(products)
        if not subcats:
            st.error("products.json has no sub_category values, so paste mode cannot suggest alternatives.")
            st.stop()
        category = st.selectbox("Sub-category (required for alternatives)", [""] + subcats)
        with st.expander("Add nutrition info (optional)"):
            st.caption("Leave blank if you only have the ingredient list. Macro percentages will be skipped rather than faked.")
            n1, n2, n3, n4 = st.columns(4)
            sugar = n1.number_input("Sugar (g)", min_value=0.0, value=0.0, step=0.1)
            sodium = n2.number_input("Sodium (mg)", min_value=0.0, value=0.0, step=1.0)
            fat = n3.number_input("Total fat (g)", min_value=0.0, value=0.0, step=0.1)
            protein = n4.number_input("Protein (g)", min_value=0.0, value=0.0, step=0.1)
            n5, n6, n7 = st.columns(3)
            sat = n5.number_input("Saturated fat (g)", min_value=0.0, value=0.0, step=0.1)
            trans = n6.number_input("Trans fat (g)", min_value=0.0, value=0.0, step=0.01)
            filled = st.checkbox("I filled the nutrition fields above (unchecked = treat as missing)")

        if st.button("Analyze pasted ingredients", type="primary"):
            if not (ingredients or "").strip():
                st.error("Ingredient text is required.")
            elif not category:
                st.error("Choose a sub-category so same-category alternatives can be found.")
            else:
                base = {
                    "product_id": "custom",
                    "name": "Custom ingredient list",
                    "brand": "User input",
                    "category": "",
                    "sub_category": category,
                    "source": "custom",
                    "Sugar_g": sugar if filled else None,
                    "Sodium_mg": sodium if filled else None,
                    "Total_Fat_g": fat if filled else None,
                    "Saturated_Fat_g": sat if filled else None,
                    "Trans_Fat_g": trans if filled else None,
                    "Proteins_g": protein if filled else None,
                    "Calories_kcal": None,
                    "Carbohydrates_g": None,
                }
                st.session_state.current_product_record = analyze_record(base, ingredients, red_flags)
                st.rerun()

    record = st.session_state.current_product_record
    if record is None:
        st.info("Search or paste ingredients to see Healthscore, Macros, and Dietician tabs.")
        return

    st.markdown("---")
    st.markdown(f"### {record.get('name')}  \n{record.get('brand')} · {record.get('sub_category') or 'no category'}")

    tab_health, tab_macros, tab_diet = st.tabs(["Healthscore", "Macros", "Dietician"])
    with tab_health:
        healthscore_tab(record, products)
    with tab_macros:
        macros_tab(record, products, st.session_state.intake_data)
    with tab_diet:
        dietician_tab(record, products, st.session_state.intake_data)


if __name__ == "__main__":
    main()
