from __future__ import annotations

import json


def parse_json_object(text: str) -> dict:
    """
    Parse a JSON object from model output.

    - Accepts raw JSON or JSON fenced in Markdown.
    - Best-effort extracts the first {...} block if extra text exists.
    """
    stripped = text.strip()
    if stripped.startswith("```"):
        # Remove a single fenced code block wrapper.
        parts = stripped.split("```")
        if len(parts) >= 3:
            stripped = parts[1].strip()
            if stripped.startswith("json"):
                stripped = stripped[4:].strip()

    try:
        obj = json.loads(stripped)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in output.")

    candidate = stripped[start : end + 1]
    obj = json.loads(candidate)
    if not isinstance(obj, dict):
        raise ValueError("Parsed JSON is not an object.")
    return obj

