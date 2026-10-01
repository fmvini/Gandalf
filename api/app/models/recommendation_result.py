from uuid import UUID

from sqlalchemy import JSON, BigInteger, Index, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class RecommendationResult(Base):
    """Short-lived anonymous snapshot shared across API processes.

    The service stores items/playlist only, without query, parsed intent or user.
    Timestamps are Unix milliseconds so expiration is comparable across workers.
    """

    __tablename__ = "recommendation_results"
    __table_args__ = (
        Index("ix_recommendation_results_created", "created_at", "id"),
        Index("ix_recommendation_results_expires", "expires_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(), primary_key=True)
    response: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False
    )
    created_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
    expires_at: Mapped[int] = mapped_column(BigInteger, nullable=False)
