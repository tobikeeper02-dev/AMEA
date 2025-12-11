"""ChatGPT-only market analysis pipeline."""
"""Market analysis pipeline that relies entirely on ChatGPT."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Dict, List

from .research.llm import ChatGPTConfig, ChatGPTNotConfiguredError, run_completion


@dataclass
class MarketResult:
    country: str
    summary: str
    recommendations: List[str] = field(default_factory=list)
    pestel: Dict[str, List[str]] = field(default_factory=dict)
    sources: List[str] = field(default_factory=list)
    raw_response: str = ""


@dataclass
class AnalysisResult:
    company: str
    industry: str
    priorities: List[str]
    company_brief: str
    markets: List[MarketResult]


def _company_prompt(company: str, industry: str) -> str:
    return (
        "You are writing an executive brief for a market entry engagement. "
        f"Company: {company}. Industry: {industry}. "
        "Provide three crisp sentences: who they serve, current positioning, and their main strategic lever."
    )


def _market_prompt(company: str, industry: str, country: str, priorities: List[str]) -> str:
    priorities_text = ", ".join(priorities) if priorities else "general market fit"
    return (
        "Act as a senior consultant creating a market snapshot. Return JSON with keys "
        "`summary`, `pestel`, `recommendations`, and `sources`. `pestel` must have keys "
        "Political, Economic, Social, Technological, Environmental, Legal—each an array of short bullets. "
        "`recommendations` should be 3 bullets. `sources` should cite news or data points when available. "
        f"Company: {company}. Industry: {industry}. Market: {country}. Priorities: {priorities_text}. "
        "Use realistic, timely signals; avoid placeholders."
    )


def _parse_json_block(raw: str) -> Dict[str, object]:
    try:
        return json.loads(raw)
    except Exception:
        # Try to locate the first JSON object in the text
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(raw[start : end + 1])
            except Exception:
                pass
    return {}


def _clean_bullets(value: object) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip(" -\n") for item in value if str(item).strip()]
    if isinstance(value, str):
        return [part.strip(" -\n") for part in value.split("\n") if part.strip()]
    return []


def generate_company_brief(config: ChatGPTConfig, company: str, industry: str) -> str:
    return run_completion(
        config,
        _company_prompt(company, industry),
        system="You craft precise company briefs with no filler.",
    )


def generate_market_result(
    config: ChatGPTConfig, *, company: str, industry: str, country: str, priorities: List[str]
) -> MarketResult:
    try:
        raw = run_completion(
            config,
            _market_prompt(company, industry, country, priorities),
            system=(
                "Return compact, relevant market analysis. Respect the JSON structure. "
                "If data is sparse, state that explicitly."
            ),
            json_mode=True,
        )
    except ChatGPTNotConfiguredError:
        raise
    except Exception as exc:  # noqa: BLE001
        return MarketResult(country=country, summary=f"ChatGPT request failed: {exc}")

    parsed = _parse_json_block(raw)
    pestel_raw = parsed.get("pestel", {}) if isinstance(parsed, dict) else {}
    pestel: Dict[str, List[str]] = {}
    if isinstance(pestel_raw, dict):
        for dim, bullets in pestel_raw.items():
            pestel[dim] = _clean_bullets(bullets)

    recommendations = _clean_bullets(parsed.get("recommendations")) if isinstance(parsed, dict) else []
    sources = _clean_bullets(parsed.get("sources")) if isinstance(parsed, dict) else []
    summary = parsed.get("summary") if isinstance(parsed, dict) else None

    if not parsed:
        summary = "ChatGPT did not return valid JSON; showing raw output instead."
        recommendations = _clean_bullets(raw)

    return MarketResult(
        country=country,
        summary=summary or "No summary returned.",
        recommendations=recommendations,
        pestel=pestel,
        sources=sources,
        raw_response=raw,
    )


def generate_analysis(
    config: ChatGPTConfig,
    *,
    company: str,
    industry: str,
    markets: List[str],
    priorities: List[str],
) -> AnalysisResult:
    brief = generate_company_brief(config, company, industry)
    market_results = [
        generate_market_result(
            config,
            company=company,
            industry=industry,
            country=country,
            priorities=priorities,
        )
        for country in markets
        if country.strip()
    ]
    return AnalysisResult(
        company=company,
        industry=industry,
        priorities=priorities,
        company_brief=brief,
        markets=market_results,
    )
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
