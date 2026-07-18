from __future__ import annotations

from fastapi import APIRouter

from app.dependencies import CurrentUser, SettingsDep
from app.schemas.ai import NaturalLanguageRequest, ParseResponse
from app.services.ai import parse_natural_language

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/parse", response_model=ParseResponse)
async def parse_request(
    request: NaturalLanguageRequest,
    _: CurrentUser,
    settings: SettingsDep,
) -> ParseResponse:
    return await parse_natural_language(request.text, settings)
