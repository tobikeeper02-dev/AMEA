"""Scoring helpers for country comparison."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


def normalize_indicator(value: float, minimum: float, maximum: float) -> float:
    if maximum == minimum:
        return 0.0
    return max(0.0, min(1.0, (value - minimum) / (maximum - minimum)))


@dataclass
class ScoreBreakdown:
    dimension_scores: Dict[str, float]
    composite: float


def compute_market_score(indicators: Dict[str, float], priority_weights: Dict[str, float]) -> ScoreBreakdown:
    """Calculate a weighted opportunity score for a market."""
    base_scores = {
        "growth": normalize_indicator(indicators.get("gdp_growth", 0), -5, 8),
        "cost_efficiency": 1 - normalize_indicator(indicators.get("labor_cost_index", 60), 40, 120),
        "risk": 1 - normalize_indicator(indicators.get("political_risk", 30), 10, 80),
        "sustainability": normalize_indicator(indicators.get("renewable_energy_share", 10), 10, 60),
        "digital": normalize_indicator(indicators.get("digital_adoption", 20), 20, 95),
    }

    # Normalize priority weights
    total_weight = sum(priority_weights.values()) or 1.0
    normalized_weights = {k: v / total_weight for k, v in priority_weights.items()}

    composite = sum(base_scores.get(k, 0.0) * normalized_weights.get(k, 0.0) for k in base_scores)
    dimension_scores = {k: round(v * 100, 1) for k, v in base_scores.items()}

    return ScoreBreakdown(dimension_scores=dimension_scores, composite=round(composite * 100, 1))
