import csv
import re
def normalize_text(text):
    "Clean ingredient text so matching is more consistent."

    if text is None:
        return ""

    text = str(text)
    text = text.upper()
    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    return text


with open("data/packaged_foods_india.csv", "r", encoding="utf-8-sig", newline="") as infile:
    reader = csv.DictReader(infile)

    with open("data/normalized_foods.csv", "w", encoding="utf-8", newline="") as outfile:
        fieldnames = reader.fieldnames + ["Normalized_Ingredients"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)

        writer.writeheader()

        for row in reader:
            ingredients = row["Ingredients"]
            row["Normalized_Ingredients"] = normalize_text(ingredients)
            writer.writerow(row)

print("Normalization complete.")
print("Output saved to data/normalized_foods.csv")