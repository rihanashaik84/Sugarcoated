import csv


filename = "data/packaged_foods_india.csv"

required_columns = [
    "Item name",
    "Brand_Name",
    "Ingredients"
]


total = 0
missing_names = 0
missing_ingredients = 0


with open(
    filename,
    "r",
    encoding="utf-8-sig",
    newline=""
) as file:

    reader = csv.DictReader(file)

    for row in reader:

        total += 1

        if not row["Item name"].strip():
            missing_names += 1

        if not row["Ingredients"].strip():
            missing_ingredients += 1


print("Total products:", total)
print("Missing product names:", missing_names)
print("Missing ingredients:", missing_ingredients)