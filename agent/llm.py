"""Mistral API client with tool-use support."""
import os
import time
import requests
from typing import Any


_API_URL = "https://api.mistral.ai/v1/chat/completions"
_MODEL = os.getenv("MISTRAL_MODEL", "mistral-medium-latest")


class LLMError(Exception):
    pass


def call(
    messages: list[dict],
    tools: list[dict] | None = None,
    temperature: float = 0.2,
    max_tokens: int = 2048,
) -> dict:
    """Call Mistral and return the first choice message dict."""
    api_key = os.environ["MISTRAL_API_KEY"]
    payload: dict[str, Any] = {
        "model": _MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    for attempt in range(3):
        resp = requests.post(
            _API_URL,
            json=payload,
            headers={"Authorization": f"Bearer {api_key}",
                     "Content-Type": "application/json"},
            timeout=60,
        )
        if resp.status_code == 429:
            time.sleep(10 * (attempt + 1))
            continue
        if resp.status_code >= 500:
            time.sleep(5)
            continue
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]

    raise LLMError("Mistral API failed after 3 attempts")
