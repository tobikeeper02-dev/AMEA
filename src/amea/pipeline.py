"""High level orchestration for the AMEA market analysis pipeline."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .analysis.pestel import generate_pestel_from_indicators
from .analysis.recommendations import build_turnaround_actions, select_entry_mode
from .analysis.scoring import ScoreBreakdown, compute_market_score
from .research.data_loader import CountryIndicator, get_recent_news_summaries, load_country_indicators


@dataclass
class MarketAnalysisResult:
    country: str
    pestel: Dict[str, List[str]]
    score: ScoreBreakdown
    news: List[str]
    entry_mode: str
    turnaround_actions: Dict[str, str]


@dataclass
class ComparativeAnalysis:
    company: str
    industry: str
    priorities: Dict[str, float]
    markets: List[MarketAnalysisResult]

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


def generate_market_analysis(
    company: str,
    industry: str,
    markets: List[str],
    priorities: List[str],
) -> ComparativeAnalysis:
    dataset = load_country_indicators()
    weights = _parse_priorities(priorities)

    results: List[MarketAnalysisResult] = []
    for market in markets:
        indicator: CountryIndicator = dataset[market]
        pestel = generate_pestel_from_indicators(market, indicator.indicators, indicator.narratives)
        score = compute_market_score(indicator.indicators, weights)
        news = get_recent_news_summaries(market)
        entry_mode = select_entry_mode(score.composite)
        turnaround_actions = build_turnaround_actions(score.dimension_scores)
        results.append(
            MarketAnalysisResult(
                country=market,
                pestel=pestel,
                score=score,
                news=news,
                entry_mode=entry_mode,
                turnaround_actions=turnaround_actions,
            )
        )

    return ComparativeAnalysis(
        company=company,
        industry=industry,
        priorities=weights,
        markets=results,
    )
