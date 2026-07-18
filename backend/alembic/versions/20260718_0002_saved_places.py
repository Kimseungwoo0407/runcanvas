"""Add saved places and pre-generated course metadata.

Revision ID: 20260718_0002
Revises: 20260715_0001
Create Date: 2026-07-18
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260718_0002"
down_revision: str | None = "20260715_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "saved_places",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("owner_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lng", sa.Float(), nullable=False),
        sa.Column("privacy_radius_m", sa.Integer(), nullable=False),
        sa.Column("prefer_riverside", sa.Boolean(), nullable=False),
        sa.Column("distances_json", sa.JSON(), nullable=False),
        sa.Column("shapes_json", sa.JSON(), nullable=False),
        sa.Column("precompute_batch_id", sa.String(36), nullable=True),
        sa.Column("precompute_requested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_saved_places_owner_id", "saved_places", ["owner_id"])

    with op.batch_alter_table("courses") as batch:
        batch.add_column(sa.Column("saved_place_id", sa.String(36), nullable=True))
        batch.add_column(sa.Column("is_pregenerated", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.add_column(sa.Column("preset_key", sa.String(160), nullable=True))
        batch.create_foreign_key(
            "fk_courses_saved_place_id", "saved_places", ["saved_place_id"], ["id"], ondelete="SET NULL"
        )
    op.create_index("ix_courses_saved_place_id", "courses", ["saved_place_id"])
    op.create_index("ix_courses_is_pregenerated", "courses", ["is_pregenerated"])
    op.create_index("ix_courses_preset_key", "courses", ["preset_key"], unique=True)

    with op.batch_alter_table("generation_jobs") as batch:
        batch.add_column(sa.Column("saved_place_id", sa.String(36), nullable=True))
        batch.add_column(sa.Column("precompute_batch_id", sa.String(36), nullable=True))
        batch.create_foreign_key(
            "fk_generation_jobs_saved_place_id",
            "saved_places",
            ["saved_place_id"],
            ["id"],
            ondelete="SET NULL",
        )
    op.create_index("ix_generation_jobs_saved_place_id", "generation_jobs", ["saved_place_id"])
    op.create_index("ix_generation_jobs_precompute_batch_id", "generation_jobs", ["precompute_batch_id"])


def downgrade() -> None:
    op.drop_index("ix_generation_jobs_precompute_batch_id", table_name="generation_jobs")
    op.drop_index("ix_generation_jobs_saved_place_id", table_name="generation_jobs")
    with op.batch_alter_table("generation_jobs") as batch:
        batch.drop_constraint("fk_generation_jobs_saved_place_id", type_="foreignkey")
        batch.drop_column("precompute_batch_id")
        batch.drop_column("saved_place_id")

    op.drop_index("ix_courses_preset_key", table_name="courses")
    op.drop_index("ix_courses_is_pregenerated", table_name="courses")
    op.drop_index("ix_courses_saved_place_id", table_name="courses")
    with op.batch_alter_table("courses") as batch:
        batch.drop_constraint("fk_courses_saved_place_id", type_="foreignkey")
        batch.drop_column("preset_key")
        batch.drop_column("is_pregenerated")
        batch.drop_column("saved_place_id")

    op.drop_index("ix_saved_places_owner_id", table_name="saved_places")
    op.drop_table("saved_places")
