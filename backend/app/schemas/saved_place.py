from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, field_validator, model_validator

from app.schemas.common import APIModel, LngLatModel

PrecomputeShape = Literal["circle", "heart", "star", "square"]


def _default_shapes() -> list[PrecomputeShape]:
    return ["circle", "heart", "star"]


def _unique_sorted_distances(values: list[float]) -> list[float]:
    return sorted(set(values))


def _unique_shapes(values: list[PrecomputeShape]) -> list[PrecomputeShape]:
    return list(dict.fromkeys(values))


class SavedPlaceCreateRequest(APIModel):
    name: str = Field(min_length=1, max_length=80)
    location: LngLatModel
    privacy_radius_m: int = Field(default=250, ge=0, le=1000)
    prefer_riverside: bool = False
    distances_km: list[float] = Field(
        default_factory=lambda: [3.0, 5.0, 7.0, 10.0], min_length=1, max_length=4
    )
    shapes: list[PrecomputeShape] = Field(
        default_factory=_default_shapes, min_length=1, max_length=4
    )

    @field_validator("distances_km")
    @classmethod
    def validate_distances(cls, values: list[float]) -> list[float]:
        values = _unique_sorted_distances(values)
        if any(value < 1 or value > 30 for value in values):
            raise ValueError("distancesKm values must be between 1 and 30")
        return values

    @field_validator("shapes")
    @classmethod
    def validate_shapes(cls, values: list[PrecomputeShape]) -> list[PrecomputeShape]:
        return _unique_shapes(values)


class SavedPlacePatchRequest(APIModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    location: LngLatModel | None = None
    privacy_radius_m: int | None = Field(default=None, ge=0, le=1000)
    prefer_riverside: bool | None = None
    distances_km: list[float] | None = Field(default=None, min_length=1, max_length=4)
    shapes: list[PrecomputeShape] | None = Field(default=None, min_length=1, max_length=4)

    @field_validator("distances_km")
    @classmethod
    def validate_distances(cls, values: list[float] | None) -> list[float] | None:
        if values is None:
            return None
        values = _unique_sorted_distances(values)
        if any(value < 1 or value > 30 for value in values):
            raise ValueError("distancesKm values must be between 1 and 30")
        return values

    @field_validator("shapes")
    @classmethod
    def validate_shapes(cls, values: list[PrecomputeShape] | None) -> list[PrecomputeShape] | None:
        return _unique_shapes(values) if values is not None else None

    @model_validator(mode="after")
    def require_change(self) -> SavedPlacePatchRequest:
        if all(
            value is None
            for value in (
                self.name,
                self.location,
                self.privacy_radius_m,
                self.prefer_riverside,
                self.distances_km,
                self.shapes,
            )
        ):
            raise ValueError("at least one field is required")
        return self


class PrecomputeStatus(APIModel):
    total: int
    queued: int
    running: int
    succeeded: int
    failed: int
    cancelled: int
    generated_courses: int


class SavedPlaceResponse(APIModel):
    id: str
    name: str
    location: LngLatModel
    privacy_radius_m: int
    prefer_riverside: bool
    distances_km: list[float]
    shapes: list[PrecomputeShape]
    precompute_requested_at: datetime | None = None
    status: PrecomputeStatus
    created_at: datetime
    updated_at: datetime


class SavedPlaceListResponse(APIModel):
    items: list[SavedPlaceResponse]
