"""Add channels table

Revision ID: 8dbdd85ed11e
Revises:
Create Date: 2025-08-28 05:58:31.796558

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8dbdd85ed11e"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "channels",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("channel_id", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("thumbnail_url", sa.String(length=500), nullable=True),
        sa.Column("subscriber_count", sa.Integer(), nullable=True),
        sa.Column("uploads_playlist_id", sa.String(length=255), nullable=True),
        sa.Column("source_input", sa.String(length=500), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_channels_id"), "channels", ["id"], unique=False)
    op.create_index(
        op.f("ix_channels_channel_id"), "channels", ["channel_id"], unique=True
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_channels_channel_id"), table_name="channels")
    op.drop_index(op.f("ix_channels_id"), table_name="channels")
    op.drop_table("channels")
