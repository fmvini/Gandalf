from sqlalchemy import JSON, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class MusicCatalog(Base):
    __tablename__ = "music_catalog"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    data: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False
    )


class AIUsage(Base):
    __tablename__ = "ai_usage"
    day: Mapped[str] = mapped_column(String(10), primary_key=True)
    calls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
