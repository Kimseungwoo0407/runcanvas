from __future__ import annotations

import hashlib
import math
from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from sqlalchemy.orm import Session

from app.config import Settings
from app.db.models import SavedPlace
from app.errors import AppError
from app.regions import region_for_point, supported_region_details
from app.repositories.jobs import JobRepository
from app.repositories.saved_places import SavedPlaceRepository
from app.schemas.common import LngLatModel
from app.schemas.generation import GenerationRequest, RoutePreferences
from app.schemas.saved_place import (
    PrecomputeShape,
    PrecomputeStatus,
    SavedPlaceCreateRequest,
    SavedPlaceListResponse,
    SavedPlacePatchRequest,
    SavedPlaceResponse,
)
from app.services.generation import cache_key


class SavedPlaceService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings
        self.repository = SavedPlaceRepository(db)
        self.jobs = JobRepository(db)

    def _validate_location(self, location: LngLatModel) -> None:
        if region_for_point(location.lng, location.lat) is None:
            raise AppError(
                "OUTSIDE_SUPPORTED_AREA",
                "현재 지원 지역은 서울과 청주입니다.",
                422,
                {"supportedRegions": supported_region_details()},
            )

    def _response(self, place: SavedPlace) -> SavedPlaceResponse:
        counts = self.repository.job_counts(place)
        return SavedPlaceResponse(
            id=place.id,
            name=place.name,
            location=LngLatModel(lng=place.lng, lat=place.lat),
            privacy_radius_m=place.privacy_radius_m,
            prefer_riverside=place.prefer_riverside,
            distances_km=[float(value) for value in place.distances_json],
            shapes=cast(list[PrecomputeShape], place.shapes_json),
            precompute_requested_at=place.precompute_requested_at,
            status=PrecomputeStatus(
                total=sum(counts.values()),
                queued=counts["queued"],
                running=counts["running"],
                succeeded=counts["succeeded"],
                failed=counts["failed"],
                cancelled=counts["cancelled"],
                generated_courses=self.repository.generated_course_count(place.id),
            ),
            created_at=place.created_at,
            updated_at=place.updated_at,
        )

    def _offset_start(self, place: SavedPlace, shape: str, distance_km: float) -> LngLatModel:
        seed = hashlib.sha256(f"{place.id}:{shape}:{distance_km:g}".encode()).digest()
        angle = int.from_bytes(seed[:8]) / (2**64 - 1) * math.tau
        radius = float(place.privacy_radius_m)
        lat = place.lat + math.sin(angle) * radius / 111_320
        lng_scale = max(0.2, math.cos(math.radians(place.lat)))
        lng = place.lng + math.cos(angle) * radius / (111_320 * lng_scale)
        region = region_for_point(place.lng, place.lat)
        if region is None:
            raise AppError("OUTSIDE_SUPPORTED_AREA", "현재 지원 지역은 서울과 청주입니다.", 422)
        min_lng, min_lat, max_lng, max_lat = region.bbox
        return LngLatModel(
            lng=max(min_lng + 0.00001, min(max_lng - 0.00001, lng)),
            lat=max(min_lat + 0.00001, min(max_lat - 0.00001, lat)),
        )

    def _enqueue(self, place: SavedPlace) -> None:
        self.repository.cancel_active_jobs(place.id)
        batch_id = str(uuid4())
        place.precompute_batch_id = batch_id
        place.precompute_requested_at = datetime.now(UTC)
        region = region_for_point(place.lng, place.lat)
        if region is None:
            raise AppError("OUTSIDE_SUPPORTED_AREA", "현재 지원 지역은 서울과 청주입니다.", 422)
        for distance_km in place.distances_json:
            for shape in place.shapes_json:
                request = GenerationRequest(
                    region=region.code,
                    start=self._offset_start(place, shape, float(distance_km)),
                    shape_type=cast(PrecomputeShape, shape),
                    target_distance_km=float(distance_km),
                    distance_tolerance_pct=15,
                    preferences=RoutePreferences(
                        avoid_major_roads=True,
                        prefer_footways=place.prefer_riverside,
                        prefer_riverside=place.prefer_riverside,
                    ),
                    max_candidates=1,
                )
                self.jobs.create(
                    place.owner_id,
                    request.model_dump(by_alias=True),
                    cache_key(request),
                    saved_place_id=place.id,
                    precompute_batch_id=batch_id,
                )

    def list(self, owner_id: str) -> SavedPlaceListResponse:
        return SavedPlaceListResponse(items=[self._response(place) for place in self.repository.list_owned(owner_id)])

    def create(self, owner_id: str, request: SavedPlaceCreateRequest) -> SavedPlaceResponse:
        if self.repository.count_owned(owner_id) >= 5:
            raise AppError("VALIDATION_ERROR", "저장 장소는 최대 5개까지 등록할 수 있습니다.", 422)
        self._validate_location(request.location)
        place = self.repository.create(
            owner_id=owner_id,
            name=request.name.strip(),
            lat=request.location.lat,
            lng=request.location.lng,
            privacy_radius_m=request.privacy_radius_m,
            prefer_riverside=request.prefer_riverside,
            distances_km=request.distances_km,
            shapes=list(request.shapes),
        )
        self._enqueue(place)
        self.db.commit()
        return self._response(place)

    def update(self, owner_id: str, place_id: str, request: SavedPlacePatchRequest) -> SavedPlaceResponse:
        place = self.repository.get_owned(place_id, owner_id)
        if place is None:
            raise AppError("FORBIDDEN", "저장 장소에 접근할 수 없습니다.", 403)
        generation_changed = False
        if request.name is not None:
            place.name = request.name.strip()
        if request.location is not None:
            self._validate_location(request.location)
            generation_changed = (place.lat, place.lng) != (request.location.lat, request.location.lng)
            place.lat = request.location.lat
            place.lng = request.location.lng
        if request.privacy_radius_m is not None:
            generation_changed = generation_changed or place.privacy_radius_m != request.privacy_radius_m
            place.privacy_radius_m = request.privacy_radius_m
        if request.prefer_riverside is not None:
            generation_changed = generation_changed or place.prefer_riverside != request.prefer_riverside
            place.prefer_riverside = request.prefer_riverside
        if request.distances_km is not None:
            generation_changed = generation_changed or place.distances_json != request.distances_km
            place.distances_json = request.distances_km
        if request.shapes is not None:
            shapes = list(request.shapes)
            generation_changed = generation_changed or place.shapes_json != shapes
            place.shapes_json = [str(shape) for shape in shapes]
        if generation_changed:
            self._enqueue(place)
        self.db.commit()
        return self._response(place)

    def precompute(self, owner_id: str, place_id: str) -> SavedPlaceResponse:
        place = self.repository.get_owned(place_id, owner_id)
        if place is None:
            raise AppError("FORBIDDEN", "저장 장소에 접근할 수 없습니다.", 403)
        self._enqueue(place)
        self.db.commit()
        return self._response(place)

    def delete(self, owner_id: str, place_id: str) -> None:
        place = self.repository.get_owned(place_id, owner_id)
        if place is None:
            raise AppError("FORBIDDEN", "저장 장소에 접근할 수 없습니다.", 403)
        self.repository.cancel_active_jobs(place.id)
        self.repository.unlink_courses(place.id)
        self.db.delete(place)
        self.db.commit()
