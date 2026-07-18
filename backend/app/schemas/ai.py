from __future__ import annotations

from typing import Literal

from pydantic import Field

from app.schemas.common import APIModel


class NaturalLanguageRequest(APIModel):
    text: str = Field(min_length=2, max_length=500)


class ParsedRequest(APIModel):
    shape_type: Literal["heart", "star", "circle", "square", "letter", "freehand"]
    target_distance_km: float = Field(ge=1, le=30)
    avoid_major_roads: bool = True
    prefer_footways: bool = False
    prefer_riverside: bool = False
    location_text: str | None = Field(default=None, max_length=120)


class ParseResponse(APIModel):
    result: ParsedRequest | None
    source: Literal["rules", "llm", "form"]
