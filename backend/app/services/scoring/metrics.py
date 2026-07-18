from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import numpy.typing as npt

from app.services.routing.base import EdgeSpan, LngLat, RouteResult
from app.services.routing.geometry import haversine_m, project_lnglat_points
from app.services.shapes.library import resample_by_length


@dataclass(frozen=True)
class ScoreMetrics:
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

    def to_api_dict(self) -> dict[str, Any]:
        return {
            "distanceM": self.distance_m,
            "durationS": self.duration_s,
            "shapeScore": self.shape_score,
            "distanceScore": self.distance_score,
            "closureScore": self.closure_score,
            "overlapRatio": self.overlap_ratio,
            "simplicityScore": self.simplicity_score,
            "totalScore": self.total_score,
            "waypointCount": self.waypoint_count,
            "maxSnapDistanceM": self.max_snap_distance_m,
            "ascendM": self.ascend_m,
            "descendM": self.descend_m,
        }

    def to_snake_dict(self) -> dict[str, Any]:
        return asdict(self)


FloatArray = npt.NDArray[np.float64]


def _normalize(array: FloatArray) -> FloatArray:
    centered = array - array.mean(axis=0)
    scale = float(np.max(np.linalg.norm(centered, axis=1)))
    if scale <= 1e-12:
        return np.asarray(centered, dtype=np.float64)
    return np.asarray(centered / scale, dtype=np.float64)


def _best_rotation(source: FloatArray, route: FloatArray) -> FloatArray:
    covariance = route.T @ source
    left, _, right = np.linalg.svd(covariance)
    rotation = left @ right
    if np.linalg.det(rotation) < 0:
        left[:, -1] *= -1
        rotation = left @ right
    return np.asarray(route @ rotation, dtype=np.float64)


def _chamfer_distance(a: FloatArray, b: FloatArray) -> float:
    distances = np.linalg.norm(a[:, None, :] - b[None, :, :], axis=2)
    return float((distances.min(axis=1).mean() + distances.min(axis=0).mean()) / 2)


def shape_similarity(source_shape: list[tuple[float, float]], route_points: list[LngLat]) -> float:
    sample_count = 128
    source_sample = np.asarray(resample_by_length(source_shape, sample_count, closed=True)[:-1])
    projected_route = project_lnglat_points(route_points)
    route_sample = np.asarray(
        resample_by_length([(x, y) for x, y in projected_route], sample_count, closed=True)[:-1],
        dtype=np.float64,
    )
    source_normalized = _normalize(source_sample)
    route_normalized = _normalize(route_sample)
    route_aligned = _best_rotation(source_normalized, route_normalized)
    distance = _chamfer_distance(source_normalized, route_aligned)
    return float(max(0.0, min(1.0, math.exp(-3.2 * distance))))


def distance_score(actual_m: float, target_m: float, tolerance_pct: float) -> float:
    tolerance_m = target_m * tolerance_pct / 100
    if tolerance_m <= 0:
        return 0.0
    return max(0.0, 1.0 - abs(actual_m - target_m) / tolerance_m)


def closure_score(points: list[LngLat], target_m: float) -> float:
    if len(points) < 2:
        return 0.0
    gap = haversine_m(points[0], points[-1])
    acceptable = max(20.0, target_m * 0.01)
    return max(0.0, 1.0 - gap / acceptable)


def overlap_ratio(coordinates: list[list[float]], spans: list[EdgeSpan], route_distance_m: float) -> float:
    if route_distance_m <= 0 or not spans:
        return 0.0
    points = [LngLat(float(item[0]), float(item[1])) for item in coordinates]
    visits: dict[int, list[float]] = {}
    for span in spans:
        start = max(0, span.from_index)
        end = min(len(points) - 1, span.to_index)
        length = sum(haversine_m(a, b) for a, b in zip(points[start:end], points[start + 1 : end + 1], strict=False))
        visits.setdefault(span.edge_id, []).append(length)
    repeated = sum(sum(lengths) for lengths in visits.values() if len(lengths) >= 2)
    return min(1.0, repeated / route_distance_m)


def simplicity_score(points: list[LngLat]) -> float:
    projected = project_lnglat_points(points)
    if len(projected) < 3:
        return 1.0
    penalties = 0.0
    considered = 0
    for a, b, c in zip(projected, projected[1:], projected[2:], strict=False):
        first = np.asarray(a) - np.asarray(b)
        second = np.asarray(c) - np.asarray(b)
        first_length = float(np.linalg.norm(first))
        second_length = float(np.linalg.norm(second))
        if min(first_length, second_length) < 3:
            penalties += 0.5
            considered += 1
            continue
        cosine = float(np.dot(first, second) / (first_length * second_length))
        cosine = max(-1.0, min(1.0, cosine))
        angle = math.degrees(math.acos(cosine))
        if angle < 35:
            penalties += (35 - angle) / 35
        considered += 1
    return max(0.0, 1.0 - penalties / max(1, considered))


def score_route(
    source_shape: list[tuple[float, float]],
    route: RouteResult,
    target_distance_m: float,
    tolerance_pct: float,
    waypoint_count: int,
) -> ScoreMetrics:
    route_points = [LngLat(float(item[0]), float(item[1])) for item in route.coordinates]
    shape = shape_similarity(source_shape, route_points)
    distance = distance_score(route.distance_m, target_distance_m, tolerance_pct)
    closure = closure_score(route_points, target_distance_m)
    overlap = overlap_ratio(route.coordinates, route.edge_spans, route.distance_m)
    simplicity = simplicity_score(route_points)
    max_snap = max(route.snap_distances_m, default=0.0)
    snap_penalty = min(0.25, max(0.0, max_snap - 150) / 600)
    total = 0.50 * shape + 0.25 * distance + 0.10 * closure + 0.10 * (1 - overlap) + 0.05 * simplicity - snap_penalty
    return ScoreMetrics(
        distance_m=route.distance_m,
        duration_s=route.duration_s,
        shape_score=round(shape, 6),
        distance_score=round(distance, 6),
        closure_score=round(closure, 6),
        overlap_ratio=round(overlap, 6),
        simplicity_score=round(simplicity, 6),
        total_score=round(max(0.0, min(1.0, total)), 6),
        waypoint_count=waypoint_count,
        max_snap_distance_m=round(max_snap, 3),
        ascend_m=route.ascend_m,
        descend_m=route.descend_m,
    )
