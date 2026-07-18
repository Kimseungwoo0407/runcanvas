from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, status

from app.db.models import InviteCode
from app.dependencies import DB, AdminUser
from app.errors import AppError
from app.repositories.users import UserRepository
from app.schemas.admin import (
    InviteCreateRequest,
    InviteCreateResponse,
    UserAdminPatch,
    UserListResponse,
)
from app.schemas.auth import UserResponse
from app.security import hash_token, new_invite_code

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/invite-codes", response_model=InviteCreateResponse, status_code=status.HTTP_201_CREATED)
def create_invite(
    request: InviteCreateRequest,
    admin: AdminUser,
    db: DB,
) -> InviteCreateResponse:
    code = new_invite_code()
    invite = InviteCode(
        code_hash=hash_token(code),
        expires_at=datetime.now(UTC) + timedelta(days=request.expires_in_days),
        max_uses=request.max_uses,
        created_by=admin.id,
    )
    db.add(invite)
    db.commit()
    return InviteCreateResponse(
        id=invite.id,
        code=code,
        expires_at=invite.expires_at,
        max_uses=invite.max_uses,
    )


@router.get("/users", response_model=UserListResponse)
def list_users(_: AdminUser, db: DB) -> UserListResponse:
    return UserListResponse(items=[UserResponse.model_validate(user) for user in UserRepository(db).list_users()])


@router.patch("/users/{user_id}", response_model=UserResponse)
def patch_user(
    user_id: str,
    request: UserAdminPatch,
    admin: AdminUser,
    db: DB,
) -> UserResponse:
    user = UserRepository(db).get_by_id(user_id)
    if user is None:
        raise AppError("FORBIDDEN", "사용자를 찾을 수 없습니다.", 404)
    if user.id == admin.id and not request.is_active:
        raise AppError("VALIDATION_ERROR", "현재 관리자 계정은 비활성화할 수 없습니다.", 422)
    user.is_active = request.is_active
    db.commit()
    return UserResponse.model_validate(user)
