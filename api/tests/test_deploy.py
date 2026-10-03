"""Environment-only startup regression, without real credentials or listeners."""

import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import deploy
from app.core.config import Settings

SECRET = "synthetic-deployment-secret-32-bytes-minimum"
PG_URL = "postgresql+psycopg://synthetic:synthetic@db.invalid:5432/disposable"


@pytest.fixture(autouse=True)
def isolated_environment(tmp_path, monkeypatch):
    # app.main has an unused default app at import; import only from this safe cwd.
    monkeypatch.chdir(tmp_path)
    for field in Settings.model_fields:
        monkeypatch.delenv(field.upper(), raising=False)
    for field in (
        "GANDALF_HOST",
        "GANDALF_PORT",
        "GANDALF_ONLINE",
        "GANDALF_LOCAL_DATA",
    ):
        monkeypatch.delenv(field, raising=False)
    monkeypatch.setenv("DATABASE_URL", PG_URL)
    monkeypatch.setenv("JWT_SECRET", SECRET)
    monkeypatch.setenv("ONLINE_CATALOG", "false")
    monkeypatch.setenv("BOOK_PROVIDER", "local")


def modules():
    local = importlib.import_module("local")
    app_main = importlib.import_module("app.main")
    return local, app_main


def test_reproduce_local_launcher_overrides_deployment_target_and_secret(
    tmp_path, monkeypatch
):
    local, _ = modules()
    monkeypatch.setenv("CORS_ORIGINS", '["https://synthetic.example.test"]')
    settings = local.local_settings(tmp_path / "legacy-local")
    assert settings.database_url.startswith("sqlite:///")
    assert settings.database_url != PG_URL
    assert settings.jwt_secret != SECRET
    assert settings.cors_origins == ["http://localhost:5173", "http://127.0.0.1:5173"]


def test_deployment_preserves_explicit_db_secret_cors_and_offline_without_local_files(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("CORS_ORIGINS", '["https://synthetic.example.test"]')
    monkeypatch.setenv(
        "GANDALF_ONLINE", "1"
    )  # Only legacy local.py consumes this flag.
    settings = deploy.deployment_settings()
    assert settings.database_url == PG_URL
    assert settings.jwt_secret == SECRET
    assert settings.cors_origins == ["https://synthetic.example.test"]
    assert settings.online_catalog is False
    assert settings.book_provider == "local"
    assert settings.groq_api_key.get_secret_value() == ""
    assert list(tmp_path.iterdir()) == []


def test_deployment_settings_do_not_consume_dotenv(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text(
        "DATABASE_URL=sqlite:///unwanted.db\nJWT_SECRET=unwanted\nONLINE_CATALOG=true\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("DATABASE_URL")
    with pytest.raises(
        deploy.DeploymentConfigurationError, match="Invalid deployment configuration"
    ):
        deploy.deployment_settings()


@pytest.mark.parametrize(
    "url",
    [
        "",
        " ",
        "not-a-url",
        "postgresql+psycopg://",
        "postgresql+psycopg://synthetic@db.invalid",
        "postgresql+psycopg://synthetic@db.invalid:99999/disposable",
        "mysql://synthetic@db.invalid/disposable",
        "sqlite://",
        "sqlite:///:memory:",
        "sqlite:///file:temporary?mode=memory&uri=true",
    ],
)
def test_invalid_database_fails_before_import_or_local_storage(
    url, tmp_path, monkeypatch, capsys
):
    monkeypatch.setenv("DATABASE_URL", url)
    assert deploy.main() == 1
    assert list(tmp_path.iterdir()) == []
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "Deployment startup failed.\n"
    assert url not in captured.err if url.strip() else True


@pytest.mark.parametrize("secret", ["", "short-secret", "x" * 31, " " * 32])
def test_invalid_jwt_fails_before_migration(secret, tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("JWT_SECRET", secret)
    assert deploy.main() == 1
    assert list(tmp_path.iterdir()) == []
    assert capsys.readouterr().err == "Deployment startup failed.\n"


def test_jwt_guard_matches_auth_utf8_byte_contract(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "ç" * 16)
    assert deploy.deployment_settings().jwt_secret == "ç" * 16


@pytest.mark.parametrize(
    "field,value",
    [
        ("GANDALF_HOST", ""),
        ("GANDALF_HOST", "https://synthetic.example.test"),
        ("GANDALF_HOST", "0.0.0.0\n"),
        ("GANDALF_PORT", "0"),
        ("GANDALF_PORT", "65536"),
        ("GANDALF_PORT", "not-a-port"),
        ("GANDALF_PORT", " 8000"),
        ("GANDALF_PORT", "٨٠٠٠"),
        ("CORS_ORIGINS", "not-json"),
        ("AI_DAILY_LIMIT", "-1"),
    ],
)
def test_invalid_binding_or_config_fails_before_migration(
    field, value, monkeypatch, capsys, tmp_path
):
    monkeypatch.setenv(field, value)
    assert deploy.main() == 1
    assert capsys.readouterr().err == "Deployment startup failed.\n"
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    "host,port",
    [("0.0.0.0", "8000"), ("127.0.0.1", "65535"), ("::", "1"), ("localhost", "8080")],
)
def test_binding_preserves_explicit_valid_values(host, port, monkeypatch):
    monkeypatch.setenv("GANDALF_HOST", host)
    monkeypatch.setenv("GANDALF_PORT", port)
    assert deploy.binding() == (host, int(port))


def test_migrate_before_serve_and_same_settings_without_secret_or_db_override(
    monkeypatch,
):
    local, app_main = modules()
    events = []
    monkeypatch.setattr(
        local, "prepare", lambda settings: events.append(("migrate", settings))
    )

    def factory(*, settings):
        events.append(("app", settings))
        return "synthetic-app"

    def serve(app, **kwargs):
        assert app == "synthetic-app"
        assert kwargs == {"host": "0.0.0.0", "port": 8000}
        events.append(("serve", None))

    monkeypatch.setattr(app_main, "create_app", factory)
    monkeypatch.setattr("uvicorn.run", serve)
    assert deploy.main() == 0
    assert [event for event, _ in events] == ["migrate", "app", "serve"]
    assert events[0][1] is events[1][1]
    assert events[0][1].database_url == PG_URL
    assert events[0][1].jwt_secret == SECRET


@pytest.mark.parametrize("failure", ["migrate", "factory"])
def test_startup_failure_is_sanitized_and_never_listens(failure, monkeypatch, capsys):
    local, app_main = modules()

    def fail(*args, **kwargs):
        raise RuntimeError(f"private DSN={PG_URL} key={SECRET}")

    monkeypatch.setattr(
        local, "prepare", fail if failure == "migrate" else lambda settings: None
    )
    monkeypatch.setattr(
        app_main, "create_app", fail if failure == "factory" else lambda **kwargs: "app"
    )
    monkeypatch.setattr(
        "uvicorn.run",
        lambda *args, **kwargs: pytest.fail("Must not listen after startup failure"),
    )
    assert deploy.main() == 1
    captured = capsys.readouterr()
    assert captured.err == "Deployment startup failed.\n"
    assert captured.out == ""


def test_prepare_uses_explicit_connection_even_when_environment_changes(monkeypatch):
    local, _ = modules()
    settings = deploy.deployment_settings()
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://wrong@wrong.invalid/wrong")
    connection = object()
    calls = []

    class Transaction:
        def __enter__(self):
            return connection

        def __exit__(self, *args):
            return False

    class Engine:
        def begin(self):
            return Transaction()

        def dispose(self):
            calls.append("disposed")

    monkeypatch.setattr(
        "app.database.session.make_engine", lambda url: calls.append(url) or Engine()
    )
    monkeypatch.setattr(
        local.command,
        "upgrade",
        lambda config, revision: calls.append(
            (config.attributes["connection"], revision)
        ),
    )
    local.prepare(settings)
    assert calls == [PG_URL, (connection, "head"), "disposed"]


def test_offline_app_migrated_sqlite_health_readiness_status_and_cors(
    tmp_path, monkeypatch
):
    local, app_main = modules()
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'deployment.db'}")
    monkeypatch.setenv("CORS_ORIGINS", '["https://synthetic.example.test"]')
    settings = deploy.deployment_settings()
    local.prepare(settings)

    def no_external_client():
        pytest.fail("Offline deployment must not open external provider/LLM client")

    monkeypatch.setattr(app_main, "external_client", no_external_client)
    with TestClient(app_main.create_app(settings=settings)) as client:
        assert client.get("/health").json() == {"status": "ok"}
        ready = client.get("/health/ready")
        assert ready.status_code == 200
        assert ready.json()["components"] == {
            "database": "ok",
            "schema": "ok",
            "pgvector": "not_required",
        }
        assert client.get("/api/v1/system/status").json() == {
            "catalog": "local",
            "ai": {"provider": None, "configured": False, "model": None},
            "gpu_used": False,
        }
        preflight = client.options(
            "/api/v1/music/search",
            headers={
                "Origin": "https://synthetic.example.test",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert (
            preflight.headers["access-control-allow-origin"]
            == "https://synthetic.example.test"
        )
    assert not (tmp_path / ".local").exists()
    assert not (tmp_path / "jwt-secret").exists()


def test_docker_copies_explicit_entrypoint_and_keeps_local_default():
    text = (Path(__file__).resolve().parents[1] / "Dockerfile").read_text(
        encoding="utf-8"
    )
    assert "COPY api/alembic.ini api/local.py api/deploy.py ./" in text
    assert 'CMD ["python", "local.py"]' in text
