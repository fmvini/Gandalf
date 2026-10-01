from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Playlist(Base):
    __tablename__ = "playlists"
    __table_args__ = (
        Index("ix_playlists_user_created", "user_id", "created_at", "id"),
        CheckConstraint("length(name) BETWEEN 1 AND 120", name="ck_playlists_name"),
        CheckConstraint("total_duration_ms >= 0", name="ck_playlists_duration"),
        CheckConstraint(
            "source IN ('MANUAL', 'READ_WITH_MUSIC')", name="ck_playlists_source"
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        Uuid(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000))
    source: Mapped[str] = mapped_column(String(16), nullable=False)
    # Anonymous recommendations expire; this is provenance, not a foreign key.
    source_recommendation_id: Mapped[UUID | None] = mapped_column(Uuid())
    total_duration_ms: Mapped[int] = mapped_column(BigInteger, nullable=False)
    duration_estimated: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class PlaylistTrack(Base):
    __tablename__ = "playlist_tracks"
    __table_args__ = (
        UniqueConstraint("playlist_id", "music_id", name="uq_playlist_tracks_music"),
        CheckConstraint("position >= 1", name="ck_playlist_tracks_position"),
    )

    playlist_id: Mapped[UUID] = mapped_column(
        Uuid(), ForeignKey("playlists.id", ondelete="CASCADE"), primary_key=True
    )
    position: Mapped[int] = mapped_column(Integer, primary_key=True)
    music_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("music_catalog.id", ondelete="RESTRICT"), nullable=False
    )
    # Preserve the saved track even if the provider/catalog changes later.
    item: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False
    )
