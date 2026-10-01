from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Favorite(Base):
    """Owner-scoped item snapshot independent of catalog/cache lifetime."""

    __tablename__ = "favorites"
    __table_args__ = (
        CheckConstraint("type IN ('MUSIC', 'BOOK')", name="ck_favorites_type"),
        UniqueConstraint(
            "user_id", "type", "item_id", name="uq_favorites_user_type_item"
        ),
        Index("ix_favorites_user_created", "user_id", "created_at", "id"),
        Index("ix_favorites_user_type_created", "user_id", "type", "created_at", "id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(5), nullable=False)
    item_id: Mapped[UUID] = mapped_column(Uuid(), nullable=False)
    item: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False
    )
    # Provenance only: saved items outlive the anonymous recommendation cache.
    source_recommendation_id: Mapped[UUID] = mapped_column(Uuid(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
