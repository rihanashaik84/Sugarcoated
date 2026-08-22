import csv
import re


SEVERITY_POINTS = {
    "high": 5,
    "medium": 3,
    "low": 1
}


def normalize_text(text):
    if text is None:
        return ""

    text = str(text).upper()
    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    return text


def load_red_flags(filename):
    red_flags = []

    with open(filename, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            ingredient = row["ingredient_name"].strip().upper()

            if ingredient:
                red_flags.append(row)

    return red_flags


def find_matches(ingredients, red_flags):
    ingredients = normalize_text(ingredients)

    matches = []

    for flag in red_flags:
        ingredient_name = normalize_text(flag["ingredient_name"])

        if not ingredient_name:
            continue

        # Escape special regex characters
        pattern = r"(?<![A-Z0-9])" + re.escape(ingredient_name) + r"(?![A-Z0-9])"

        if re.search(pattern, ingredients):
            matches.append(flag)

    # Remove shorter overlapping matches
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

def calculate_score(matches):
    score = 0

    for match in matches:
        severity = match["severity"].strip().lower()

        if severity in SEVERITY_POINTS:
            score += SEVERITY_POINTS[severity]

    return score


def get_risk_level(score):
    if score <= 4:
        return "Low"
    elif score <= 9:
        return "Moderate"
    else:
        return "High"


def analyze_ingredients(ingredients, red_flags):
    ingredients = normalize_text(ingredients)

    if not ingredients:
        return {
            "matched_ingredients": [],
            "matched_categories": [],
            "matched_severities": [],
            "score": 0,
            "risk_level": "Low"
        }

    matches = find_matches(ingredients, red_flags)

    matched_ingredients = [
        match["ingredient_name"]
        for match in matches
    ]

    matched_categories = [
        match["category"]
        for match in matches
    ]

    matched_severities = [
        match["severity"]
        for match in matches
    ]

    score = calculate_score(matches)

    return {
        "matched_ingredients": matched_ingredients,
        "matched_categories": matched_categories,
        "matched_severities": matched_severities,
        "score": score,
        "risk_level": get_risk_level(score)
    }

if __name__ == "__main__":

    red_flags = load_red_flags(
        "data/redflag_ingredients.csv"
    )
    test = "Sugar, Dextrose, Maltodextrin, Palm Oil"
    result = analyze_ingredients(test, red_flags)

    print(result)