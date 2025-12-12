"""Unit tests for AMEA Next analysis helpers."""

from amea_new.analysis import _parse_pestel


def test_parse_pestel_from_json_object() -> None:
    response = (
        "{\n"
        '  "Political": "Stable governance with recent policy incentives",\n'
        '  "Economic": ["GDP growth above EU average", "Strong consumer confidence"],\n'
        '  "Social": "Digital adoption accelerating",\n'
        '  "Technological": "Dense startup ecosystem",\n'
        '  "Environmental": "Aggressive decarbonization targets",\n'
        '  "Legal": "Data residency rules tightening"\n'
        "}"
    )

    parsed = _parse_pestel(response)

    assert parsed["Political"] == "Stable governance with recent policy incentives"
    assert parsed["Economic"] == "GDP growth above EU average Strong consumer confidence"
    assert parsed["Social"] == "Digital adoption accelerating"
    assert parsed["Technological"] == "Dense startup ecosystem"
    assert parsed["Environmental"] == "Aggressive decarbonization targets"
    assert parsed["Legal"] == "Data residency rules tightening"


def test_parse_pestel_from_colon_bullets() -> None:
    response = """
    Political: Stable coalition
    Economic: High inflation
    Social: Urbanization rising
    Technological: 5G coverage expanding
    Environmental: Severe droughts
    Legal: New consumer protections
    """

    parsed = _parse_pestel(response)

    assert parsed == {
        "Political": "Stable coalition",
        "Economic": "High inflation",
        "Social": "Urbanization rising",
        "Technological": "5G coverage expanding",
        "Environmental": "Severe droughts",
        "Legal": "New consumer protections",
    }
