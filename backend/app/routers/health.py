from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter
from sqlalchemy import text

from app.dependencies import DB
from app.schemas.common import HealthResponse
from app.services.routing.factory import get_routing_provider

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
def health(db: DB) -> HealthResponse:
    db.execute(text("SELECT 1"))
    return HealthResponse(
        status="ok",
        database="ok",
        version="1.0.0",
        timestamp=datetime.now(UTC),
    )


@router.get("/routing")
async def routing_health() -> dict[str, object]:
    return await get_routing_provider().health()
