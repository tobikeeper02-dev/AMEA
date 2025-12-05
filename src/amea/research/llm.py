"""OpenAI ChatGPT helpers for AMEA."""
from __future__ import annotations

import json
import logging
import os
import time
from functools import lru_cache
from typing import Any, Dict, Iterable, Mapping

from openai import OpenAI


TEMPERATURE_UNSUPPORTED_PREFIXES = ("gpt-5-nano",)


LOGGER = logging.getLogger(__name__)

PESTEL_DIMENSIONS = [
    "Political",
    "Economic",
    "Social",
    "Technological",
    "Environmental",
    "Legal",
]

SESSION_API_KEY = "amea_openai_api_key"
SESSION_BASE_URL = "amea_openai_base_url"
SESSION_MODEL = "amea_openai_model"
SESSION_TEMPERATURE = "amea_openai_temperature"


class ChatGPTNotConfiguredError(RuntimeError):
    """Raised when ChatGPT credentials are not available."""


def _get_streamlit_module():  # pragma: no cover - optional dependency
    try:  # Import lazily to avoid a hard dependency outside the app runtime
        import streamlit as st  # type: ignore
    except Exception:  # noqa: BLE001 - any import issue means Streamlit is unavailable
        return None
    return st


def _from_session_state(key: str) -> str | None:
    st = _get_streamlit_module()
    if not st:
        return None
    try:
        value = st.session_state.get(key)
    except Exception:  # noqa: BLE001 - guard against SessionState access errors
        return None
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    value = value.strip()
    return value or None


def _from_streamlit_secrets(key: str) -> str | None:
    st = _get_streamlit_module()
    if not st:
        return None
    try:
        value = st.secrets.get(key)
    except Exception:  # noqa: BLE001 - secrets may not be configured
        return None
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    value = value.strip()
    return value or None


def _resolve_config_value(env_var: str, *, session_key: str | None = None) -> str | None:
    """Resolve configuration with Streamlit session > env var > secrets."""

    if session_key:
        if session_value := _from_session_state(session_key):
            return session_value

    # Allow matching session key fallback when not explicitly provided
    if not session_key:
        inferred_session_key = f"amea_{env_var.lower()}"
        if session_value := _from_session_state(inferred_session_key):
            return session_value

    env_value = os.getenv(env_var)
    if env_value:
        env_value = env_value.strip()
        if env_value:
            return env_value

    return _from_streamlit_secrets(env_var)


def _get_temperature() -> float:
    raw = _resolve_config_value("AMEA_OPENAI_TEMPERATURE", session_key=SESSION_TEMPERATURE) or "0.2"
    try:
        value = float(raw)
    except ValueError:
        return 0.2
    return max(0.0, min(value, 1.0))


def _model_name() -> str:
    return _resolve_config_value("AMEA_OPENAI_MODEL", session_key=SESSION_MODEL) or "gpt-5-nano"


@lru_cache(maxsize=1)
def _cached_client(api_key: str, base_url: str | None) -> OpenAI:
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)


def _client() -> OpenAI:
    api_key = _resolve_config_value("OPENAI_API_KEY", session_key=SESSION_API_KEY)
    if not api_key:
        raise ChatGPTNotConfiguredError("Provide an OpenAI API key to enable ChatGPT features.")

    base_url = _resolve_config_value("OPENAI_BASE_URL", session_key=SESSION_BASE_URL)
    return _cached_client(api_key, base_url)


def _supports_temperature(model: str) -> bool:
    return not any(model.startswith(prefix) for prefix in TEMPERATURE_UNSUPPORTED_PREFIXES)


def _response_text(response: Any) -> str:
    """Extract concatenated text output from a Responses API payload."""

    def _get(obj: Any, key: str, default: Any = None) -> Any:
        if obj is None:
            return default
        if isinstance(obj, Mapping):
            return obj.get(key, default)
        return getattr(obj, key, default)

    def _coerce_text(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, Mapping):
            return _coerce_text(value.get("value") or value.get("text"))
        if isinstance(value, Iterable):
            result: list[str] = []
            for item in value:
                result.extend(_coerce_text(item))
            return result
        return [str(value)]

    if response is None:
        return ""

    text = _get(response, "output_text")
    if response is None:
        return ""

    text = getattr(response, "output_text", None)
    if isinstance(text, str) and text.strip():
        return text

    parts: list[str] = []
    for output in _get(response, "output", []) or []:
        for content in _get(output, "content", []) or []:
            content_type = _get(content, "type")
            if content_type not in {"text", "output_text"}:
                continue
            parts.extend(_coerce_text(_get(content, "text")))
    if parts:
        return "".join(parts)

    # Handle responses that expose a raw "text" or "message" field at the output level
    for output in _get(response, "output", []) or []:
        parts.extend(_coerce_text(_get(output, "text")))
        parts.extend(_coerce_text(_get(output, "message")))
    if parts:
        return "".join(parts)

    # Fall back to any top-level text-like payload
    for candidate in ("message", "text", "content"):
        parts.extend(_coerce_text(_get(response, candidate)))
    for output in getattr(response, "output", []) or []:
        output_type = getattr(output, "type", None)
        if output_type != "output_text":
            continue
        for content in getattr(output, "content", []) or []:
            if getattr(content, "type", None) != "text":
                continue
            text_block = getattr(getattr(content, "text", None), "value", None)
            if isinstance(text_block, str) and text_block:
                parts.append(text_block)

    return "".join(parts)


def _request_kwargs(model: str) -> Dict[str, Any]:
    """Build keyword arguments for the Responses API call."""

    kwargs: Dict[str, Any] = {"model": model}
    if _supports_temperature(model):
        kwargs["temperature"] = _get_temperature()
    return kwargs


def is_chatgpt_configured() -> bool:
    """Return True when an API key is available for ChatGPT calls."""

    return bool(_resolve_config_value("OPENAI_API_KEY", session_key=SESSION_API_KEY))


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


def _normalize_bullets(items: Iterable[object]) -> list[str]:
    bullets: list[str] = []
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


def _format_company_brief(company_brief: Mapping[str, Any] | None) -> str:
    if not company_brief:
        return "No prior context captured."
    try:
        return json.dumps(company_brief, ensure_ascii=False, indent=2)
    except TypeError:
        return str(company_brief)


def generate_company_market_brief(
    *,
    company: str,
    industry: str,
    use_case: str,
    priorities: Mapping[str, float],
) -> Dict[str, Any]:
    """Return a company and industry context pack using ChatGPT."""

    client = _client()
    prompt = (
        "You are drafting the executive brief for a market entry strategy engagement.\n"
        "Synthesize what makes the client distinctive and which industry forces matter most before the country deep-dives begin.\n"
        "Respond with a JSON object containing these keys: profile_summary (string), strategic_fit (array of strings), demand_drivers (array of strings), technology_enablers (array of strings), regulatory_watch (array of strings), sustainability_factors (array of strings), risk_watch (array of strings).\n"
        "Each array item should be a concise, insight-driven bullet (max 28 words) that ties directly to the company and its industry.\n"
        "Draw on well-known facts through 2024 and clarify assumptions if direct evidence is limited.\n"
        f"Company: {company or 'Client'}\n"
        f"Industry focus: {industry or 'Not specified'}\n"
        f"Engagement goal: {use_case or 'Market expansion'}\n"
        f"{_format_priorities(priorities)}\n"
        "Avoid generic statements that could apply to any sector; be specific about the business model, value chain, and regulatory posture.\n"
    )

    model = _model_name()
    response = client.responses.create(
        input=prompt,
        max_output_tokens=900,
        **_request_kwargs(model),
    )

    text = _response_text(response)
    if not text:
        raise ValueError("ChatGPT returned an empty payload for company briefing")

    raw = _extract_json_structure(text)
    if not isinstance(raw, dict):
        raise ValueError("ChatGPT company briefing response was not a JSON object")

    def _normalize_section(key: str) -> list[str]:
        value = raw.get(key) or raw.get(key.lower()) or raw.get(key.replace("_", ""))
        if value is None:
            return []
        if isinstance(value, list):
            return _normalize_bullets(value)
        return _normalize_bullets([value])

    result: Dict[str, Any] = {
        "profile_summary": raw.get("profile_summary")
        or raw.get("summary")
        or raw.get("profile"),
        "strategic_fit": _normalize_section("strategic_fit"),
        "demand_drivers": _normalize_section("demand_drivers"),
        "technology_enablers": _normalize_section("technology_enablers"),
        "regulatory_watch": _normalize_section("regulatory_watch"),
        "sustainability_factors": _normalize_section("sustainability_factors"),
        "risk_watch": _normalize_section("risk_watch"),
    }
    summary = result.get("profile_summary")
    if isinstance(summary, list):
        result["profile_summary"] = "; ".join(summary)
    elif isinstance(summary, (int, float)):
        result["profile_summary"] = str(summary)
    elif isinstance(summary, str):
        result["profile_summary"] = summary.strip()

    return result


def generate_market_snapshot(
    *,
    country: str,
    company: str,
    industry: str,
    use_case: str,
    priorities: Mapping[str, float],
    company_brief: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Ask ChatGPT for a market snapshot tailored to the engagement."""

    client = _client()
    brief_section = _format_company_brief(company_brief)
    priorities_sentence = _format_priorities(priorities)

    prompt = (
        "You are AMEA, an AI consultant building a market entry pack.\n"
        "Leverage domain knowledge, recent macro trends (through 2024), and logical inference to draft country-specific insights.\n"
        "Do NOT reuse canned or placeholder text—tailor every point to the company, industry, and country.\n"
        "If concrete datapoints are uncertain, note the assumption explicitly rather than fabricating figures.\n"
        "Return STRICT JSON with this structure:\n"
        "{"
        "  \"pestel\": {dimension -> array of 2-3 bullets},\n"
        "  \"scores\": {\"composite\": number 0-100, \"dimensions\": {dimension -> number 0-100}},\n"
        "  \"recent_signals\": array of 2-3 bullets tying to news, policy, or demand shifts,\n"
        "  \"entry_mode\": string,\n"
        "  \"turnaround_actions\": object mapping focus areas to mitigation actions (omit keys if none),\n"
        "  \"sources\": array of citations or reputable references (title + year + URL when available).\n"
        "}\n"
        "Dimension keys for scores should include: growth, cost_efficiency, risk, sustainability, digital.\n"
        "Ensure PESTEL keys are exactly: Political, Economic, Social, Technological, Environmental, Legal.\n"
        "Context to ground your analysis:\n"
        f"Country: {country}\n"
        f"Company: {company or 'Client'}\n"
        f"Industry: {industry or 'Not specified'}\n"
        f"Engagement goal: {use_case or 'Market expansion'}\n"
        f"{priorities_sentence}\n"
        "Company intelligence (JSON):\n"
        f"{brief_section}\n"
        "Deliver differentiated, decision-useful insights relevant for this exact engagement."
    )

    model = _model_name()
    response = client.responses.create(
        input=prompt,
        max_output_tokens=1600,
        **_request_kwargs(model),
    )

    text = _response_text(response)
    if not text:
        raise ValueError("ChatGPT returned an empty payload for market snapshot")

    raw = _extract_json_structure(text)
    if not isinstance(raw, dict):
        raise ValueError("ChatGPT market snapshot response was not a JSON object")

    return raw


def run_chatgpt_healthcheck() -> Dict[str, Any]:
    """Perform a lightweight API call to verify connectivity."""

    start = time.perf_counter()
    client = _client()
    model = _model_name()
    request_kwargs = _request_kwargs(model)
    if _supports_temperature(model):
        request_kwargs["temperature"] = 0.0
    response = client.responses.create(
        input="Return JSON {\"status\": \"ok\", \"echo\": \"AMEA\"}.",
        max_output_tokens=50,
        **request_kwargs,
    )
    latency_ms = (time.perf_counter() - start) * 1000
    text = _response_text(response)
    payload = _extract_json_structure(text)
    if not isinstance(payload, dict) or payload.get("status") != "ok":
        raise ValueError("ChatGPT health check did not return the expected payload")

    return {
        "status": payload.get("status", "unknown"),
        "echo": payload.get("echo"),
        "latency_ms": round(latency_ms, 1),
        "model": getattr(response, "model", _model_name()),
    }


__all__ = [
    "ChatGPTNotConfiguredError",
    "generate_company_market_brief",
    "generate_market_snapshot",
    "is_chatgpt_configured",
    "run_chatgpt_healthcheck",
]
