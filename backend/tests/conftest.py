from __future__ import annotations

import os
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TEST_DB = Path("/tmp/runcanvas-test.db")
TEST_DB.unlink(missing_ok=True)
os.environ.update(
    {
        "APP_ENV": "test",
        "APP_SECRET_KEY": "test-secret-key-with-at-least-thirty-two-characters",
        "DATABASE_URL": f"sqlite:///{TEST_DB}",
        "CORS_ORIGINS": '["http://testserver"]',
        "ROUTING_PROVIDER": "mock",
        "SUPPORTED_BBOX": "126.0,36.0,128.0,38.5",
    }
)

from app.db.models import Base, InviteCode, User  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.security import hash_password, hash_token  # noqa: E402


@pytest.fixture(autouse=True)
def reset_database() -> Generator[None, None, None]:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_and_invite() -> tuple[User, str]:
    code = "RC-TESTINVITECODE"
    with SessionLocal() as db:
        admin = User(
            username="admin",
            password_hash=hash_password("StrongPassword123!"),
            role="admin",
        )
        db.add(admin)
        db.flush()
        db.add(
            InviteCode(
                code_hash=hash_token(code),
                expires_at=datetime.now(UTC) + timedelta(days=1),
                max_uses=10,
                created_by=admin.id,
            )
        )
        db.commit()
        db.refresh(admin)
        return admin, code


def register_user(client: TestClient, invite: str, username: str = "runner") -> dict[str, object]:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "password": "RunnerPassword123!",
            "inviteCode": invite,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()
