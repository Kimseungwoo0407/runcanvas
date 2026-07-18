from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.config import Settings


def test_production_rejects_development_secret() -> None:
    with pytest.raises(ValidationError, match="APP_SECRET_KEY"):
        Settings(
            APP_ENV="production",
            APP_SECRET_KEY="development-only-secret-change-before-production",
            CORS_ORIGINS=["https://run.example.com"],
            NOMINATIM_USER_AGENT="RunCanvas/1.0 operator@example.com",
            _env_file=None,
        )


def test_production_accepts_explicit_security_settings() -> None:
    settings = Settings(
        APP_ENV="production",
        APP_SECRET_KEY="a-production-secret-key-that-is-longer-than-thirty-two-characters",
        CORS_ORIGINS=["https://run.example.com"],
        NOMINATIM_USER_AGENT="RunCanvas/1.0 operator@example.com",
        _env_file=None,
    )
    assert settings.APP_ENV == "production"
