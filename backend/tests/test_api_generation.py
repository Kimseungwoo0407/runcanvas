from __future__ import annotations

import asyncio

from conftest import register_user
from fastapi.testclient import TestClient

from app.config import get_settings
from app.schemas.generation import GenerationRequest
from app.services.optimization.optimizer import optimize_candidates
from app.services.routing.mock import MockRoutingProvider

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


def test_optimizer_returns_sorted_candidates() -> None:
    request = GenerationRequest.model_validate(REQUEST)
    candidates = asyncio.run(optimize_candidates(request, MockRoutingProvider(), get_settings()))
    assert 1 <= len(candidates) <= 3
    assert [item.metrics.total_score for item in candidates] == sorted(
        [item.metrics.total_score for item in candidates], reverse=True
    )
