from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from app.schemas.common import APIModel, GeoJSONLineString, LngLatModel

ShapeType = Literal["heart", "star", "circle", "square", "letter", "freehand"]


class RoutePreferences(APIModel):
    avoid_major_roads: bool = True
    prefer_footways: bool = False
    prefer_riverside: bool = False


class GenerationRequest(APIModel):
    start: LngLatModel
    shape_type: ShapeType
    target_distance_km: float = Field(ge=1, le=30)
    distance_tolerance_pct: float = Field(default=12, ge=5, le=25)
    closed_loop: bool = True
    rotation_mode: Literal["auto", "fixed"] = "auto"
    rotation_deg: float | None = Field(default=None, ge=0, lt=360)
    waypoint_count: int | None = Field(default=None, ge=6, le=24)
    shape_text: str | None = Field(default=None, min_length=1, max_length=3)
    freehand_points: list[list[float]] | None = None
    preferences: RoutePreferences = RoutePreferences()
    max_candidates: int = Field(default=3, ge=1, le=5)

    @model_validator(mode="after")
    def validate_shape_options(self) -> GenerationRequest:
        if self.rotation_mode == "fixed" and self.rotation_deg is None:
            raise ValueError("rotationDeg is required when rotationMode is fixed")
        if self.shape_type == "letter":
            if not self.shape_text or not self.shape_text.isascii() or not self.shape_text.isalpha():
                raise ValueError("shapeText must contain 1-3 ASCII letters")
            self.shape_text = self.shape_text.upper()
        if self.shape_type == "freehand" and not self.freehand_points:
            raise ValueError("freehandPoints is required for freehand shape")
        if self.shape_type != "freehand" and self.freehand_points is not None:
            raise ValueError("freehandPoints is only allowed for freehand shape")
        return self


class GenerationJobResponse(APIModel):
    id: str
    state: Literal["queued", "running", "succeeded", "failed", "cancelled"]
    progress: int
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None


class CandidateMetrics(APIModel):
    distance_m: float
    duration_s: float
    shape_score: float
    distance_score: float
    closure_score: float
    overlap_ratio: float
    simplicity_score: float
    total_score: float
    waypoint_count: int
    max_snap_distance_m: float
    ascend_m: float | None = None
    descend_m: float | None = None


class CandidateResponse(APIModel):
    candidate_id: str
    rank: int
    rotation_deg: float
    route: GeoJSONLineString
    source_shape: dict[str, object]
    waypoints: list[list[float]]
    snapped_points: list[list[float]]
    metrics: CandidateMetrics


class CandidateListResponse(APIModel):
    items: list[CandidateResponse]


class RecalculateRequest(APIModel):
    source_shape: dict[str, object]
    waypoints: list[LngLatModel] = Field(min_length=3, max_length=24)
    target_distance_km: float = Field(ge=1, le=30)
    distance_tolerance_pct: float = Field(default=12, ge=5, le=25)
    closed_loop: bool = True
    preferences: RoutePreferences = RoutePreferences()


class RecalculateResponse(APIModel):
    route: GeoJSONLineString
    waypoints: list[list[float]]
    snapped_points: list[list[float]]
    metrics: CandidateMetrics
