from __future__ import annotations

import os
from typing import Any


def _client():
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError(
            "openai package is required for LLM calls. Install with `pip install openai`."
        ) from exc

    api_key = os.environ.get("CHAT_AI_API_KEY")
    endpoint = os.environ.get("CHAT_AI_ENDPOINT", "https://chat-ai.academiccloud.de/v1")

    if not api_key:
        raise RuntimeError(
            "CHAT_AI_API_KEY environment variable is not set. "
            "Add it to your .env file or export it before starting the server."
        )

    return OpenAI(api_key=api_key, base_url=endpoint)


def chat(prompt: str, system: str = "", model: str | None = None) -> str:
    """Send a prompt to the configured Chat-AI endpoint and return the text response."""
    model = model or os.environ.get("CHAT_AI_MODEL", "meta-llama/Meta-Llama-3.1-70B-Instruct")
    messages: list[dict[str, Any]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = _client().chat.completions.create(model=model, messages=messages)
    return response.choices[0].message.content or ""
