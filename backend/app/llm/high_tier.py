from __future__ import annotations
import httpx
from app.core.config import settings


def _openai_chat(prompt: str) -> str:
    """
    Send a prompt to OpenAI's Responses API and return the model's text output.

    This function:
    - Validates that OPENAI_API_KEY is configured
    - Calls the Responses endpoint
    - Extracts all text blocks from the response payload and concatenates them

    Args:
        prompt: The user prompt to send to the model.

    Returns:
        The model-generated text response.

    Raises:
        RuntimeError: If OPENAI_API_KEY is not set.
        httpx.HTTPStatusError: If the API returns a non-2xx status code.
    """
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    # OpenAI Responses API endpoint.
    url = "https://api.openai.com/v1/responses"

    # Standard OpenAI bearer auth header.
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }

    # Minimal payload: model + input prompt.
    payload = {
        "model": settings.high_tier_model,
        "input": prompt,
    }

    # Use a short-lived client for simplicity + explicit timeout.
    with httpx.Client(timeout=120) as client:
        r = client.post(url, headers=headers, json=payload)
        r.raise_for_status()

        data = r.json()

        # Responses API returns an "output" array with content blocks.
        out = data.get("output", [])

        # Collect all text segments across all output items.
        texts: list[str] = []
        for item in out:
            for c in item.get("content", []):
                if c.get("type") in ("output_text", "text"):
                    texts.append(c.get("text", ""))

        return "\n".join(texts).strip()


def chat(prompt: str) -> str:
    """
    High-level chat wrapper that routes requests to the configured provider.

    Provider selection is controlled by:
        settings.high_tier_provider

    Supported values:
        - anything else defaults to OpenAI

    Args:
        prompt: The user prompt to send to the configured model provider.

    Returns:
        The model-generated text response.
    """

    return _openai_chat(prompt)
