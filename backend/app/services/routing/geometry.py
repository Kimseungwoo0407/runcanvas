from __future__ import annotations

import itertools
import math

from pyproj import CRS, Transformer

from app.services.routing.base import LngLat

Point2D = tuple[float, float]
EARTH_RADIUS_M = 6_371_008.8


def haversine_m(a: LngLat, b: LngLat) -> float:
    lat1 = math.radians(a.lat)
    lat2 = math.radians(b.lat)
    delta_lat = lat2 - lat1
    delta_lng = math.radians(b.lng - a.lng)
    value = math.sin(delta_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lng / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(min(1.0, math.sqrt(value)))


def local_transformers(origin: LngLat) -> tuple[Transformer, Transformer]:
    local = CRS.from_proj4(f"+proj=aeqd +lat_0={origin.lat} +lon_0={origin.lng} +datum=WGS84 +units=m +no_defs")
    wgs84 = CRS.from_epsg(4326)
    return (
        Transformer.from_crs(wgs84, local, always_xy=True),
        Transformer.from_crs(local, wgs84, always_xy=True),
    )


def transform_shape_to_lnglat(
    normalized_points: list[Point2D],
    start: LngLat,
    scale_m: float,
    rotation_deg: float,
) -> list[LngLat]:
    if len(normalized_points) < 2:
        raise ValueError("shape requires at least two points")
    radians = math.radians(rotation_deg)
    cosine = math.cos(radians)
    sine = math.sin(radians)
    centered = [(x - 0.5, y - 0.5) for x, y in normalized_points]
    projected: list[Point2D] = []
    for x, y in centered:
        scaled_x, scaled_y = x * scale_m, y * scale_m
        projected.append((scaled_x * cosine - scaled_y * sine, scaled_x * sine + scaled_y * cosine))
    anchor_x, anchor_y = projected[0]
    inverse = local_transformers(start)[1]
    result: list[LngLat] = []
    for x, y in projected:
        lng, lat = inverse.transform(x - anchor_x, y - anchor_y)
        result.append(LngLat(float(lng), float(lat)))
    return result


def project_lnglat_points(points: list[LngLat], origin: LngLat | None = None) -> list[Point2D]:
    if not points:
        return []
    transformer = local_transformers(origin or points[0])[0]
    result: list[Point2D] = []
    for point in points:
        x, y = transformer.transform(point.lng, point.lat)
        result.append((float(x), float(y)))
    return result


def polyline_distance_m(points: list[LngLat]) -> float:
    return sum(haversine_m(a, b) for a, b in itertools.pairwise(points))
