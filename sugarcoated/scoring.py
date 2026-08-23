"""Severity scoring and 0–10 healthscore conversion."""

from __future__ import annotations


SEVERITY_POINTS = {"high": 5, "medium": 3, "low": 1}


def calculate_score(matches) -> int:
    score = 0
    if not matches:
        return 0
    for match in matches:
        if isinstance(match, dict):
            severity = str(match.get("severity") or "").strip().lower()
        else:
            severity = str(match).strip().lower()
        if severity in SEVERITY_POINTS:
            score += SEVERITY_POINTS[severity]
    return score


def normalize_to_ten(score, max_expected: int = 25) -> float:
    """
    Convert a raw severity-point total into a 0–10 healthscore.

    10 = cleanest (no matched red flags). 0 = worst.

    max_expected=25 is an explicit saturation assumption: five high-severity
    flags (5 × 5 points) fill the scale. Products that score above that still
    map to 0 rather than going negative.
    """
    try:
        raw = float(score)
    except (TypeError, ValueError):
        raw = 0.0
    if max_expected <= 0:
        return 10.0
    clamped = min(max(raw, 0.0), float(max_expected))
    healthscore = 10.0 * (1.0 - (clamped / float(max_expected)))
    return round(healthscore, 1)


def get_risk_level(score) -> str:
    """Internal buckets on the raw point total (not the /10 healthscore)."""
    try:
        raw = float(score)
    except (TypeError, ValueError):
        raw = 0.0
    if raw <= 4:
        return "Low"
    if raw <= 9:
        return "Moderate"
    return "High"
