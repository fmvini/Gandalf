from pathlib import Path
from uuid import UUID, uuid4

import pytest
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, inspect, null, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from alembic import command
from app.core.config import Settings
from app.database.base import Base
from app.database.session import make_engine
from app.main import create_app
from app.models import (
    Book,
    Favorite,
    MusicCatalog,
    Playlist,
    PlaylistTrack,
    RecommendationResult,
    User,
)


def test_migrations_upgrade_and_downgrade_on_sqlite(
    tmp_path: Path, monkeypatch
) -> None:
    database_url = f"sqlite:///{tmp_path / 'migration.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))

    command.upgrade(config, "head")
    engine = create_engine(database_url)
    assert {
        "users",
        "refresh_tokens",
        "user_preferences",
        "interactions",
        "search_history",
        "books",
        "external_search_cache",
        "music_catalog",
        "ai_usage",
        "playlists",
        "playlist_tracks",
        "recommendation_results",
        "favorites",
        "alembic_version",
    } <= set(inspect(engine).get_table_names())
    engine.dispose()

    with TestClient(create_app(settings=Settings(database_url=database_url))) as client:
        readiness = client.get("/health/ready")
        assert readiness.status_code == 200
        assert readiness.json()["components"] == {
            "database": "ok",
            "schema": "ok",
            "pgvector": "not_required",
        }

    command.downgrade(config, "base")
    engine = create_engine(database_url)
    assert "users" not in inspect(engine).get_table_names()
    assert "books" not in inspect(engine).get_table_names()
    assert "external_search_cache" not in inspect(engine).get_table_names()
    assert "playlists" not in inspect(engine).get_table_names()
    assert "playlist_tracks" not in inspect(engine).get_table_names()
    assert "recommendation_results" not in inspect(engine).get_table_names()
    assert "favorites" not in inspect(engine).get_table_names()
    engine.dispose()


def test_postgresql_migration_generates_extensions_and_tables(
    monkeypatch, capsys
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+psycopg://gandalf:local@127.0.0.1:5433/gandalf"
    )
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))

    command.upgrade(config, "head", sql=True)
    script = capsys.readouterr().out
    assert "CREATE EXTENSION IF NOT EXISTS citext" in script
    assert "CREATE EXTENSION IF NOT EXISTS vector" in script
    assert "CREATE TABLE users" in script
    assert "CREATE TABLE external_search_cache" in script
    assert "CREATE TABLE playlists" in script
    assert "CREATE TABLE playlist_tracks" in script
    assert "CREATE TABLE recommendation_results" in script
    assert "CREATE TABLE favorites" in script
    assert "item_id UUID NOT NULL" in script
    assert "item JSONB NOT NULL" in script
    assert "source_recommendation_id UUID NOT NULL" in script
    assert "created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL" in script
    assert "CONSTRAINT ck_favorites_type CHECK (type IN ('MUSIC', 'BOOK'))" in script
    assert (
        "CONSTRAINT uq_favorites_user_type_item UNIQUE (user_id, type, item_id)"
        in script
    )
    assert (
        "CREATE INDEX ix_favorites_user_created ON favorites (user_id, created_at, id)"
        in script
    )
    assert (
        "CREATE INDEX ix_favorites_user_type_created ON favorites (user_id, type, created_at, id)"
        in script
    )
    favorite_sql = script.split("CREATE TABLE favorites", 1)[1].split(";", 1)[0]
    assert favorite_sql.count("FOREIGN KEY") == 1
    assert (
        "FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE" in favorite_sql
    )
    command.downgrade(config, "0008_favorites:0007_recommendation_results", sql=True)
    downgrade_sql = capsys.readouterr().out
    assert "DROP INDEX ix_favorites_user_type_created" in downgrade_sql
    assert "DROP INDEX ix_favorites_user_created" in downgrade_sql
    assert "DROP TABLE favorites" in downgrade_sql
    assert "DROP TABLE users" not in downgrade_sql
    assert "response JSONB NOT NULL" in script
    assert "created_at BIGINT NOT NULL" in script
    assert "expires_at BIGINT NOT NULL" in script
    assert (
        "CREATE INDEX ix_recommendation_results_created "
        "ON recommendation_results (created_at, id)" in script
    )
    assert (
        "CREATE INDEX ix_recommendation_results_expires "
        "ON recommendation_results (expires_at)" in script
    )
    assert "FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE" in script
    assert (
        "FOREIGN KEY(music_id) REFERENCES music_catalog (id) ON DELETE RESTRICT"
        in script
    )


def test_result_cache_migration_preserves_accounts_playlists_and_snapshots(
    tmp_path: Path, monkeypatch
) -> None:
    database_url = f"sqlite:///{tmp_path / 'result-cache.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(config, "0006_playlists")
    engine = create_engine(database_url)
    user_id, playlist_id, result_id = uuid4(), uuid4(), uuid4()
    music_id = str(uuid4())
    item = {"id": music_id, "title": "Chuva", "artist": "Teste", "duration_ms": 120000}
    response = {
        "items": [{"position": 1, "item": item, "explanation": "Piano para leitura."}],
        "playlist": {"total_duration_ms": 120000, "duration_estimated": False},
    }
    with Session(engine) as session:
        session.add(
            User(
                id=user_id,
                email="schema@example.com",
                username="schema",
                password_hash="test",
            )
        )
        session.add(MusicCatalog(id=music_id, data=item))
        session.flush()
        session.add(
            Playlist(
                id=playlist_id,
                user_id=user_id,
                name="Leitura",
                source="MANUAL",
                total_duration_ms=120000,
                duration_estimated=False,
            )
        )
        session.flush()
        session.add(
            PlaylistTrack(
                playlist_id=playlist_id, position=1, music_id=music_id, item=item
            )
        )
        session.commit()
    command.upgrade(config, "head")
    with engine.connect() as connection:
        assert (
            compare_metadata(MigrationContext.configure(connection), Base.metadata)
            == []
        )
    with Session(engine) as session:
        session.add(
            RecommendationResult(
                id=result_id,
                response=response,
                created_at=1790852400000,
                expires_at=1790856000000,
            )
        )
        session.commit()
    # An independent engine/process reads the same Unicode snapshot and 64-bit timestamps.
    reader = create_engine(database_url)
    try:
        with Session(reader) as session:
            cached = session.get(RecommendationResult, result_id)
            assert cached.response == response
            assert cached.created_at == 1790852400000
            assert cached.expires_at == 1790856000000
            assert session.get(User, user_id).username == "schema"
            assert session.get(Playlist, playlist_id).name == "Leitura"
            assert session.get(PlaylistTrack, (playlist_id, 1)).item == item
            assert session.get(MusicCatalog, music_id).data == item
    finally:
        reader.dispose()
    command.downgrade(config, "0006_playlists")
    assert "recommendation_results" not in inspect(engine).get_table_names()
    command.upgrade(config, "head")
    with Session(engine) as session:
        assert session.scalar(select(RecommendationResult.id)) is None
        assert session.get(User, user_id) is not None
        assert session.get(Playlist, playlist_id) is not None
        assert session.get(PlaylistTrack, (playlist_id, 1)).item == item
        assert session.get(MusicCatalog, music_id).data == item
    engine.dispose()


def test_result_cache_rejects_duplicate_ids_and_missing_snapshots(
    tmp_path: Path, monkeypatch
) -> None:
    database_url = f"sqlite:///{tmp_path / 'result-constraints.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(config, "head")
    engine = create_engine(database_url)
    result_id = uuid4()
    table = RecommendationResult.__table__
    values = {
        "id": result_id,
        "response": {"items": []},
        "created_at": 1790852400000,
        "expires_at": 1790856000000,
    }
    with engine.begin() as connection:
        connection.execute(table.insert().values(**values))
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(table.insert().values(**values))
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(
            table.insert().values(id=uuid4(), created_at=1, expires_at=2)
        )
    with engine.connect() as connection:
        assert connection.execute(select(table)).one().response == {"items": []}
    engine.dispose()


@pytest.fixture
def favorite_schema(tmp_path: Path, monkeypatch):
    database_url = f"sqlite:///{tmp_path / 'favorites.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(config, "head")
    engine = make_engine(database_url)
    user_id, other_user_id = uuid4(), uuid4()
    with Session(engine) as session:
        session.add_all(
            [
                User(
                    id=user_id,
                    email="favorite@example.com",
                    username="favorite",
                    password_hash="test",
                ),
                User(
                    id=other_user_id,
                    email="other@example.com",
                    username="other",
                    password_hash="test",
                ),
            ]
        )
        session.commit()
    yield engine, config, user_id, other_user_id
    engine.dispose()


def favorite_values(user_id):
    item_id = uuid4()
    return {
        "user_id": user_id,
        "type": "MUSIC",
        "item_id": item_id,
        "item": {"id": str(item_id), "title": "Canção de chuva", "artist": "Teste"},
        "source_recommendation_id": uuid4(),
    }


def test_favorites_uniqueness_is_scoped_to_owner_and_type(favorite_schema) -> None:
    engine, _, user_id, other_user_id = favorite_schema
    values = favorite_values(user_id)
    with Session(engine) as session:
        favorite = Favorite(**values)
        session.add(favorite)
        session.commit()
        favorite_id, created_at = favorite.id, favorite.created_at
        assert isinstance(favorite_id, UUID) and favorite_id.version == 4
        assert created_at is not None
    with pytest.raises(IntegrityError), Session(engine) as session:
        session.add(Favorite(**{**values, "item": {"title": "Outro snapshot"}}))
        session.commit()
    with Session(engine) as session:
        session.add_all(
            [
                Favorite(**{**values, "type": "BOOK"}),
                Favorite(**{**values, "user_id": other_user_id}),
            ]
        )
        session.commit()
        rows = session.scalars(select(Favorite)).all()
        assert len(rows) == 3
        original = session.get(Favorite, favorite_id)
        assert original.item == values["item"]
        assert original.source_recommendation_id == values["source_recommendation_id"]
        assert original.created_at == created_at


@pytest.mark.parametrize(
    "invalid",
    [
        {"type": "OTHER"},
        {"type": "music"},
        {"type": null()},
        {"id": null()},
        {"user_id": null()},
        {"item_id": null()},
        {"item": null()},
        {"source_recommendation_id": null()},
        {"created_at": null()},
        {"user_id": uuid4()},
    ],
)
def test_favorites_enforce_checks_required_fields_and_owner_fk(
    favorite_schema, invalid
) -> None:
    engine, _, user_id, _ = favorite_schema
    with engine.connect() as connection:
        assert connection.scalar(text("PRAGMA foreign_keys")) == 1
    with pytest.raises(IntegrityError), engine.begin() as connection:
        connection.execute(
            Favorite.__table__.insert().values(
                **{**favorite_values(user_id), **invalid}
            )
        )
    with Session(engine) as session:
        assert session.scalar(select(Favorite.id)) is None


def test_favorites_outlive_origin_and_catalog_but_cascade_with_owner(
    favorite_schema,
) -> None:
    engine, _, user_id, other_user_id = favorite_schema
    values = favorite_values(user_id)
    origin_id = values["source_recommendation_id"]
    with Session(engine) as session:
        session.add(
            RecommendationResult(
                id=origin_id, response={"items": []}, created_at=1, expires_at=2
            )
        )
        session.add(MusicCatalog(id=str(values["item_id"]), data=values["item"]))
        session.add_all(
            [Favorite(**values), Favorite(**{**values, "user_id": other_user_id})]
        )
        session.commit()
        first_id = session.scalar(
            select(Favorite.id).where(Favorite.user_id == user_id)
        )
        second_id = session.scalar(
            select(Favorite.id).where(Favorite.user_id == other_user_id)
        )
        session.execute(
            delete(RecommendationResult).where(RecommendationResult.id == origin_id)
        )
        session.execute(delete(MusicCatalog))
        session.commit()
        assert session.get(Favorite, first_id).item == values["item"]
        assert session.get(Favorite, second_id).source_recommendation_id == origin_id
        session.execute(delete(User).where(User.id == user_id))
        session.commit()
    with Session(engine) as session:
        assert session.get(Favorite, first_id) is None
        assert session.get(Favorite, second_id).item == values["item"]
        assert session.get(User, other_user_id) is not None
        assert session.scalar(select(MusicCatalog.id)) is None
        assert session.scalar(select(RecommendationResult.id)) is None
    foreign_keys = inspect(engine).get_foreign_keys("favorites")
    assert len(foreign_keys) == 1
    assert foreign_keys[0]["constrained_columns"] == ["user_id"]
    assert foreign_keys[0]["options"]["ondelete"] == "CASCADE"


def test_favorites_migration_round_trip_preserves_all_existing_tables(
    tmp_path: Path, monkeypatch
) -> None:
    database_url = f"sqlite:///{tmp_path / 'favorite-round-trip.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(config, "0007_recommendation_results")
    engine = make_engine(database_url)
    user_id, playlist_id, result_id, book_id = uuid4(), uuid4(), uuid4(), uuid4()
    values = favorite_values(user_id)
    music_id, item = str(values["item_id"]), values["item"]
    with Session(engine) as session:
        session.add(
            User(
                id=user_id,
                email="roundtrip@example.com",
                username="roundtrip",
                password_hash="test",
            )
        )
        session.add(MusicCatalog(id=music_id, data=item))
        session.add(
            Book(
                id=book_id,
                provider="test",
                external_id="book",
                title="Livro",
                authors=["Autor"],
                genres=[],
                subjects=[],
                external_url="https://example.com/book",
                metadata_json={},
            )
        )
        session.add(
            RecommendationResult(
                id=result_id, response={"items": []}, created_at=1, expires_at=2
            )
        )
        session.flush()
        session.add(
            Playlist(
                id=playlist_id,
                user_id=user_id,
                name="Trilha",
                source="MANUAL",
                total_duration_ms=0,
                duration_estimated=True,
            )
        )
        session.flush()
        session.add(
            PlaylistTrack(
                playlist_id=playlist_id, position=1, music_id=music_id, item=item
            )
        )
        session.commit()
    existing_tables = set(inspect(engine).get_table_names()) - {"alembic_version"}

    def rows_before_or_after():
        with engine.connect() as connection:
            return {
                name: connection.execute(Base.metadata.tables[name].select()).all()
                for name in existing_tables
            }

    before = rows_before_or_after()
    command.upgrade(config, "head")
    assert rows_before_or_after() == before
    with engine.connect() as connection:
        assert (
            compare_metadata(MigrationContext.configure(connection), Base.metadata)
            == []
        )
    with Session(engine) as session:
        session.add(Favorite(**values))
        session.commit()
    command.downgrade(config, "0007_recommendation_results")
    assert "favorites" not in inspect(engine).get_table_names()
    assert rows_before_or_after() == before
    command.upgrade(config, "head")
    assert rows_before_or_after() == before
    with Session(engine) as session:
        assert session.scalar(select(Favorite.id)) is None
    engine.dispose()
