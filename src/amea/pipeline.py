"""High level orchestration for the AMEA market analysis pipeline."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List

from .analysis.scoring import ScoreBreakdown
from .research.llm import (
    ChatGPTNotConfiguredError,
    generate_company_market_brief,
    generate_market_snapshot,
)


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
        weights = {"growth": 1.0, "risk": 1.0}
    return weights


def _sanitize_pestel(payload: Dict[str, object]) -> Dict[str, List[str]]:
    result: Dict[str, List[str]] = {}
    for dimension in ["Political", "Economic", "Social", "Technological", "Environmental", "Legal"]:
        value = payload.get(dimension) or payload.get(dimension.lower()) if isinstance(payload, dict) else None
        bullets: List[str] = []
        if isinstance(value, list):
            bullets = [str(item).strip() for item in value if str(item).strip()]
        elif isinstance(value, str):
            bullets = [value.strip()] if value.strip() else []
        result[dimension] = bullets
    return result


def _sanitize_turnaround_actions(raw: object) -> Dict[str, str]:
    if not isinstance(raw, dict):
        return {}
    sanitized: Dict[str, str] = {}
    for key, value in raw.items():
        if value is None:
            continue
        text = str(value).strip()
        if text:
            sanitized[str(key)] = text
    return sanitized


def _sanitize_sources(raw: object) -> List[str]:
    if not raw:
        return []
    if isinstance(raw, str):
        cleaned = raw.strip()
        return [cleaned] if cleaned else []
    if isinstance(raw, list):
        sources: List[str] = []
        for item in raw:
            if item is None:
                continue
            cleaned = str(item).strip()
            if cleaned:
                sources.append(cleaned)
        return sources
    return []


def _sanitize_news(raw: object) -> List[str]:
    if not raw:
        return []
    if isinstance(raw, str):
        cleaned = raw.strip()
        return [cleaned] if cleaned else []
    if isinstance(raw, list):
        headlines: List[str] = []
        for item in raw:
            if item is None:
                continue
            cleaned = str(item).strip()
            if cleaned:
                headlines.append(cleaned)
        return headlines
    return []


def generate_market_analysis(
    company: str,
    industry: str,
    use_case: str,
    markets: List[str],
    priorities: List[str],
) -> ComparativeAnalysis:
    weights = _parse_priorities(priorities)

    company_brief = generate_company_market_brief(
        company=company,
        industry=industry,
        use_case=use_case,
        priorities=weights,
    )

    results: List[MarketAnalysisResult] = []
    for market in markets:
        if not market:
            continue
        try:
            snapshot = generate_market_snapshot(
                country=market,
                company=company,
                industry=industry,
                use_case=use_case,
                priorities=weights,
                company_brief=company_brief,
            )
        except ChatGPTNotConfiguredError:
            raise
        except Exception as exc:  # noqa: BLE001 - provide context for debugging
            raise RuntimeError(f"Failed to generate ChatGPT snapshot for {market}: {exc}") from exc

        pestel_payload = snapshot.get("pestel") if isinstance(snapshot, dict) else {}
        scores_payload = snapshot.get("scores") if isinstance(snapshot, dict) else {}

        score = ScoreBreakdown.from_payload(scores_payload if isinstance(scores_payload, dict) else {})
        news = _sanitize_news(snapshot.get("recent_signals"))
        entry_mode = str(snapshot.get("entry_mode") or "").strip()
        turnaround = _sanitize_turnaround_actions(snapshot.get("turnaround_actions"))
        sources = _sanitize_sources(snapshot.get("sources"))

        results.append(
            MarketAnalysisResult(
                country=market,
                pestel=_sanitize_pestel(pestel_payload if isinstance(pestel_payload, dict) else {}),
                score=score,
                news=news,
                entry_mode=entry_mode,
                turnaround_actions=turnaround,
                sources=sources,
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


__all__ = ["MarketAnalysisResult", "ComparativeAnalysis", "generate_market_analysis"]
