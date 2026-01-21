import json
import re
from typing import Any

def extract_json(text: str) -> dict[str, Any]:
    """
    Extract the first JSON object found inside a text blob.

    This is useful when an LLM returns extra non-JSON content (e.g., explanations)
    but you only want the JSON payload.

    Args:
        text: Raw text that may contain a JSON object.

    Returns:
        A parsed JSON object as a Python dict.

    Raises:
        ValueError: If no JSON object is found in the text.
        json.JSONDecodeError: If the extracted substring is not valid JSON.
    """
    # Normalize whitespace and remove leading/trailing newlines.
    text = text.strip()

    # Find the first {...} block in the text (including multi-line JSON).
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not m:
        raise ValueError("No JSON object found")

    # Parse the matched substring as JSON.
    return json.loads(m.group(0))
