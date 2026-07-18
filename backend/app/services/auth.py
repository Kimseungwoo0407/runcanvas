from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import Settings
from app.db.models import User
from app.errors import AppError
from app.repositories.users import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.security import (
    create_access_token,
    hash_password,
    hash_token,
    new_refresh_token,
    verify_password,
)


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class AuthService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.users = UserRepository(db)

    def register(self, request: RegisterRequest) -> TokenResponse:
        invite = self.users.find_invite(hash_token(request.invite_code.strip()))
        now = datetime.now(UTC)
        if invite is None or _as_utc(invite.expires_at) <= now or invite.used_count >= invite.max_uses:
            raise AppError("FORBIDDEN", "초대 코드가 유효하지 않습니다.", 403)
        if self.users.get_by_username(request.username):
            raise AppError("VALIDATION_ERROR", "이미 사용 중인 사용자명입니다.", 422)
        try:
            user = self.users.create(request.username, hash_password(request.password))
            invite.used_count += 1
            response = self._issue_tokens(user)
            self.db.commit()
            return response
        except IntegrityError as error:
            self.db.rollback()
            raise AppError("VALIDATION_ERROR", "이미 사용 중인 사용자명입니다.", 422) from error

    def login(self, request: LoginRequest) -> TokenResponse:
        user = self.users.get_by_username(request.username)
        if user is None or not verify_password(request.password, user.password_hash):
            raise AppError("UNAUTHORIZED", "사용자명 또는 비밀번호가 올바르지 않습니다.", 401)
        if not user.is_active:
            raise AppError("FORBIDDEN", "비활성화된 계정입니다.", 403)
        response = self._issue_tokens(user)
        self.db.commit()
        return response

    def refresh(self, raw_token: str) -> TokenResponse:
        stored = self.users.get_refresh_token(hash_token(raw_token))
        now = datetime.now(UTC)
        if stored is None or stored.revoked_at is not None or _as_utc(stored.expires_at) <= now:
            raise AppError("UNAUTHORIZED", "refresh token이 만료되었거나 폐기되었습니다.", 401)
        user = self.users.get_by_id(stored.user_id)
        if user is None or not user.is_active:
            raise AppError("UNAUTHORIZED", "사용할 수 없는 계정입니다.", 401)
        self.users.revoke_refresh_token(stored)
        response = self._issue_tokens(user)
        self.db.commit()
        return response

    def logout(self, raw_token: str) -> None:
        stored = self.users.get_refresh_token(hash_token(raw_token))
        if stored and stored.revoked_at is None:
            self.users.revoke_refresh_token(stored)
            self.db.commit()

    def _issue_tokens(self, user: User) -> TokenResponse:
        access_token, access_expires_at = create_access_token(user.id, user.role, self.settings)
        refresh_token = new_refresh_token()
        refresh_expires_at = datetime.now(UTC) + timedelta(days=self.settings.REFRESH_TOKEN_DAYS)
        self.users.add_refresh_token(user.id, hash_token(refresh_token), refresh_expires_at)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            access_expires_at=access_expires_at,
            refresh_expires_at=refresh_expires_at,
            user=UserResponse.model_validate(user),
        )
