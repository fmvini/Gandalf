from copy import deepcopy
from time import time
from uuid import UUID

from sqlalchemy import delete, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.exceptions import AppError
from app.models import RecommendationResult

RESULT_TTL_SECONDS = 3600
RESULT_LIMIT = 256
# A fixed application namespace shared by all PostgreSQL writers/cleaners.
CACHE_LOCK_ID = 0x47414E44414C46


def result_snapshot(result: dict) -> dict:
    """Only data needed to explain/save; no query, parsed intent or account."""
    return deepcopy(
        {
            "recommendation_id": result["recommendation_id"],
            "items": result["items"],
            **({"playlist": result["playlist"]} if "playlist" in result else {}),
        }
    )


class RecommendationCache:
    def __init__(self, factory: sessionmaker[Session]):
        self.factory = factory

    @staticmethod
    def _lock_and_prune(session: Session, now: int) -> None:
        if session.get_bind().dialect.name == "postgresql":
            session.execute(
                text("SELECT pg_advisory_xact_lock(:key)"), {"key": CACHE_LOCK_ID}
            )
        # SQLite acquires its writer lock before we inspect the cache. On
        # PostgreSQL the transaction-scoped advisory lock serializes writers.
        session.execute(
            delete(RecommendationResult).where(RecommendationResult.expires_at <= now)
        )

    def put(self, result: dict) -> None:
        snapshot = result_snapshot(result)
        try:
            with self.factory.begin() as session:
                now = int(time() * 1000)
                self._lock_and_prune(session, now)
                insert = (
                    pg_insert
                    if session.get_bind().dialect.name == "postgresql"
                    else sqlite_insert
                )
                session.execute(
                    insert(RecommendationResult)
                    .values(
                        id=UUID(result["recommendation_id"]),
                        response=snapshot,
                        created_at=now,
                        expires_at=now + RESULT_TTL_SECONDS * 1000,
                    )
                    .on_conflict_do_update(
                        index_elements=["id"], set_={"response": snapshot}
                    )
                )
                # Keep the just-published result even when several IDs have
                # the same millisecond timestamp.
                overflow = (
                    select(RecommendationResult.id)
                    .where(RecommendationResult.id != UUID(result["recommendation_id"]))
                    .order_by(
                        RecommendationResult.created_at.desc(),
                        RecommendationResult.id.desc(),
                    )
                    .offset(RESULT_LIMIT - 1)
                )
                session.execute(
                    delete(RecommendationResult).where(
                        RecommendationResult.id.in_(overflow)
                    )
                )
        except SQLAlchemyError as exc:
            raise self._unavailable() from exc

    def get(self, recommendation_id: str) -> dict | None:
        try:
            with self.factory.begin() as session:
                self._lock_and_prune(session, int(time() * 1000))
                row = session.scalar(
                    select(RecommendationResult).where(
                        RecommendationResult.id == UUID(recommendation_id),
                        RecommendationResult.expires_at > int(time() * 1000),
                    )
                )
                return deepcopy(row.response) if row is not None else None
        except SQLAlchemyError as exc:
            raise self._unavailable() from exc

    def prune(self) -> None:
        try:
            with self.factory.begin() as session:
                self._lock_and_prune(session, int(time() * 1000))
        except SQLAlchemyError as exc:
            raise self._unavailable() from exc

    @staticmethod
    def _unavailable() -> AppError:
        return AppError(
            503,
            "SERVICE_UNAVAILABLE",
            "As sugestões estão indisponíveis. Tente novamente.",
        )
