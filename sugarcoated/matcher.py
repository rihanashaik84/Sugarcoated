import csv


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
    matches = []

    ingredients = ingredients.upper()

    for flag in red_flags:
        ingredient_name = flag["ingredient_name"].strip().upper()

        if ingredient_name in ingredients:
            matches.append(flag)

    return matches


red_flags = load_red_flags("data/redflag_ingredients.csv")

test_ingredients = "SUGAR, COCOA SOLIDS, DEXTROSE, REFINED PALM OIL"

matches = find_matches(test_ingredients, red_flags)

for match in matches:
    print(match["ingredient_name"], "-", match["category"], "-", match["severity"])