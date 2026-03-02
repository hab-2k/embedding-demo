import logging
import os
import time

import requests

logger = logging.getLogger(__name__)

LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://nano-gpt.com/api/v1")
LLM_API_KEY = os.environ.get("LLM_API_KEY")
LLM_MODEL = os.environ.get("LLM_MODEL", "zai-org/glm-4.7")

_TIMEOUT = 30
_MAX_RETRIES = 4
_BASE_BACKOFF = 1.0  # seconds


def is_configured() -> bool:
    """Return True if an API key is set."""
    return bool(LLM_API_KEY)


def chat_completion(
    messages: list[dict],
    temperature: float = 0.3,
    max_tokens: int = 1024,
) -> str:
    """Non-streaming chat completion via OpenAI-compatible API.

    Retries with exponential backoff on 429 rate-limit responses.
    Returns the assistant message content string.
    Raises on non-retryable HTTP or parsing errors.
    """
    headers = {
        "Authorization": f"Bearer {LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }

    for attempt in range(_MAX_RETRIES):
        response = requests.post(
            f"{LLM_BASE_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=_TIMEOUT,
        )

        if response.status_code == 429:
            wait = _BASE_BACKOFF * (2 ** attempt)
            logger.warning(
                "LLM rate-limited (429), retrying in %.1fs (attempt %d/%d)",
                wait, attempt + 1, _MAX_RETRIES,
            )
            time.sleep(wait)
            continue

        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    # Final attempt after all retries exhausted
    response = requests.post(
        f"{LLM_BASE_URL}/chat/completions",
        headers=headers,
        json=payload,
        timeout=_TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]
