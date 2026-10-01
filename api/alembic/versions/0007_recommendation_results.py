"""Shared short-lived anonymous recommendation snapshots."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "0007_recommendation_results"
down_revision = "0006_playlists"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recommendation_results",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "response", JSONB().with_variant(sa.JSON(), "sqlite"), nullable=False
        ),
        sa.Column("created_at", sa.BigInteger(), nullable=False),
        sa.Column("expires_at", sa.BigInteger(), nullable=False),
    )
    op.create_index(
        "ix_recommendation_results_created",
        "recommendation_results",
        ["created_at", "id"],
    )
    op.create_index(
        "ix_recommendation_results_expires", "recommendation_results", ["expires_at"]
    )


def downgrade() -> None:
    op.drop_index(
        "ix_recommendation_results_expires", table_name="recommendation_results"
    )
    op.drop_index(
        "ix_recommendation_results_created", table_name="recommendation_results"
    )
    op.drop_table("recommendation_results")
