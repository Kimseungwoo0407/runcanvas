from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.db.models import Course, GenerationJob, SavedPlace


class SavedPlaceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_owned(self, owner_id: str) -> list[SavedPlace]:
        return list(
            self.db.scalars(
                select(SavedPlace)
                .where(SavedPlace.owner_id == owner_id)
                .order_by(SavedPlace.created_at.asc())
            ).all()
        )

    def count_owned(self, owner_id: str) -> int:
        return int(
            self.db.scalar(select(func.count()).select_from(SavedPlace).where(SavedPlace.owner_id == owner_id)) or 0
        )

    def get_owned(self, place_id: str, owner_id: str) -> SavedPlace | None:
        return self.db.scalar(
            select(SavedPlace).where(SavedPlace.id == place_id, SavedPlace.owner_id == owner_id)
        )

    def create(
        self,
        *,
        owner_id: str,
        name: str,
        lat: float,
        lng: float,
        privacy_radius_m: int,
        prefer_riverside: bool,
        distances_km: list[float],
        shapes: list[str],
    ) -> SavedPlace:
        place = SavedPlace(
            owner_id=owner_id,
            name=name,
            lat=lat,
            lng=lng,
            privacy_radius_m=privacy_radius_m,
            prefer_riverside=prefer_riverside,
            distances_json=distances_km,
            shapes_json=shapes,
        )
        self.db.add(place)
        self.db.flush()
        return place

    def job_counts(self, place: SavedPlace) -> dict[str, int]:
        counts = {state: 0 for state in ("queued", "running", "succeeded", "failed", "cancelled")}
        if not place.precompute_batch_id:
            return counts
        rows = self.db.execute(
            select(GenerationJob.state, func.count())
            .where(
                GenerationJob.saved_place_id == place.id,
                GenerationJob.precompute_batch_id == place.precompute_batch_id,
            )
            .group_by(GenerationJob.state)
        ).all()
        for state, count in rows:
            if state in counts:
                counts[str(state)] = int(count)
        return counts

    def generated_course_count(self, place_id: str) -> int:
        return int(
            self.db.scalar(
                select(func.count())
                .select_from(Course)
                .where(Course.saved_place_id == place_id, Course.is_pregenerated.is_(True))
            )
            or 0
        )

    def cancel_active_jobs(self, place_id: str) -> None:
        now = datetime.now(UTC)
        self.db.execute(
            update(GenerationJob)
            .where(GenerationJob.saved_place_id == place_id, GenerationJob.state == "queued")
            .values(state="cancelled", progress=100, finished_at=now)
        )
        self.db.execute(
            update(GenerationJob)
            .where(GenerationJob.saved_place_id == place_id, GenerationJob.state == "running")
            .values(cancel_requested=True)
        )

    def unlink_courses(self, place_id: str) -> None:
        self.db.execute(
            update(Course)
            .where(Course.saved_place_id == place_id)
            .values(saved_place_id=None, preset_key=None)
        )
