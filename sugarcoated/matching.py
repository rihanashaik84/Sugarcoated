"""Single source of truth for red-flag ingredient matching."""

from __future__ import annotations

import csv
import re
from pathlib import Path

from rapidfuzz import fuzz, process


def normalize_text(text) -> str:
    if text is None:
        return ""
    text = str(text).upper()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def load_red_flags(filename: str | Path) -> list[dict]:
    red_flags = []
    with open(filename, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            ingredient = (row.get("ingredient_name") or "").strip()
            if ingredient:
                red_flags.append(dict(row))
    return red_flags


def _word_boundary_match(token: str, ingredient_name: str) -> bool:
    if not token or not ingredient_name:
        return False
    pattern = r"(?<![A-Z0-9])" + re.escape(ingredient_name) + r"(?![A-Z0-9])"
    return re.search(pattern, token) is not None


def _match_record(flag: dict, original_text: str, match_type: str, confidence: float) -> dict:
    return {
        "ingredient_name": (flag.get("ingredient_name") or "").strip(),
        "original_text": original_text,
        "category": (flag.get("category") or "").strip(),
        "severity": (flag.get("severity") or "").strip(),
        "match_type": match_type,
        "confidence": int(round(confidence)),
    }


def _drop_shorter_overlapping_matches(matches: list[dict]) -> list[dict]:
    """Drop a match whose ingredient name is a substring of a longer matched name."""
    final_matches = []
    for match in matches:
        ingredient = normalize_text(match["ingredient_name"])
        is_part_of_longer_match = False
        for other in matches:
            other_ingredient = normalize_text(other["ingredient_name"])
            if (
                ingredient != other_ingredient
                and ingredient in other_ingredient
                and len(other_ingredient) > len(ingredient)
            ):
                is_part_of_longer_match = True
                break
        if not is_part_of_longer_match:
            final_matches.append(match)
    return final_matches


def _dedupe_by_ingredient_name(matches: list[dict]) -> list[dict]:
    """Keep one row per red-flag name (highest confidence, exact preferred)."""
    best: dict[str, dict] = {}
    for match in matches:
        key = normalize_text(match["ingredient_name"])
        if not key:
            continue
        existing = best.get(key)
        if existing is None:
            best[key] = match
            continue
        existing_rank = (1 if existing["match_type"] == "exact" else 0, existing["confidence"])
        new_rank = (1 if match["match_type"] == "exact" else 0, match["confidence"])
        if new_rank > existing_rank:
            best[key] = match
    return list(best.values())


def match_ingredients(ingredient_text, red_flags, fuzzy_threshold: int = 85) -> list[dict]:
    """
    Split ingredient_text on commas, then for each token:
    1. exact regex word-boundary match against red-flag names
    2. if none, fuzzy token_sort_ratio match if score >= fuzzy_threshold
    """
    if not ingredient_text or not red_flags:
        return []

    raw_tokens = [part.strip() for part in str(ingredient_text).split(",")]
    flag_names = [normalize_text(flag.get("ingredient_name")) for flag in red_flags]
    name_to_flag = {}
    for flag, name in zip(red_flags, flag_names):
        if name and name not in name_to_flag:
            name_to_flag[name] = flag

    collected = []
    for raw_token in raw_tokens:
        if not raw_token:
            continue
        token = normalize_text(raw_token)
        if not token:
            continue

        exact_hits = []
        for flag, name in zip(red_flags, flag_names):
            if name and _word_boundary_match(token, name):
                exact_hits.append(_match_record(flag, raw_token, "exact", 100))

        if exact_hits:
            collected.extend(exact_hits)
            continue

        result = process.extractOne(
            token,
            list(name_to_flag.keys()),
            scorer=fuzz.token_sort_ratio,
        )
        if result is None:
            continue
        matched_name, score, _ = result
        if score >= fuzzy_threshold:
            collected.append(
                _match_record(name_to_flag[matched_name], raw_token, "fuzzy", score)
            )

    collected = _drop_shorter_overlapping_matches(collected)
    return _dedupe_by_ingredient_name(collected)
