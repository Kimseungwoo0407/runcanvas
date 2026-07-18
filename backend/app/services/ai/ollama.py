from __future__ import annotations

import json

import httpx

from app.config import Settings
from app.schemas.ai import ParsedRequest

SYSTEM_PROMPT = """You convert a Korean or English running-course request into the supplied JSON Schema.
Only extract explicit user intent. Never invent coordinates.
locationText may contain a place name, never latitude or longitude.
Map shapes to heart, star, circle, square, dog, cat, letter, or freehand. Dog and cat mean face-only shapes.
Distances are kilometers from 1 to 30.
Set avoidMajorRoads true unless the user explicitly prefers large roads.
Set preferFootways true for paths, parks, trails, or quiet walking roads.
Set preferRiverside true when the user mentions the Han River, Musimcheon, riverside, river parks, or river paths.
"""


class OllamaAIProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def parse(self, text: str) -> ParsedRequest | None:
        payload = {
            "model": self.settings.AI_MODEL,
            "stream": False,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            "format": ParsedRequest.model_json_schema(by_alias=True),
            "options": {"temperature": 0, "num_ctx": 2048},
        }
        try:
            async with httpx.AsyncClient(timeout=self.settings.OLLAMA_TIMEOUT_SECONDS) as client:
                response = await client.post(f"{self.settings.OLLAMA_URL.rstrip('/')}/api/chat", json=payload)
                response.raise_for_status()
            content = response.json()["message"]["content"]
            return ParsedRequest.model_validate(json.loads(content))
        except (httpx.HTTPError, KeyError, ValueError, TypeError):
            return None
