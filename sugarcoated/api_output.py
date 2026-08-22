import csv
import json


products = []

with open("data/scored_foods.csv", "r", encoding="utf-8-sig", newline="") as file:
    reader = csv.DictReader(file)

    for row in reader:
        product = {
            "product_id": row["S.No"],
            "name": row["Item name"],
            "brand": row["Brand_Name"],
            "category": row["Category"],
            "sub_category": row["Sub_Category"],
            "matched_ingredients": [
                item.strip()
                for item in row["Matched_Ingredients"].split(";")
                if item.strip()
            ],
            "matched_categories": [
                item.strip()
                for item in row["Matched_Categories"].split(";")
                if item.strip()
            ],
            "matched_severities": [
                item.strip()
                for item in row["Matched_Severities"].split(";")
                if item.strip()
            ],
            "score": int(row["Score"]),
            "risk_level": row["Risk_Level"]
        }

        products.append(product)


with open("data/products.json", "w", encoding="utf-8") as file:
    json.dump(products, file, indent=2)


print("JSON generation complete.")
print("Output saved to data/products.json")
print("Products:", len(products))