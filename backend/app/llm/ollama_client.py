from __future__ import annotations
import httpx
from app.core.config import settings

def chat(prompt: str, model: str | None = None) -> str:
    """
    Send a prompt to the configured Ollama server and return the generated text.

    This is a lightweight wrapper around Ollama's `/api/generate` endpoint.

    Args:
        prompt: The prompt text to send to the model.
        model: Optional override for which Ollama model to use. If not provided,
               defaults to `settings.ollama_model_small`.

    Returns:
        The generated response text from Ollama.

    Raises:
        httpx.HTTPStatusError: If the Ollama server returns a non-2xx response.
        httpx.RequestError: If the request fails due to network/connection issues.
    """
    # Pick a model: either caller override or the configured default.
    m = model or settings.ollama_model_small

    # Ollama generate endpoint (non-streaming mode).
    url = f"{settings.ollama_base_url}/api/generate"

    # Minimal request payload.
    payload = {
        "model": m,
        "prompt": prompt,
        "stream": False,
    }

    # Send the request and extract the "response" field from the JSON payload.
    with httpx.Client(timeout=120) as client:
        r = client.post(url, json=payload)
        r.raise_for_status()
        return r.json().get("response", "")
