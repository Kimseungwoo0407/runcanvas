from __future__ import annotations

import asyncio
import time
from collections import defaultdict

from fastapi import APIRouter

from app.dependencies import CurrentUser
from app.errors import AppError
from app.schemas.generation import RecalculateRequest, RecalculateResponse
from app.services.generation import recalculate_route
from app.services.routing.factory import get_routing_provider

router = APIRouter(prefix="/routes", tags=["routes"])
_last_request: dict[str, float] = defaultdict(float)
_lock = asyncio.Lock()


@router.post("/recalculate", response_model=RecalculateResponse)
async def recalculate(request: RecalculateRequest, user: CurrentUser) -> RecalculateResponse:
    async with _lock:
        now = time.monotonic()
        if now - _last_request[user.id] < 1:
            raise AppError("RATE_LIMITED", "재라우팅은 초당 한 번만 요청할 수 있습니다.", 429)
        _last_request[user.id] = now
    return await recalculate_route(request, get_routing_provider())
