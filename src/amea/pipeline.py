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
