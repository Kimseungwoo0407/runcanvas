from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.schemas.auth import UserResponse
from app.schemas.common import APIModel


class InviteCreateRequest(APIModel):
    expires_in_days: int = Field(default=7, ge=1, le=90)
    max_uses: int = Field(default=1, ge=1, le=20)


class InviteCreateResponse(APIModel):
    id: str
    code: str
    expires_at: datetime
    max_uses: int


class UserAdminPatch(APIModel):
    is_active: bool


class UserListResponse(APIModel):
    items: list[UserResponse]
