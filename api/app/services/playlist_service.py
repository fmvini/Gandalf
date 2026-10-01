from collections.abc import Iterator
from contextlib import contextmanager
from copy import deepcopy
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models import MusicCatalog, Playlist, PlaylistTrack
from app.providers.local_catalog import MUSIC
from app.schemas.playlist import (
    PlaylistCreate,
    PlaylistDetail,
    PlaylistList,
    PlaylistSummary,
    PlaylistTrackResponse,
)
from app.services.auth_service import as_utc


class PlaylistService:
    def __init__(self, session: Session):
        self.session = session

    @contextmanager
    def _database(self) -> Iterator[None]:
        try:
            yield
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise AppError(
                503,
                "SERVICE_UNAVAILABLE",
                "As playlists estão indisponíveis. Tente novamente.",
            ) from exc

    def create(
        self, user_id: UUID, body: PlaylistCreate, recommendation: dict | None = None
    ) -> PlaylistDetail:
        with self._database():
            items = self._items(body, recommendation)
            total = 0
            estimated = False
            for item in items:
                duration = item.get("duration_ms")
                known = type(duration) is int and 0 < duration < 86_400_000
                if not known:
                    duration = item.get("estimated_duration_ms")
                    if type(duration) is not int or not 0 < duration < 86_400_000:
                        duration = 300_000
                    estimated = True
                total += duration

            playlist = Playlist(
                user_id=user_id,
                name=body.name,
                description=body.description,
                source="READ_WITH_MUSIC" if recommendation is not None else "MANUAL",
                source_recommendation_id=body.source_recommendation_id,
                total_duration_ms=total,
                duration_estimated=estimated,
            )
            self.session.add(playlist)
            self.session.flush()
            insert = (
                sqlite_insert
                if self.session.get_bind().dialect.name == "sqlite"
                else pg_insert
            )
            tracks = []
            for position, item in enumerate(items, start=1):
                # Local tracks join the persistent catalog only when saved.
                self.session.execute(
                    insert(MusicCatalog)
                    .values(id=item["id"], data=item)
                    .on_conflict_do_nothing(index_elements=["id"])
                )
                track = PlaylistTrack(
                    playlist_id=playlist.id,
                    position=position,
                    music_id=item["id"],
                    item=item,
                )
                self.session.add(track)
                tracks.append(track)
            self.session.flush()
            response = self._detail(playlist, tracks)
            self.session.commit()
            return response

    def _items(self, body: PlaylistCreate, recommendation: dict | None) -> list[dict]:
        if recommendation is not None:
            if "playlist" not in recommendation:
                raise AppError(
                    422,
                    "VALIDATION_ERROR",
                    "Use uma recomendação de trilha de leitura.",
                )
            rows = recommendation["items"]
            by_id = {row["item"]["id"]: row["item"] for row in rows}
            ids = (
                [str(value) for value in body.music_ids]
                if body.music_ids is not None
                else list(by_id)
            )
            if not ids:
                raise AppError(422, "VALIDATION_ERROR", "A trilha não contém músicas.")
            if len(ids) > 60:
                raise AppError(
                    422, "VALIDATION_ERROR", "Escolha até 60 músicas da trilha."
                )
            if any(item_id not in by_id for item_id in ids):
                raise AppError(
                    422,
                    "VALIDATION_ERROR",
                    "Escolha apenas músicas da trilha informada.",
                )
            return [deepcopy(by_id[item_id]) for item_id in ids]

        local = {item["id"]: item for item in MUSIC}
        ids = [str(value) for value in body.music_ids]
        remote = {
            item.id: item.data
            for item in self.session.scalars(
                select(MusicCatalog).where(MusicCatalog.id.in_(ids))
            )
        }
        if any(item_id not in local and item_id not in remote for item_id in ids):
            raise AppError(404, "NOT_FOUND", "Música não encontrada no catálogo.")
        return [deepcopy(local.get(item_id) or remote[item_id]) for item_id in ids]

    def list_playlists(self, user_id: UUID, limit: int, offset: int) -> PlaylistList:
        with self._database():
            total = self.session.scalar(
                select(func.count())
                .select_from(Playlist)
                .where(Playlist.user_id == user_id)
            )
            rows = self.session.execute(
                select(Playlist, func.count(PlaylistTrack.position))
                .outerjoin(PlaylistTrack, PlaylistTrack.playlist_id == Playlist.id)
                .where(Playlist.user_id == user_id)
                .group_by(Playlist.id)
                .order_by(Playlist.created_at.desc(), Playlist.id.desc())
                .limit(limit)
                .offset(offset)
            )
            return PlaylistList(
                items=[self._summary(playlist, count) for playlist, count in rows],
                total=total,
                limit=limit,
                offset=offset,
            )

    def get(self, user_id: UUID, playlist_id: UUID) -> PlaylistDetail:
        with self._database():
            playlist = self._owned(user_id, playlist_id)
            tracks = self.session.scalars(
                select(PlaylistTrack)
                .where(PlaylistTrack.playlist_id == playlist.id)
                .order_by(PlaylistTrack.position)
            ).all()
            return self._detail(playlist, tracks)

    def delete(self, user_id: UUID, playlist_id: UUID) -> None:
        with self._database():
            playlist = self._owned(user_id, playlist_id)
            # Explicit deletion also works with existing SQLite connections that
            # predate foreign-key enforcement. The catalog remains shared.
            self.session.execute(
                delete(PlaylistTrack).where(PlaylistTrack.playlist_id == playlist.id)
            )
            self.session.delete(playlist)
            self.session.commit()

    def _owned(self, user_id: UUID, playlist_id: UUID) -> Playlist:
        playlist = self.session.scalar(
            select(Playlist).where(
                Playlist.id == playlist_id, Playlist.user_id == user_id
            )
        )
        if playlist is None:
            raise AppError(404, "NOT_FOUND", "Playlist não encontrada.")
        return playlist

    @staticmethod
    def _summary(playlist: Playlist, count: int) -> PlaylistSummary:
        return PlaylistSummary(
            id=playlist.id,
            name=playlist.name,
            description=playlist.description,
            source=playlist.source,
            source_recommendation_id=playlist.source_recommendation_id,
            total_duration_ms=playlist.total_duration_ms,
            duration_estimated=playlist.duration_estimated,
            tracks_count=count,
            created_at=as_utc(playlist.created_at),
            updated_at=as_utc(playlist.updated_at),
        )

    @classmethod
    def _detail(cls, playlist: Playlist, tracks: list[PlaylistTrack]) -> PlaylistDetail:
        return PlaylistDetail(
            **cls._summary(playlist, len(tracks)).model_dump(),
            tracks=[
                PlaylistTrackResponse(
                    position=track.position, item=deepcopy(track.item)
                )
                for track in tracks
            ],
        )
