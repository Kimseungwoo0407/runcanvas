from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Response, status
from sqlalchemy import update

from app.db.models import RefreshToken
from app.dependencies import DB, CurrentUser
from app.errors import AppError
from app.schemas.auth import UserResponse
from app.schemas.user import DeleteAccountRequest, PasswordChangeRequest, UserSettings
from app.security import hash_password, verify_password

router = APIRouter(tags=["users"])


@router.get("/me", response_model=UserResponse)
def me(user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(user)


@router.get("/me/settings", response_model=UserSettings)
def get_settings(user: CurrentUser) -> UserSettings:
    return UserSettings.model_validate(user.settings_json)


@router.patch("/me/settings", response_model=UserSettings)
def update_settings(request: UserSettings, user: CurrentUser, db: DB) -> UserSettings:
    user.settings_json = request.model_dump(by_alias=True)
    db.commit()
    return request


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(request: PasswordChangeRequest, user: CurrentUser, db: DB) -> Response:
    if not verify_password(request.current_password, user.password_hash):
        raise AppError("VALIDATION_ERROR", "현재 비밀번호가 일치하지 않습니다.", 422)
    user.password_hash = hash_password(request.new_password)
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(request: DeleteAccountRequest, user: CurrentUser, db: DB) -> Response:
    if not verify_password(request.password, user.password_hash):
        raise AppError("VALIDATION_ERROR", "비밀번호가 일치하지 않습니다.", 422)
    db.delete(user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
