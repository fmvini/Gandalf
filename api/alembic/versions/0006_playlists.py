"""Owner-scoped playlists with ordered track snapshots."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "0006_playlists"
down_revision = "0005_online_catalog"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "playlists",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.String(1000)),
        sa.Column("source", sa.String(16), nullable=False),
        sa.Column("source_recommendation_id", sa.Uuid()),
        sa.Column("total_duration_ms", sa.BigInteger(), nullable=False),
        sa.Column("duration_estimated", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("length(name) BETWEEN 1 AND 120", name="ck_playlists_name"),
        sa.CheckConstraint("total_duration_ms >= 0", name="ck_playlists_duration"),
        sa.CheckConstraint(
            "source IN ('MANUAL', 'READ_WITH_MUSIC')", name="ck_playlists_source"
        ),
    )
    op.create_index(
        "ix_playlists_user_created", "playlists", ["user_id", "created_at", "id"]
    )
    op.create_table(
        "playlist_tracks",
        sa.Column(
            "playlist_id",
            sa.Uuid(),
            sa.ForeignKey("playlists.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("position", sa.Integer(), primary_key=True),
        sa.Column(
            "music_id",
            sa.String(36),
            sa.ForeignKey("music_catalog.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("item", JSONB().with_variant(sa.JSON(), "sqlite"), nullable=False),
        sa.UniqueConstraint("playlist_id", "music_id", name="uq_playlist_tracks_music"),
        sa.CheckConstraint("position >= 1", name="ck_playlist_tracks_position"),
    )


def downgrade() -> None:
    op.drop_table("playlist_tracks")
    op.drop_index("ix_playlists_user_created", table_name="playlists")
    op.drop_table("playlists")
