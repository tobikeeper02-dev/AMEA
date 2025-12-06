"""ChatGPT client utilities for AMEA.

Everything in this module is geared toward reliable, request-time usage of
OpenAI's API. There is no cached or bundled data—every analysis is pulled from
ChatGPT when the user clicks run.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from openai import OpenAI


class ChatGPTNotConfiguredError(RuntimeError):
    """Raised when an OpenAI API key is missing."""


@dataclass
class ChatGPTConfig:
    api_key: Optional[str]
    base_url: Optional[str] = None
    model: str = "gpt-5-nano"
    temperature: float = 0.2

    @classmethod
    def from_inputs(
        cls,
        api_key: Optional[str],
        base_url: Optional[str],
        model: Optional[str],
        temperature: Optional[float],
    ) -> "ChatGPTConfig":
        return cls(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            base_url=base_url or os.getenv("OPENAI_BASE_URL"),
            model=model or os.getenv("AMEA_OPENAI_MODEL", "gpt-5-nano"),
            temperature=float(os.getenv("AMEA_OPENAI_TEMPERATURE", temperature or 0.2)),
        )

    def ensure_key(self) -> None:
        if not self.api_key:
            raise ChatGPTNotConfiguredError(
                "OpenAI API key is required. Provide it in the sidebar or as OPENAI_API_KEY."
            )

    @property
    def resolved_temperature(self) -> Optional[float]:
        # gpt-5-nano ignores temperature; skip to avoid parameter issues.
        if "gpt-5-nano" in self.model:
            return None
        return self.temperature


class ChatGPTClient:
    """Minimal wrapper around the OpenAI Chat Completions API."""

    def __init__(self, config: ChatGPTConfig):
        config.ensure_key()
        self.config = config
        self._client = OpenAI(api_key=config.api_key, base_url=config.base_url)

    def _request_kwargs(self, *, json_mode: bool) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = {
            "model": self.config.model,
            "messages": [],
        }
        temperature = self.config.resolved_temperature
        if temperature is not None:
            kwargs["temperature"] = temperature
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        return kwargs

    @staticmethod
    def _extract_text(choice: Any) -> str:
        if not choice:
            return ""
        message = getattr(choice, "message", None) or {}
        content = getattr(message, "content", "") or ""
        if isinstance(content, str):
            return content.strip()
        # Handle content blocks (list of dicts) if returned
        if isinstance(content, list):
            parts: List[str] = []
            for block in content:
                if isinstance(block, dict):
                    part = block.get("text") or block.get("content")
                    if isinstance(part, str):
                        parts.append(part)
            return "\n".join(part.strip() for part in parts if part)
        return ""

    def complete(self, *, prompt: str, system: str, json_mode: bool = False) -> str:
        kwargs = self._request_kwargs(json_mode=json_mode)
        kwargs["messages"] = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]
        response = self._client.chat.completions.create(**kwargs)
        if not response or not getattr(response, "choices", None):
            raise RuntimeError("ChatGPT returned an empty response.")
        text = self._extract_text(response.choices[0])
        if not text:
            raise RuntimeError("ChatGPT response did not include content.")
        return text

    def healthcheck(self) -> str:
        return self.complete(
            prompt="State in one sentence that ChatGPT is reachable for AMEA.",
            system="You confirm API connectivity briefly.",
        )


def is_chatgpt_configured(config: ChatGPTConfig) -> bool:
    try:
        config.ensure_key()
    except ChatGPTNotConfiguredError:
        return False
    return True


def run_completion(config: ChatGPTConfig, prompt: str, *, system: str, json_mode: bool = False) -> str:
    client = ChatGPTClient(config)
    return client.complete(prompt=prompt, system=system, json_mode=json_mode)


def run_healthcheck(config: ChatGPTConfig) -> str:
    try:
        client = ChatGPTClient(config)
    except ChatGPTNotConfiguredError:
        return "OpenAI API key is required for the health check."
    try:
        return client.healthcheck()
    except Exception as exc:  # noqa: BLE001
        return f"Health check failed: {exc}"
