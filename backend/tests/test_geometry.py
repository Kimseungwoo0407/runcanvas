from __future__ import annotations

from app.services.routing.base import LngLat
from app.services.routing.geometry import haversine_m, local_transformers, transform_shape_to_lnglat


def test_projection_round_trip_is_sub_meter() -> None:
    origin = LngLat(127.1001, 37.5133)
    forward, inverse = local_transformers(origin)
    x, y = forward.transform(origin.lng, origin.lat)
    lng, lat = inverse.transform(x + 100, y + 50)
    x2, y2 = forward.transform(lng, lat)
    assert abs(x2 - 100) < 0.01
    assert abs(y2 - 50) < 0.01


def test_shape_anchor_is_start() -> None:
    start = LngLat(127.1001, 37.5133)
    points = transform_shape_to_lnglat([(0, 0), (1, 0), (0, 0)], start, 1000, 35)
    assert haversine_m(points[0], start) < 0.01
    assert haversine_m(points[-1], start) < 0.01
