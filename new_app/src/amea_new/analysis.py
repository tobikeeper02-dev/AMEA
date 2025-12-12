"""Pipeline to generate market analysis via ChatGPT."""
import json
from dataclasses import dataclass
from typing import Dict, List

from .llm import OpenAIConfig, chat_complete


@dataclass
class AnalysisResult:
    country: str
    pestel: Dict[str, str]
    raw_text: str


def _format_request(company: str, industry: str, country: str, priorities: List[str]) -> str:
    priorities_text = "\n".join(f"- {p}" for p in priorities) if priorities else "- Not specified"
    return (
        "Return a concise JSON object with the keys Political, Economic, Social, Technological, "
        "Environmental, Legal. Each value should be a short paragraph with data-driven insight relevant to the request.\n"
        f"Company: {company}\nIndustry: {industry}\nCountry: {country}\nPriorities:\n{priorities_text}\n"
        "Use recent and relevant factors only."
    )


def analyze_request(
    *,
    company: str,
    industry: str,
    markets: List[str],
    priorities: List[str],
    config: OpenAIConfig,
) -> List[AnalysisResult]:
    system_prompt = "You are a consultant producing PESTEL insights for market entry decisions."
    results: List[AnalysisResult] = []
    for country in markets:
        request = _format_request(company, industry, country, priorities)
        raw_text = chat_complete(config, system_prompt=system_prompt, user_prompt=request)
        pestel = _parse_pestel(raw_text)
        results.append(AnalysisResult(country=country, pestel=pestel, raw_text=raw_text))
    return results


def _parse_pestel(response_text: str) -> Dict[str, str]:
    if not response_text.strip():
        return {}

    json_pestel = _parse_json_block(response_text)
    if json_pestel:
        return json_pestel

    return _parse_colon_lines(response_text)


def _parse_json_block(response_text: str) -> Dict[str, str]:
    try:
        parsed = json.loads(response_text)
    except json.JSONDecodeError:
        return {}

    if not isinstance(parsed, dict):
        return {}

    normalized: Dict[str, str] = {}
    for key in ["Political", "Economic", "Social", "Technological", "Environmental", "Legal"]:
        value = parsed.get(key) or parsed.get(key.lower())
        if isinstance(value, list):
            value = " ".join(str(item).strip() for item in value if str(item).strip())
        if isinstance(value, str) and value.strip():
            normalized[key] = value.strip()
    return normalized


def _parse_colon_lines(response_text: str) -> Dict[str, str]:
    lines = [line.strip() for line in response_text.splitlines() if line.strip()]
    if not lines:
        return {}

    data: Dict[str, str] = {}
    for line in lines:
        prefix, sep, rest = line.partition(":")
        if not sep:
            continue
        lower_prefix = prefix.lower()
        if lower_prefix.startswith("p"):
            data["Political"] = rest.strip()
        elif lower_prefix.startswith("e"):
            if "environmental" in lower_prefix:
                data["Environmental"] = rest.strip()
            else:
                data.setdefault("Economic", rest.strip())
        elif lower_prefix.startswith("s"):
            data["Social"] = rest.strip()
        elif lower_prefix.startswith("t"):
            data["Technological"] = rest.strip()
        elif lower_prefix.startswith("l"):
            data["Legal"] = rest.strip()
    return data
