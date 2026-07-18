from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


def to_camel(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(part[:1].upper() + part[1:] for part in parts[1:])


class APIModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        extra="forbid",
    )


class LngLatModel(APIModel):
    lng: float = Field(ge=-180, le=180)
    lat: float = Field(ge=-90, le=90)


class GeoJSONLineString(APIModel):
    type: str = "LineString"
    coordinates: list[list[float]]

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        if value != "LineString":
            raise ValueError("type must be LineString")
        return value

    @field_validator("coordinates")
    @classmethod
    def validate_coordinates(cls, value: list[list[float]]) -> list[list[float]]:
        if len(value) < 2:
            raise ValueError("LineString requires at least two coordinates")
        for coordinate in value:
            if len(coordinate) not in {2, 3}:
                raise ValueError("coordinates must be [lng, lat] or [lng, lat, elevation]")
            if not (-180 <= coordinate[0] <= 180 and -90 <= coordinate[1] <= 90):
                raise ValueError("invalid longitude or latitude")
        return value


class CursorPage(APIModel):
    items: list[Any]
    next_cursor: str | None = None


class HealthResponse(APIModel):
    status: str
    database: str
    version: str
    timestamp: datetime


USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,40}$")
