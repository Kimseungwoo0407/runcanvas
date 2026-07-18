from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.config import Settings
from app.errors import AppError

_password_hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def new_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def new_invite_code() -> str:
    return "RC-" + secrets.token_urlsafe(12).replace("-", "").replace("_", "").upper()


def new_share_token() -> str:
    return secrets.token_urlsafe(24)


def create_access_token(user_id: str, role: str, settings: Settings) -> tuple[str, datetime]:
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_MINUTES)
    payload: dict[str, Any] = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "iat": datetime.now(UTC),
        "exp": expires_at,
    }
    encoded = jwt.encode(payload, settings.APP_SECRET_KEY, algorithm="HS256")
    token = encoded.decode("utf-8") if isinstance(encoded, bytes) else str(encoded)
    return token, expires_at


def decode_access_token(token: str, settings: Settings) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.APP_SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as error:
        raise AppError("UNAUTHORIZED", "세션이 만료되었습니다.", 401) from error
    except jwt.PyJWTError as error:
        raise AppError("UNAUTHORIZED", "유효하지 않은 인증 정보입니다.", 401) from error
    if payload.get("type") != "access" or not payload.get("sub"):
        raise AppError("UNAUTHORIZED", "유효하지 않은 인증 정보입니다.", 401)
    return payload
