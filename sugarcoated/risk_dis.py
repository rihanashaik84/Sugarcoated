import csv


counts = {
    "Low": 0,
    "Moderate": 0,
    "High": 0
}


with open(
    "data/scored_foods.csv",
    "r",
    encoding="utf-8",
    newline=""
) as file:

    reader = csv.DictReader(file)

    for row in reader:

        risk = row["Risk_Level"]

        if risk in counts:
            counts[risk] += 1


print("Risk distribution:")

for risk, count in counts.items():

    print(
        risk + ":",
        count
    )