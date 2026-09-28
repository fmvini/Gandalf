"""Music catalog and persistent daily AI call allowance."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "0005_online_catalog"
down_revision = "0004_external_search_cache"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "music_catalog",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("data", JSONB().with_variant(sa.JSON(), "sqlite"), nullable=False),
    )
    op.create_table(
        "ai_usage",
        sa.Column("day", sa.String(10), primary_key=True),
        sa.Column("calls", sa.Integer(), nullable=False),
    )


def downgrade():
    op.drop_table("ai_usage")
    op.drop_table("music_catalog")
