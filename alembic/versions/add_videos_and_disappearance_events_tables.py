"""add videos and disappearance events tables

Revision ID: b1c2d3e4f5g6
Revises: 8dbdd85ed11e
Create Date: 2025-08-28 09:05:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "b1c2d3e4f5g6"
down_revision: Union[str, Sequence[str], None] = "8dbdd85ed11e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "videos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("video_id", sa.String(length=255), nullable=False),
        sa.Column("channel_id", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("thumbnail_url", sa.String(length=500), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration", sa.String(length=50), nullable=True),
        sa.Column("view_count", sa.Integer(), nullable=True),
        sa.Column("is_available", sa.Boolean(), nullable=False),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "first_detected_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["channel_id"],
            ["channels.channel_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_videos_id"), "videos", ["id"], unique=False)
    op.create_index(op.f("ix_videos_video_id"), "videos", ["video_id"], unique=True)
    op.create_index(
        "ix_videos_channel_id_published_at",
        "videos",
        ["channel_id", sa.text("published_at DESC")],
        unique=False,
    )

    op.create_table(
        "disappearance_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("video_id", sa.String(length=255), nullable=False),
        sa.Column(
            "event_type",
            sa.Enum(
                "PRIVATE",
                "DELETED",
                "GEO_BLOCKED",
                "AGE_RESTRICTED",
                "UNKNOWN",
                name="eventtype",
            ),
            nullable=False,
        ),
        sa.Column(
            "detected_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(
            ["video_id"],
            ["videos.video_id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_disappearance_events_id"), "disappearance_events", ["id"], unique=False
    )
    op.create_index(
        "ix_disappearance_events_video_id_detected_at",
        "disappearance_events",
        ["video_id", sa.text("detected_at DESC")],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "ix_disappearance_events_video_id_detected_at",
        table_name="disappearance_events",
    )
    op.drop_index(op.f("ix_disappearance_events_id"), table_name="disappearance_events")
    op.drop_table("disappearance_events")
    op.execute("DROP TYPE eventtype")
    op.drop_index("ix_videos_channel_id_published_at", table_name="videos")
    op.drop_index(op.f("ix_videos_video_id"), table_name="videos")
    op.drop_index(op.f("ix_videos_id"), table_name="videos")
    op.drop_table("videos")
