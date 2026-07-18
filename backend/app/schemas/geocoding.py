from __future__ import annotations

from app.schemas.common import APIModel


class GeocodingResult(APIModel):
    display_name: str
    lat: float
    lng: float
    bounding_box: list[float] | None = None


class GeocodingResponse(APIModel):
    items: list[GeocodingResult]
