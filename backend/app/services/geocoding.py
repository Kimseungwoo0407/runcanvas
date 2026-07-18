from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy.orm import Session

from app.config import Settings
from app.db.models import GeocodingCache
from app.errors import AppError
from app.schemas.geocoding import GeocodingResponse, GeocodingResult

_rate_lock = asyncio.Lock()
_last_call = 0.0


async def search_geocoding(db: Session, settings: Settings, query: str) -> GeocodingResponse:
    normalized = " ".join(query.strip().lower().split())
    if len(normalized) < 2:
        raise AppError("VALIDATION_ERROR", "검색어를 두 글자 이상 입력해 주세요.", 422)
    cached = db.get(GeocodingCache, normalized)
    now = datetime.now(UTC)
    if cached is not None:
        expires = cached.expires_at.replace(tzinfo=UTC) if cached.expires_at.tzinfo is None else cached.expires_at
        if expires > now:
            return GeocodingResponse(items=[GeocodingResult.model_validate(item) for item in cached.response_json])

    global _last_call
    async with _rate_lock:
        loop = asyncio.get_running_loop()
        wait = 1.0 - (loop.time() - _last_call)
        if wait > 0:
            await asyncio.sleep(wait)
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    f"{settings.NOMINATIM_URL.rstrip('/')}/search",
                    params={"q": query, "format": "jsonv2", "limit": 5, "countrycodes": "kr"},
                    headers={"User-Agent": settings.NOMINATIM_USER_AGENT},
                )
                response.raise_for_status()
        except httpx.HTTPError as error:
            raise AppError("GEOCODING_UNAVAILABLE", "주소 검색 서비스를 사용할 수 없습니다.", 503) from error
        _last_call = loop.time()
    items = [
        GeocodingResult(
            display_name=str(item["display_name"]),
            lat=float(item["lat"]),
            lng=float(item["lon"]),
            bounding_box=[float(value) for value in item.get("boundingbox", [])] or None,
        )
        for item in response.json()
    ]
    payload = [item.model_dump(by_alias=True) for item in items]
    if cached is None:
        cached = GeocodingCache(query_key=normalized, response_json=payload, expires_at=now + timedelta(days=30))
        db.add(cached)
    else:
        cached.response_json = payload
        cached.expires_at = now + timedelta(days=30)
    db.commit()
    return GeocodingResponse(items=items)
