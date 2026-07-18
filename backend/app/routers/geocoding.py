from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from app.dependencies import DB, CurrentUser, SettingsDep
from app.regions import RegionCode
from app.schemas.geocoding import GeocodingResponse
from app.services.geocoding import search_geocoding

router = APIRouter(prefix="/geocoding", tags=["geocoding"])


@router.get("/search", response_model=GeocodingResponse)
async def search(
    _: CurrentUser,
    db: DB,
    settings: SettingsDep,
    q: str = Query(min_length=2, max_length=120),
    region: Annotated[RegionCode | None, Query()] = None,
) -> GeocodingResponse:
    return await search_geocoding(db, settings, q, region)
