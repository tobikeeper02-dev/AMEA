"""High level orchestration for the AMEA market analysis pipeline."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List

from .analysis.pestel import generate_pestel_from_indicators
from .analysis.recommendations import build_turnaround_actions, select_entry_mode
from .analysis.scoring import ScoreBreakdown, compute_market_score
from .research.data_loader import CountryIndicator, get_recent_news_summaries, load_country_indicators
from .research.llm import ChatGPTNotConfiguredError, generate_company_market_brief


LOGGER = logging.getLogger(__name__)


@dataclass
class MarketAnalysisResult:
    country: str
    pestel: Dict[str, List[str]]
    score: ScoreBreakdown
    news: List[str]
    entry_mode: str
    turnaround_actions: Dict[str, str]
    sources: List[str]


@dataclass
class ComparativeAnalysis:
    company: str
    industry: str
    priorities: Dict[str, float]
    use_case: str
    markets: List[MarketAnalysisResult]
    company_brief: Dict[str, object]

    def best_market(self) -> MarketAnalysisResult | None:
        if not self.markets:
            return None
        return max(self.markets, key=lambda market: market.score.composite)


PRIORITY_MAP = {
    "Growth potential": "growth",
    "Cost efficiency": "cost_efficiency",
    "Risk mitigation": "risk",
    "Sustainability": "sustainability",
    "Digital acceleration": "digital",
}


def _parse_priorities(priority_input: List[str]) -> Dict[str, float]:
    weights = {PRIORITY_MAP.get(item, item): 1.0 for item in priority_input}
    if not weights:
        # Default to equal emphasis on growth and risk mitigation
        weights = {"growth": 1.0, "risk": 1.0}
    return weights


def _fallback_company_brief(
    company: str,
    industry: str,
    use_case: str,
    priorities: Dict[str, float],
) -> Dict[str, object]:
    """Generate a deterministic context pack when ChatGPT is unavailable."""

    display_company = company or "The client"
    sector = industry or "target industry"
    agenda = use_case or "market expansion"
    priority_sentence = "balanced objectives"
    if priorities:
        ordered = sorted(priorities.items(), key=lambda item: item[1], reverse=True)
        priority_sentence = ", ".join(f"{name.replace('_', ' ')}" for name, _ in ordered[:3])

    summary = (
        f"{display_company} is preparing for {agenda.lower()} in the {sector.lower()} space, "
        f"with emphasis on {priority_sentence}."
    )

    strategic_fit: List[str] = [
        f"Align {display_company}'s {sector.lower()} capabilities with localized operating partners to accelerate execution."
    ]
    demand_drivers: List[str] = [
        f"Validate demand signals for {sector.lower()} offerings across priority customer segments before scaling investments."
    ]
    technology_enablers: List[str] = [
        f"Leverage digital tooling and data assets to differentiate {display_company}'s {sector.lower()} proposition in new markets."
    ]
    regulatory_watch: List[str] = [
        f"Map licensing, labor, and data requirements governing {sector.lower()} operators ahead of launch."
    ]
    sustainability_factors: List[str] = [
        f"Assess environmental expectations for {sector.lower()} value chains to inform product design and sourcing."
    ]
    risk_watch: List[str] = [
        f"Monitor geopolitical and supply-chain volatility that could disrupt {display_company}'s expansion roadmap."
    ]

    if "cost_efficiency" in priorities:
        strategic_fit.append(
            f"Prioritize near-term efficiencies, such as shared services or automation, to protect {display_company}'s margin profile."
        )
    if "digital" in priorities:
        technology_enablers.append(
            f"Invest in localized integrations and APIs to embed {display_company}'s platform within regional ecosystems."
        )
    if "sustainability" in priorities:
        sustainability_factors.append(
            f"Embed measurable sustainability KPIs into the market entry case for {display_company}."
        )
    if "growth" in priorities:
        demand_drivers.append(
            f"Size white-space demand pools for {sector.lower()} solutions to justify scaling capital deployment."
        )
    if "risk" in priorities:
        risk_watch.append(
            f"Define contingency plans for regulatory or macro shocks that could impede {agenda.lower()} milestones."
        )

    return {
        "profile_summary": summary,
        "strategic_fit": strategic_fit,
        "demand_drivers": demand_drivers,
        "technology_enablers": technology_enablers,
        "regulatory_watch": regulatory_watch,
        "sustainability_factors": sustainability_factors,
        "risk_watch": risk_watch,
    }


def generate_market_analysis(
    company: str,
    industry: str,
    use_case: str,
    markets: List[str],
    priorities: List[str],
) -> ComparativeAnalysis:
    dataset = load_country_indicators()
    weights = _parse_priorities(priorities)

    try:
        company_brief = generate_company_market_brief(
            company=company,
            industry=industry,
            use_case=use_case,
            priorities=weights,
        )
    except ChatGPTNotConfiguredError:
        company_brief = _fallback_company_brief(company, industry, use_case, weights)
    except Exception as exc:  # noqa: BLE001 - log unexpected API issues
        LOGGER.warning("Falling back to heuristic company brief: %s", exc)
        company_brief = _fallback_company_brief(company, industry, use_case, weights)

    results: List[MarketAnalysisResult] = []
    for market in markets:
        indicator: CountryIndicator = dataset[market]
        pestel = generate_pestel_from_indicators(
            market,
            indicator.indicators,
            indicator.narratives,
            company=company,
            industry=industry,
            priorities=weights,
            use_case=use_case,
            company_brief=company_brief,
        )
        score = compute_market_score(indicator.indicators, weights)
        news = get_recent_news_summaries(market, indicator)
        entry_mode = select_entry_mode(score.composite, use_case)
        turnaround_actions = build_turnaround_actions(score.dimension_scores)
        results.append(
            MarketAnalysisResult(
                country=market,
                pestel=pestel,
                score=score,
                news=news,
                entry_mode=entry_mode,
                turnaround_actions=turnaround_actions,
                sources=indicator.sources,
            )
        )

    return ComparativeAnalysis(
        company=company,
        industry=industry,
        priorities=weights,
        use_case=use_case,
        markets=results,
        company_brief=company_brief,
    )
