from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.db.models import Course, CourseGeometry, CourseMetric


def _as_float(value: object) -> float:
    if isinstance(value, (int, float, str)):
        return float(value)
    raise ValueError("metric must be numeric")


def _as_int(value: object) -> int:
    if isinstance(value, (int, float, str)):
        return int(value)
    raise ValueError("metric must be numeric")


class CourseRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_owned(self, course_id: str, owner_id: str) -> Course | None:
        return self.db.scalar(
            select(Course)
            .options(joinedload(Course.geometry), joinedload(Course.metrics))
            .where(Course.id == course_id, Course.owner_id == owner_id)
        )

    def get_shared(self, token: str) -> Course | None:
        return self.db.scalar(
            select(Course)
            .options(joinedload(Course.geometry), joinedload(Course.metrics))
            .where(Course.share_enabled.is_(True), Course.share_token == token)
        )

    def list_owned(
        self,
        owner_id: str,
        *,
        limit: int,
        cursor: str | None,
        query: str | None,
        favorite: bool | None,
    ) -> list[Course]:
        statement = (
            select(Course)
            .options(joinedload(Course.metrics))
            .where(Course.owner_id == owner_id)
            .order_by(Course.created_at.desc(), Course.id.desc())
            .limit(limit + 1)
        )
        if cursor:
            cursor_course = self.db.get(Course, cursor)
            if cursor_course and cursor_course.owner_id == owner_id:
                statement = statement.where(
                    or_(
                        Course.created_at < cursor_course.created_at,
                        (Course.created_at == cursor_course.created_at) & (Course.id < cursor_course.id),
                    )
                )
        if query:
            statement = statement.where(Course.name.ilike(f"%{query}%"))
        if favorite is not None:
            statement = statement.where(Course.is_favorite == favorite)
        return list(self.db.scalars(statement).unique().all())

    def create(
        self,
        *,
        owner_id: str,
        name: str,
        shape_type: str,
        target_distance_m: float,
        actual_distance_m: float,
        source_shape: dict[str, object],
        waypoints: list[list[float]],
        route: dict[str, object],
        bbox: list[float],
        metrics: dict[str, object],
        saved_place_id: str | None = None,
        is_pregenerated: bool = False,
        preset_key: str | None = None,
    ) -> Course:
        course = Course(
            owner_id=owner_id,
            name=name,
            shape_type=shape_type,
            target_distance_m=target_distance_m,
            actual_distance_m=actual_distance_m,
            saved_place_id=saved_place_id,
            is_pregenerated=is_pregenerated,
            preset_key=preset_key,
        )
        course.geometry = CourseGeometry(
            source_shape_json=source_shape,
            waypoints_json=waypoints,
            route_geojson=route,
            bbox_json=bbox,
        )
        course.metrics = CourseMetric(
            shape_score=_as_float(metrics["shapeScore"]),
            distance_score=_as_float(metrics["distanceScore"]),
            closure_score=_as_float(metrics["closureScore"]),
            overlap_ratio=_as_float(metrics["overlapRatio"]),
            simplicity_score=_as_float(metrics["simplicityScore"]),
            total_score=_as_float(metrics["totalScore"]),
            waypoint_count=_as_int(metrics["waypointCount"]),
            duration_s=_as_float(metrics["durationS"]),
            ascend_m=_as_float(metrics["ascendM"]) if metrics.get("ascendM") is not None else None,
            descend_m=(_as_float(metrics["descendM"]) if metrics.get("descendM") is not None else None),
        )
        self.db.add(course)
        self.db.flush()
        return course

    def upsert_pregenerated(
        self,
        *,
        owner_id: str,
        saved_place_id: str,
        preset_key: str,
        name: str,
        shape_type: str,
        target_distance_m: float,
        actual_distance_m: float,
        source_shape: dict[str, object],
        waypoints: list[list[float]],
        route: dict[str, object],
        bbox: list[float],
        metrics: dict[str, object],
    ) -> Course:
        course = self.db.scalar(
            select(Course)
            .options(joinedload(Course.geometry), joinedload(Course.metrics))
            .where(Course.owner_id == owner_id, Course.preset_key == preset_key)
        )
        if course is None:
            return self.create(
                owner_id=owner_id,
                name=name,
                shape_type=shape_type,
                target_distance_m=target_distance_m,
                actual_distance_m=actual_distance_m,
                source_shape=source_shape,
                waypoints=waypoints,
                route=route,
                bbox=bbox,
                metrics=metrics,
                saved_place_id=saved_place_id,
                is_pregenerated=True,
                preset_key=preset_key,
            )
        course.name = name
        course.shape_type = shape_type
        course.target_distance_m = target_distance_m
        course.actual_distance_m = actual_distance_m
        course.saved_place_id = saved_place_id
        course.is_pregenerated = True
        course.status = "ready"
        course.updated_at = datetime.now(UTC)
        course.geometry.source_shape_json = source_shape
        course.geometry.waypoints_json = waypoints
        course.geometry.route_geojson = route
        course.geometry.bbox_json = bbox
        course.metrics.shape_score = _as_float(metrics["shapeScore"])
        course.metrics.distance_score = _as_float(metrics["distanceScore"])
        course.metrics.closure_score = _as_float(metrics["closureScore"])
        course.metrics.overlap_ratio = _as_float(metrics["overlapRatio"])
        course.metrics.simplicity_score = _as_float(metrics["simplicityScore"])
        course.metrics.total_score = _as_float(metrics["totalScore"])
        course.metrics.waypoint_count = _as_int(metrics["waypointCount"])
        course.metrics.duration_s = _as_float(metrics["durationS"])
        course.metrics.ascend_m = _as_float(metrics["ascendM"]) if metrics.get("ascendM") is not None else None
        course.metrics.descend_m = _as_float(metrics["descendM"]) if metrics.get("descendM") is not None else None
        self.db.flush()
        return course
