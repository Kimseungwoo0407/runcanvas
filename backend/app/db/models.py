from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(UTC)


def new_id() -> str:
    return str(uuid4())


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    username: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(16), default="user", index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    settings_json: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        default=lambda: {
            "defaultPaceMinPerKm": 6.0,
            "distanceUnit": "km",
            "mapTheme": "default",
            "showSourceShape": True,
        },
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    courses: Mapped[list[Course]] = relationship(back_populates="owner", cascade="all, delete")
    saved_places: Mapped[list[SavedPlace]] = relationship(cascade="all, delete-orphan")


class InviteCode(Base):
    __tablename__ = "invite_codes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    code_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    max_uses: Mapped[int] = mapped_column(Integer, default=1)
    used_count: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SavedPlace(Base):
    __tablename__ = "saved_places"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(80))
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    privacy_radius_m: Mapped[int] = mapped_column(Integer, default=250)
    prefer_riverside: Mapped[bool] = mapped_column(Boolean, default=False)
    distances_json: Mapped[list[float]] = mapped_column(JSON, default=lambda: [3.0, 5.0, 7.0, 10.0])
    shapes_json: Mapped[list[str]] = mapped_column(JSON, default=lambda: ["circle", "heart", "star"])
    precompute_batch_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    precompute_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    shape_type: Mapped[str] = mapped_column(String(24), index=True)
    target_distance_m: Mapped[float] = mapped_column(Float)
    actual_distance_m: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(16), default="ready", index=True)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    share_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    share_token: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    saved_place_id: Mapped[str | None] = mapped_column(
        ForeignKey("saved_places.id", ondelete="SET NULL"), nullable=True, index=True
    )
    is_pregenerated: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    preset_key: Mapped[str | None] = mapped_column(String(160), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    owner: Mapped[User] = relationship(back_populates="courses")
    geometry: Mapped[CourseGeometry] = relationship(
        back_populates="course", cascade="all, delete-orphan", uselist=False
    )
    metrics: Mapped[CourseMetric] = relationship(back_populates="course", cascade="all, delete-orphan", uselist=False)


class CourseGeometry(Base):
    __tablename__ = "course_geometries"

    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True)
    source_shape_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    waypoints_json: Mapped[list[list[float]]] = mapped_column(JSON)
    route_geojson: Mapped[dict[str, Any]] = mapped_column(JSON)
    bbox_json: Mapped[list[float]] = mapped_column(JSON)

    course: Mapped[Course] = relationship(back_populates="geometry")


class CourseMetric(Base):
    __tablename__ = "course_metrics"

    course_id: Mapped[str] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True)
    shape_score: Mapped[float] = mapped_column(Float)
    distance_score: Mapped[float] = mapped_column(Float)
    closure_score: Mapped[float] = mapped_column(Float)
    overlap_ratio: Mapped[float] = mapped_column(Float)
    simplicity_score: Mapped[float] = mapped_column(Float)
    total_score: Mapped[float] = mapped_column(Float)
    waypoint_count: Mapped[int] = mapped_column(Integer)
    duration_s: Mapped[float] = mapped_column(Float)
    ascend_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    descend_m: Mapped[float | None] = mapped_column(Float, nullable=True)

    course: Mapped[Course] = relationship(back_populates="metrics")


class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    request_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    cache_key: Mapped[str] = mapped_column(String(64), index=True)
    state: Mapped[str] = mapped_column(String(16), default="queued", index=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    saved_place_id: Mapped[str | None] = mapped_column(
        ForeignKey("saved_places.id", ondelete="SET NULL"), nullable=True, index=True
    )
    precompute_batch_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    candidates: Mapped[list[GenerationCandidate]] = relationship(
        back_populates="job", cascade="all, delete-orphan", order_by="GenerationCandidate.rank"
    )


class GenerationCandidate(Base):
    __tablename__ = "generation_candidates"
    __table_args__ = (UniqueConstraint("job_id", "rank", name="uq_candidate_job_rank"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    job_id: Mapped[str] = mapped_column(ForeignKey("generation_jobs.id", ondelete="CASCADE"), index=True)
    rank: Mapped[int] = mapped_column(Integer)
    rotation_deg: Mapped[float] = mapped_column(Float)
    scale_m: Mapped[float] = mapped_column(Float)
    source_shape_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    waypoints_json: Mapped[list[list[float]]] = mapped_column(JSON)
    route_geojson: Mapped[dict[str, Any]] = mapped_column(JSON)
    snapped_points_json: Mapped[list[list[float]]] = mapped_column(JSON)
    metrics_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    job: Mapped[GenerationJob] = relationship(back_populates="candidates")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SystemSetting(Base):
    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(120), primary_key=True)
    value_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class GeocodingCache(Base):
    __tablename__ = "geocoding_cache"

    query_key: Mapped[str] = mapped_column(String(255), primary_key=True)
    response_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
