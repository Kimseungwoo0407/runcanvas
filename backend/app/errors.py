from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}


def error_payload(request: Request, error: AppError) -> dict[str, Any]:
    return {
        "code": error.code,
        "message": error.message,
        "details": error.details,
        "requestId": getattr(request.state, "request_id", None),
    }


async def app_error_handler(request: Request, error: AppError) -> JSONResponse:
    return JSONResponse(status_code=error.status_code, content=error_payload(request, error))


async def validation_error_handler(request: Request, error: RequestValidationError) -> JSONResponse:
    app_error = AppError(
        "VALIDATION_ERROR",
        "입력값을 확인해 주세요.",
        422,
        {"errors": error.errors()},
    )
    return JSONResponse(status_code=422, content=error_payload(request, app_error))
