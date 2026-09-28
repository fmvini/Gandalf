from datetime import UTC, datetime
from time import time

from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.models import AIUsage, ExternalSearchCache, MusicCatalog


class OnlineStore:
    """Persistent cache and allowance; AI fails closed without a migrated database."""

    def __init__(self, factory):
        self.factory = factory

    @staticmethod
    def insert(session, model):
        return (
            pg_insert if session.bind.dialect.name == "postgresql" else sqlite_insert
        )(model)

    def get(self, provider, key, limit):
        if self.factory is None:
            return None
        with self.factory() as session:
            row = session.scalar(
                select(ExternalSearchCache).where(
                    ExternalSearchCache.entity_type == "ONLINE",
                    ExternalSearchCache.provider == provider,
                    ExternalSearchCache.query == key,
                    ExternalSearchCache.result_limit == limit,
                    ExternalSearchCache.expires_at > int(time() * 1000),
                )
            )
            return row.response if row else None

    def put(self, provider, key, limit, value, ttl):
        if self.factory is None or not ttl:
            return
        with self.factory() as session:
            now = int(time() * 1000)
            statement = self.insert(session, ExternalSearchCache).values(
                entity_type="ONLINE",
                provider=provider,
                query=key,
                result_limit=limit,
                response=value,
                expires_at=now + ttl * 1000,
            )
            session.execute(
                statement.on_conflict_do_update(
                    index_elements=["entity_type", "provider", "query", "result_limit"],
                    set_={"response": value, "expires_at": now + ttl * 1000},
                )
            )
            session.execute(
                delete(ExternalSearchCache).where(ExternalSearchCache.expires_at <= now)
            )
            session.commit()

    def reserve_ai_call(self, limit):
        if self.factory is None or not limit:
            return False
        day = datetime.now(UTC).date().isoformat()
        with self.factory() as session:
            session.execute(
                self.insert(session, AIUsage)
                .values(day=day, calls=0)
                .on_conflict_do_nothing(index_elements=["day"])
            )
            result = session.execute(
                update(AIUsage)
                .where(AIUsage.day == day, AIUsage.calls < limit)
                .values(calls=AIUsage.calls + 1)
            )
            session.execute(delete(AIUsage).where(AIUsage.day < day))
            session.commit()
            return result.rowcount == 1

    def save_music(self, items):
        if self.factory is None:
            return
        with self.factory() as session:
            for item in items:
                statement = self.insert(session, MusicCatalog).values(
                    id=item["id"], data=item
                )
                session.execute(
                    statement.on_conflict_do_update(
                        index_elements=["id"], set_={"data": item}
                    )
                )
            session.commit()

    def music_by_id(self, item_id):
        if self.factory is None:
            return None
        with self.factory() as session:
            row = session.get(MusicCatalog, str(item_id))
            return row.data if row else None
