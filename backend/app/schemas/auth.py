from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator

from app.schemas.common import USERNAME_RE, APIModel


class RegisterRequest(APIModel):
    username: str
    password: str = Field(min_length=8, max_length=128)
    invite_code: str = Field(min_length=8, max_length=64)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        value = value.strip()
        if not USERNAME_RE.fullmatch(value):
            raise ValueError(
                "사용자명은 영문자, 숫자, 마침표(.), 하이픈(-), 밑줄(_)만 사용해 3~40자로 입력해 주세요."
            )
        return value


class LoginRequest(APIModel):
    username: str
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(APIModel):
    refresh_token: str = Field(min_length=32, max_length=256)


class LogoutRequest(APIModel):
    refresh_token: str = Field(min_length=32, max_length=256)


class UserResponse(APIModel):
    id: str
    username: str
    role: str
    is_active: bool
    created_at: datetime


class TokenResponse(APIModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    access_expires_at: datetime
    refresh_expires_at: datetime
    user: UserResponse
