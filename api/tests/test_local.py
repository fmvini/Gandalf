import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database.session import make_engine
from app.main import create_app

spec = importlib.util.spec_from_file_location(
    "local_runner", Path(__file__).resolve().parents[1] / "local.py"
)
local = importlib.util.module_from_spec(spec)
spec.loader.exec_module(local)


def test_local_bootstrap_is_persistent_and_isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://must-not-connect.invalid/paid")
    monkeypatch.setenv("BOOK_PROVIDER", "open_library")
    settings = local.local_settings(tmp_path)
    assert settings.book_provider == "local"
    assert len(settings.jwt_secret) >= 32
    local.prepare(settings)
    with TestClient(create_app(settings=settings)) as client:
        assert client.get("/health/ready").status_code == 200
        assert (
            client.post(
                "/api/v1/auth/register",
                json={
                    "email": "local@example.com",
                    "username": "local_user",
                    "password": "a-local-password",
                },
            ).status_code
            == 201
        )
        assert client.get("/api/v1/books/search?q=Duna").status_code == 200
    again = local.local_settings(tmp_path)
    assert again.jwt_secret == settings.jwt_secret
    local.prepare(again)
    with TestClient(create_app(settings=again)) as client:
        assert (
            client.post(
                "/api/v1/auth/login",
                json={"email": "local@example.com", "password": "a-local-password"},
            ).status_code
            == 200
        )
        assert client.get("/health/ready").status_code == 200
    engine = make_engine(settings.database_url)
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE external_search_cache"))
    engine.dispose()
    with TestClient(create_app(settings=settings)) as client:
        assert client.get("/health/ready").status_code == 503
