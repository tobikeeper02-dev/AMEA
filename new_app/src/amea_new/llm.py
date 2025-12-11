"""ChatGPT helpers for the AMEA Next project."""
from dataclasses import dataclass
import os
from typing import Any, Dict, List, Optional

from openai import OpenAI


@dataclass
class OpenAIConfig:
    api_key: str
    base_url: Optional[str] = None
    model: str = "gpt-5-nano"
    temperature: float = 0.2

    @classmethod
    def from_env(cls) -> "OpenAIConfig":
        return cls(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            base_url=os.getenv("AMEA_OPENAI_BASE_URL"),
            model=os.getenv("AMEA_OPENAI_MODEL", "gpt-5-nano"),
            temperature=float(os.getenv("AMEA_OPENAI_TEMPERATURE", "0.2")),
        )

    def as_kwargs(self) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = {"api_key": self.api_key}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        return kwargs


def _build_client(config: OpenAIConfig) -> OpenAI:
    if not config.api_key:
        raise ValueError("OPENAI_API_KEY is required to call ChatGPT")
    return OpenAI(**config.as_kwargs())


def _chat_messages(system_prompt: str, user_prompt: str) -> List[Dict[str, str]]:
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def _temperature_arg(config: OpenAIConfig) -> Dict[str, float]:
    if config.model == "gpt-5-nano":
        return {}
    return {"temperature": config.temperature}


def _extract_text(chat_response: Any) -> str:
    if not chat_response or not getattr(chat_response, "choices", None):
        return ""
    first = chat_response.choices[0]
    message = getattr(first, "message", None)
    if message and getattr(message, "content", None):
        return str(message.content)
    return ""


def chat_complete(config: OpenAIConfig, *, system_prompt: str, user_prompt: str) -> str:
    client = _build_client(config)
    response = client.chat.completions.create(
        model=config.model,
        messages=_chat_messages(system_prompt, user_prompt),
        **_temperature_arg(config),
    )
    text = _extract_text(response)
    if not text:
        raise RuntimeError("ChatGPT returned an empty response")
    return text


def health_check(config: OpenAIConfig) -> str:
    prompt = "You are a connectivity probe. Reply with READY."
    return chat_complete(
        config,
        system_prompt="Connectivity check",
        user_prompt=prompt,
    )
