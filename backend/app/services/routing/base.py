from __future__ import annotations

from dataclasses import dataclass, field
from typing import NamedTuple, Protocol


class LngLat(NamedTuple):
    lng: float
    lat: float


@dataclass(frozen=True)
class EdgeSpan:
    from_index: int
    to_index: int
    edge_id: int


@dataclass(frozen=True)
class RouteInstruction:
    text: str
    distance_m: float
    duration_s: float


@dataclass(frozen=True)
class RouteOptions:
    profile: str = "foot"
    locale: str = "ko"
    pass_through: bool = True
    avoid_major_roads: bool = True
    prefer_footways: bool = False
    prefer_riverside: bool = False
    want_elevation: bool = False
    want_edge_ids: bool = True
    timeout_ms: int = 5000


@dataclass(frozen=True)
class RouteResult:
    distance_m: float
    duration_s: float
    coordinates: list[list[float]]
    snapped_points: list[LngLat]
    snap_distances_m: list[float]
    edge_spans: list[EdgeSpan] = field(default_factory=list)
    ascend_m: float | None = None
    descend_m: float | None = None
    instructions: list[RouteInstruction] = field(default_factory=list)


class RoutingProvider(Protocol):
    async def route(self, points: list[LngLat], options: RouteOptions | None = None) -> RouteResult: ...

    async def health(self) -> dict[str, object]: ...
