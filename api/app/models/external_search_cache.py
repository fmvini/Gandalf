from sqlalchemy import JSON, BigInteger, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ExternalSearchCache(Base):
    __tablename__ = "external_search_cache"
    __table_args__ = (
        UniqueConstraint(
            "entity_type",
            "provider",
            "query",
            "result_limit",
            name="uq_external_search_cache_key",
        ),
        Index("ix_external_search_cache_expires_at", "expires_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(16), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    result_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    response: Mapped[dict[str, object]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False
    )
    expires_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
