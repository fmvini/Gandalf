"""Adiciona o catálogo local de livros.

Revision ID: 0003_books_catalog
Revises: 0002_accounts
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

from alembic import op

revision = "0003_books_catalog"
down_revision = "0002_accounts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "books",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("provider", sa.String(32), nullable=False),
        sa.Column("external_id", sa.String(128), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column(
            "authors",
            ARRAY(sa.String()).with_variant(sa.JSON(), "sqlite"),
            nullable=False,
        ),
        sa.Column("description", sa.Text()),
        sa.Column(
            "genres",
            ARRAY(sa.String()).with_variant(sa.JSON(), "sqlite"),
            nullable=False,
        ),
        sa.Column(
            "subjects",
            ARRAY(sa.String()).with_variant(sa.JSON(), "sqlite"),
            nullable=False,
        ),
        sa.Column("publication_year", sa.Integer()),
        sa.Column("cover_url", sa.Text()),
        sa.Column("external_url", sa.Text(), nullable=False),
        sa.Column(
            "metadata",
            JSONB().with_variant(sa.JSON(), "sqlite"),
            nullable=False,
        ),
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
        sa.UniqueConstraint(
            "provider", "external_id", name="uq_books_provider_external"
        ),
    )
    op.create_index("ix_books_title", "books", ["title"])


def downgrade() -> None:
    op.drop_index("ix_books_title", table_name="books")
    op.drop_table("books")
