from __future__ import annotations

import re

from app.schemas.ai import ParsedRequest
from app.schemas.generation import ShapeType

SHAPES: dict[str, ShapeType] = {
    "하트": "heart",
    "heart": "heart",
    "별": "star",
    "star": "star",
    "원": "circle",
    "동그라미": "circle",
    "circle": "circle",
    "사각형": "square",
    "네모": "square",
    "square": "square",
    "글자": "letter",
    "letter": "letter",
    "자유": "freehand",
    "freehand": "freehand",
}

DISTANCE_RE = re.compile(r"(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>km|킬로미터|키로|k|m|미터)\b", re.I)
LOCATION_RE = re.compile(r"(?P<location>[가-힣A-Za-z0-9·\- ]{2,30})(?:\s*(?:근처|주변|에서))")


def parse_rules(text: str) -> ParsedRequest | None:
    lowered = text.lower()
    shape = next((value for key, value in SHAPES.items() if key in lowered), None)
    distance_match = DISTANCE_RE.search(lowered)
    if shape is None or distance_match is None:
        return None
    distance = float(distance_match.group("value"))
    if distance_match.group("unit").lower() in {"m", "미터"}:
        distance /= 1000
    if not 1 <= distance <= 30:
        return None
    avoid_major = not any(phrase in lowered for phrase in ["큰길 상관", "대로 선호", "큰길로"])
    prefer_footways = any(phrase in lowered for phrase in ["산책로", "보행로", "공원길", "조용한 길"])
    prefer_riverside = any(phrase in lowered for phrase in ["한강", "강변", "강가", "river", "riverside"])
    location_match = LOCATION_RE.search(text)
    location = location_match.group("location").strip() if location_match else None
    return ParsedRequest(
        shape_type=shape,
        target_distance_km=distance,
        avoid_major_roads=avoid_major,
        prefer_footways=prefer_footways or prefer_riverside,
        prefer_riverside=prefer_riverside,
        location_text=location,
    )
