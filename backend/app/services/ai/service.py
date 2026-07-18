from __future__ import annotations

from app.config import Settings
from app.schemas.ai import ParseResponse
from app.services.ai.base import NullAIProvider
from app.services.ai.ollama import OllamaAIProvider
from app.services.ai.rules import parse_rules


async def parse_natural_language(text: str, settings: Settings) -> ParseResponse:
    rule_result = parse_rules(text)
    if rule_result is not None:
        return ParseResponse(result=rule_result, source="rules")
    provider = OllamaAIProvider(settings) if settings.AI_ENABLED else NullAIProvider()
    result = await provider.parse(text)
    if result is not None:
        return ParseResponse(result=result, source="llm")
    return ParseResponse(result=None, source="form")
