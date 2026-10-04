"""Serverless startup contract with synthetic settings and no remote database."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import make_url

from app.core.config import Settings

ENTRYPOINT = Path(__file__).resolve().parents[1] / "vercel_app.py"
SECRET = "synthetic-vercel-jwt-secret-at-least-32-bytes"
URL = "postgresql://synthetic:synthetic@ep-public-pooler.eu-central-1.aws.neon.tech/disposable?sslmode=require&channel_binding=require"


@pytest.fixture(autouse=True)
def isolated_environment(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for field in Settings.model_fields:
        monkeypatch.delenv(field.upper(), raising=False)
    monkeypatch.setenv("DATABASE_URL", URL)
    monkeypatch.setenv("JWT_SECRET", SECRET)
    monkeypatch.setenv("ONLINE_CATALOG", "false")
    monkeypatch.setenv("BOOK_PROVIDER", "local")


def load_entrypoint():
    spec = importlib.util.spec_from_file_location(
        "isolated_vercel_entrypoint", ENTRYPOINT
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fake_factory(monkeypatch, *, import_failure=False):
    events = []

    def import_main(name):
        assert name == "app.main"
        assert Settings.model_config["env_file"] is None
        if import_failure:
            raise RuntimeError("synthetic import failure")
        events.append(("default", Settings()))

        def create_app(*, settings):
            events.append(("selected", settings))
            return SimpleNamespace(settings=settings)

        return SimpleNamespace(create_app=create_app)

    monkeypatch.setattr("importlib.import_module", import_main)
    return events


def test_normalized_url_and_environment_passed_to_factory_without_dotenv(
    tmp_path, monkeypatch
):
    (tmp_path / ".env").write_text(
        "ONLINE_CATALOG=true\nBOOK_PROVIDER=open_library\nGROQ_API_KEY=forbidden\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CORS_ORIGINS", '["https://gandalf.example.com"]')
    previous = Settings.model_config
    events = fake_factory(monkeypatch)
    module = load_entrypoint()
    assert [name for name, _ in events] == ["default", "selected"]
    assert Settings.model_config is previous
    for _, settings in events:
        assert settings.online_catalog is False
        assert settings.book_provider == "local"
        assert settings.groq_api_key.get_secret_value() == ""
    settings = module.app.settings
    assert make_url(settings.database_url) == make_url(URL).set(
        drivername="postgresql+psycopg"
    )
    assert settings.jwt_secret == SECRET
    assert settings.cors_origins == ["https://gandalf.example.com"]
    assert list(tmp_path.iterdir()) == [tmp_path / ".env"]


@pytest.mark.parametrize("mode", ["require", "verify-ca", "verify-full"])
@pytest.mark.parametrize("scheme", ["postgresql", "postgresql+psycopg"])
def test_accepts_explicit_encrypted_neon_urls(mode, scheme, monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        URL.replace("postgresql://", scheme + "://").replace("require", mode, 1),
    )
    fake_factory(monkeypatch)
    assert load_entrypoint().app.settings.database_url.startswith(
        "postgresql+psycopg://"
    )


@pytest.mark.parametrize(
    "url",
    [
        None,
        "",
        "not-a-url-secret-marker",
        "sqlite:///forbidden.db",
        URL.replace("postgresql://", "postgres://"),
        URL.replace("postgresql://", "postgresql+psycopg2://"),
        URL.replace(".neon.tech", ".neon.tech.attacker.example"),
        URL.replace("ep-public-pooler.eu-central-1.aws.neon.tech", "127.0.0.1"),
        URL.replace("ep-public-pooler.eu-central-1.aws.neon.tech", "neon.tech"),
        URL.replace("synthetic:synthetic@", "synthetic@"),
        URL.replace("synthetic:synthetic@", ":synthetic@"),
        URL.replace("/disposable?", "/?"),
        URL.replace(".tech/", ".tech:8000/"),
        URL.replace("sslmode=require", "sslmode=disable"),
        URL.replace("sslmode=require", "sslmode=prefer"),
        URL.replace("sslmode=require&", ""),
        URL + "&sslmode=disable",
        URL + "&host=attacker.example",
        URL + "&hostaddr=127.0.0.1",
        URL + "&service=unexpected",
        URL + "&connect_timeout=0",
        URL + "&connect_timeout=61",
        URL + "&connect_timeout=secret-marker",
        URL.replace("channel_binding=require", "channel_binding=secret-marker"),
    ],
)
def test_invalid_database_fails_generically_before_main_import(
    url, tmp_path, monkeypatch, capsys
):
    if url is None:
        monkeypatch.delenv("DATABASE_URL")
    else:
        monkeypatch.setenv("DATABASE_URL", url)
    events = fake_factory(monkeypatch)
    with pytest.raises(ValueError) as error:
        load_entrypoint()
    assert str(error.value) == "Invalid Vercel configuration."
    assert error.value.__suppress_context__ is True
    assert not events
    assert list(tmp_path.iterdir()) == []
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize("secret", [None, "", " ", "x" * 31, " " * 64])
def test_invalid_secret_fails_before_factory(secret, monkeypatch):
    if secret is None:
        monkeypatch.delenv("JWT_SECRET")
    else:
        monkeypatch.setenv("JWT_SECRET", secret)
    events = fake_factory(monkeypatch)
    with pytest.raises(ValueError, match="^Invalid Vercel configuration.$"):
        load_entrypoint()
    assert not events


def test_dotenv_cannot_supply_required_database(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text(
        "DATABASE_URL=" + URL + "\nJWT_SECRET=" + SECRET + "\n", encoding="utf-8"
    )
    monkeypatch.delenv("DATABASE_URL")
    monkeypatch.delenv("JWT_SECRET")
    events = fake_factory(monkeypatch)
    with pytest.raises(ValueError, match="^Invalid Vercel configuration.$"):
        load_entrypoint()
    assert not events


def test_dotenv_guard_restored_even_when_import_fails(monkeypatch):
    previous = Settings.model_config
    fake_factory(monkeypatch, import_failure=True)
    with pytest.raises(ValueError, match="^Vercel startup failed.$"):
        load_entrypoint()
    assert Settings.model_config is previous


def test_factory_failure_never_exposes_credentials(monkeypatch, capsys):
    previous = Settings.model_config

    def create_app(**_kwargs):
        raise RuntimeError(URL + SECRET)

    monkeypatch.setattr(
        "importlib.import_module", lambda _name: SimpleNamespace(create_app=create_app)
    )
    with pytest.raises(ValueError) as error:
        load_entrypoint()
    assert str(error.value) == "Vercel startup failed."
    assert error.value.__suppress_context__ is True
    assert Settings.model_config is previous
    assert capsys.readouterr() == ("", "")


def test_invalid_other_settings_are_sanitized(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "sensitive-invalid-input")
    events = fake_factory(monkeypatch)
    with pytest.raises(ValueError, match="^Invalid Vercel configuration.$"):
        load_entrypoint()
    assert not events


def test_public_timeout_and_online_settings_preserved(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", URL + "&connect_timeout=10")
    monkeypatch.setenv("ONLINE_CATALOG", "true")
    monkeypatch.setenv("BOOK_PROVIDER", "open_library")
    fake_factory(monkeypatch)
    settings = load_entrypoint().app.settings
    assert make_url(settings.database_url).query["connect_timeout"] == "10"
    assert settings.online_catalog is True
    assert settings.book_provider == "open_library"
    assert settings.groq_api_key.get_secret_value() == ""


def test_actual_factory_lifespan_uses_only_fake_pg_engine_and_disposes(
    tmp_path, monkeypatch
):
    module = load_entrypoint()
    main = __import__("app.main", fromlist=["make_engine"])
    events = []

    class FakeEngine:
        def dispose(self):
            events.append("disposed")

    def make_engine(url):
        assert make_url(url) == make_url(URL).set(drivername="postgresql+psycopg")
        events.append("engine")
        return FakeEngine()

    monkeypatch.setattr(main, "make_engine", make_engine)
    assert events == []  # Import creates neither an engine nor a connection.
    with TestClient(module.app) as client:
        assert client.get("/health").json() == {"status": "ok"}
        assert client.get("/api/v1/system/status").json()["ai"]["configured"] is False
        assert events == ["engine"]
    assert events == ["engine", "disposed"]
    assert list(tmp_path.iterdir()) == []


def test_entrypoint_contains_no_migration_or_server_launcher():
    import ast

    tree = ast.parse(ENTRYPOINT.read_text(encoding="utf-8"))
    names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for node in node.names
    }
    assert not {"uvicorn", "alembic", "local", "deploy"} & names
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"upgrade", "run", "prepare"}
        for node in ast.walk(tree)
    )
