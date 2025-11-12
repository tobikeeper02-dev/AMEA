"""Generate PESTEL narratives from indicator data."""
from __future__ import annotations

from typing import Dict, List

from .scoring import normalize_indicator


PESTEL_DIMENSIONS = ["Political", "Economic", "Social", "Technological", "Environmental", "Legal"]


def generate_pestel_from_indicators(
    country: str,
    indicators: Dict[str, float],
    narratives: Dict[str, List[str]],
    *,
    company: str,
    industry: str,
    priorities: Dict[str, float],
    use_case: str,
) -> Dict[str, List[str]]:
    """Create qualitative commentary for PESTEL dimensions.

    The heuristics combine indicator values and curated narratives to mimic
    what an analyst might conclude when scanning the raw data.
    """
    pestel: Dict[str, List[str]] = {dimension: [] for dimension in PESTEL_DIMENSIONS}

    priority_labels = {
        "growth": "growth potential",
        "cost_efficiency": "cost efficiency",
        "risk": "risk mitigation",
        "sustainability": "sustainability impact",
        "digital": "digital acceleration",
    }
    priority_dimension_map = {
        "growth": "Economic",
        "cost_efficiency": "Economic",
        "risk": "Political",
        "sustainability": "Environmental",
        "digital": "Technological",
    }
    top_priority = None
    if priorities:
        top_priority = max(priorities.items(), key=lambda item: item[1])[0]

    industry_label = industry.lower() if industry else "target industry"
    use_case_label = use_case.lower() if use_case else "market expansion"
    context_clause = (
        f"For {company}'s {use_case_label} agenda in the {industry_label} space in {country}, "
    )

    # Political
    governance = indicators.get("governance_index", 50)
    stability = indicators.get("political_stability", 50)
    pestel["Political"].append(
        context_clause
        + f"political institutions score {governance:.0f}/100 with stability at {stability:.0f}, supporting regulatory planning."
    )
    pestel["Political"].extend(narratives.get("political", []))

    # Economic
    gdp_growth = indicators.get("gdp_growth", 0)
    inflation = indicators.get("inflation", 2)
    consumer_spend = indicators.get("consumer_spending_index", 50)
    pestel["Economic"].append(
        context_clause
        + f"GDP growth sits at {gdp_growth:.1f}% while inflation is {inflation:.1f}%, with consumer demand indexed at {consumer_spend:.0f}."
    )
    pestel["Economic"].extend(narratives.get("economic", []))

    # Social
    urbanization = indicators.get("urbanization_rate", 70)
    demographics = indicators.get("median_age", 35)
    social_score = (
        normalize_indicator(urbanization, 0, 100) * 40
        + normalize_indicator(100 - abs(40 - demographics), 0, 40) * 60
    )
    pestel["Social"].append(
        context_clause
        + f"urbanization at {urbanization:.0f}% and median age {demographics:.1f} indicate a social readiness score near {social_score:.0f}/100."
    )
    pestel["Social"].extend(narratives.get("social", []))

    # Technological
    digital = indicators.get("digital_adoption", 60)
    broadband = indicators.get("broadband_penetration", 60)
    pestel["Technological"].append(
        context_clause
        + f"digital adoption is {digital:.0f}/100 with broadband penetration at {broadband:.0f}%."
    )
    pestel["Technological"].extend(narratives.get("technological", []))

    # Environmental
    emissions = indicators.get("co2_per_capita", 8)
    renewables = indicators.get("renewable_energy_share", 30)
    pestel["Environmental"].append(
        context_clause
        + f"CO₂ footprint is {emissions:.1f} tons per capita with renewables covering {renewables:.0f}% of energy needs."
    )
    pestel["Environmental"].extend(narratives.get("environmental", []))

    # Legal
    ease_business = indicators.get("ease_of_doing_business", 70)
    regulatory = indicators.get("regulatory_quality", 65)
    pestel["Legal"].append(
        context_clause
        + f"ease of doing business is {ease_business:.0f}/100 and regulatory quality hits {regulatory:.0f}/100."
    )
    pestel["Legal"].extend(narratives.get("legal", []))

    if top_priority:
        dimension = priority_dimension_map.get(top_priority)
        if dimension:
            focus = priority_labels[top_priority]
            pestel[dimension].insert(
                0,
                f"Primary client focus on {focus} suggests prioritizing {dimension.lower()} signals when shaping the go-to-market plan.",
            )

    return pestel
