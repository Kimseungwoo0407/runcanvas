from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.models import User
from app.db.session import get_db
from app.errors import AppError
from app.repositories.users import UserRepository
from app.security import decode_access_token

bearer = HTTPBearer(auto_error=False)
DB = Annotated[Session, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_current_user(
    db: DB,
    settings: SettingsDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError("UNAUTHORIZED", "로그인이 필요합니다.", 401)
    payload = decode_access_token(credentials.credentials, settings)
    user = UserRepository(db).get_by_id(str(payload["sub"]))
    if user is None or not user.is_active:
        raise AppError("UNAUTHORIZED", "사용할 수 없는 계정입니다.", 401)
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_admin(user: CurrentUser) -> User:
    if user.role != "admin":
        raise AppError("FORBIDDEN", "관리자 권한이 필요합니다.", 403)
    return user


AdminUser = Annotated[User, Depends(require_admin)]
