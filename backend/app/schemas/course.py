from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field, model_validator

from app.schemas.common import APIModel, GeoJSONLineString
from app.schemas.generation import CandidateMetrics, ShapeType


class CourseCreateRequest(APIModel):
    name: str = Field(min_length=1, max_length=120)
    candidate_id: str | None = None
    shape_type: ShapeType | None = None
    target_distance_m: float | None = Field(default=None, gt=0)
    source_shape: dict[str, object] | None = None
    waypoints: list[list[float]] | None = None
    route: GeoJSONLineString | None = None
    metrics: CandidateMetrics | None = None

    @model_validator(mode="after")
    def validate_source(self) -> CourseCreateRequest:
        direct_fields = [
            self.shape_type,
            self.target_distance_m,
            self.source_shape,
            self.waypoints,
            self.route,
            self.metrics,
        ]
        if self.candidate_id is None and any(field is None for field in direct_fields):
            raise ValueError("candidateId or complete edited course data is required")
        return self


class CoursePatchRequest(APIModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    is_favorite: bool | None = None
    status: Literal["draft", "ready", "archived"] | None = None
    share_enabled: bool | None = None


class CourseSummary(APIModel):
    id: str
    name: str
    shape_type: str
    target_distance_m: float
    actual_distance_m: float
    status: str
    is_favorite: bool
    share_enabled: bool
    saved_place_id: str | None = None
    is_pregenerated: bool = False
    total_score: float
    created_at: datetime
    updated_at: datetime


class CourseListResponse(APIModel):
    items: list[CourseSummary]
    next_cursor: str | None = None


class CourseDetail(CourseSummary):
    owner_id: str
    share_token: str | None = None
    source_shape: dict[str, object]
    waypoints: list[list[float]]
    route: GeoJSONLineString
    bbox: list[float]
    metrics: CandidateMetrics
