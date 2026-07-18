from __future__ import annotations

from typing import Protocol

from app.schemas.ai import ParsedRequest


class AIProvider(Protocol):
    async def parse(self, text: str) -> ParsedRequest | None: ...


class NullAIProvider:
    async def parse(self, text: str) -> ParsedRequest | None:
        return None
