from analyzer import load_red_flags, analyze_ingredients


red_flags = load_red_flags(
    "data/redflag_ingredients.csv"
)


def test_sugar():
    result = analyze_ingredients("Sugar", red_flags)

    assert "SUGAR" in result["matched_ingredients"]
    assert result["score"] == 3
    assert result["risk_level"] == "Moderate"


def test_multiple_ingredients():
    result = analyze_ingredients(
        "Sugar, Dextrose, Refined Palm Oil",
        red_flags
    )

    assert result["score"] == 9
    assert result["risk_level"] == "Moderate"


def test_empty_input():
    result = analyze_ingredients("", red_flags)

    assert result["score"] == 0
    assert result["risk_level"] == "Low"
    assert result["matched_ingredients"] == []


def test_none_input():
    result = analyze_ingredients(None, red_flags)

    assert result["score"] == 0
    assert result["risk_level"] == "Low"


def test_no_overlap():
    result = analyze_ingredients(
        "Refined Palm Oil",
        red_flags
    )

    assert "REFINED PALM OIL" in result["matched_ingredients"]

    assert "PALM OIL" not in result["matched_ingredients"]


print("All tests passed!")