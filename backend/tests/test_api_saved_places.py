from __future__ import annotations

import asyncio

from conftest import register_user
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import GenerationJob
from app.db.session import SessionLocal
from app.workers.runner import process_job


def test_saved_place_precomputes_and_keeps_course_after_delete(
    client: TestClient,
    admin_and_invite: tuple[object, str],
) -> None:
    token = register_user(client, admin_and_invite[1])["accessToken"]
    headers = {"Authorization": f"Bearer {token}"}
    source_location = {"lat": 37.5133, "lng": 127.1001}

    created = client.post(
        "/api/v1/saved-places",
        headers=headers,
        json={
            "name": "집 근처",
            "location": source_location,
            "privacyRadiusM": 250,
            "preferRiverside": True,
            "distancesKm": [5],
            "shapes": ["circle"],
        },
    )
    assert created.status_code == 201, created.text
    place = created.json()
    assert place["preferRiverside"] is True
    assert place["status"]["queued"] == 1

    with SessionLocal() as db:
        job = db.scalar(select(GenerationJob).where(GenerationJob.saved_place_id == place["id"]))
        assert job is not None
        assert job.request_json["start"] != source_location
        assert job.request_json["preferences"]["preferRiverside"] is True
        job_id = job.id

    asyncio.run(process_job(job_id))

    fetched = client.get("/api/v1/saved-places", headers=headers)
    assert fetched.status_code == 200
    status = fetched.json()["items"][0]["status"]
    assert status["succeeded"] == 1
    assert status["generatedCourses"] == 1

    courses = client.get("/api/v1/courses", headers=headers)
    assert courses.status_code == 200
    course = courses.json()["items"][0]
    assert course["savedPlaceId"] == place["id"]
    assert course["isPregenerated"] is True

    deleted = client.delete(f"/api/v1/saved-places/{place['id']}", headers=headers)
    assert deleted.status_code == 204
    retained = client.get(f"/api/v1/courses/{course['id']}", headers=headers)
    assert retained.status_code == 200
    assert retained.json()["savedPlaceId"] is None
    assert retained.json()["isPregenerated"] is True


def test_saved_place_validation_and_user_isolation(
    client: TestClient,
    admin_and_invite: tuple[object, str],
) -> None:
    first = register_user(client, admin_and_invite[1], "runner1")
    second = register_user(client, admin_and_invite[1], "runner2")
    first_headers = {"Authorization": f"Bearer {first['accessToken']}"}
    second_headers = {"Authorization": f"Bearer {second['accessToken']}"}
    created = client.post(
        "/api/v1/saved-places",
        headers=first_headers,
        json={
            "name": "한강",
            "location": {"lat": 37.52, "lng": 127.02},
            "privacyRadiusM": 0,
            "preferRiverside": True,
            "distancesKm": [3],
            "shapes": ["heart"],
        },
    )
    assert created.status_code == 201
    place_id = created.json()["id"]

    forbidden = client.post(f"/api/v1/saved-places/{place_id}/precompute", headers=second_headers)
    assert forbidden.status_code == 403

    invalid = client.post(
        "/api/v1/saved-places",
        headers=first_headers,
        json={
            "name": "지원 밖",
            "location": {"lat": 35.0, "lng": 129.0},
            "distancesKm": [5],
            "shapes": ["circle"],
        },
    )
    assert invalid.status_code == 422
