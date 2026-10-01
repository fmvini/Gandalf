from pathlib import Path

from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect

from alembic import command
from app.core.config import Settings
from app.main import create_app


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
    assert "FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE" in script
    assert (
        "FOREIGN KEY(music_id) REFERENCES music_catalog (id) ON DELETE RESTRICT"
        in script
    )
