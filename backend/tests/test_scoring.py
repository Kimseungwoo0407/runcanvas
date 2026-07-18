from __future__ import annotations

from app.services.routing.base import LngLat, RouteResult
from app.services.scoring.metrics import distance_score, score_route


def route(coordinates: list[list[float]]) -> RouteResult:
    points = [LngLat(item[0], item[1]) for item in coordinates]
    return RouteResult(
        distance_m=1000,
        duration_s=400,
        coordinates=coordinates,
        snapped_points=points,
        snap_distances_m=[0] * len(points),
    )


def test_distance_score_boundaries() -> None:
    assert distance_score(1000, 1000, 10) == 1
    assert distance_score(1200, 1000, 10) == 0


def test_matching_shape_scores_above_distorted_shape() -> None:
    source = [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]
    matching = route([[127.0, 37.0], [127.01, 37.0], [127.01, 37.01], [127.0, 37.01], [127.0, 37.0]])
    distorted = route([[127.0, 37.0], [127.02, 37.0], [127.019, 37.0001], [127.001, 37.0001], [127.0, 37.0]])
    assert (
        score_route(source, matching, 1000, 20, 5).shape_score > score_route(source, distorted, 1000, 20, 5).shape_score
    )
