"""Open Food Facts image lookup — display-only, never blocks app rendering.

All network calls are wrapped in try/except; any failure returns None and the
caller must fall back to get_category_icon().  Results (including None) are
cached in data/image_cache.json so repeated renders don't re-hit the API.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent
CACHE_PATH = ROOT / "data" / "image_cache.json"
ICONS_DIR = ROOT / "assets" / "icons"

_OFF_SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"
_USER_AGENT = "Sugarcoated - Hackathon Project - https://github.com/rihanashaik84/Sugarcoated"

# ---------------------------------------------------------------------------
# Disk-backed image cache
# ---------------------------------------------------------------------------

def _load_cache() -> dict:
    try:
        if CACHE_PATH.exists():
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


def _save_cache(cache: dict) -> None:
    try:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# Module-level cache loaded once per process; written after every lookup.
_cache: dict = _load_cache()


# ---------------------------------------------------------------------------
# Public API: get_product_image
# ---------------------------------------------------------------------------

def get_product_image(name: str, brand: str = "") -> Optional[str]:
    """Return an image URL for *name*/*brand* from Open Food Facts, or None.

    - Checks the local disk cache first (including cached None/null values).
    - Sends search requests with a 5-second timeout.
    - Returns None on any network/parse failure — never raises.
    - Persists the result (including None) to the disk cache.
    """
    cache_key = f"{brand}|{name}".lower().strip()

    # Sentinel for cached None in disk JSON
    _NONE_SENTINEL = "__none__"

    if cache_key in _cache:
        value = _cache[cache_key]
        if value is None or value == _NONE_SENTINEL or not str(value).startswith("http"):
            return None
        return str(value)

    result: Optional[str] = None
    try:
        import requests  # imported lazily so missing package doesn't crash on import

        brand_clean = (brand or "").strip()
        name_clean = (name or "").strip()
        if brand_clean.lower() in name_clean.lower():
            search_term = name_clean
        else:
            search_term = f"{brand_clean} {name_clean}".strip()

        resp = requests.get(
            _OFF_SEARCH_URL,
            params={"search_terms": search_term, "json": 1, "page_size": 1},
            headers={"User-Agent": _USER_AGENT},
            timeout=5,
        )
        resp.raise_for_status()
        payload = resp.json()
        products = payload.get("products") or []
        if not products and brand_clean and search_term != name_clean:
            # Retry with just the product name if brand+name returned nothing
            try:
                resp2 = requests.get(
                    _OFF_SEARCH_URL,
                    params={"search_terms": name_clean, "json": 1, "page_size": 1},
                    headers={"User-Agent": _USER_AGENT},
                    timeout=5,
                )
                if resp2.status_code == 200:
                    payload2 = resp2.json()
                    products = payload2.get("products") or []
            except Exception:
                pass
        if products:
            product = products[0]
            result = (
                product.get("image_front_url")
                or product.get("image_url")
                or None
            )
    except Exception:
        result = None

    # Persist (including None)
    _cache[cache_key] = result if (result and str(result).startswith("http")) else _NONE_SENTINEL
    _save_cache(_cache)
    return result if (result and str(result).startswith("http")) else None


# ---------------------------------------------------------------------------
# Public API: get_category_icon
# ---------------------------------------------------------------------------

# Keyword → icon filename mapping (order matters — first match wins)
_ICON_RULES: list[tuple[str, str]] = [
    ("biscuit", "biscuit.svg"),
    ("cookie", "biscuit.svg"),
    ("cracker", "biscuit.svg"),
    ("chocolate", "chocolate.svg"),
    ("choco", "chocolate.svg"),
    ("chip", "chips.svg"),
    ("namkeen", "chips.svg"),
    ("wafer", "chips.svg"),
    ("crisp", "chips.svg"),
    ("beverage", "beverage.svg"),
    ("drink", "beverage.svg"),
    ("juice", "beverage.svg"),
    ("water", "beverage.svg"),
    ("soda", "beverage.svg"),
    ("tea", "beverage.svg"),
    ("coffee", "beverage.svg"),
    ("dairy", "dairy.svg"),
    ("milk", "dairy.svg"),
    ("cheese", "dairy.svg"),
    ("yogurt", "dairy.svg"),
    ("curd", "dairy.svg"),
    ("butter", "dairy.svg"),
    ("candy", "candy.svg"),
    ("toffee", "candy.svg"),
    ("gummy", "candy.svg"),
    ("lollipop", "candy.svg"),
    ("snack", "snack.svg"),
    ("nut", "snack.svg"),
    ("popcorn", "snack.svg"),
    ("munch", "snack.svg"),
]

_FALLBACK_ICON = "generic.svg"


def get_category_icon(sub_category: str) -> str:
    """Return an absolute path to a local SVG icon for *sub_category*.

    Falls back to generic.svg if no keyword matches.
    """
    text = (sub_category or "").lower()
    for keyword, filename in _ICON_RULES:
        if keyword in text:
            return str((ICONS_DIR / filename).resolve())
    return str((ICONS_DIR / _FALLBACK_ICON).resolve())
