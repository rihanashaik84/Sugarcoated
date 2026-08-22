import csv


SEVERITY_POINTS = {
    "high": 5,
    "medium": 3,
    "low": 1
}


def calculate_score(severities):
    score = 0

    for severity in severities:
        severity = severity.strip().lower()

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


with open("data/matched_foods.csv", "r", encoding="utf-8-sig", newline="") as infile:
    reader = csv.DictReader(infile)

    fieldnames = reader.fieldnames + ["Score", "Risk_Level"]

    with open("data/scored_foods.csv", "w", encoding="utf-8", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            if row["Matched_Severities"].strip():
                severities = row["Matched_Severities"].split(";")
                score = calculate_score(severities)
            else:
                score = 0

            risk_level = get_risk_level(score)

            row["Score"] = score
            row["Risk_Level"] = risk_level

            writer.writerow(row)


print("Scoring complete.")
print("Output saved to data/scored_foods.csv")