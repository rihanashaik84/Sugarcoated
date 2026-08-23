"""Generic same-category alternate finder used by every app tab."""

from __future__ import annotations


def _as_product_and_category(product_or_category):
    if isinstance(product_or_category, dict):
        sub_category = (product_or_category.get("sub_category") or "").strip()
        product_id = product_or_category.get("product_id")
        name = (product_or_category.get("name") or "").strip()
        return product_or_category, sub_category, product_id, name
    return None, str(product_or_category or "").strip(), None, None


def find_alternates(
    product_or_category,
    all_products,
    sort_key_fn,
    filter_fn=None,
    top_n: int = 3,
):
    """
    Filter to the same sub_category (excluding the current product),
    optionally apply filter_fn, sort with sort_key_fn, return top_n.
    """
    if not all_products:
        return []

    current, sub_category, product_id, name = _as_product_and_category(product_or_category)
    if not sub_category:
        return []

    candidates = []
    for product in all_products:
        if not isinstance(product, dict):
            continue
        if (product.get("sub_category") or "").strip() != sub_category:
            continue
        if product_id is not None and product.get("product_id") == product_id:
            continue
        if name and product.get("product_id") is None:
            if (product.get("name") or "").strip() == name:
                continue
        if current is product:
            continue
        if filter_fn is not None and not filter_fn(product):
            continue
        candidates.append(product)

    ranked = sorted(candidates, key=sort_key_fn, reverse=True)
    return ranked[:top_n]
