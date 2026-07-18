from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.dependencies import DB, SettingsDep
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: DB, settings: SettingsDep) -> TokenResponse:
    return AuthService(db, settings).register(request)


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: DB, settings: SettingsDep) -> TokenResponse:
    return AuthService(db, settings).login(request)


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: RefreshRequest, db: DB, settings: SettingsDep) -> TokenResponse:
    return AuthService(db, settings).refresh(request.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: LogoutRequest, db: DB, settings: SettingsDep) -> Response:
    AuthService(db, settings).logout(request.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
