from collections.abc import Iterator
from contextlib import contextmanager
from copy import deepcopy
from uuid import UUID, uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.models import Favorite
from app.schemas.favorite import (
    FavoriteCreate,
    FavoriteList,
    FavoriteResponse,
    FavoriteStatus,
    FavoriteStatusRequest,
    FavoriteType,
)
from app.services.auth_service import as_utc


class FavoriteService:
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
                "Os favoritos estão indisponíveis. Tente novamente.",
            ) from exc

    def create(
        self, user_id: UUID, body: FavoriteCreate, recommendation: dict
    ) -> tuple[FavoriteResponse, bool]:
        # Only an item actually returned by this source can be saved. Never
        # accept client metadata or copy the score/explanation/request context.
        item = next(
            (
                row["item"]
                for row in recommendation["items"]
                if row["item"]["id"] == str(body.item_id)
            ),
            None,
        )
        if item is None:
            raise AppError(404, "NOT_FOUND", "Item não encontrado nesta sugestão.")
        if isinstance(item.get("artist"), str):
            item_type = "MUSIC"
        elif isinstance(item.get("authors"), list):
            item_type = "BOOK"
        else:
            raise AppError(404, "NOT_FOUND", "Item não encontrado nesta sugestão.")

        with self._database():
            insert = (
                sqlite_insert
                if self.session.get_bind().dialect.name == "sqlite"
                else pg_insert
            )
            candidate_id = uuid4()
            # Returning the existing snapshot in the upsert itself avoids a
            # SELECT racing a concurrent DELETE under PostgreSQL READ COMMITTED.
            # The no-op update locks the row while preserving all saved values.
            saved = self.session.scalar(
                insert(Favorite)
                .values(
                    id=candidate_id,
                    user_id=user_id,
                    type=item_type,
                    item_id=body.item_id,
                    item=deepcopy(item),
                    source_recommendation_id=body.recommendation_id,
                )
                .on_conflict_do_update(
                    index_elements=["user_id", "type", "item_id"],
                    set_={"id": Favorite.id},
                )
                .returning(Favorite)
                .execution_options(populate_existing=True)
            )
            response = self._response(saved)
            self.session.commit()
            return response, response.id == candidate_id

    def list_favorites(
        self, user_id: UUID, item_type: FavoriteType | None, limit: int, offset: int
    ) -> FavoriteList:
        with self._database():
            filters = [Favorite.user_id == user_id]
            if item_type is not None:
                filters.append(Favorite.type == item_type)
            total = self.session.scalar(
                select(func.count()).select_from(Favorite).where(*filters)
            )
            rows = self.session.scalars(
                select(Favorite)
                .where(*filters)
                .order_by(Favorite.created_at.desc(), Favorite.id.desc())
                .limit(limit)
                .offset(offset)
            )
            return FavoriteList(
                items=[self._response(row) for row in rows],
                total=total,
                limit=limit,
                offset=offset,
            )

    def status(self, user_id: UUID, body: FavoriteStatusRequest) -> FavoriteStatus:
        with self._database():
            rows = self.session.execute(
                select(Favorite.item_id, Favorite.id).where(
                    Favorite.user_id == user_id,
                    Favorite.type == body.type,
                    Favorite.item_id.in_(body.item_ids),
                )
            )
            return FavoriteStatus(favorites=dict(rows.all()))

    def delete(self, user_id: UUID, favorite_id: UUID) -> None:
        with self._database():
            self.session.execute(
                delete(Favorite).where(
                    Favorite.id == favorite_id, Favorite.user_id == user_id
                )
            )
            self.session.commit()

    @staticmethod
    def _response(row: Favorite) -> FavoriteResponse:
        return FavoriteResponse(
            id=row.id,
            type=row.type,
            item_id=row.item_id,
            item=deepcopy(row.item),
            created_at=as_utc(row.created_at),
        )
