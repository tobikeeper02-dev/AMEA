"""Lightweight OpenAI helpers for AMEA.

This module intentionally avoids external dependencies so the Streamlit app can run
cleanly. All prompts request concise, engagement-specific content.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from openai import OpenAI


class ChatGPTNotConfiguredError(RuntimeError):
    """Raised when an OpenAI API key is not available."""


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
                "OpenAI API key is required. Add it in the sidebar or as OPENAI_API_KEY."
            )


def build_client(config: ChatGPTConfig) -> OpenAI:
    config.ensure_key()
    if config.base_url:
        return OpenAI(api_key=config.api_key, base_url=config.base_url)
    return OpenAI(api_key=config.api_key)


def run_completion(config: ChatGPTConfig, prompt: str, *, system: str) -> str:
    client = build_client(config)
    response = client.chat.completions.create(
        model=config.model,
        temperature=config.temperature if "gpt-5-nano" not in config.model else None,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    )
    content = response.choices[0].message.content or ""
    return content.strip()


def run_healthcheck(config: ChatGPTConfig) -> str:
    """Return a short proof that the API responds."""
    config.ensure_key()
    try:
        text = run_completion(
            config,
            "Summarize AMEA's purpose in one sentence.",
            system="You are a concise assistant that confirms API connectivity.",
        )
        if not text:
            return "ChatGPT returned an empty response."
        return text
    except Exception as exc:  # noqa: BLE001
        return f"Health check failed: {exc}" 


def is_chatgpt_configured(config: ChatGPTConfig) -> bool:
    try:
        config.ensure_key()
        return True
    except ChatGPTNotConfiguredError:
        return False

