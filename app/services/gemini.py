import json
from typing import Any

import httpx

from app.core.config import settings


def _generate_content_url() -> str:
    base = settings.gemini_api_base_url.rstrip("/")
    return f"{base}/models/{settings.gemini_model}:generateContent"


def generate_structured_json(prompt: str, response_json_schema: dict[str, Any]) -> Any | None:
    if not settings.gemini_api_key:
        return None

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseJsonSchema": response_json_schema,
        },
    }

    try:
        response = httpx.post(
            _generate_content_url(),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": settings.gemini_api_key,
            },
            json=payload,
            timeout=settings.gemini_timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        text = next((part.get("text") for part in parts if isinstance(part, dict) and part.get("text")), None)
        if not text:
            return None
        return json.loads(text)
    except Exception:
        return None
