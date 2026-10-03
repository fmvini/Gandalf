"""No PostgreSQL/network: refusal fakes and a real two-app temporary SQLite flow."""

import importlib
import json
import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from scripts import postgres_http_gate as gate

DATABASE = "gandalf_gate_00000000000000000000000000000001"
TARGET = f"postgresql+psycopg://gandalf_gate:test-only@127.0.0.1:55432/{DATABASE}"


@pytest.fixture
def runtime():
    return gate.load_runtime()


def public_fixture():
    return {
        "status": "PASS",
        "transport": "ASGI_TWO_APPS_SINGLE_PROCESS",
        "checks": list(gate.CHECKS),
        "counts": dict(zip(gate.COUNT_FIELDS, (2, 1, 1, 3, 1, 8, 1, 0), strict=True)),
        "requests": {"a": 24, "b": 25},
        "source_unchanged": True,
        "source_sha256": "0" * 64,
        "head": ["0008_favorites"],
        "observer_disposed": True,
    }


def test_runtime_imports_use_empty_cwd_and_sanitized_environment(monkeypatch):
    before = Path.cwd()
    monkeypatch.setenv("DATABASE_URL", "private-marker")
    monkeypatch.setenv("JWT_SECRET", "private-marker")
    imported = []

    def safe_import(name):
        require_empty = not list(Path.cwd().iterdir())
        assert require_empty and Path.cwd() != before
        assert "DATABASE_URL" not in os.environ and "JWT_SECRET" not in os.environ
        imported.append(name)
        return MagicMock()

    monkeypatch.setattr(gate.importlib, "import_module", safe_import)
    gate.load_runtime()
    assert "app.main" in imported and Path.cwd() == before
    assert os.environ["DATABASE_URL"] == os.environ["JWT_SECRET"] == "private-marker"


def test_import_failure_restores_cwd_environment_and_removes_own_empty_directory(
    monkeypatch,
):
    before = Path.cwd()
    monkeypatch.setenv("JWT_SECRET", "private-marker")
    captured = []

    def fail(_name):
        captured.append(Path.cwd())
        raise RuntimeError("private-marker")

    monkeypatch.setattr(gate.importlib, "import_module", fail)
    with pytest.raises(RuntimeError):
        gate.load_runtime()
    assert Path.cwd() == before and os.environ["JWT_SECRET"] == "private-marker"
    assert not captured[0].exists()


@pytest.mark.parametrize("allow", [None, "", "true", "isolated-coordinated"])
def test_no_specific_allow_never_imports_or_executes(monkeypatch, capsys, allow):
    if allow is None:
        monkeypatch.delenv("GANDALF_HTTP_PG_ALLOW", raising=False)
    else:
        monkeypatch.setenv("GANDALF_HTTP_PG_ALLOW", allow)
    execute, imports = MagicMock(), MagicMock()
    monkeypatch.setattr(gate, "execute", execute)
    monkeypatch.setattr(gate, "load_runtime", imports)
    assert gate.main() == 1
    execute.assert_not_called()
    imports.assert_not_called()
    output = capsys.readouterr()
    assert not output.err and len(output.out.splitlines()) == 1
    assert json.loads(output.out)["stage"] == "coordination"


def test_execute_also_requires_allow_before_import(monkeypatch):
    monkeypatch.delenv("GANDALF_HTTP_PG_ALLOW", raising=False)
    imports = MagicMock()
    monkeypatch.setattr(gate, "load_runtime", imports)
    with pytest.raises(ValueError):
        gate.execute(TARGET)
    imports.assert_not_called()


def test_missing_url_refuses_before_execution(monkeypatch, capsys):
    monkeypatch.setenv("GANDALF_HTTP_PG_ALLOW", gate.ALLOW)
    monkeypatch.delenv("GANDALF_HTTP_PG_URL", raising=False)
    execute = MagicMock()
    monkeypatch.setattr(gate, "execute", execute)
    assert gate.main() == 1
    execute.assert_not_called()
    assert json.loads(capsys.readouterr().out)["error_class"] == "KeyError"


@pytest.mark.parametrize(
    "target",
    [
        TARGET.replace(":55432", ":5432"),
        TARGET.replace(":55432", ":8000"),
        TARGET.replace("127.0.0.1", "database.example"),
        TARGET.replace(DATABASE, "gandalf"),
        TARGET.replace("gandalf_gate:test-only", "postgres:test-only"),
        TARGET.replace("postgresql+psycopg", "sqlite"),
        TARGET + "?host=database.example",
    ],
)
def test_target_refusal_precedes_engine_creation(monkeypatch, runtime, target):
    monkeypatch.setenv("GANDALF_HTTP_PG_ALLOW", gate.ALLOW)
    monkeypatch.setattr(gate, "load_runtime", lambda: runtime)
    factory = MagicMock()
    monkeypatch.setattr(runtime.base, "engine_for", factory)
    with pytest.raises(ValueError):
        gate.execute(target)
    factory.assert_not_called()


def fake_preflight(
    monkeypatch,
    runtime,
    *,
    database=DATABASE,
    user="gandalf_gate",
    occupied=0,
    extensions=None,
):
    engine = MagicMock()
    engine.dialect.name = "postgresql"
    connection = engine.connect.return_value.__enter__.return_value
    connection.execute.return_value.one.return_value = (
        database,
        user,
        "PostgreSQL 18.6 synthetic",
    )
    connection.scalar.side_effect = [occupied, "read committed"]
    connection.scalars.side_effect = [
        extensions if extensions is not None else {"citext", "vector"},
        ["0008_favorites"],
        {"citext", "vector"},
    ]
    upgrade = MagicMock()
    monkeypatch.setenv("GANDALF_HTTP_PG_ALLOW", gate.ALLOW)
    monkeypatch.setattr(gate, "load_runtime", lambda: runtime)
    monkeypatch.setattr(runtime.base, "engine_for", lambda _value: engine)
    monkeypatch.setattr(runtime.command, "upgrade", upgrade)
    return engine, upgrade


@pytest.mark.parametrize(
    "values",
    [
        {"occupied": 1},
        {"database": "postgres"},
        {"user": "postgres"},
        {"extensions": {"citext"}},
        {"extensions": set()},
    ],
)
def test_preflight_refusal_never_migrates_and_disposes(monkeypatch, runtime, values):
    engine, upgrade = fake_preflight(monkeypatch, runtime, **values)
    with pytest.raises(ValueError):
        gate.execute(TARGET)
    upgrade.assert_not_called()
    engine.begin.assert_not_called()
    engine.dispose.assert_called_once()


def test_preflight_connection_error_disposes_without_migration(monkeypatch, runtime):
    engine, upgrade = fake_preflight(monkeypatch, runtime)
    engine.connect.return_value.__enter__.side_effect = RuntimeError("private-marker")
    with pytest.raises(RuntimeError):
        gate.execute(TARGET)
    upgrade.assert_not_called()
    engine.dispose.assert_called_once()


def test_migration_uses_verified_connection_and_explicit_offline_settings(
    monkeypatch, runtime
):
    engine, upgrade = fake_preflight(monkeypatch, runtime)
    capture = {}

    def flow(settings, observer, used_runtime):
        assert observer is engine and used_runtime is runtime
        capture["settings"] = settings
        return {key: public_fixture()[key] for key in ("checks", "counts", "requests")}

    monkeypatch.setenv("DATABASE_URL", "private-wrong-database")
    monkeypatch.setenv("ACCESS_TOKEN_MINUTES", "1")
    monkeypatch.setenv("AUTH_RATE_LIMIT_PER_MINUTE", "1")
    monkeypatch.setattr(gate, "http_contract", flow)
    result = gate.execute(TARGET)
    config, head = upgrade.call_args.args
    assert (
        config.attributes["connection"]
        is engine.begin.return_value.__enter__.return_value
    )
    assert head == "head" and upgrade.call_count == 1
    settings = capture["settings"]
    assert settings.database_url == TARGET and len(settings.jwt_secret.encode()) >= 32
    assert not settings.online_catalog and settings.book_provider == "local"
    assert (
        settings.groq_api_key.get_secret_value() == "" and settings.cors_origins == []
    )
    assert (
        settings.access_token_minutes == 15
        and settings.auth_rate_limit_per_minute == 10
    )
    assert gate.public_result(result)["status"] == "PASS"
    engine.dispose.assert_called_once()


def test_failed_http_and_changed_sources_cannot_pass(monkeypatch, runtime):
    engine, _ = fake_preflight(monkeypatch, runtime)
    monkeypatch.setattr(
        gate,
        "source_snapshot",
        MagicMock(side_effect=[{"source": "before"}, {"source": "after"}]),
    )
    monkeypatch.setattr(
        gate,
        "http_contract",
        lambda *_: {
            key: public_fixture()[key] for key in ("checks", "counts", "requests")
        },
    )
    with pytest.raises(ValueError):
        gate.execute(TARGET)
    engine.dispose.assert_called_once()


@pytest.mark.parametrize("kind", ["RuntimeError", "custom"])
def test_cli_failure_redacts_all_exception_content(monkeypatch, capsys, kind):
    monkeypatch.setenv("GANDALF_HTTP_PG_ALLOW", gate.ALLOW)
    monkeypatch.setenv("GANDALF_HTTP_PG_URL", TARGET)

    def fail(_value):
        gate.stage("http_contract")
        exception = (
            RuntimeError
            if kind == "RuntimeError"
            else type("PrivateMarker", (Exception,), {})
        )
        raise exception("private-marker-dsn-email-token-body")

    monkeypatch.setattr(gate, "execute", fail)
    assert gate.main() == 1
    output = capsys.readouterr()
    assert not output.err and "private-marker" not in output.out.lower()
    assert len(output.out.splitlines()) == 1
    assert json.loads(output.out)["stage"] == "http_contract"


@pytest.mark.parametrize(
    "key,value",
    [
        ("checks", [{"token": "private-marker"}]),
        ("counts", {"users": {"token": "private-marker"}}),
        ("requests", {"a": True, "b": 1}),
        ("head", [{"token": "private-marker"}]),
        ("head", ["private@example.test"]),
        ("source_sha256", "private-marker"),
        ("source_unchanged", False),
        ("observer_disposed", False),
        ("transport", "TCP"),
    ],
)
def test_public_result_rejects_invalid_nested_or_claims(key, value):
    with pytest.raises(ValueError):
        gate.public_result({**public_fixture(), key: value})


def test_pass_stdout_reconstructs_contract_without_extra_input(monkeypatch, capsys):
    monkeypatch.setenv("GANDALF_HTTP_PG_ALLOW", gate.ALLOW)
    monkeypatch.setenv("GANDALF_HTTP_PG_URL", TARGET)
    monkeypatch.setattr(
        gate,
        "execute",
        lambda _value: {
            **public_fixture(),
            "body": {"password": "private-marker"},
            "token": "private-marker",
        },
    )
    assert gate.main() == 0
    output = capsys.readouterr()
    assert not output.err and len(output.out.splitlines()) == 1
    assert (
        "private-marker" not in output.out
        and json.loads(output.out) == public_fixture()
    )


def test_counts_require_correct_sql_totals_and_strict_ints():
    for field, value in (("ai_calls", True), ("users", 3), ("playlist_tracks", 0)):
        result = public_fixture()
        result["counts"][field] = value
        with pytest.raises(ValueError):
            gate.public_result(result)


def test_real_two_app_sqlite_http_flow_without_network_or_overrides(
    tmp_path, monkeypatch, runtime
):
    settings = runtime.Settings(
        _env_file=None,
        database_url=f"sqlite:///{tmp_path / 'two-app.db'}",
        jwt_secret="synthetic-test-" + "s" * 64,
        online_catalog=False,
        book_provider="local",
        groq_api_key="",
        cors_origins=[],
    )
    engine = runtime.sa.create_engine(settings.database_url)
    config = runtime.Config(str(gate.API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(gate.API_ROOT / "alembic"))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        runtime.command.upgrade(config, "head")
    external = MagicMock(side_effect=AssertionError("No external client permitted"))
    monkeypatch.setattr(
        importlib.import_module("app.main"), "external_client", external
    )
    try:
        result = gate.http_contract(settings, engine, runtime)
        assert result["checks"] == list(gate.CHECKS)
        assert result["counts"] == dict(
            zip(gate.COUNT_FIELDS, (2, 1, 1, 3, 1, 8, 1, 0), strict=True)
        )
        assert set(result["requests"]) == {"a", "b"}
        external.assert_not_called()
    finally:
        engine.dispose()


def test_http_failure_closes_both_real_app_lifespans(tmp_path, monkeypatch, runtime):
    settings = runtime.Settings(
        _env_file=None,
        database_url=f"sqlite:///{tmp_path / 'failure.db'}",
        jwt_secret="synthetic-test-" + "s" * 64,
        online_catalog=False,
        book_provider="local",
        groq_api_key="",
    )
    observer = runtime.sa.create_engine(settings.database_url)
    closed = []
    original = runtime.TestClient

    class FailedTransport(original):
        def __enter__(self):
            client = super().__enter__()
            runtime.sa.event.listen(
                self.app.state.engine, "engine_disposed", closed.append
            )
            return client

        def request(self, method, url, **kwargs):
            # Transport failure; no route/dependency/database/service override.
            raise RuntimeError("synthetic transport failure")

    monkeypatch.setattr(runtime, "TestClient", FailedTransport)
    try:
        with pytest.raises(RuntimeError):
            gate.http_contract(settings, observer, runtime)
        assert len(closed) == 2 and closed[0] is not closed[1]
    finally:
        observer.dispose()
