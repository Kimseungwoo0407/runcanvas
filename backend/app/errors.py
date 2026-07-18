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


def _serializable_validation_errors(error: RequestValidationError) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for item in error.errors():
        cleaned = dict(item)
        if context := cleaned.get("ctx"):
            cleaned["ctx"] = {key: str(value) for key, value in context.items()}
        errors.append(cleaned)
    return errors


def _validation_message(error: RequestValidationError) -> str:
    first = error.errors()[0] if error.errors() else {}
    location = first.get("loc", ())
    field = str(location[-1]) if location else ""
    messages = {
        "username": "사용자명은 영문자, 숫자, 마침표(.), 하이픈(-), 밑줄(_)만 사용해 3~40자로 입력해 주세요.",
        "password": "비밀번호는 8~128자로 입력해 주세요.",
        "invite_code": "초대 코드는 8~64자로 입력해 주세요.",
        "inviteCode": "초대 코드는 8~64자로 입력해 주세요.",
        "region": "지역은 서울 또는 청주 중에서 선택해 주세요.",
    }
    return messages.get(field, "입력값을 확인해 주세요.")


async def validation_error_handler(request: Request, error: RequestValidationError) -> JSONResponse:
    app_error = AppError(
        "VALIDATION_ERROR",
        _validation_message(error),
        422,
        {"errors": _serializable_validation_errors(error)},
    )
    return JSONResponse(status_code=422, content=error_payload(request, app_error))
