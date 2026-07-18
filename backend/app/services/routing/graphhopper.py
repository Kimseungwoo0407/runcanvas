from __future__ import annotations

from typing import Any

import httpx
import structlog

from app.errors import AppError
from app.services.routing.base import (
    EdgeSpan,
    LngLat,
    RouteInstruction,
    RouteOptions,
    RouteResult,
)
from app.services.routing.geometry import haversine_m
from app.services.routing.han_river import HAN_RIVER_CORRIDOR

logger = structlog.get_logger()


class GraphHopperRoutingProvider:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    @staticmethod
    def _custom_model(options: RouteOptions) -> dict[str, object] | None:
        priority: list[dict[str, str]] = [
            {"if": "road_environment == TUNNEL", "multiply_by": "0.35"},
            {"if": "road_class == TRACK", "multiply_by": "0.6"},
        ]
        if options.avoid_major_roads:
            priority.extend(
                [
                    {
                        "if": "road_class == MOTORWAY || road_class == TRUNK",
                        "multiply_by": "0.0",
                    },
                    {
                        "if": "road_class == PRIMARY || road_class == SECONDARY",
                        "multiply_by": "0.3",
                    },
                ]
            )
        if options.prefer_footways:
            priority.append(
                {
                    "if": (
                        "road_class != PATH && road_class != FOOTWAY && road_class != PEDESTRIAN "
                        "&& road_class != LIVING_STREET"
                    ),
                    "multiply_by": "0.8",
                }
            )
        model: dict[str, object] = {"priority": priority}
        if options.prefer_riverside:
            priority.extend(
                [
                    {"if": "!in_han_river_corridor", "multiply_by": "0.45"},
                    {
                        "if": (
                            "in_han_river_corridor && road_class != PATH && road_class != FOOTWAY "
                            "&& road_class != PEDESTRIAN && road_class != LIVING_STREET"
                        ),
                        "multiply_by": "0.75",
                    },
                ]
            )
            model["areas"] = HAN_RIVER_CORRIDOR
        return model

    async def route(self, points: list[LngLat], options: RouteOptions | None = None) -> RouteResult:
        options = options or RouteOptions()
        if len(points) < 2:
            raise AppError("VALIDATION_ERROR", "경유점이 2개 이상 필요합니다.", 422)
        if not options.pass_through:
            raise AppError("ROUTING_UNAVAILABLE", "pass_through가 필요한 라우팅 요청입니다.", 503)
        payload: dict[str, Any] = {
            "profile": options.profile,
            "points": [[point.lng, point.lat] for point in points],
            "locale": options.locale,
            "instructions": True,
            "points_encoded": False,
            "ch.disable": True,
            "pass_through": True,
            "elevation": options.want_elevation,
            "timeout_ms": options.timeout_ms,
            "snap_preventions": ["ferry"],
        }
        if options.want_edge_ids:
            payload["details"] = ["edge_id"]
        custom_model = self._custom_model(options)
        if custom_model:
            payload["custom_model"] = custom_model
        try:
            async with httpx.AsyncClient(timeout=(options.timeout_ms / 1000) + 1) as client:
                response = await client.post(f"{self.base_url}/route", json=payload)
        except httpx.TimeoutException as error:
            raise AppError("GENERATION_TIMEOUT", "라우팅 요청 시간이 초과되었습니다.", 504) from error
        except httpx.HTTPError as error:
            raise AppError("ROUTING_UNAVAILABLE", "라우팅 엔진에 연결할 수 없습니다.", 503) from error
        if response.status_code >= 500:
            raise AppError("ROUTING_UNAVAILABLE", "라우팅 엔진이 응답하지 않습니다.", 503)
        if response.status_code >= 400:
            body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            message = str(body.get("message", "보행 경로를 찾을 수 없습니다."))
            code = "OUTSIDE_SUPPORTED_AREA" if "Cannot find point" in message else "NO_ROUTE_FOUND"
            raise AppError(code, "경유점 사이의 보행 경로를 찾을 수 없습니다.", 422)
        body = response.json()
        paths = body.get("paths") or []
        if not paths:
            raise AppError("NO_ROUTE_FOUND", "보행 경로를 찾을 수 없습니다.", 422)
        path = paths[0]
        point_geojson = path.get("points") or {}
        coordinates = point_geojson.get("coordinates") if isinstance(point_geojson, dict) else None
        snapped_geojson = path.get("snapped_waypoints") or {}
        snapped_coordinates = snapped_geojson.get("coordinates") if isinstance(snapped_geojson, dict) else None
        if not isinstance(coordinates, list) or not isinstance(snapped_coordinates, list):
            raise AppError("ROUTING_UNAVAILABLE", "라우팅 응답 좌표 형식이 올바르지 않습니다.", 503)
        snapped = [LngLat(float(item[0]), float(item[1])) for item in snapped_coordinates]
        if len(snapped) != len(points):
            raise AppError("ROUTING_UNAVAILABLE", "라우팅 엔진이 경유점 순서를 보존하지 않았습니다.", 503)
        snap_distances = [haversine_m(source, target) for source, target in zip(points, snapped, strict=True)]
        details = path.get("details", {}).get("edge_id", [])
        edge_spans = [EdgeSpan(int(item[0]), int(item[1]), int(item[2])) for item in details]
        instructions = [
            RouteInstruction(
                text=str(item.get("text", "")),
                distance_m=float(item.get("distance", 0)),
                duration_s=float(item.get("time", 0)) / 1000,
            )
            for item in path.get("instructions", [])
        ]
        logger.info(
            "graphhopper_route",
            duration_ms=float(path.get("time", 0)),
            distance_m=round(float(path["distance"]), 1),
            waypoint_count=len(points),
        )
        return RouteResult(
            distance_m=float(path["distance"]),
            duration_s=float(path.get("time", 0)) / 1000,
            coordinates=[[float(value) for value in item] for item in coordinates],
            snapped_points=snapped,
            snap_distances_m=snap_distances,
            edge_spans=edge_spans,
            ascend_m=float(path["ascend"]) if path.get("ascend") is not None else None,
            descend_m=float(path["descend"]) if path.get("descend") is not None else None,
            instructions=instructions,
        )

    async def health(self) -> dict[str, object]:
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                response = await client.get(f"{self.base_url}/info")
                response.raise_for_status()
        except httpx.HTTPError as error:
            raise AppError("ROUTING_UNAVAILABLE", "라우팅 엔진이 응답하지 않습니다.", 503) from error
        info = response.json()
        return {
            "status": "ok",
            "provider": "graphhopper",
            "version": info.get("version"),
            "bbox": info.get("bbox"),
            "profiles": info.get("profiles", []),
        }
