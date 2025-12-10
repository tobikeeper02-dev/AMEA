"""Generate PESTEL narratives from indicator data."""
from __future__ import annotations

import logging
from typing import Dict, Iterable, List

from ..research.llm import ChatGPTNotConfiguredError, generate_pestel_with_chatgpt
from .scoring import normalize_indicator


LOGGER = logging.getLogger(__name__)

PESTEL_DIMENSIONS = ["Political", "Economic", "Social", "Technological", "Environmental", "Legal"]


def _iter_brief_items(payload: Dict[str, object], key: str) -> List[str]:
    value = payload.get(key)
    if value is None:
        return []
    if isinstance(value, str):
        cleaned = value.strip()
        return [cleaned] if cleaned else []
    if isinstance(value, Iterable):
        results: List[str] = []
        for item in value:
            if item is None:
                continue
            cleaned = str(item).strip()
            if cleaned:
                results.append(cleaned)
        return results
    cleaned = str(value).strip()
    return [cleaned] if cleaned else []


def _heuristic_pestel(
    country: str,
    indicators: Dict[str, float],
    narratives: Dict[str, List[str]],
    *,
    company: str,
    industry: str,
    priorities: Dict[str, float],
    use_case: str,
    company_brief: Dict[str, object] | None,
) -> Dict[str, List[str]]:
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
    context_clause = f"For {company}'s {use_case_label} agenda in the {industry_label} space in {country}, "

    brief = company_brief or {}
    profile_summary_items = _iter_brief_items(brief, "profile_summary")
    if profile_summary_items:
        pestel["Economic"].extend(profile_summary_items)

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
        context_clause + f"digital adoption is {digital:.0f}/100 with broadband penetration at {broadband:.0f}%."
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

    if brief:
        for note in _iter_brief_items(brief, "strategic_fit"):
            pestel["Economic"].append(note)
        for note in _iter_brief_items(brief, "demand_drivers"):
            pestel["Social"].append(note)
        for note in _iter_brief_items(brief, "technology_enablers"):
            pestel["Technological"].append(note)
        for note in _iter_brief_items(brief, "regulatory_watch"):
            pestel["Legal"].append(note)
        for note in _iter_brief_items(brief, "sustainability_factors"):
            pestel["Environmental"].append(note)
        for note in _iter_brief_items(brief, "risk_watch"):
            pestel["Political"].append(note)

    if top_priority:
        dimension = priority_dimension_map.get(top_priority)
        if dimension:
            focus = priority_labels[top_priority]
            pestel[dimension].insert(
                0,
                f"Primary client focus on {focus} suggests prioritizing {dimension.lower()} signals when shaping the go-to-market plan.",
            )

    return pestel


def generate_pestel_from_indicators(
    country: str,
    indicators: Dict[str, float],
    narratives: Dict[str, List[str]],
    *,
    company: str,
    industry: str,
    priorities: Dict[str, float],
    use_case: str,
    company_brief: Dict[str, object] | None,
) -> Dict[str, List[str]]:
    """Create qualitative commentary for PESTEL dimensions."""

    baseline = _heuristic_pestel(
        country,
        indicators,
        narratives,
        company=company,
        industry=industry,
        priorities=priorities,
        use_case=use_case,
        company_brief=company_brief,
    )

    try:
        llm_output = generate_pestel_with_chatgpt(
            country=country,
            company=company,
            industry=industry,
            use_case=use_case,
            priorities=priorities,
            indicators=indicators,
            narratives=narratives,
            company_brief=company_brief,
        )
    except ChatGPTNotConfiguredError:
        return baseline
    except Exception as exc:  # noqa: BLE001 - log unexpected API issues
        LOGGER.warning("Falling back to heuristic PESTEL for %s: %s", country, exc)
        return baseline

    merged = baseline.copy()
    for dimension, bullets in llm_output.items():
        if dimension in merged and bullets:
            merged[dimension] = bullets
    return merged
