from __future__ import annotations

import math

import numpy as np

from app.errors import AppError

Point2D = tuple[float, float]


def _point_line_distance(point: Point2D, start: Point2D, end: Point2D) -> float:
    if start == end:
        return math.dist(point, start)
    x, y = point
    x1, y1 = start
    x2, y2 = end
    numerator = abs((y2 - y1) * x - (x2 - x1) * y + x2 * y1 - y2 * x1)
    denominator = math.hypot(y2 - y1, x2 - x1)
    return numerator / denominator


def rdp(points: list[Point2D], epsilon: float) -> list[Point2D]:
    if len(points) < 3:
        return points
    max_distance = 0.0
    max_index = 0
    for index in range(1, len(points) - 1):
        distance = _point_line_distance(points[index], points[0], points[-1])
        if distance > max_distance:
            max_distance = distance
            max_index = index
    if max_distance <= epsilon:
        return [points[0], points[-1]]
    left = rdp(points[: max_index + 1], epsilon)
    right = rdp(points[max_index:], epsilon)
    return left[:-1] + right


def normalize_freehand(raw_points: list[list[float]], *, closed_loop: bool) -> list[Point2D]:
    if len(raw_points) < 3:
        raise AppError("VALIDATION_ERROR", "자유 드로잉은 점이 3개 이상이어야 합니다.", 422)
    points: list[Point2D] = []
    for raw in raw_points:
        if len(raw) != 2 or not all(math.isfinite(float(value)) for value in raw):
            raise AppError("VALIDATION_ERROR", "자유 드로잉 좌표가 올바르지 않습니다.", 422)
        points.append((float(raw[0]), float(raw[1])))
    array = np.asarray(points)
    extent = array.max(axis=0) - array.min(axis=0)
    if min(extent) <= 1e-9:
        raise AppError("VALIDATION_ERROR", "자유 드로잉의 폭과 높이가 필요합니다.", 422)
    ratio = float(max(extent) / min(extent))
    if ratio > 10:
        raise AppError("VALIDATION_ERROR", "자유 드로잉 종횡비는 10:1 이하여야 합니다.", 422)
    diagonal = float(np.linalg.norm(extent))
    simplified = rdp(points, epsilon=diagonal * 0.0075)
    if len(simplified) < 3:
        raise AppError("VALIDATION_ERROR", "자유 드로잉이 너무 단순합니다.", 422)
    if closed_loop and simplified[0] != simplified[-1]:
        simplified.append(simplified[0])
    array = np.asarray(simplified, dtype=float)
    minimum = array.min(axis=0)
    extent = array.max(axis=0) - minimum
    scale = float(max(extent))
    normalized = (array - minimum) / scale
    normalized += (1.0 - extent / scale) / 2.0
    return [(float(x), float(y)) for x, y in normalized]
