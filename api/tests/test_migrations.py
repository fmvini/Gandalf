from pathlib import Path
from uuid import uuid4

import pytest
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from alembic import command
from app.core.config import Settings
from app.database.base import Base
from app.main import create_app
from app.models import MusicCatalog, Playlist, PlaylistTrack, RecommendationResult, User


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
