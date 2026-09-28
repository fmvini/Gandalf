"""Adiciona cache persistente de buscas externas.

Revision ID: 0004_external_search_cache
Revises: 0003_books_catalog
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "0004_external_search_cache"
down_revision = "0003_books_catalog"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "external_search_cache",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("entity_type", sa.String(16), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("result_limit", sa.Integer(), nullable=False),
        sa.Column(
            "response", JSONB().with_variant(sa.JSON(), "sqlite"), nullable=False
        ),
        sa.Column("expires_at", sa.BigInteger(), nullable=False),
        sa.UniqueConstraint(
            "entity_type",
            "provider",
            "query",
            "result_limit",
            name="uq_external_search_cache_key",
        ),
    )
    op.create_index(
        "ix_external_search_cache_expires_at", "external_search_cache", ["expires_at"]
    )


def downgrade() -> None:
    op.drop_index(
        "ix_external_search_cache_expires_at", table_name="external_search_cache"
    )
    op.drop_table("external_search_cache")
