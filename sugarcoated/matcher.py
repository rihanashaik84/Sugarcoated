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

        if ingredient_name and ingredient_name in ingredients:
            matches.append(flag)

    # Remove shorter matches when they are part of a longer match
    final_matches = []

    for match in matches:
        ingredient = match["ingredient_name"].strip().upper()

        is_part_of_longer_match = False

        for other in matches:
            other_ingredient = other["ingredient_name"].strip().upper()

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


red_flags = load_red_flags("data/redflag_ingredients.csv")

with open("data/normalized_foods.csv", "r", encoding="utf-8-sig", newline="") as infile:
    reader = csv.DictReader(infile)

    fieldnames = [
        "S.No",
        "Item name",
        "Brand_Name",
        "Category",
        "Sub_Category",
        "Matched_Ingredients",
        "Matched_Categories",
        "Matched_Severities"
    ]

    with open("data/matched_foods.csv", "w", encoding="utf-8", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            ingredients = row["Normalized_Ingredients"]
            matches = find_matches(ingredients, red_flags)

            matched_ingredients = "; ".join(
                match["ingredient_name"] for match in matches
            )

            matched_categories = "; ".join(
                match["category"] for match in matches
            )

            matched_severities = "; ".join(
                match["severity"] for match in matches
            )

            writer.writerow({
                "S.No": row["S.No"],
                "Item name": row["Item name"],
                "Brand_Name": row["Brand_Name"],
                "Category": row["Category"],
                "Sub_Category": row["Sub_Category"],
                "Matched_Ingredients": matched_ingredients,
                "Matched_Categories": matched_categories,
                "Matched_Severities": matched_severities
            })

print("Matching complete.")
print("Output saved to data/matched_foods.csv")