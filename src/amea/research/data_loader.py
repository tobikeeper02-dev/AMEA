"""Utilities for loading market indicators and contextual information."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .llm import ChatGPTNotConfiguredError, summarize_news_with_chatgpt


LOGGER = logging.getLogger(__name__)

DATA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "country_indicators.json"


@dataclass
class CountryIndicator:
    """Structured economic and strategic indicators for a country."""

    name: str
    indicators: Dict[str, float]
    narratives: Dict[str, List[str]]
    sources: List[str]


def load_country_indicators() -> Dict[str, CountryIndicator]:
    """Load country indicator data from the packaged JSON file."""
    with DATA_PATH.open("r", encoding="utf-8") as handle:
        raw_data = json.load(handle)

    result: Dict[str, CountryIndicator] = {}
    for country, payload in raw_data.items():
        result[country] = CountryIndicator(
            name=country,
            indicators=payload.get("indicators", {}),
            narratives=payload.get("narratives", {}),
            sources=payload.get("sources", []),
        )
    return result


def get_recent_news_summaries(country: str, indicator: Optional[CountryIndicator] = None) -> List[str]:
    """Return synthesized news bullets for a market.

    When ChatGPT credentials are available we ask the model to rewrite the
    curated notes into polished highlights. Otherwise the curated bullets are
    returned unchanged.
    """

    if indicator is None:
        indicator = load_country_indicators()[country]

    baseline = indicator.narratives.get("news", [])
    if not baseline:
        return []

    try:
        return summarize_news_with_chatgpt(
            country=country,
            news_bullets=baseline,
            sources=indicator.sources,
        )
    except ChatGPTNotConfiguredError:
        return baseline
    except Exception as exc:  # noqa: BLE001 - logging for observability
        LOGGER.warning("Falling back to curated news for %s: %s", country, exc)
        return baseline
