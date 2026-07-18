from __future__ import annotations

import asyncio
import signal
import time
from datetime import UTC, datetime
from typing import cast

import structlog
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import Base, GenerationJob, SavedPlace
from app.db.session import SessionLocal, engine
from app.errors import AppError
from app.repositories.courses import CourseRepository
from app.repositories.jobs import JobRepository
from app.schemas.generation import GenerationRequest
from app.services.optimization.optimizer import optimize_candidates
from app.services.routing.factory import get_routing_provider

logger = structlog.get_logger()
stop_requested = False

SHAPE_NAMES = {
    "circle": "원",
    "heart": "하트",
    "star": "별",
    "square": "사각형",
    "dog": "강아지",
    "cat": "고양이",
}


def route_bbox(coordinates: list[list[float]]) -> list[float]:
    lngs = [point[0] for point in coordinates]
    lats = [point[1] for point in coordinates]
    return [min(lngs), min(lats), max(lngs), max(lats)]


def save_pregenerated_course(db: Session, job: GenerationJob, candidate: dict[str, object]) -> None:
    if not job.saved_place_id or not job.precompute_batch_id:
        return
    place = db.get(SavedPlace, job.saved_place_id)
    if place is None or place.precompute_batch_id != job.precompute_batch_id:
        return
    shape_type = str(job.request_json["shapeType"])
    distance_km = float(job.request_json["targetDistanceKm"])
    source_shape = cast(dict[str, object], candidate["source_shape_json"])
    waypoints = cast(list[list[float]], candidate["waypoints_json"])
    route = cast(dict[str, object], candidate["route_geojson"])
    coordinates = cast(list[list[float]], route["coordinates"])
    metrics = cast(dict[str, object], candidate["metrics_json"])
    CourseRepository(db).upsert_pregenerated(
        owner_id=job.owner_id,
        saved_place_id=place.id,
        preset_key=f"{place.id}:{shape_type}:{distance_km:g}",
        name=f"{place.name} · {distance_km:g}km {SHAPE_NAMES.get(shape_type, shape_type)}",
        shape_type=shape_type,
        target_distance_m=distance_km * 1000,
        actual_distance_m=cast(float, metrics["distanceM"]),
        source_shape=source_shape,
        waypoints=waypoints,
        route=route,
        bbox=route_bbox(coordinates),
        metrics=metrics,
    )


def request_stop(*_: object) -> None:
    global stop_requested
    stop_requested = True


async def process_job(job_id: str) -> None:
    settings = get_settings()
    provider = get_routing_provider()

    async def progress(value: int) -> None:
        with SessionLocal() as db:
            job = db.get(GenerationJob, job_id)
            if job and job.state == "running":
                job.progress = max(job.progress, value)
                db.commit()

    async def cancelled() -> bool:
        with SessionLocal() as db:
            job = db.get(GenerationJob, job_id)
            return bool(job is None or job.cancel_requested or job.state == "cancelled")

    with SessionLocal() as db:
        job = db.get(GenerationJob, job_id)
        if job is None:
            return
        request = GenerationRequest.model_validate(job.request_json)

    try:
        candidates = await optimize_candidates(
            request,
            provider,
            settings,
            progress_callback=progress,
            cancel_callback=cancelled,
        )
        candidate_rows: list[dict[str, object]] = []
        for candidate in candidates:
            candidate_rows.append(
                {
                    "rotation_deg": candidate.rotation_deg,
                    "scale_m": candidate.scale_m,
                    "source_shape_json": {
                        "type": "LineString",
                        "coordinates": [[x, y] for x, y in candidate.source_shape],
                    },
                    "waypoints_json": [[point.lng, point.lat] for point in candidate.waypoints],
                    "route_geojson": {
                        "type": "LineString",
                        "coordinates": candidate.route.coordinates,
                    },
                    "snapped_points_json": [[point.lng, point.lat] for point in candidate.route.snapped_points],
                    "metrics_json": candidate.metrics.to_api_dict(),
                }
            )
        with SessionLocal() as db:
            repository = JobRepository(db)
            job = db.get(GenerationJob, job_id)
            if job is None:
                return
            if job.cancel_requested:
                job.state = "cancelled"
            else:
                repository.replace_candidates(job, candidate_rows)
                save_pregenerated_course(db, job, candidate_rows[0])
                job.state = "succeeded"
            job.progress = 100
            job.finished_at = datetime.now(UTC)
            db.commit()
    except AppError as error:
        with SessionLocal() as db:
            job = db.get(GenerationJob, job_id)
            if job:
                job.state = "cancelled" if error.code == "JOB_CANCELLED" else "failed"
                job.error_code = error.code
                job.error_message = error.message
                job.progress = 100
                job.finished_at = datetime.now(UTC)
                db.commit()
        logger.warning("generation_failed", job_id=job_id, error_code=error.code)
    except Exception:
        with SessionLocal() as db:
            job = db.get(GenerationJob, job_id)
            if job:
                job.state = "failed"
                job.error_code = "INTERNAL_ERROR"
                job.error_message = "코스 생성 중 내부 오류가 발생했습니다."
                job.progress = 100
                job.finished_at = datetime.now(UTC)
                db.commit()
        logger.exception("generation_crashed", job_id=job_id)


def main() -> None:
    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    settings = get_settings()
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        recovered = JobRepository(db).recover_stale_running()
        db.commit()
    if recovered:
        print({"recoveredJobs": recovered})
    while not stop_requested:
        with SessionLocal() as db:
            repository = JobRepository(db)
            job = repository.claim_next()
            db.commit()
            job_id = job.id if job else None
        if job_id:
            asyncio.run(process_job(job_id))
        else:
            time.sleep(settings.WORKER_POLL_SECONDS)


if __name__ == "__main__":
    main()
