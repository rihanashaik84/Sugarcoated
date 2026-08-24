from __future__ import annotations

import base64
import json
import urllib.parse
from pathlib import Path

import streamlit as st
from rapidfuzz import fuzz, process

from alternates import find_alternates
from diet_profiles import check_profile
from image_fetch import get_category_icon, get_product_image
from macro_insights import (
    calculate_bmr_targets,
    daily_limits_for_intake,
    efficiency_ratio,
    find_better_efficiency_alternative,
    percent_of_daily_limit,
)
from matching import load_red_flags, match_ingredients
from scoring import calculate_score, get_risk_level, normalize_to_ten

# ─────────────────────────────────────────────────────────────────────────────
# Modern SaaS Dashboard Design System (Inter / Jakarta + Linear / Notion Aesthetic)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Playfair+Display:wght@700&display=swap');

    :root {
        --primary: #00B86B;
        --primary-dark: #009E5C;
        --primary-glow: rgba(0, 184, 107, 0.25);
        --secondary: #1E293B;
        --navy: #1A1A2E;
        --dark-green: #0F3D2E;
        --bg-app: #F8FAFC;
        --surface: #FFFFFF;
        --border: #E2E8F0;
        --text-main: #0F172A;
        --text-muted: #64748B;
        --badge-low-bg: #DCFCE7;
        --badge-low-text: #15803D;
        --badge-low-dot: #16A34A;
        --badge-mod-bg: #FEF3C7;
        --badge-mod-text: #B45309;
        --badge-mod-dot: #D97706;
        --badge-high-bg: #FEE2E2;
        --badge-high-text: #B91C1C;
        --badge-high-dot: #DC2626;
    }

    /* Global base */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"], .main {
        background-color: var(--bg-app) !important;
        color: var(--text-main) !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    }

    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3.5rem !important;
        max-width: 1120px !important;
    }

    /* Typography */
    h1, h2, h3, h4 {
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif !important;
        letter-spacing: -0.02em !important;
    }
    h1 {
        font-size: 2.1rem !important;
        font-weight: 800 !important;
        color: #0F172A !important;
    }
    h2 {
        font-size: 1.35rem !important;
        font-weight: 700 !important;
        color: #1E293B !important;
        margin-top: 1.5rem !important;
        margin-bottom: 0.75rem !important;
    }
    h3 {
        font-size: 1.1rem !important;
        font-weight: 700 !important;
        color: #334155 !important;
        margin-top: 1rem !important;
    }
    p, label, .stMarkdown, span {
        color: #334155 !important;
    }

    /* Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, #1A1A2E 0%, #0F3D2E 100%);
        border-radius: 20px;
        padding: 3rem 2.5rem;
        color: #FFFFFF;
        box-shadow: 0 12px 32px -4px rgba(15, 61, 46, 0.28);
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }
    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(255, 255, 255, 0.12);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 9999px;
        padding: 4px 14px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: #A7F3D0;
        margin-bottom: 1rem;
    }
    .hero-title {
        font-size: 2.4rem;
        font-weight: 800;
        line-height: 1.15;
        letter-spacing: -0.03em;
        color: #FFFFFF !important;
        margin-bottom: 0.6rem;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        color: #CBD5E1 !important;
        line-height: 1.5;
        max-width: 680px;
        font-weight: 400;
    }

    /* SaaS Cards with Hover Lift */
    .saas-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.04), 0 2px 6px -1px rgba(0, 0, 0, 0.02);
        margin-bottom: 1.5rem;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .saas-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 28px -4px rgba(0, 0, 0, 0.08), 0 4px 10px -2px rgba(0, 0, 0, 0.04);
        border-color: #CBD5E1;
    }

    /* Risk Score Badges with Dot Indicator */
    .badge-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.01em;
    }
    .badge-low {
        background: var(--badge-low-bg);
        color: var(--badge-low-text) !important;
        border: 1px solid #BBF7D0;
    }
    .badge-low .badge-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background-color: var(--badge-low-dot);
    }
    .badge-mod {
        background: var(--badge-mod-bg);
        color: var(--badge-mod-text) !important;
        border: 1px solid #FDE68A;
    }
    .badge-mod .badge-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background-color: var(--badge-mod-dot);
    }
    .badge-high {
        background: var(--badge-high-bg);
        color: var(--badge-high-text) !important;
        border: 1px solid #FECACA;
    }
    .badge-high .badge-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background-color: var(--badge-high-dot);
    }

    /* Form Inputs */
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        color: #0F172A !important;
        background-color: #FFFFFF !important;
        border: 1.5px solid #E2E8F0 !important;
        border-radius: 12px !important;
        padding: 0.65rem 0.95rem !important;
        font-size: 0.95rem !important;
        transition: all 0.15s ease !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus, .stSelectbox select:focus {
        border-color: #00B86B !important;
        box-shadow: 0 0 0 3px rgba(0, 184, 107, 0.18) !important;
    }

    /* Buttons: Rounded-Full Gradient with Hover Glow */
    .stButton button {
        background: linear-gradient(135deg, #00B86B 0%, #009E5C 100%) !important;
        color: #FFFFFF !important;
        border-radius: 9999px !important;
        border: none !important;
        padding: 0.6rem 1.6rem !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        letter-spacing: -0.01em !important;
        box-shadow: 0 4px 14px 0 rgba(0, 184, 107, 0.35) !important;
        transition: all 0.2s ease !important;
    }
    .stButton button:hover {
        background: linear-gradient(135deg, #009E5C 0%, #00874E 100%) !important;
        box-shadow: 0 6px 20px 0 rgba(0, 184, 107, 0.45) !important;
        transform: translateY(-1px) !important;
    }
    .stButton button:active {
        transform: translateY(0px) !important;
    }

    /* Tab Navigation */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background-color: #F1F5F9;
        padding: 0.35rem;
        border-radius: 14px;
        margin-bottom: 1.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px !important;
        padding: 0.55rem 1.25rem !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        color: #475569 !important;
        border: none !important;
        background: transparent !important;
        transition: all 0.15s ease !important;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #00B86B !important;
        font-weight: 700 !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06) !important;
    }

    /* Store Pill Links */
    .store-pill {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 5px 12px;
        border-radius: 9999px;
        font-size: 0.76rem;
        font-weight: 700;
        text-decoration: none !important;
        transition: all 0.15s ease;
    }
    .store-pill-blinkit {
        background-color: #FEF08A;
        color: #713F12 !important;
        border: 1px solid #FDE047;
    }
    .store-pill-blinkit:hover {
        background-color: #FDE047;
    }
    .store-pill-zepto {
        background-color: #EDE9FE;
        color: #5B21B6 !important;
        border: 1px solid #DDD6FE;
    }
    .store-pill-zepto:hover {
        background-color: #DDD6FE;
    }

    div[data-testid="stMetricValue"] {
        color: #00B86B !important;
        font-weight: 800 !important;
    }
    .stApp {
        background: linear-gradient(180deg, #EEFBF5 0%, #F8F9FA 500px, #F8F9FA 100%) !important;
    }
 
    .big-score {
        font-size: 4.5rem !important;
        font-weight: 800 !important;
        line-height: 1 !important;
        margin: 0.2rem 0 !important;
    }
    .big-score.low { color: #00875A !important; }
    .big-score.moderate { color: #B45309 !important; }
    .big-score.high { color: #B91C1C !important; }
 
    .score-hero {
        background: #ffffff;
        border-radius: 20px;
        padding: 2rem;
        text-align: center;
        box-shadow: 0 6px 28px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
        border: 1px solid #E5E7EB;
    }
    .score-hero .label {
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 1.5px;
        color: #6B7280;
        text-transform: uppercase;
    }
 
    div[data-testid="stExpander"] {
        background-color: #ffffff !important;
        border-radius: 14px !important;
        border: 1px solid #E5E7EB !important;
        box-shadow: 0 2px 12px rgba(0,0,0,0.04) !important;
    }
 
    .stButton button, .stLinkButton a {
        background: linear-gradient(135deg, #00B86B, #009E5C) !important;
        color: #ffffff !important;
        border-radius: 999px !important;
        border: none !important;
        padding: 0.6rem 1.4rem !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 14px rgba(0,184,107,0.3) !important;
        transition: all 0.15s ease !important;
    }
    .stButton button:hover, .stLinkButton a:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(0,184,107,0.4) !important;
    }
 
    div[data-testid="column"] > div {
        background: #ffffff;
        border-radius: 16px;
        padding: 1rem;
        box-shadow: 0 3px 16px rgba(0,0,0,0.06);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
        border: 1px solid #F0F0F0;
    }
    div[data-testid="column"] > div:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.1);
    }
 
    .stTextInput input {
        border-radius: 12px !important;
        border: 2px solid #E5E7EB !important;
        padding: 0.7rem 1rem !important;
    }
    .stTextInput input:focus {
        border-color: #00B86B !important;
        box-shadow: 0 0 0 3px rgba(0,184,107,0.15) !important;
    }
       .block-container {
        padding-top: 2rem !important;
        max-width: 1100px !important;
    }
 
    div[data-testid="stVerticalBlock"] > div {
        gap: 0.6rem !important;
    }
 
    /* Make any st.image bigger by default */
    div[data-testid="stImage"] img {
        border-radius: 14px !important;
        min-width: 90px !important;
    }
 
    /* Tighten default Streamlit element spacing */
    div[data-testid="element-container"] {
        margin-bottom: 0.4rem !important;
    }
 
    .score-hero {
        padding: 2.5rem !important;
    }
    .big-score {
        font-size: 5.5rem !important;
    }
 
</style>
""", unsafe_allow_html=True)

ROOT = Path(__file__).resolve().parent
PRODUCTS_PATH = ROOT / "data" / "products.json"
REDFLAGS_PATH = ROOT / "data" / "redflag_ingredients.csv"
INTAKE_PATH = ROOT / "data" / "last_intake.json"

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


def load_saved_intake() -> dict | None:
    try:
        if INTAKE_PATH.exists():
            with open(INTAKE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return None


def save_intake_to_disk(data: dict) -> None:
    try:
        INTAKE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(INTAKE_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def delete_saved_intake() -> None:
    try:
        if INTAKE_PATH.exists():
            INTAKE_PATH.unlink(missing_ok=True)
    except Exception:
        pass


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


def _get_risk_badge_html(score: float | None, risk: str) -> str:
    """Return an HTML snippet for a pill-shaped risk badge with a dot indicator."""
    score_str = f"{score}/10" if score is not None else "—"
    risk_clean = (risk or "Unknown").capitalize()
    if risk_clean == "Low":
        cls = "badge-low"
    elif risk_clean == "Moderate":
        cls = "badge-mod"
    else:
        cls = "badge-high"
    return f'<span class="badge-pill {cls}"><span class="badge-dot"></span>{score_str} · {risk_clean} Risk</span>'


def _render_product_image(name: str, brand: str, sub_category: str, width: int = 64) -> None:
    """Display a product image (OFF API) or a category icon fallback. Never crashes."""
    try:
        img_url = get_product_image(name, brand)
        if img_url and str(img_url).startswith("http"):
            st.image(str(img_url), width=width)
            return
        icon_path = Path(get_category_icon(sub_category or ""))
        if icon_path.exists():
            b64_svg = base64.b64encode(icon_path.read_bytes()).decode("utf-8")
            html = f'<img src="data:image/svg+xml;base64,{b64_svg}" width="{width}" height="{width}" style="border-radius:12px; display:block; object-fit:contain; background:#F1F5F9; padding:4px; border:1px solid #E2E8F0;" />'
            st.markdown(html, unsafe_allow_html=True)
    except Exception:
        pass


def render_big_score(score: float, risk_level: str):
    risk_class = risk_level.lower()
    st.markdown(f"""
    <div class="score-hero">
        <div class="label">Healthscore</div>
        <div class="big-score {risk_class}">{score}<span style="font-size:1.5rem;color:#9CA3AF;">/10</span></div>
        <div style="font-weight:600; color:#374151; font-size:1.1rem;">{risk_level} Risk</div>
    </div>
    """, unsafe_allow_html=True)

def _build_search_links(name: str, brand: str) -> str:
    """Return markdown links for Blinkit and Zepto styled as rounded pill buttons."""
    q = urllib.parse.quote(f"{name} {brand}".strip())
    blinkit = f"https://blinkit.com/s/?q={q}"
    zepto = f"https://www.zeptonow.com/search?query={q}"
    return f'<a href="{blinkit}" target="_blank" class="store-pill store-pill-blinkit">🛒 Blinkit</a> &nbsp; <a href="{zepto}" target="_blank" class="store-pill store-pill-zepto">⚡ Zepto</a>'


def render_intake_form():
    if st.session_state.get("intake_done"):
        with st.expander("👤 Your saved profile & intake", expanded=False):
            data = st.session_state.intake_data or {}
            if data.get("skipped"):
                st.info("You skipped intake. Macro percentages use standard population daily limits.")
            else:
                st.write(
                    f"**Weight:** {data.get('weight_kg') or '—'} kg  ·  "
                    f"**Height:** {data.get('height_cm') or '—'} cm  ·  "
                    f"**Age:** {data.get('age') or '—'}  ·  "
                    f"**Gender:** {data.get('gender') or '—'}  ·  "
                    f"**Diet:** {data.get('diet_pref_label') or '—'}"
                )
            if st.button("Reset my details"):
                delete_saved_intake()
                st.session_state.intake_done = False
                st.session_state.intake_data = None
                st.rerun()
        return

    st.subheader("Personalize your intake (optional)")
    st.caption("Used only to scale sugar and saturated-fat daily limits from estimated calories. Skip if you prefer standard population guidelines.")
    with st.form("intake_form"):
        col1, col2, col3, col4 = st.columns(4)
        weight = col1.number_input("Weight (kg)", min_value=0.0, max_value=400.0, value=0.0, step=0.1)
        height = col2.number_input("Height (cm)", min_value=0.0, max_value=250.0, value=0.0, step=0.1)
        age = col3.number_input("Age", min_value=0, max_value=120, value=0, step=1)
        gender = col4.selectbox("Gender", ["", "Female", "Male"])
        diet_label = st.selectbox("Diet preference (optional)", ["", *PROFILE_OPTIONS.keys()])
        
        c_save, c_skip = st.columns([1, 2])
        save = c_save.form_submit_button("Save profile")
        skip = c_skip.form_submit_button("Skip — use population defaults")

    if skip:
        st.session_state.intake_data = {"skipped": True, "diet_pref": None, "diet_pref_label": None}
        save_intake_to_disk(st.session_state.intake_data)
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
        save_intake_to_disk(st.session_state.intake_data)
        st.session_state.intake_done = True
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — Healthscore
# ─────────────────────────────────────────────────────────────────────────────
def healthscore_tab(record: dict, products: list[dict]):
    score = record.get("healthscore")
    risk = record.get("risk_level", "Unknown")
    badge_html = _get_risk_badge_html(score, risk)

    # Large bold metric with colored risk badge
    render_big_score(record['healthscore'], record['risk_level'])

    with st.expander("ℹ️ How is this calculated?"):
        st.markdown(
            "Each matched red-flag ingredient adds severity points: **High = 5 pts**, "
            "**Medium = 3 pts**, **Low = 1 pt**. The raw point total is then inverted and "
            "scaled onto 0–10 (calibrated to the real catalog range of 0–33 severity points, "
            "so the worst ~10% of products score near 1–2 and a completely clean product scores 10).\n\n"
            "**Risk buckets** (on the raw point total, not the /10 score):  \n"
            "- 🟢 **Low:** 0–4 pts  \n"
            "- 🟡 **Moderate:** 5–9 pts  \n"
            "- 🔴 **High:** 10+ pts"
        )

    matches = record.get("matched_ingredients") or []
    if not matches:
        st.success("🌱 No red-flag ingredients matched this list.")
    else:
        st.markdown("### Matched ingredients")
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
        st.dataframe(rows, hide_index=True, width="stretch")

    st.markdown("---")
    st.markdown("### 🛍️ Better healthscore in the same sub-category")

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

    if not alts:
        st.info(f"No other catalog products found in sub-category \"{record.get('sub_category')}\".")
        return

    current_score = _to_float(record.get("healthscore")) or 0.0
    current_flags = len(record.get("matched_ingredients") or [])

    for alt in alts:
        alt_score = _to_float(alt.get("healthscore")) or 0.0
        alt_flags = len(alt.get("matched_ingredients") or [])
        score_diff = round(alt_score - current_score, 1)
        flag_diff = current_flags - alt_flags

        score_diff_str = f"+{score_diff}" if score_diff >= 0 else str(score_diff)
        flag_str = (
            f"{flag_diff} fewer flagged ingredient{'s' if abs(flag_diff) != 1 else ''}"
            if flag_diff > 0
            else (f"{abs(flag_diff)} more flagged ingredient{'s' if abs(flag_diff) != 1 else ''}"
                  if flag_diff < 0
                  else "same number of flagged ingredients")
        )

        alt_name = alt.get("name", "Unknown")
        alt_brand = alt.get("brand", "")
        alt_subcat = alt.get("sub_category", "")
        alt_badge = _get_risk_badge_html(alt_score, alt.get("risk_level", "Unknown"))
        store_links = _build_search_links(alt_name, alt_brand)

        with st.container():
            img_col, info_col = st.columns([1, 8])
            with img_col:
                _render_product_image(alt_name, alt_brand, alt_subcat, width=110)
            with info_col:
                st.markdown(
                    f"<div style='margin-bottom:2px;'><strong style='font-size:1.05rem; color:#0F172A;'>{alt_name}</strong> "
                    f"<span style='color:#64748B; font-size:0.85rem;'>({alt_brand})</span> &nbsp; {alt_badge}</div>"
                    f"<div style='color:#15803D; font-size:0.85rem; font-weight:600; margin-bottom:6px;'>✨ {score_diff_str} pts healthscore · {flag_str}</div>"
                    f"<div>{store_links}</div>",
                    unsafe_allow_html=True,
                )


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — Macros
# ─────────────────────────────────────────────────────────────────────────────
def macros_tab(record: dict, products: list[dict], intake_data: dict | None):
    if record.get("source") == "custom" and not nutrition_present(record):
        st.warning(
            "This is a custom ingredient paste with no nutrition fields filled in. "
            "The Macros tab needs sugar, sodium, fat, or protein numbers. "
            "Open 'Add nutrition info' on the input form, or search a catalog product instead."
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
    elif sodium == 0.0:
        matched = record.get("matched_ingredients") or []
        salt_flagged = any(
            "salt" in (m.get("ingredient_name") or "").lower()
            or "sodium" in (m.get("ingredient_name") or "").lower()
            or "salt" in (m.get("original_text") or "").lower()
            for m in matched
        )
        if salt_flagged:
            c2.warning(
                "Sodium value not available in source data — "
                "ingredient list suggests this product does contain sodium (salt matched)."
            )
        else:
            c2.metric("Sodium vs daily limit", "0%", f"0 mg / {limits['sodium_mg']} mg")
    else:
        c2.metric("Sodium vs daily limit", f"{sodium_pct}%" if sodium_pct is not None else "—", f"{sodium} mg / {limits['sodium_mg']} mg")

    if sat is None:
        c3.error("Saturated fat (g) is missing for this product.")
    else:
        c3.metric("Saturated fat vs daily limit", f"{sat_pct}%" if sat_pct is not None else "—", f"{sat} g / {limits['saturated_fat_g']} g")

    st.markdown("### Trans fat")
    if trans is None:
        st.warning("Trans fat is not in this record, so presence cannot be judged.")
    elif trans > 0:
        st.error(f"Trans fat is present on the label: {trans} g per serving.")
    else:
        st.success("Trans fat is listed as 0 g (absent on the nutrition panel).")

    st.markdown("### Protein per gram of fat (same sub-category)")
    ratio = efficiency_ratio(protein, fat)
    if protein is None or fat is None:
        st.warning("Protein and/or total fat is missing, so an efficiency ratio cannot be calculated.")
        return
    if ratio is None:
        st.warning("Total fat is 0, so protein/fat efficiency is undefined (division by zero avoided).")
        return

    st.write(f"This product: **{ratio:.2f}** g protein per g fat ({protein} g protein / {fat} g fat).")

    if not (record.get("ingredients_raw") or "").strip():
        st.info("Enter ingredients above to see alternates.")
        return

    alts = find_better_efficiency_alternative(record, products, ("Proteins_g", "Total_Fat_g"))
    if not alts:
        st.info("No same-category catalog products with a usable fat value were found for comparison.")
        return

    st.markdown("---")
    st.markdown("### 🛍️ Better protein/fat ratio alternatives")
    for alt in alts:
        alt_ratio = efficiency_ratio(alt.get("Proteins_g"), alt.get("Total_Fat_g"))
        alt_label = f"{alt_ratio:.2f}" if alt_ratio is not None else "n/a"
        ratio_diff = round(alt_ratio - ratio, 2) if alt_ratio is not None else None
        diff_str = (f" (+{ratio_diff} vs this product)" if ratio_diff is not None and ratio_diff >= 0
                    else (f" ({ratio_diff} vs this product)" if ratio_diff is not None else ""))

        alt_name = alt.get("name", "Unknown")
        alt_brand = alt.get("brand", "")
        alt_subcat = alt.get("sub_category", "")
        store_links = _build_search_links(alt_name, alt_brand)

        with st.container():
            img_col, info_col = st.columns([1, 8])
            with img_col:
                _render_product_image(alt_name, alt_brand, alt_subcat, width=13)
            with info_col:
                st.markdown(
                    f"<div style='margin-bottom:2px;'><strong style='font-size:1.05rem; color:#0F172A;'>{alt_name}</strong> "
                    f"<span style='color:#64748B; font-size:0.85rem;'>({alt_brand})</span> — "
                    f"<span style='color:#0F172A; font-weight:700;'>{alt_label} g protein/g fat</span>"
                    f"<span style='color:#15803D; font-size:0.85rem; font-weight:600;'>{diff_str}</span></div>"
                    f"<div>{store_links}</div>",
                    unsafe_allow_html=True,
                )


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — Dietician
# ─────────────────────────────────────────────────────────────────────────────
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
    chosen_label = st.selectbox("Diet profile to evaluate", labels, index=index)
    profile_key = PROFILE_OPTIONS[chosen_label]

    result = check_profile(profile_key, record)
    if result["passes"]:
        st.success(f"✅ Passes {chosen_label} criteria.")
    else:
        st.error(f"❌ Does not pass {chosen_label} criteria.")

    for reason in result.get("reasons") or ["No reason was returned."]:
        st.write(f"- {reason}")

    if result["passes"]:
        return

    if not (record.get("ingredients_raw") or "").strip():
        st.info("Enter ingredients above to see alternates.")
        return

    def passes_profile(product: dict) -> bool:
        return bool(check_profile(profile_key, product).get("passes"))

    alts = find_alternates(
        record,
        products,
        sort_key_fn=lambda p: _to_float(p.get("healthscore")) or 0.0,
        filter_fn=passes_profile,
        top_n=3,
    )
    
    st.markdown("---")
    st.markdown(f"### 🛍️ Same sub-category alternatives that pass {chosen_label}")
    if not alts:
        st.info(
            f"No catalog products in \"{record.get('sub_category') or 'unknown'}\" passed this profile. "
            "That can happen when the category is small or the rule is strict."
        )
        return

    for alt in alts:
        alt_result = check_profile(profile_key, alt)
        passing_reasons = []
        orig_reasons = result.get("reasons") or []
        alt_reasons = alt_result.get("reasons") or []
        if not alt_reasons:
            passing_reasons.append(f"passes all {chosen_label} checks")
        else:
            for orig_r in orig_reasons:
                if not any(orig_r[:30] in ar for ar in alt_reasons):
                    passing_reasons.append(f"passes: {orig_r}")
        why_str = "; ".join(passing_reasons) if passing_reasons else f"meets {chosen_label} criteria"

        alt_name = alt.get("name", "Unknown")
        alt_brand = alt.get("brand", "")
        alt_subcat = alt.get("sub_category", "")
        alt_score = _to_float(alt.get("healthscore")) or 0.0
        alt_badge = _get_risk_badge_html(alt_score, alt.get("risk_level", "Unknown"))
        store_links = _build_search_links(alt_name, alt_brand)

        with st.container():
            img_col, info_col = st.columns([1, 8])
            with img_col:
                _render_product_image(alt_name, alt_brand, alt_subcat, width=90)
            with info_col:
                st.markdown(
                    f"<div style='margin-bottom:2px;'><strong style='font-size:1.05rem; color:#0F172A;'>{alt_name}</strong> "
                    f"<span style='color:#64748B; font-size:0.85rem;'>({alt_brand})</span> &nbsp; {alt_badge}</div>"
                    f"<div style='color:#15803D; font-size:0.85rem; font-weight:600; margin-bottom:6px;'>✨ {why_str}</div>"
                    f"<div>{store_links}</div>",
                    unsafe_allow_html=True,
                )


# ─────────────────────────────────────────────────────────────────────────────
# MAIN APP ENTRY
# ─────────────────────────────────────────────────────────────────────────────
def main():
    st.set_page_config(
        page_title="Sugarcoated? — Food Label Risk & Macro Analyzer",
        page_icon="🔍",
        layout="wide",
    )

    # ── Full-Width Hero Header ───────────────────────────────────────────────
    st.markdown(
        """
        <div class="hero-banner">
            <div class="hero-badge">🔍 Food Label Risk & Macro Intelligence</div>
            <div class="hero-title">Sugarcoated?</div>
            <div class="hero-subtitle">Instant ingredient-level risk flags, macro limit analysis, and clean alternatives for Indian packaged foods.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "intake_data" not in st.session_state:
        saved_intake = load_saved_intake()
        if saved_intake is not None:
            st.session_state.intake_data = saved_intake
            st.session_state.intake_done = True
        else:
            st.session_state.intake_data = None
            st.session_state.intake_done = False
    elif "intake_done" not in st.session_state:
        st.session_state.intake_done = bool(st.session_state.intake_data is not None)

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

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    st.subheader("🔍 Look up a product")
    mode = st.radio("Input mode", ["Search existing product", "Paste custom ingredients"], horizontal=True)

    if mode == "Search existing product":
        query = st.text_input("Product name or brand", placeholder="e.g. Parle Marie, Britannia Nutrichoice, Amul, Lay's...")
        if query.strip():
            hits = search_products(query, products)
            if not hits:
                st.error("No catalog products matched that search. Try another spelling, or paste ingredients instead.")
            else:
                labels = [f"{p.get('name')} — {p.get('brand')} ({int(score)}% match)" for score, p in hits]
                choice = st.selectbox("Pick a product", labels)
                if st.button("⚡ Analyze selected product", type="primary"):
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

        if st.button("⚡ Analyze pasted ingredients", type="primary"):
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
        st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
        st.info("👆 Search or paste ingredients above to see Healthscore, Macros, and Dietician insights.")
        return

    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)

    # ── Main Analyzed Product Header Card ────────────────────────────────────
    hdr_img, hdr_text = st.columns([1, 8])
    with hdr_img:
        _render_product_image(
            record.get("name", ""),
            record.get("brand", ""),
            record.get("sub_category", ""),
            width=80,
        )
    with hdr_text:
        main_badge = _get_risk_badge_html(_to_float(record.get("healthscore")), record.get("risk_level", "Unknown"))
        st.markdown(
            f"<div style='margin-bottom:2px;'><span style='color:#64748B; font-size:0.85rem; font-weight:600; text-transform:uppercase; letter-spacing:0.04em;'>{record.get('brand') or ''}</span> "
            f"<span style='background:#F1F5F9; color:#475569; font-size:0.75rem; font-weight:600; padding:2px 8px; border-radius:6px; margin-left:6px;'>{record.get('sub_category') or 'no category'}</span></div>"
            f"<div style='font-size:1.6rem; font-weight:800; color:#0F172A; line-height:1.2; margin-bottom:8px;'>{record.get('name')}</div>"
            f"<div>{main_badge}</div>",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)

    # ── SaaS Tabs Navigation ─────────────────────────────────────────────────
    tab_health, tab_macros, tab_diet = st.tabs([
        "🛡️ Healthscore",
        "📊 Macros & Nutrients",
        "🥗 Dietician Checks",
    ])
    with tab_health:
        healthscore_tab(record, products)
    with tab_macros:
        macros_tab(record, products, st.session_state.intake_data)
    with tab_diet:
        dietician_tab(record, products, st.session_state.intake_data)

    # ── Open Food Facts Attribution Footer ───────────────────────────────────
    st.markdown("---")
    st.caption(
        "Product images provided by [Open Food Facts](https://openfoodfacts.org), "
        "available under the [Open Database License](https://opendatacommons.org/licenses/odbl/). "
        "Alternate product links are search-query links to Blinkit/Zepto — not live inventory or pricing."
    )


if __name__ == "__main__":
    main()
