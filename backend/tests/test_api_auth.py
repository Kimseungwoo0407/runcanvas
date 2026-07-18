from __future__ import annotations

from conftest import register_user
from fastapi.testclient import TestClient


def test_register_login_refresh_logout(client: TestClient, admin_and_invite: tuple[object, str]) -> None:
    _, invite = admin_and_invite
    registered = register_user(client, invite)
    assert registered["user"]["username"] == "runner"
    me = client.get("/api/v1/me", headers={"Authorization": f"Bearer {registered['accessToken']}"})
    assert me.status_code == 200

    refreshed = client.post("/api/v1/auth/refresh", json={"refreshToken": registered["refreshToken"]})
    assert refreshed.status_code == 200
    assert refreshed.json()["refreshToken"] != registered["refreshToken"]

    old_refresh = client.post("/api/v1/auth/refresh", json={"refreshToken": registered["refreshToken"]})
    assert old_refresh.status_code == 401

    logout = client.post("/api/v1/auth/logout", json={"refreshToken": refreshed.json()["refreshToken"]})
    assert logout.status_code == 204


def test_unauthenticated_access_is_blocked(client: TestClient) -> None:
    response = client.get("/api/v1/courses")
    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHORIZED"


def test_user_settings_and_password_change(
    client: TestClient,
    admin_and_invite: tuple[object, str],
) -> None:
    registered = register_user(client, admin_and_invite[1], "settings-runner")
    headers = {"Authorization": f"Bearer {registered['accessToken']}"}

    defaults = client.get("/api/v1/me/settings", headers=headers)
    assert defaults.status_code == 200
    assert defaults.json()["distanceUnit"] == "km"

    updated = client.patch(
        "/api/v1/me/settings",
        headers=headers,
        json={
            "defaultPaceMinPerKm": 5.5,
            "distanceUnit": "mi",
            "mapTheme": "contrast",
            "showSourceShape": False,
        },
    )
    assert updated.status_code == 200
    assert updated.json()["defaultPaceMinPerKm"] == 5.5

    changed = client.post(
        "/api/v1/me/password",
        headers=headers,
        json={
            "currentPassword": "RunnerPassword123!",
            "newPassword": "NewRunnerPassword456!",
        },
    )
    assert changed.status_code == 204
    old_login = client.post(
        "/api/v1/auth/login",
        json={"username": "settings-runner", "password": "RunnerPassword123!"},
    )
    assert old_login.status_code == 401
    new_login = client.post(
        "/api/v1/auth/login",
        json={"username": "settings-runner", "password": "NewRunnerPassword456!"},
    )
    assert new_login.status_code == 200


def test_registration_password_minimum_is_eight_characters(
    client: TestClient, admin_and_invite: tuple[object, str]
) -> None:
    too_short = client.post(
        "/api/v1/auth/register",
        json={"username": "short-pass", "password": "1234567", "inviteCode": admin_and_invite[1]},
    )
    assert too_short.status_code == 422

    accepted = client.post(
        "/api/v1/auth/register",
        json={"username": "eight-pass", "password": "12345678", "inviteCode": admin_and_invite[1]},
    )
    assert accepted.status_code == 201
