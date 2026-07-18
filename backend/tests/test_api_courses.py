from __future__ import annotations

from conftest import register_user
from fastapi.testclient import TestClient

DIRECT_COURSE = {
    "name": "테스트 하트",
    "shapeType": "heart",
    "targetDistanceM": 5000,
    "sourceShape": {"type": "LineString", "coordinates": [[0, 0], [1, 0], [0, 0]]},
    "waypoints": [[127.0, 37.0], [127.01, 37.01], [127.0, 37.0]],
    "route": {"type": "LineString", "coordinates": [[127.0, 37.0], [127.01, 37.01], [127.0, 37.0]]},
    "metrics": {
        "distanceM": 5000,
        "durationS": 1800,
        "shapeScore": 0.8,
        "distanceScore": 1,
        "closureScore": 1,
        "overlapRatio": 0.05,
        "simplicityScore": 0.9,
        "totalScore": 0.88,
        "waypointCount": 3,
        "maxSnapDistanceM": 0,
        "ascendM": None,
        "descendM": None,
    },
}


def test_course_crud_and_user_isolation(client: TestClient, admin_and_invite: tuple[object, str]) -> None:
    first = register_user(client, admin_and_invite[1], "runner1")
    second = register_user(client, admin_and_invite[1], "runner2")
    first_headers = {"Authorization": f"Bearer {first['accessToken']}"}
    second_headers = {"Authorization": f"Bearer {second['accessToken']}"}

    created = client.post("/api/v1/courses", json=DIRECT_COURSE, headers=first_headers)
    assert created.status_code == 201, created.text
    course_id = created.json()["id"]

    forbidden = client.get(f"/api/v1/courses/{course_id}", headers=second_headers)
    assert forbidden.status_code == 403

    patched = client.patch(
        f"/api/v1/courses/{course_id}",
        json={"isFavorite": True, "shareEnabled": True},
        headers=first_headers,
    )
    assert patched.status_code == 200
    assert patched.json()["isFavorite"] is True
    share_token = patched.json()["shareToken"]
    assert share_token

    shared = client.get(f"/api/v1/shared/courses/{share_token}")
    assert shared.status_code == 200
    assert shared.json()["shareToken"] is None

    shared_clone = client.post(
        f"/api/v1/shared/courses/{share_token}/clone",
        headers=second_headers,
    )
    assert shared_clone.status_code == 201
    assert shared_clone.json()["ownerId"] == second["user"]["id"]

    gpx = client.get(f"/api/v1/courses/{course_id}/gpx", headers=first_headers)
    assert gpx.status_code == 200
    assert gpx.headers["content-type"].startswith("application/gpx+xml")

    deleted = client.delete(f"/api/v1/courses/{course_id}", headers=first_headers)
    assert deleted.status_code == 204
