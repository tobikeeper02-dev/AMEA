"""Lightweight ChatGPT client utilities."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import os


class ChatGPTNotConfiguredError(RuntimeError):
    """Raised when ChatGPT credentials are missing."""


@dataclass
class ChatGPTConfig:
    api_key: str
    base_url: Optional[str]
    model: str
    temperature: float = 0.2

    @classmethod
    def from_inputs(
        cls,
        api_key: Optional[str],
        base_url: Optional[str],
        model: Optional[str],
        temperature: Optional[float] = None,
    ) -> "ChatGPTConfig":
        env_key = os.getenv("OPENAI_API_KEY", "")
        env_base = os.getenv("OPENAI_BASE_URL")
        env_model = os.getenv("AMEA_OPENAI_MODEL", "gpt-5-nano")
        env_temp = os.getenv("AMEA_OPENAI_TEMPERATURE")
        resolved_temp = temperature
        if resolved_temp is None and env_temp:
            try:
                resolved_temp = float(env_temp)
            except ValueError:
                resolved_temp = None
        return cls(
            api_key=(api_key or env_key or ""),
            base_url=base_url or env_base,
            model=model or env_model,
            temperature=resolved_temp if resolved_temp is not None else 0.2,
        )


def is_chatgpt_configured(config: ChatGPTConfig) -> bool:
    return bool(config.api_key.strip())


def _client(config: ChatGPTConfig):
    if not is_chatgpt_configured(config):
        raise ChatGPTNotConfiguredError("OpenAI API key is missing.")

    try:
        from openai import OpenAI  # local import to avoid hard failure if dependency is missing
    except ImportError as exc:  # noqa: F841
        raise ChatGPTNotConfiguredError(
            "OpenAI SDK is not installed. Run `pip install -r requirements.txt` first."
        ) from exc

    kwargs: Dict[str, Any] = {"api_key": config.api_key}
    if config.base_url:
        kwargs["base_url"] = config.base_url
    return OpenAI(**kwargs)


def _response_kwargs(model: str, *, force_json: bool = False) -> Dict[str, Any]:
    kwargs: Dict[str, Any] = {"model": model}
    if force_json:
        kwargs["response_format"] = {"type": "json_object"}
    return kwargs


def _temperature_for_model(model: str, temperature: float) -> Optional[float]:
    if model.strip().lower() == "gpt-5-nano":
        return None
    return temperature


def _extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join([_extract_text(item) for item in content if item])
    if isinstance(content, dict):
        parts: List[str] = []
        for value in content.values():
            text = _extract_text(value)
            if text:
                parts.append(text)
        return "\n".join([p for p in parts if p])
    return ""


def _completion_to_text(response: Any) -> str:
    try:
        message = response.choices[0].message  # type: ignore[attr-defined]
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"ChatGPT returned an unexpected payload: {exc}")

    content = getattr(message, "content", "")
    text = _extract_text(content)
    if text:
        return text
    raise RuntimeError("ChatGPT returned an empty payload")


def run_completion(
    config: ChatGPTConfig,
    prompt: str,
    *,
    system: Optional[str] = None,
    json_mode: bool = False,
) -> str:
    client = _client(config)
    messages: List[Dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    kwargs = _response_kwargs(config.model, force_json=json_mode)
    temperature = _temperature_for_model(config.model, config.temperature)
    if temperature is not None:
        kwargs["temperature"] = temperature

    response = client.chat.completions.create(messages=messages, **kwargs)
    return _completion_to_text(response)


def run_healthcheck(config: ChatGPTConfig) -> str:
    if not is_chatgpt_configured(config):
        return "OpenAI API key is missing. Add it in the sidebar to run analyses."
    try:
        echo = run_completion(
            config,
            "Respond with a short JSON object: {\"status\":\"ok\"}",
            system="Return only JSON.",
            json_mode=True,
        )
        if "ok" in echo.lower():
            return "ChatGPT health check succeeded."
        return f"Health check returned unexpected content: {echo}"
    except Exception as exc:  # noqa: BLE001
        return f"Health check failed: {exc}"
