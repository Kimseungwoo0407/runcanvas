from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.dependencies import DB, CurrentUser, SettingsDep
from app.schemas.saved_place import (
    SavedPlaceCreateRequest,
    SavedPlaceListResponse,
    SavedPlacePatchRequest,
    SavedPlaceResponse,
)
from app.services.saved_places import SavedPlaceService

router = APIRouter(prefix="/saved-places", tags=["saved places"])


@router.get("", response_model=SavedPlaceListResponse)
def list_saved_places(user: CurrentUser, db: DB, settings: SettingsDep) -> SavedPlaceListResponse:
    return SavedPlaceService(db, settings).list(user.id)


@router.post("", response_model=SavedPlaceResponse, status_code=status.HTTP_201_CREATED)
def create_saved_place(
    request: SavedPlaceCreateRequest,
    user: CurrentUser,
    db: DB,
    settings: SettingsDep,
) -> SavedPlaceResponse:
    return SavedPlaceService(db, settings).create(user.id, request)


@router.patch("/{place_id}", response_model=SavedPlaceResponse)
def update_saved_place(
    place_id: str,
    request: SavedPlacePatchRequest,
    user: CurrentUser,
    db: DB,
    settings: SettingsDep,
) -> SavedPlaceResponse:
    return SavedPlaceService(db, settings).update(user.id, place_id, request)


@router.post("/{place_id}/precompute", response_model=SavedPlaceResponse, status_code=status.HTTP_202_ACCEPTED)
def precompute_saved_place(
    place_id: str,
    user: CurrentUser,
    db: DB,
    settings: SettingsDep,
) -> SavedPlaceResponse:
    return SavedPlaceService(db, settings).precompute(user.id, place_id)


@router.delete("/{place_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_place(
    place_id: str,
    user: CurrentUser,
    db: DB,
    settings: SettingsDep,
) -> Response:
    SavedPlaceService(db, settings).delete(user.id, place_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
