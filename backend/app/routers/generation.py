from __future__ import annotations

from fastapi import APIRouter, status

from app.dependencies import DB, CurrentUser, SettingsDep
from app.schemas.generation import (
    CandidateListResponse,
    GenerationJobResponse,
    GenerationRequest,
)
from app.services.generation import GenerationService

router = APIRouter(prefix="/generation-jobs", tags=["generation"])


@router.post("", response_model=GenerationJobResponse, status_code=status.HTTP_202_ACCEPTED)
def create_job(
    request: GenerationRequest,
    user: CurrentUser,
    db: DB,
    settings: SettingsDep,
) -> GenerationJobResponse:
    return GenerationService(db, settings).create(user.id, request)


@router.get("/{job_id}", response_model=GenerationJobResponse)
def get_job(job_id: str, user: CurrentUser, db: DB, settings: SettingsDep) -> GenerationJobResponse:
    return GenerationService(db, settings).get(user.id, job_id)


@router.post("/{job_id}/cancel", response_model=GenerationJobResponse)
def cancel_job(job_id: str, user: CurrentUser, db: DB, settings: SettingsDep) -> GenerationJobResponse:
    return GenerationService(db, settings).cancel(user.id, job_id)


@router.get("/{job_id}/candidates", response_model=CandidateListResponse)
def get_candidates(
    job_id: str,
    user: CurrentUser,
    db: DB,
    settings: SettingsDep,
) -> CandidateListResponse:
    return GenerationService(db, settings).candidates(user.id, job_id)
