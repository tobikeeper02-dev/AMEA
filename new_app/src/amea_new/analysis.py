"""Pipeline to generate market analysis via ChatGPT."""
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
    lines = [line.strip() for line in response_text.splitlines() if line.strip()]
    if not lines:
        return {}
    data: Dict[str, str] = {}
    for line in lines:
        prefix, sep, rest = line.partition(":")
        if sep and prefix.lower().startswith("p"):
            data["Political"] = rest.strip()
        elif sep and prefix.lower().startswith("e"):
            if "Environmental" in prefix or prefix.lower().startswith("env"):
                data["Environmental"] = rest.strip()
            else:
                data.setdefault("Economic", rest.strip())
        elif sep and prefix.lower().startswith("s"):
            data["Social"] = rest.strip()
        elif sep and prefix.lower().startswith("t"):
            data["Technological"] = rest.strip()
        elif sep and prefix.lower().startswith("l"):
            data["Legal"] = rest.strip()
    return data
