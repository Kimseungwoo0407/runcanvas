from __future__ import annotations

import asyncio
from dataclasses import replace

from conftest import register_user
from fastapi.testclient import TestClient

from app.config import get_settings
from app.schemas.generation import GenerationRequest
from app.services.optimization.optimizer import optimize_candidates
from app.services.routing.base import LngLat, RouteOptions, RouteResult
from app.services.routing.mock import MockRoutingProvider


class AlwaysTooLongRoutingProvider(MockRoutingProvider):
    async def route(
        self, points: list[LngLat], options: RouteOptions | None = None
    ) -> RouteResult:
        route = await super().route(points, options)
        return replace(route, distance_m=50_000, duration_s=20_000)

REQUEST = {
    "start": {"lat": 37.5133, "lng": 127.1001},
    "shapeType": "heart",
    "targetDistanceKm": 5,
    "distanceTolerancePct": 12,
    "closedLoop": True,
    "rotationMode": "auto",
    "preferences": {"avoidMajorRoads": True, "preferFootways": False},
    "maxCandidates": 3,
}


def test_job_create_and_cancel(client: TestClient, admin_and_invite: tuple[object, str]) -> None:
    token = register_user(client, admin_and_invite[1])["accessToken"]
    headers = {"Authorization": f"Bearer {token}"}
    created = client.post("/api/v1/generation-jobs", json=REQUEST, headers=headers)
    assert created.status_code == 202
    assert created.json()["state"] == "queued"
    cancelled = client.post(f"/api/v1/generation-jobs/{created.json()['id']}/cancel", headers=headers)
    assert cancelled.status_code == 200
    assert cancelled.json()["state"] == "cancelled"


def test_job_accepts_cheongju_and_rejects_region_mismatch(
    client: TestClient, admin_and_invite: tuple[object, str]
) -> None:
    token = register_user(client, admin_and_invite[1])["accessToken"]
    headers = {"Authorization": f"Bearer {token}"}
    cheongju_request = {
        **REQUEST,
        "region": "cheongju",
        "start": {"lat": 36.6424, "lng": 127.4890},
    }

    accepted = client.post("/api/v1/generation-jobs", json=cheongju_request, headers=headers)
    assert accepted.status_code == 202, accepted.text
    client.post(f"/api/v1/generation-jobs/{accepted.json()['id']}/cancel", headers=headers)

    mismatch = client.post(
        "/api/v1/generation-jobs",
        json={**cheongju_request, "start": REQUEST["start"]},
        headers=headers,
    )
    assert mismatch.status_code == 422
    assert mismatch.json()["details"]["selectedRegion"] == "cheongju"


def test_optimizer_returns_sorted_candidates() -> None:
    request = GenerationRequest.model_validate(REQUEST)
    candidates = asyncio.run(optimize_candidates(request, MockRoutingProvider(), get_settings()))
    assert 1 <= len(candidates) <= 3
    assert [item.metrics.total_score for item in candidates] == sorted(
        [item.metrics.total_score for item in candidates], reverse=True
    )


def test_optimizer_returns_best_effort_when_distance_tolerance_cannot_be_met() -> None:
    request = GenerationRequest.model_validate(REQUEST)
    candidates = asyncio.run(
        optimize_candidates(request, AlwaysTooLongRoutingProvider(), get_settings())
    )

    assert candidates
    assert all(candidate.metrics.distance_score == 0 for candidate in candidates)
