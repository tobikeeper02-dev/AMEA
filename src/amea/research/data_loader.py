"""Utilities for loading market indicators and contextual information."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import json


DATA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "country_indicators.json"


@dataclass
class CountryIndicator:
    """Structured economic and strategic indicators for a country."""

    name: str
    indicators: Dict[str, float]
    narratives: Dict[str, List[str]]


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
        )
    return result


def get_recent_news_summaries(country: str) -> List[str]:
    """Placeholder for a live news retrieval layer.

    In production, this function would leverage news APIs or web scraping.
    For now, we return curated talking points from the packaged dataset.
    """
    return load_country_indicators()[country].narratives.get("news", [])
