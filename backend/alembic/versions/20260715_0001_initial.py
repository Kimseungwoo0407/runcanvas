"""Initial RunCanvas schema.

Revision ID: 20260715_0001
Revises:
Create Date: 2026-07-15
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260715_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("username", sa.String(40), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("settings_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("username"),
    )
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_is_active", "users", ["is_active"])

    op.create_table(
        "invite_codes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("max_uses", sa.Integer(), nullable=False),
        sa.Column("used_count", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("code_hash"),
    )
    op.create_index("ix_invite_codes_code_hash", "invite_codes", ["code_hash"])

    op.create_table(
        "courses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("shape_type", sa.String(24), nullable=False),
        sa.Column("target_distance_m", sa.Float(), nullable=False),
        sa.Column("actual_distance_m", sa.Float(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("is_favorite", sa.Boolean(), nullable=False),
        sa.Column("share_enabled", sa.Boolean(), nullable=False),
        sa.Column("share_token", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("share_token"),
    )
    for name in ["owner_id", "shape_type", "status", "is_favorite", "created_at"]:
        op.create_index(f"ix_courses_{name}", "courses", [name])

    op.create_table(
        "course_geometries",
        sa.Column("course_id", sa.String(36), sa.ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("source_shape_json", sa.JSON(), nullable=False),
        sa.Column("waypoints_json", sa.JSON(), nullable=False),
        sa.Column("route_geojson", sa.JSON(), nullable=False),
        sa.Column("bbox_json", sa.JSON(), nullable=False),
    )
    op.create_table(
        "course_metrics",
        sa.Column("course_id", sa.String(36), sa.ForeignKey("courses.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("shape_score", sa.Float(), nullable=False),
        sa.Column("distance_score", sa.Float(), nullable=False),
        sa.Column("closure_score", sa.Float(), nullable=False),
        sa.Column("overlap_ratio", sa.Float(), nullable=False),
        sa.Column("simplicity_score", sa.Float(), nullable=False),
        sa.Column("total_score", sa.Float(), nullable=False),
        sa.Column("waypoint_count", sa.Integer(), nullable=False),
        sa.Column("duration_s", sa.Float(), nullable=False),
        sa.Column("ascend_m", sa.Float(), nullable=True),
        sa.Column("descend_m", sa.Float(), nullable=True),
    )

    op.create_table(
        "generation_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("request_json", sa.JSON(), nullable=False),
        sa.Column("cache_key", sa.String(64), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("error_code", sa.String(64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("cancel_requested", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    for name in ["owner_id", "cache_key", "state", "created_at"]:
        op.create_index(f"ix_generation_jobs_{name}", "generation_jobs", [name])

    op.create_table(
        "generation_candidates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("job_id", sa.String(36), sa.ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("rotation_deg", sa.Float(), nullable=False),
        sa.Column("scale_m", sa.Float(), nullable=False),
        sa.Column("source_shape_json", sa.JSON(), nullable=False),
        sa.Column("waypoints_json", sa.JSON(), nullable=False),
        sa.Column("route_geojson", sa.JSON(), nullable=False),
        sa.Column("snapped_points_json", sa.JSON(), nullable=False),
        sa.Column("metrics_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("job_id", "rank", name="uq_candidate_job_rank"),
    )
    op.create_index("ix_generation_candidates_job_id", "generation_candidates", ["job_id"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"])

    op.create_table(
        "system_settings",
        sa.Column("key", sa.String(120), primary_key=True),
        sa.Column("value_json", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "geocoding_cache",
        sa.Column("query_key", sa.String(255), primary_key=True),
        sa.Column("response_json", sa.JSON(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_geocoding_cache_expires_at", "geocoding_cache", ["expires_at"])


def downgrade() -> None:
    op.drop_table("geocoding_cache")
    op.drop_table("system_settings")
    op.drop_table("refresh_tokens")
    op.drop_table("generation_candidates")
    op.drop_table("generation_jobs")
    op.drop_table("course_metrics")
    op.drop_table("course_geometries")
    op.drop_table("courses")
    op.drop_table("invite_codes")
    op.drop_table("users")
