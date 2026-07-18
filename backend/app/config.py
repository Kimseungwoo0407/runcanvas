from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_ENV: Literal["development", "test", "production"] = "development"
    APP_SECRET_KEY: str = "development-only-secret-change-before-production"
    DATABASE_URL: str = "sqlite:///./storage/db/app.db"
    CORS_ORIGINS: Annotated[list[str], NoDecode] = ["http://localhost:5173"]
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    GRAPHHOPPER_URL: str = "http://localhost:8989"
    ROUTING_PROVIDER: Literal["graphhopper", "mock"] = "graphhopper"
    SUPPORTED_BBOX: Annotated[tuple[float, float, float, float], NoDecode] = (
        126.76,
        37.41,
        127.18,
        37.70,
    )
    ACCESS_TOKEN_MINUTES: int = Field(default=15, ge=1, le=120)
    REFRESH_TOKEN_DAYS: int = Field(default=30, ge=1, le=365)
    EXPORT_DIR: Path = Path("./storage/exports")
    BACKUP_DIR: Path = Path("./storage/backups")
    MAX_ROUTING_CALLS: int = Field(default=40, ge=1, le=120)
    GENERATION_TIMEOUT_SECONDS: int = Field(default=90, ge=10, le=300)
    WORKER_POLL_SECONDS: float = Field(default=1, ge=0.1, le=30)
    WORKER_CONCURRENCY: int = Field(default=1, ge=1, le=2)
    NOMINATIM_URL: str = "https://nominatim.openstreetmap.org"
    NOMINATIM_USER_AGENT: str = "RunCanvas/1.0 admin@example.invalid"
    AI_ENABLED: bool = False
    AI_MODEL: str = "qwen3:1.7b"
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_TIMEOUT_SECONDS: float = Field(default=3, ge=0.5, le=10)

    @model_validator(mode="after")
    def validate_production_settings(self) -> Settings:
        if self.APP_ENV != "production":
            return self
        if self.APP_SECRET_KEY == "development-only-secret-change-before-production":
            raise ValueError("production APP_SECRET_KEY must be replaced")
        if "*" in self.CORS_ORIGINS:
            raise ValueError("production CORS_ORIGINS cannot contain a wildcard")
        if "example.invalid" in self.NOMINATIM_USER_AGENT:
            raise ValueError("production NOMINATIM_USER_AGENT must contain real operator contact information")
        return self

    @field_validator("APP_SECRET_KEY")
    @classmethod
    def validate_secret(cls, value: str, info: object) -> str:
        if len(value) < 32:
            raise ValueError("APP_SECRET_KEY must contain at least 32 characters")
        return value

    @field_validator("SUPPORTED_BBOX", mode="before")
    @classmethod
    def parse_bbox(cls, value: object) -> object:
        if isinstance(value, str):
            parts = [float(part.strip()) for part in value.split(",")]
            if len(parts) != 4:
                raise ValueError("SUPPORTED_BBOX must be minLng,minLat,maxLng,maxLat")
            return tuple(parts)
        return value

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, value: object) -> object:
        if isinstance(value, str):
            if value.startswith("["):
                parsed = json.loads(value)
                if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
                    raise ValueError("CORS_ORIGINS must be a list of origins")
                return parsed
            return [part.strip() for part in value.split(",") if part.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    settings.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    return settings
