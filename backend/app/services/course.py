from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import GenerationCandidate, GenerationJob
from app.errors import AppError
from app.repositories.courses import CourseRepository
from app.schemas.course import (
    CourseCreateRequest,
    CourseDetail,
    CourseListResponse,
    CoursePatchRequest,
    CourseSummary,
)
from app.schemas.generation import CandidateMetrics
from app.security import new_share_token
from app.services.gpx import build_gpx


def _bbox(coordinates: list[list[float]]) -> list[float]:
    lngs = [point[0] for point in coordinates]
    lats = [point[1] for point in coordinates]
    return [min(lngs), min(lats), max(lngs), max(lats)]


def _summary(course: Any) -> CourseSummary:
    return CourseSummary(
        id=course.id,
        name=course.name,
        shape_type=course.shape_type,
        target_distance_m=course.target_distance_m,
        actual_distance_m=course.actual_distance_m,
        status=course.status,
        is_favorite=course.is_favorite,
        share_enabled=course.share_enabled,
        saved_place_id=course.saved_place_id,
        is_pregenerated=course.is_pregenerated,
        total_score=course.metrics.total_score,
        created_at=course.created_at,
        updated_at=course.updated_at,
    )


def _metrics_model(course: Any) -> CandidateMetrics:
    metrics = course.metrics
    return CandidateMetrics(
        distance_m=course.actual_distance_m,
        duration_s=metrics.duration_s,
        shape_score=metrics.shape_score,
        distance_score=metrics.distance_score,
        closure_score=metrics.closure_score,
        overlap_ratio=metrics.overlap_ratio,
        simplicity_score=metrics.simplicity_score,
        total_score=metrics.total_score,
        waypoint_count=metrics.waypoint_count,
        max_snap_distance_m=0,
        ascend_m=metrics.ascend_m,
        descend_m=metrics.descend_m,
    )


def course_detail(course: Any, *, include_share_token: bool = True) -> CourseDetail:
    return CourseDetail(
        **_summary(course).model_dump(),
        owner_id=course.owner_id,
        share_token=course.share_token if include_share_token else None,
        source_shape=course.geometry.source_shape_json,
        waypoints=course.geometry.waypoints_json,
        route=course.geometry.route_geojson,
        bbox=course.geometry.bbox_json,
        metrics=_metrics_model(course),
    )


class CourseService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = CourseRepository(db)

    def create(self, owner_id: str, request: CourseCreateRequest) -> CourseDetail:
        if request.candidate_id:
            candidate = self.db.scalar(
                select(GenerationCandidate)
                .join(GenerationJob)
                .where(
                    GenerationCandidate.id == request.candidate_id,
                    GenerationJob.owner_id == owner_id,
                    GenerationJob.state == "succeeded",
                )
            )
            if candidate is None:
                raise AppError("FORBIDDEN", "저장할 수 없는 후보입니다.", 403)
            job = self.db.get(GenerationJob, candidate.job_id)
            if job is None:
                raise AppError("NO_ROUTE_FOUND", "후보의 생성 작업을 찾을 수 없습니다.", 404)
            shape_type = str(job.request_json["shapeType"])
            target_distance_m = float(job.request_json["targetDistanceKm"]) * 1000
            source_shape = candidate.source_shape_json
            waypoints = candidate.waypoints_json
            route = candidate.route_geojson
            metrics = candidate.metrics_json
        else:
            assert request.shape_type is not None
            assert request.target_distance_m is not None
            assert request.source_shape is not None
            assert request.waypoints is not None
            assert request.route is not None
            assert request.metrics is not None
            shape_type = request.shape_type
            target_distance_m = request.target_distance_m
            source_shape = request.source_shape
            waypoints = request.waypoints
            route = request.route.model_dump(by_alias=True)
            metrics = request.metrics.model_dump(by_alias=True)
        coordinates = route["coordinates"]
        course = self.repository.create(
            owner_id=owner_id,
            name=request.name.strip(),
            shape_type=shape_type,
            target_distance_m=target_distance_m,
            actual_distance_m=float(metrics["distanceM"]),
            source_shape=source_shape,
            waypoints=waypoints,
            route=route,
            bbox=_bbox(coordinates),
            metrics=metrics,
        )
        self.db.commit()
        return course_detail(course)

    def list(
        self,
        owner_id: str,
        *,
        limit: int,
        cursor: str | None,
        query: str | None,
        favorite: bool | None,
    ) -> CourseListResponse:
        rows = self.repository.list_owned(owner_id, limit=limit, cursor=cursor, query=query, favorite=favorite)
        has_more = len(rows) > limit
        items = rows[:limit]
        return CourseListResponse(
            items=[_summary(course) for course in items],
            next_cursor=items[-1].id if has_more and items else None,
        )

    def get(self, owner_id: str, course_id: str) -> CourseDetail:
        course = self.repository.get_owned(course_id, owner_id)
        if course is None:
            raise AppError("FORBIDDEN", "코스에 접근할 수 없습니다.", 403)
        return course_detail(course)

    def get_shared(self, token: str) -> CourseDetail:
        course = self.repository.get_shared(token)
        if course is None:
            raise AppError("FORBIDDEN", "공유 코스를 찾을 수 없습니다.", 404)
        return course_detail(course, include_share_token=False)

    def patch(self, owner_id: str, course_id: str, request: CoursePatchRequest) -> CourseDetail:
        course = self.repository.get_owned(course_id, owner_id)
        if course is None:
            raise AppError("FORBIDDEN", "코스에 접근할 수 없습니다.", 403)
        if request.name is not None:
            course.name = request.name.strip()
        if request.is_favorite is not None:
            course.is_favorite = request.is_favorite
        if request.status is not None:
            course.status = request.status
        if request.share_enabled is not None:
            course.share_enabled = request.share_enabled
            if request.share_enabled and not course.share_token:
                course.share_token = new_share_token()
            if not request.share_enabled:
                course.share_token = None
        self.db.commit()
        return course_detail(course)

    def delete(self, owner_id: str, course_id: str) -> None:
        course = self.repository.get_owned(course_id, owner_id)
        if course is None:
            raise AppError("FORBIDDEN", "코스에 접근할 수 없습니다.", 403)
        self.db.delete(course)
        self.db.commit()

    def _clone_course(self, owner_id: str, original: Any) -> CourseDetail:
        metrics = _metrics_model(original).model_dump(by_alias=True)
        clone = self.repository.create(
            owner_id=owner_id,
            name=f"{original.name} 복사본",
            shape_type=original.shape_type,
            target_distance_m=original.target_distance_m,
            actual_distance_m=original.actual_distance_m,
            source_shape=original.geometry.source_shape_json,
            waypoints=original.geometry.waypoints_json,
            route=original.geometry.route_geojson,
            bbox=original.geometry.bbox_json,
            metrics=metrics,
        )
        self.db.commit()
        return course_detail(clone)

    def clone(self, owner_id: str, course_id: str) -> CourseDetail:
        original = self.repository.get_owned(course_id, owner_id)
        if original is None:
            raise AppError("FORBIDDEN", "코스에 접근할 수 없습니다.", 403)
        return self._clone_course(owner_id, original)

    def clone_shared(self, owner_id: str, token: str) -> CourseDetail:
        original = self.repository.get_shared(token)
        if original is None:
            raise AppError("FORBIDDEN", "공유 코스를 찾을 수 없습니다.", 404)
        return self._clone_course(owner_id, original)

    def gpx(self, owner_id: str, course_id: str) -> tuple[str, str]:
        course = self.repository.get_owned(course_id, owner_id)
        if course is None:
            raise AppError("FORBIDDEN", "코스에 접근할 수 없습니다.", 403)
        safe_id = course.id.replace("-", "")[:12]
        filename = f"runcanvas-{safe_id}.gpx"
        content = build_gpx(
            name=course.name,
            coordinates=course.geometry.route_geojson["coordinates"],
            waypoints=course.geometry.waypoints_json,
            created_at=course.created_at,
        )
        return filename, content
