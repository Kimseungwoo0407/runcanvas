from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import case, delete, select, update
from sqlalchemy.orm import Session, selectinload

from app.db.models import GenerationCandidate, GenerationJob


class JobRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def active_for_owner(self, owner_id: str) -> GenerationJob | None:
        return self.db.scalar(
            select(GenerationJob).where(
                GenerationJob.owner_id == owner_id,
                GenerationJob.state.in_(["queued", "running"]),
                GenerationJob.saved_place_id.is_(None),
            )
        )

    def create(
        self,
        owner_id: str,
        request_json: dict[str, object],
        cache_key: str,
        *,
        saved_place_id: str | None = None,
        precompute_batch_id: str | None = None,
    ) -> GenerationJob:
        job = GenerationJob(
            owner_id=owner_id,
            request_json=request_json,
            cache_key=cache_key,
            saved_place_id=saved_place_id,
            precompute_batch_id=precompute_batch_id,
        )
        self.db.add(job)
        self.db.flush()
        return job

    def get_owned(self, job_id: str, owner_id: str) -> GenerationJob | None:
        return self.db.scalar(
            select(GenerationJob)
            .options(selectinload(GenerationJob.candidates))
            .where(GenerationJob.id == job_id, GenerationJob.owner_id == owner_id)
        )

    def claim_next(self) -> GenerationJob | None:
        job = self.db.scalar(
            select(GenerationJob)
            .where(GenerationJob.state == "queued")
            .order_by(
                case((GenerationJob.saved_place_id.is_(None), 0), else_=1),
                GenerationJob.created_at.asc(),
            )
            .limit(1)
        )
        if job is None:
            return None
        job.state = "running"
        job.progress = 1
        job.started_at = datetime.now(UTC)
        self.db.flush()
        return job

    def replace_candidates(self, job: GenerationJob, candidates: list[dict[str, object]]) -> None:
        self.db.execute(delete(GenerationCandidate).where(GenerationCandidate.job_id == job.id))
        for rank, item in enumerate(candidates, start=1):
            self.db.add(GenerationCandidate(job_id=job.id, rank=rank, **item))

    def recover_stale_running(self, older_than_minutes: int = 5) -> int:
        threshold = datetime.now(UTC) - timedelta(minutes=older_than_minutes)
        result = self.db.execute(
            update(GenerationJob)
            .where(
                GenerationJob.state == "running",
                GenerationJob.started_at < threshold,
            )
            .values(state="queued", progress=0, started_at=None)
        )
        return int(getattr(result, "rowcount", 0) or 0)
