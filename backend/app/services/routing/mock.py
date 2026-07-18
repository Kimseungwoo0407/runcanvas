from __future__ import annotations

from app.services.routing.base import EdgeSpan, LngLat, RouteOptions, RouteResult
from app.services.routing.geometry import polyline_distance_m


class MockRoutingProvider:
    async def route(self, points: list[LngLat], options: RouteOptions | None = None) -> RouteResult:
        options = options or RouteOptions()
        distance = polyline_distance_m(points)
        coordinates = [[point.lng, point.lat] for point in points]
        edge_spans = [EdgeSpan(index, index + 1, index + 1) for index in range(len(points) - 1)]
        return RouteResult(
            distance_m=distance,
            duration_s=distance / 2.4,
            coordinates=coordinates,
            snapped_points=points,
            snap_distances_m=[0.0] * len(points),
            edge_spans=edge_spans,
        )

    async def health(self) -> dict[str, object]:
        return {"status": "ok", "provider": "mock", "version": "1"}
