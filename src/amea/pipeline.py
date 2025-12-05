"""Straightforward market analysis pipeline using ChatGPT.

The goal is reliability over sophistication: the functions below gather engagement
inputs, query ChatGPT for tailored insights, and assemble a simple structure for the
Streamlit UI to render.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .research.llm import ChatGPTConfig, ChatGPTNotConfiguredError, run_completion


@dataclass
class MarketResult:
    country: str
    summary: str
    recommendations: List[str] = field(default_factory=list)
    pestel: Dict[str, List[str]] = field(default_factory=dict)
    sources: List[str] = field(default_factory=list)


@dataclass
class AnalysisResult:
    company: str
    industry: str
    priorities: List[str]
    company_brief: str
    markets: List[MarketResult]


def _pestel_prompt(company: str, industry: str, country: str, priorities: List[str]) -> str:
    priority_text = ", ".join(priorities) if priorities else "general growth"
    return (
        "You are a consulting analyst. Write JSON with keys `summary`, `pestel`, "
        "`recommendations`, and `sources`. `pestel` should contain arrays for "
        "Political, Economic, Social, Technological, Environmental, and Legal. Each bullet "
        "must reflect the company and industry context. Use current, realistic factors. "
        "Country: "
        f"{country}. Company: {company}. Industry: {industry}. Priorities: {priority_text}."
    )


def generate_company_brief(config: ChatGPTConfig, company: str, industry: str) -> str:
    prompt = (
        f"Provide a 3-sentence overview of {company} in the {industry} space, including "
        "customer needs and competitive posture."
    )
    try:
        return run_completion(
            config,
            prompt,
            system="You craft concise, factual company briefs.",
        )
    except ChatGPTNotConfiguredError:
        raise
    except Exception as exc:  # noqa: BLE001
        return f"Unable to retrieve company brief: {exc}"


def _safe_parse_list(value: Optional[str]) -> List[str]:
    if not value:
        return []
    parts = [part.strip(" -\n") for part in value.split("\n") if part.strip()]
    return parts


def generate_market_result(
    config: ChatGPTConfig, company: str, industry: str, country: str, priorities: List[str]
) -> MarketResult:
    prompt = _pestel_prompt(company, industry, country, priorities)
    try:
        raw = run_completion(
            config,
            prompt,
            system=(
                "Return valid JSON. Keep bullets short and relevant. "
                "Use real-world signals; avoid placeholders."
            ),
        )
    except ChatGPTNotConfiguredError:
        raise
    except Exception as exc:  # noqa: BLE001
        return MarketResult(country=country, summary=f"ChatGPT request failed: {exc}")

    try:
        import json

        parsed = json.loads(raw)
    except Exception:
        return MarketResult(
            country=country,
            summary="ChatGPT did not return valid JSON.",
            recommendations=_safe_parse_list(raw),
        )

    pestel = {k: _safe_parse_list(v) if isinstance(v, str) else v for k, v in parsed.get("pestel", {}).items()}
    return MarketResult(
        country=country,
        summary=parsed.get("summary", ""),
        recommendations=parsed.get("recommendations", []),
        pestel=pestel,
        sources=parsed.get("sources", []),
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
        generate_market_result(config, company, industry, country, priorities) for country in markets
    ]
    return AnalysisResult(
        company=company,
        industry=industry,
        priorities=priorities,
        company_brief=brief,
        markets=market_results,
    )

