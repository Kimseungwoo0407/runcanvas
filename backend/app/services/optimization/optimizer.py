from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from app.config import Settings
from app.errors import AppError
from app.schemas.generation import GenerationRequest
from app.services.routing.base import LngLat, RouteOptions, RouteResult, RoutingProvider
from app.services.routing.geometry import transform_shape_to_lnglat
from app.services.scoring.metrics import ScoreMetrics, score_route
from app.services.shapes.library import generate_shape, polyline_length, resample_by_length

ProgressCallback = Callable[[int], Awaitable[None]]
CancelCallback = Callable[[], Awaitable[bool]]


@dataclass(frozen=True)
class Candidate:
    rotation_deg: float
    scale_m: float
    source_shape: list[tuple[float, float]]
    waypoints: list[LngLat]
    route: RouteResult
    metrics: ScoreMetrics


class RoutingBudget:
    def __init__(self, max_calls: int, timeout_seconds: int) -> None:
        self.max_calls = max_calls
        self.calls = 0
        self.deadline = time.monotonic() + timeout_seconds

    def exhausted(self) -> bool:
        return self.calls >= self.max_calls or time.monotonic() >= self.deadline

    def consume(self) -> None:
        self.calls += 1


def candidate_rotations(request: GenerationRequest) -> list[float]:
    if request.rotation_mode == "fixed":
        return [float(request.rotation_deg or 0)]
    if request.shape_type == "circle":
        return [0.0]
    if request.shape_type == "square":
        return [0.0, 30.0, 60.0]
    if request.shape_type == "star":
        return [0.0, 24.0, 48.0]
    return [float(value) for value in range(0, 360, 45)]


def _deduplicate(
    candidates: list[Candidate],
    limit: int,
    *,
    best_effort_target_m: float | None = None,
) -> list[Candidate]:
    selected: list[Candidate] = []
    if best_effort_target_m is None:
        ordered = sorted(candidates, key=lambda item: item.metrics.total_score, reverse=True)
    else:
        ordered = sorted(
            candidates,
            key=lambda item: (
                abs(item.route.distance_m - best_effort_target_m),
                -item.metrics.total_score,
            ),
        )
    for candidate in ordered:
        too_similar = any(
            abs(candidate.rotation_deg - prior.rotation_deg) < 4
            and abs(candidate.route.distance_m - prior.route.distance_m) < 100
            for prior in selected
        )
        if not too_similar:
            selected.append(candidate)
        if len(selected) >= limit:
            break
    return selected


async def optimize_candidates(
    request: GenerationRequest,
    provider: RoutingProvider,
    settings: Settings,
    *,
    progress_callback: ProgressCallback | None = None,
    cancel_callback: CancelCallback | None = None,
) -> list[Candidate]:
    source_shape = generate_shape(
        request.shape_type,
        shape_text=request.shape_text,
        freehand_points=request.freehand_points,
        preview_count=180,
    )
    waypoint_count = request.waypoint_count or (14 if request.shape_type in {"heart", "letter", "freehand"} else 12)
    waypoint_shape = resample_by_length(source_shape, waypoint_count, closed=True)
    normalized_length = polyline_length(waypoint_shape)
    target_m = request.target_distance_km * 1000
    initial_scale = target_m / normalized_length * 0.78
    rotations = candidate_rotations(request)
    budget = RoutingBudget(settings.MAX_ROUTING_CALLS, settings.GENERATION_TIMEOUT_SECONDS)
    candidates: list[Candidate] = []
    total_planned = max(1, len(rotations) * 3)
    completed = 0

    for rotation in rotations:
        scale = initial_scale
        for _ in range(3):
            if budget.exhausted():
                break
            if cancel_callback and await cancel_callback():
                raise AppError("JOB_CANCELLED", "생성 작업이 취소되었습니다.", 409)
            waypoints = transform_shape_to_lnglat(
                waypoint_shape,
                LngLat(request.start.lng, request.start.lat),
                scale,
                rotation,
            )
            try:
                route = await asyncio.wait_for(
                    provider.route(
                        waypoints,
                        RouteOptions(
                            avoid_major_roads=request.preferences.avoid_major_roads,
                            prefer_footways=request.preferences.prefer_footways,
                            prefer_riverside=request.preferences.prefer_riverside,
                            timeout_ms=min(7000, settings.GENERATION_TIMEOUT_SECONDS * 1000),
                        ),
                    ),
                    timeout=min(8.0, max(1.0, budget.deadline - time.monotonic())),
                )
            except (AppError, TimeoutError):
                budget.consume()
                completed += 1
                scale *= 0.9
                if progress_callback:
                    await progress_callback(min(95, int(completed / total_planned * 90) + 5))
                continue
            budget.consume()
            completed += 1
            metrics = score_route(
                source_shape,
                route,
                target_m,
                request.distance_tolerance_pct,
                len(waypoints),
            )
            candidates.append(Candidate(rotation, scale, source_shape, waypoints, route, metrics))
            ratio = target_m / max(route.distance_m, 1)
            if abs(1 - ratio) < 0.02:
                if progress_callback:
                    await progress_callback(min(95, int(completed / total_planned * 90) + 5))
                break
            scale *= max(0.85, min(1.15, ratio))
            if progress_callback:
                await progress_callback(min(95, int(completed / total_planned * 90) + 5))
        if budget.exhausted():
            break

    tolerance_m = target_m * request.distance_tolerance_pct / 100
    within_tolerance = [
        candidate
        for candidate in candidates
        if abs(candidate.route.distance_m - target_m) <= tolerance_m
    ]
    selected = _deduplicate(
        within_tolerance or candidates,
        request.max_candidates,
        best_effort_target_m=None if within_tolerance else target_m,
    )
    if not selected:
        if budget.exhausted() and time.monotonic() >= budget.deadline:
            raise AppError("GENERATION_TIMEOUT", "후보 생성 제한 시간이 초과되었습니다.", 504)
        raise AppError(
            "NO_ROUTE_FOUND",
            "이 위치에서 연결 가능한 보행 코스를 찾지 못했습니다.",
            422,
            {"routingCalls": budget.calls},
        )
    return selected
