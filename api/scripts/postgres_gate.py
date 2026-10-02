"""Opt-in PostgreSQL gate; requires an empty, dedicated local test database."""

import json
import os
import re
import sys
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import freeze_support
from pathlib import Path
from time import time
from unittest.mock import patch
from uuid import UUID, uuid4

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))

from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, func, inspect, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from alembic import command
from app.core.config import Settings
from app.database.base import Base
from app.main import create_app
from app.models import Favorite, RecommendationResult, User
from app.schemas.favorite import FavoriteCreate, FavoriteStatusRequest
from app.services.favorite_service import FavoriteService
from app.services.recommendation_cache import RecommendationCache

STAGE = "target_validation"


def stage(name):
    global STAGE
    STAGE = name
    print(json.dumps({"stage": name}), file=sys.stderr, flush=True)


def validate_target(value):
    url = make_url(value)
    if not (
        url.drivername == "postgresql+psycopg"
        and url.host in {"127.0.0.1", "localhost"}
        and url.port in {55432, 55433}
        and url.username == "gandalf_gate"
        and re.fullmatch(r"gandalf_gate_[0-9a-f]{32}", url.database or "")
        and not url.query
    ):
        raise ValueError("Target must be a dedicated loopback gate database.")
    return url


def engine_for(value):
    validate_target(value)
    return create_engine(
        value,
        isolation_level="READ COMMITTED",
        connect_args={"connect_timeout": 5, "options": "-c statement_timeout=15000"},
    )


def validate_database(url, database, user, occupied, available):
    if database != url.database or user != "gandalf_gate":
        raise ValueError("Connected database identity does not match gate target.")
    if occupied != 0:
        raise ValueError("Refusing a database containing user objects.")
    if available != {"citext", "vector"}:
        raise ValueError("Required extensions not available in disposable server.")


def favorite_worker(value, owner, body, result, mode):
    engine = engine_for(value)
    try:
        with Session(engine) as session:
            service = FavoriteService(session)
            if mode == "once":
                saved, created = service.create(owner, FavoriteCreate(**body), result)
                return str(saved.id), created
            for _ in range(20):
                if mode == "delete":
                    fid = session.scalar(
                        select(Favorite.id).where(
                            Favorite.user_id == owner,
                            Favorite.item_id == UUID(body["item_id"]),
                        )
                    )
                    service.delete(owner, fid or uuid4())
                else:
                    saved, _ = service.create(owner, FavoriteCreate(**body), result)
                    assert saved.item == result["items"][0]["item"]
            return True
    finally:
        engine.dispose()


def cache_worker(value, count):
    engine = engine_for(value)
    try:
        cache = RecommendationCache(sessionmaker(engine))
        for _ in range(count):
            result = {"recommendation_id": str(uuid4()), "items": []}
            cache.put(result)
            cache.get(result["recommendation_id"])
        return True
    finally:
        engine.dispose()


def run(value):
    stage("preflight")
    url = validate_target(value)
    engine = engine_for(value)
    # This guard is checked BEFORE any schema/data mutation.
    with engine.connect() as connection:
        database, user, version = connection.execute(
            text("SELECT current_database(), current_user, version()")
        ).one()
        occupied = connection.scalar(
            text(
                "SELECT count(*) FROM pg_class c JOIN pg_namespace n "
                "ON n.oid=c.relnamespace WHERE n.nspname NOT LIKE 'pg_%' "
                "AND n.nspname <> 'information_schema' "
                "AND c.relkind IN ('r','p','v','m','S','f')"
            )
        )
        available = set(
            connection.scalars(
                text(
                    "SELECT name FROM pg_available_extensions WHERE name IN ('citext','vector')"
                )
            )
        )
        validate_database(url, database, user, occupied, available)
    checks = []
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "alembic"))

    # Never consult DATABASE_URL/.env for Alembic; always pass this connection.
    def migrate(target, downgrade=False):
        with engine.begin() as connection:
            config.attributes["connection"] = connection
            (command.downgrade if downgrade else command.upgrade)(config, target)

    try:
        stage("migration_0007_seed_upgrade_head")
        migrate("0007_recommendation_results")
        owner, other, item_id, origin = uuid4(), uuid4(), uuid4(), uuid4()
        with Session(engine) as session:
            session.add_all(
                User(
                    id=uid,
                    email=f"{uid}@example.test",
                    username=uid.hex[:20],
                    password_hash="gate",
                )
                for uid in (owner, other)
            )
            session.commit()
        migrate("head")
        stage("metadata_extensions")
        with engine.connect() as connection:
            assert not compare_metadata(
                MigrationContext.configure(connection), Base.metadata
            )
            assert (
                connection.scalar(text("SHOW transaction_isolation"))
                == "read committed"
            )
            extensions = dict(
                connection.execute(
                    text(
                        "SELECT extname, extversion FROM pg_extension WHERE extname IN ('vector','citext')"
                    )
                ).all()
            )
            assert set(extensions) == {"vector", "citext"}
            assert (
                connection.scalar(text("SELECT '[1,0]'::vector <=> '[1,0]'::vector"))
                == 0
            )
            assert (
                connection.scalar(text("SELECT 'Gate'::citext = 'gate'::citext"))
                is True
            )
        settings = Settings(
            _env_file=None,
            database_url=value,
            book_provider="local",
            online_catalog=False,
        )
        stage("readiness")
        with TestClient(create_app(settings=settings)) as client:
            readiness = client.get("/health/ready")
            assert readiness.status_code == 200
            assert readiness.json()["components"]["pgvector"] == "ok"
        checks.append("real_migrations_metadata_extensions_readiness")
        stage("multiprocess_upsert_snapshot_owner")
        item = {"id": str(item_id), "title": "Gate", "artist": "Fixture"}
        result = {"recommendation_id": str(origin), "items": [{"item": item}]}
        body = {"recommendation_id": str(origin), "item_id": str(item_id)}
        with ProcessPoolExecutor(max_workers=3) as pool:
            futures = [
                pool.submit(favorite_worker, value, owner, body, result, "once")
                for _ in range(6)
            ]
            answers = [f.result(timeout=45) for f in futures]
        assert (
            len({fid for fid, _ in answers}) == 1
            and sum(created for _, created in answers) == 1
        )
        fid = UUID(answers[0][0])
        with Session(engine) as session:
            service = FavoriteService(session)
            original = session.get(Favorite, fid)
            created_at, source = original.created_at, original.source_recommendation_id
            changed = {"items": [{"item": {**item, "title": "Changed"}}]}
            repeated, created = service.create(
                owner,
                FavoriteCreate(**{**body, "recommendation_id": str(uuid4())}),
                changed,
            )
            assert not created and repeated.id == fid and repeated.item == item
            row = session.get(Favorite, fid)
            assert (
                row.created_at == created_at and row.source_recommendation_id == source
            )
            assert row.created_at.utcoffset() is not None
            service.delete(other, fid)
            assert session.get(Favorite, fid) is not None
            assert not service.status(
                other, FavoriteStatusRequest(type="MUSIC", item_ids=[item_id])
            ).favorites
        checks.append("multiprocess_upsert_first_snapshot_owner_isolation")
        stage("multiprocess_create_delete")
        with ProcessPoolExecutor(max_workers=3) as pool:
            futures = [
                pool.submit(favorite_worker, value, owner, body, result, mode)
                for mode in ("create", "create", "delete")
            ]
            assert all(f.result(timeout=60) for f in futures)
        with Session(engine) as session:
            assert session.scalar(select(func.count()).select_from(Favorite)) <= 1
            saved, _ = FavoriteService(session).create(
                owner, FavoriteCreate(**body), result
            )
            assert saved.item == item
        checks.append("multiprocess_create_delete_returning")
        stage("cache_ttl")
        cache = RecommendationCache(sessionmaker(engine))
        clock = 1000.0
        with patch("app.services.recommendation_cache.time", return_value=clock):
            cache.put(result)
        with patch("app.services.recommendation_cache.time", return_value=clock + 10):
            assert cache.get(str(origin)) == result
            cache.put(result)
        with Session(engine) as session:
            row = session.get(RecommendationResult, origin)
            assert row.created_at == 1000000 and row.expires_at == 4600000
        with patch("app.services.recommendation_cache.time", return_value=clock + 3600):
            assert cache.get(str(origin)) is None
        stage("multiprocess_cache_capacity_cascade")
        with ProcessPoolExecutor(max_workers=3) as pool:
            futures = [pool.submit(cache_worker, value, 95) for _ in range(3)]
            assert all(f.result(timeout=90) for f in futures)
        with Session(engine) as session:
            assert (
                session.scalar(select(func.count()).select_from(RecommendationResult))
                == 256
            )
            session.execute(delete(RecommendationResult))
            session.commit()
            assert session.get(Favorite, saved.id).item == item
            session.execute(delete(User).where(User.id == owner))
            session.commit()
            assert session.get(Favorite, saved.id) is None
            assert session.get(User, other) is not None
        checks.append("postgres_advisory_cache_capacity_ttl_snapshot_cascade")
        stage("migration_round_trip_base")
        migrate("0007_recommendation_results", downgrade=True)
        assert "favorites" not in inspect(engine).get_table_names()
        with Session(engine) as session:
            assert session.get(User, other) is not None
        migrate("head")
        migrate("base", downgrade=True)
        assert set(inspect(engine).get_table_names()) <= {"alembic_version"}
        checks.append("downgrade_upgrade_preserves_other_owner_then_base")
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "server": version,
                    "extensions": extensions,
                    "checks": checks,
                    "utc_ms": int(time() * 1000),
                }
            )
        )
    finally:
        # On failure leave disposable state intact for diagnosis; never auto-drop.
        engine.dispose()


def main():
    freeze_support()
    try:
        if not __debug__:
            raise ValueError("Functional assertions require Python without -O.")
        if os.environ.get("GANDALF_PG_GATE_ALLOW") != "isolated-coordinated":
            raise ValueError(
                "Run only after Maestro coordinates the disposable container."
            )
        run(os.environ["GANDALF_PG_GATE_URL"])
    except Exception as exc:  # noqa: BLE001 - terminal boundary redacts DB secrets
        # No DSN/password or arbitrary DB exception content in terminal output.
        print(
            json.dumps(
                {
                    "status": "NOT_PASSED",
                    "stage": STAGE,
                    "error_class": type(exc).__name__,
                }
            )
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
