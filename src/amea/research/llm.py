"""OpenAI ChatGPT helpers for AMEA."""
from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from typing import Dict, Iterable, List, Mapping, Sequence

from openai import OpenAI


LOGGER = logging.getLogger(__name__)

PESTEL_DIMENSIONS = [
    "Political",
    "Economic",
    "Social",
    "Technological",
    "Environmental",
    "Legal",
]


class ChatGPTNotConfiguredError(RuntimeError):
    """Raised when ChatGPT credentials are not available."""


def _get_temperature() -> float:
    raw = os.getenv("AMEA_OPENAI_TEMPERATURE", "0.2")
    try:
        value = float(raw)
    except ValueError:
        return 0.2
    return max(0.0, min(value, 1.0))


def _model_name() -> str:
    return os.getenv("AMEA_OPENAI_MODEL", "gpt-4o-mini")


@lru_cache(maxsize=1)
def _client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ChatGPTNotConfiguredError("Set OPENAI_API_KEY to enable ChatGPT features.")

    base_url = os.getenv("OPENAI_BASE_URL")
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)


def is_chatgpt_configured() -> bool:
    """Return True when an API key is available for ChatGPT calls."""

    return bool(os.getenv("OPENAI_API_KEY"))


def _extract_json_structure(text: str) -> object:
    """Attempt to parse JSON from a model response."""

    snippet = text.strip()
    if not snippet:
        raise ValueError("Empty ChatGPT response")

    start_index = None
    end_index = None
    if "{" in snippet:
        start_index = snippet.find("{")
        end_index = snippet.rfind("}")
    if (start_index is None or end_index is None) and "[" in snippet:
        start_index = snippet.find("[")
        end_index = snippet.rfind("]")

    if start_index is None or end_index is None or end_index <= start_index:
        raise ValueError("ChatGPT response did not include JSON content")

    candidate = snippet[start_index : end_index + 1]
    return json.loads(candidate)


def _normalize_bullets(items: Iterable[object]) -> List[str]:
    bullets: List[str] = []
    for item in items:
        if item is None:
            continue
        if isinstance(item, str):
            cleaned = item.strip()
            if cleaned:
                bullets.append(cleaned)
        else:
            cleaned = str(item).strip()
            if cleaned and cleaned.lower() != "none":
                bullets.append(cleaned)
    return bullets


def _format_priorities(priorities: Mapping[str, float]) -> str:
    if not priorities:
        return "Client indicated balanced priorities across strategic themes."
    ordered = sorted(priorities.items(), key=lambda item: item[1], reverse=True)
    formatted = ", ".join(f"{name} ({weight:.1f})" for name, weight in ordered)
    return f"Client priorities ranked by emphasis: {formatted}."


def _indicator_section(indicators: Mapping[str, float]) -> str:
    if not indicators:
        return "No quantitative indicators supplied."
    return "\n".join(f"- {key}: {value}" for key, value in sorted(indicators.items()))


def _narrative_section(narratives: Mapping[str, Sequence[str]]) -> str:
    lines: List[str] = []
    for dimension in PESTEL_DIMENSIONS:
        key = dimension.lower()
        hints = narratives.get(key, [])
        if hints:
            joined = "; ".join(hints)
        else:
            joined = "No additional curated notes provided."
        lines.append(f"{dimension}: {joined}")
    return "\n".join(lines)


def generate_pestel_with_chatgpt(
    *,
    country: str,
    company: str,
    industry: str,
    use_case: str,
    priorities: Mapping[str, float],
    indicators: Mapping[str, float],
    narratives: Mapping[str, Sequence[str]],
) -> Dict[str, List[str]]:
    """Request a PESTEL analysis from ChatGPT."""

    client = _client()
    prompt = (
        "You are a senior strategy consultant supporting a market entry analysis.\n"
        "Using the structured data below, produce a concise PESTEL summary with 2-3 bullets per dimension.\n"
        "Each bullet should tie back to the quantitative indicators or curated context.\n"
        "Return valid JSON with the keys Political, Economic, Social, Technological, Environmental, Legal.\n"
        "Do not include commentary outside of the JSON object.\n"
        f"Country: {country}\n"
        f"Company: {company or 'Client'}\n"
        f"Industry: {industry or 'Not specified'}\n"
        f"Engagement use case: {use_case or 'Market expansion'}\n"
        f"{_format_priorities(priorities)}\n"
        "Quantitative indicators:\n"
        f"{_indicator_section(indicators)}\n"
        "Curated talking points by dimension:\n"
        f"{_narrative_section(narratives)}\n"
        "Respond with concise, executive-ready language."
    )

    response = client.responses.create(
        model=_model_name(),
        input=prompt,
        temperature=_get_temperature(),
        max_output_tokens=1200,
    )

    text = getattr(response, "output_text", "")
    if not text:
        raise ValueError("ChatGPT returned an empty payload for PESTEL request")

    raw = _extract_json_structure(text)
    if not isinstance(raw, dict):
        raise ValueError("ChatGPT PESTEL response was not a JSON object")

    result: Dict[str, List[str]] = {}
    for dimension in PESTEL_DIMENSIONS:
        value = raw.get(dimension) or raw.get(dimension.lower()) or raw.get(dimension.upper())
        if value is None:
            result[dimension] = []
        elif isinstance(value, list):
            result[dimension] = _normalize_bullets(value)
        else:
            result[dimension] = _normalize_bullets([value])

    return result


def summarize_news_with_chatgpt(
    *,
    country: str,
    news_bullets: Sequence[str],
    sources: Sequence[str] | None = None,
) -> List[str]:
    """Ask ChatGPT to rewrite curated headlines into fresh highlights."""

    if not news_bullets:
        return []

    client = _client()
    source_section = "\n".join(f"- {item}" for item in sources or [])
    prompt = (
        "You help consultants synthesize market signals.\n"
        "Rewrite the provided news bullets into 2-3 crisp highlights that a C-suite audience can skim quickly.\n"
        "Keep all statements factual and grounded in the supplied notes.\n"
        "Return a JSON array of strings (each string is one bullet).\n"
        f"Country: {country}\n"
        "Curated notes:\n"
        + "\n".join(f"- {bullet}" for bullet in news_bullets)
    )
    if source_section:
        prompt += "\nRelevant sources:\n" + source_section

    response = client.responses.create(
        model=_model_name(),
        input=prompt,
        temperature=_get_temperature(),
        max_output_tokens=600,
    )

    text = getattr(response, "output_text", "")
    if not text:
        raise ValueError("ChatGPT returned an empty payload for news summary")

    raw = _extract_json_structure(text)
    candidates: Sequence[object]
    if isinstance(raw, dict):
        candidates = raw.get("bullets") or raw.get("highlights") or []
    elif isinstance(raw, list):
        candidates = raw
    else:
        raise ValueError("ChatGPT news response was not a JSON list")

    bullets = _normalize_bullets(candidates)
    if not bullets:
        raise ValueError("ChatGPT news response did not contain usable bullets")
    return bullets


__all__ = [
    "ChatGPTNotConfiguredError",
    "generate_pestel_with_chatgpt",
    "summarize_news_with_chatgpt",
    "is_chatgpt_configured",
]

