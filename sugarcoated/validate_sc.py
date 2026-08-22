import csv


filename = "data/scored_foods.csv"

scores = []

with open(
    filename,
    "r",
    encoding="utf-8",
    newline=""
) as file:

    reader = csv.DictReader(file)

    for row in reader:

        score = int(row["Score"])

        if score < 0:
            print(
                "ERROR: Negative score:",
                row["Item name"]
            )

        scores.append(score)


print("Products:", len(scores))
print("Minimum score:", min(scores))
print("Maximum score:", max(scores))
print(
    "Average score:",
    round(sum(scores) / len(scores), 2)
)

print(
    "Zero-score products:",
    scores.count(0)
)