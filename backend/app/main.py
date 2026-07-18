from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.db.models import Base
from app.db.session import engine
from app.errors import AppError, app_error_handler, validation_error_handler
from app.logging import configure_logging
from app.middleware import RequestContextMiddleware
from app.routers import admin, ai, auth, courses, generation, geocoding, health, me, routes, saved_places

configure_logging()
logger = structlog.get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    if settings.APP_ENV != "production":
        Base.metadata.create_all(engine)
    logger.info("application_started", environment=settings.APP_ENV)
    yield
    engine.dispose()


app = FastAPI(
    title="RunCanvas API",
    version="1.0.0",
    description="AI GPS art running course generation backend",
    lifespan=lifespan,
)
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID", "Content-Disposition"],
)
app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore[arg-type]


@app.exception_handler(Exception)
async def unhandled_error(request: Request, error: Exception) -> JSONResponse:
    logger.exception("unhandled_error", path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_ERROR",
            "message": "서버 내부 오류가 발생했습니다.",
            "details": {},
            "requestId": getattr(request.state, "request_id", None),
        },
    )


for router in [
    auth.router,
    me.router,
    saved_places.router,
    generation.router,
    routes.router,
    courses.router,
    health.router,
    geocoding.router,
    ai.router,
    admin.router,
]:
    app.include_router(router, prefix="/api/v1")
