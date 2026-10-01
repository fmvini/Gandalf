"""Owner-scoped individual music/book snapshots."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "0008_favorites"
down_revision = "0007_recommendation_results"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "favorites",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("type", sa.String(5), nullable=False),
        sa.Column("item_id", sa.Uuid(), nullable=False),
        sa.Column("item", JSONB().with_variant(sa.JSON(), "sqlite"), nullable=False),
        sa.Column("source_recommendation_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("type IN ('MUSIC', 'BOOK')", name="ck_favorites_type"),
        sa.UniqueConstraint(
            "user_id", "type", "item_id", name="uq_favorites_user_type_item"
        ),
    )
    op.create_index(
        "ix_favorites_user_created", "favorites", ["user_id", "created_at", "id"]
    )
    op.create_index(
        "ix_favorites_user_type_created",
        "favorites",
        ["user_id", "type", "created_at", "id"],
    )


def downgrade() -> None:
    op.drop_index("ix_favorites_user_type_created", table_name="favorites")
    op.drop_index("ix_favorites_user_created", table_name="favorites")
    op.drop_table("favorites")
