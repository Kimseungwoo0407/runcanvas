from __future__ import annotations

from typing import Literal

from pydantic import Field

from app.schemas.common import APIModel


class UserSettings(APIModel):
    default_pace_min_per_km: float = Field(default=6.0, ge=2.5, le=15)
    distance_unit: Literal["km", "mi"] = "km"
    map_theme: Literal["default", "contrast"] = "default"
    show_source_shape: bool = True


class PasswordChangeRequest(APIModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class DeleteAccountRequest(APIModel):
    password: str = Field(min_length=1, max_length=128)
