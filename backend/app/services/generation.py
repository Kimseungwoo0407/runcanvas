from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.config import Settings
from app.db.models import GenerationJob
from app.errors import AppError
from app.regions import get_region, supported_region_details
from app.repositories.jobs import JobRepository
from app.schemas.common import GeoJSONLineString
from app.schemas.generation import (
    CandidateListResponse,
    CandidateMetrics,
    CandidateResponse,
    GenerationJobResponse,
    GenerationRequest,
    RecalculateRequest,
    RecalculateResponse,
)
from app.services.routing.base import LngLat, RouteOptions, RoutingProvider
from app.services.scoring.metrics import score_route


def cache_key(request: GenerationRequest) -> str:
    stable = json.dumps(request.model_dump(by_alias=True), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(stable.encode("utf-8")).hexdigest()


def job_response(job: GenerationJob) -> GenerationJobResponse:
    return GenerationJobResponse.model_validate(job)


class GenerationService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.repository = JobRepository(db)

    def create(self, owner_id: str, request: GenerationRequest) -> GenerationJobResponse:
        region = get_region(request.region)
        if not region.contains(request.start.lng, request.start.lat):
            raise AppError(
                "OUTSIDE_SUPPORTED_AREA",
                f"출발점을 {region.label} 지원 범위 안에서 선택해 주세요.",
                422,
                {
                    "selectedRegion": region.code,
                    "supportedBbox": list(region.bbox),
                    "supportedRegions": supported_region_details(),
                },
            )
        if self.repository.active_for_owner(owner_id):
            raise AppError("RATE_LIMITED", "사용자당 생성 작업은 한 번에 하나만 실행할 수 있습니다.", 429)
        job = self.repository.create(
            owner_id,
            request.model_dump(by_alias=True),
            cache_key(request),
        )
        self.db.commit()
        return job_response(job)

    def get(self, owner_id: str, job_id: str) -> GenerationJobResponse:
        job = self.repository.get_owned(job_id, owner_id)
        if job is None:
            raise AppError("FORBIDDEN", "작업에 접근할 수 없습니다.", 403)
        return job_response(job)

    def cancel(self, owner_id: str, job_id: str) -> GenerationJobResponse:
        job = self.repository.get_owned(job_id, owner_id)
        if job is None:
            raise AppError("FORBIDDEN", "작업에 접근할 수 없습니다.", 403)
        if job.state == "queued":
            job.state = "cancelled"
            job.progress = 100
            job.finished_at = datetime.now(UTC)
        elif job.state == "running":
            job.cancel_requested = True
        self.db.commit()
        return job_response(job)

    def candidates(self, owner_id: str, job_id: str) -> CandidateListResponse:
        job = self.repository.get_owned(job_id, owner_id)
        if job is None:
            raise AppError("FORBIDDEN", "작업에 접근할 수 없습니다.", 403)
        if job.state != "succeeded":
            raise AppError("JOB_NOT_READY", "후보가 아직 준비되지 않았습니다.", 409)
        return CandidateListResponse(
            items=[
                CandidateResponse(
                    candidate_id=candidate.id,
                    rank=candidate.rank,
                    rotation_deg=candidate.rotation_deg,
                    route=GeoJSONLineString.model_validate(candidate.route_geojson),
                    source_shape=candidate.source_shape_json,
                    waypoints=candidate.waypoints_json,
                    snapped_points=candidate.snapped_points_json,
                    metrics=CandidateMetrics.model_validate(candidate.metrics_json),
                    is_best_effort=abs(
                        float(candidate.metrics_json["distanceM"])
                        - float(job.request_json["targetDistanceKm"]) * 1000
                    )
                    > (
                        float(job.request_json["targetDistanceKm"])
                        * 1000
                        * float(job.request_json.get("distanceTolerancePct", 12))
                        / 100
                    ),
                )
                for candidate in job.candidates
            ]
        )


async def recalculate_route(
    request: RecalculateRequest,
    provider: RoutingProvider,
) -> RecalculateResponse:
    points = [LngLat(point.lng, point.lat) for point in request.waypoints]
    if request.closed_loop and points[0] != points[-1]:
        points.append(points[0])
    route = await provider.route(
        points,
        RouteOptions(
            avoid_major_roads=request.preferences.avoid_major_roads,
            prefer_footways=request.preferences.prefer_footways,
            prefer_riverside=request.preferences.prefer_riverside,
            timeout_ms=7000,
        ),
    )
    source_coordinates = request.source_shape.get("coordinates")
    if not isinstance(source_coordinates, list):
        raise AppError("VALIDATION_ERROR", "sourceShape 좌표가 없습니다.", 422)
    source_shape = [(float(item[0]), float(item[1])) for item in source_coordinates]
    metrics = score_route(
        source_shape,
        route,
        request.target_distance_km * 1000,
        request.distance_tolerance_pct,
        len(points),
    )
    return RecalculateResponse(
        route=GeoJSONLineString(type="LineString", coordinates=route.coordinates),
        waypoints=[[point.lng, point.lat] for point in points],
        snapped_points=[[point.lng, point.lat] for point in route.snapped_points],
        metrics=CandidateMetrics.model_validate(metrics.to_api_dict()),
    )
