"""Offline refusals and exact-connection/serialization fakes; not a Neon gate."""

import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import sqlalchemy as sa

from scripts import neon_migrate as gate

TARGET = "postgresql://fixture:private-marker@ep-cool-darkness-ab123.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
HEAD = ["0008_favorites"]


@pytest.mark.parametrize("scheme", ["postgres", "postgresql", "postgresql+psycopg"])
@pytest.mark.parametrize("tls", ["require", "verify-ca", "verify-full"])
def test_direct_neon_target_selects_psycopg_without_network(scheme, tls):
    target = TARGET.replace("postgresql:", scheme + ":").replace(
        "sslmode=require", "sslmode=" + tls
    )
    normalized = gate.validate_target(target)
    assert normalized.startswith("postgresql+psycopg://")
    assert sa.engine.make_url(normalized).query["sslmode"] == tls


@pytest.mark.parametrize(
    "host",
    [
        "ep-fixture-ab123.c-2.us-east-1.aws.neon.tech",
        "ep-fixture-ab123.eastus2.azure.neon.tech",
    ],
)
def test_public_endpoint_variants(host):
    assert gate.validate_target(
        TARGET.replace("ep-cool-darkness-ab123.us-east-2.aws.neon.tech", host)
    )


@pytest.mark.parametrize(
    "target",
    [
        None,
        "",
        "sqlite:///test.db",
        "sqlite:///:memory:",
        TARGET.replace("postgresql", "postgresql+psycopg2", 1),
        TARGET.replace(".neon.tech", ".neon.tech.attacker.invalid"),
        TARGET.replace("ep-cool-darkness-ab123", "ep-cool-darkness-ab123-pooler"),
        TARGET.replace("ep-cool-darkness-ab123.us-east-2.aws.neon.tech", "localhost"),
        TARGET.replace("ep-cool-darkness-ab123.us-east-2.aws.neon.tech", "127.0.0.1"),
        TARGET.replace("ep-cool-darkness-ab123.us-east-2.aws.neon.tech", "neon.tech"),
        TARGET.replace(
            "ep-cool-darkness-ab123.us-east-2.aws.neon.tech", "www.neon.tech"
        ),
        TARGET.replace("/neondb?", ":55432/neondb?"),
        TARGET.replace("/neondb?", ":broken/neondb?"),
        TARGET.replace("fixture:private-marker@", "fixture@"),
        TARGET.replace("fixture:private-marker@", "fixture:@"),
        TARGET.replace("/neondb?", "/?"),
        TARGET.replace("/neondb?", "/neondb/other?"),
        TARGET.split("?")[0],
        TARGET.replace("sslmode=require", "sslmode=prefer"),
        TARGET.replace("sslmode=require", "sslmode=disable"),
        TARGET.replace("channel_binding=require", "channel_binding=disable"),
        TARGET + "&sslmode=disable",
        TARGET + "&channel_binding=prefer",
        TARGET + "&host=127.0.0.1",
        TARGET + "&hostaddr=127.0.0.1",
        TARGET + "&service=real",
        TARGET + "&options=-csearch_path%3Dother",
        TARGET + "#fragment",
        TARGET + "#",
        TARGET + "\n",
        " " + TARGET,
    ],
)
def test_invalid_target_raises_only_sanitized_message(target):
    with pytest.raises(gate.MigrationError) as error:
        gate.validate_target(target)
    assert str(error.value) == "Invalid Neon migration target."
    assert "private-marker" not in str(error.value)


@pytest.mark.parametrize("allow", [None, "", "true", "owned_project"])
def test_cli_refuses_optin_before_import_connect(monkeypatch, capsys, allow):
    monkeypatch.setattr(sys, "argv", ["neon_migrate.py"])
    if allow is None:
        monkeypatch.delenv("GANDALF_NEON_MIGRATE", raising=False)
    else:
        monkeypatch.setenv("GANDALF_NEON_MIGRATE", allow)
    imports = MagicMock()
    monkeypatch.setattr(gate, "load_runtime", imports)
    assert gate.main() == 1
    imports.assert_not_called()
    assert json.loads(capsys.readouterr().out) == {
        "status": "NOT_PASSED",
        "stage": "coordination",
        "error_class": "MigrationError",
    }


def test_cli_refuses_credential_args_before_import(monkeypatch, capsys):
    monkeypatch.setenv("GANDALF_NEON_MIGRATE", gate.ALLOW)
    monkeypatch.setattr(sys, "argv", ["neon_migrate.py", TARGET])
    imports = MagicMock()
    monkeypatch.setattr(gate, "load_runtime", imports)
    assert gate.main() == 1
    imports.assert_not_called()
    assert "private-marker" not in capsys.readouterr().out


def test_cli_invalid_url_never_imports_or_connects(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["neon_migrate.py"])
    monkeypatch.setenv("GANDALF_NEON_MIGRATE", gate.ALLOW)
    monkeypatch.setenv("NEON_DATABASE_URL_UNPOOLED", "sqlite:///private-marker")
    imports = MagicMock()
    monkeypatch.setattr(gate, "load_runtime", imports)
    assert gate.main() == 1
    imports.assert_not_called()
    assert json.loads(capsys.readouterr().out)["stage"] == "target_validation"


def test_sanitized_runtime_excludes_pg_dotenv_and_restores_after_error(monkeypatch):
    for key in (
        "PGHOST",
        "PGSERVICE",
        "PGSSLROOTCERT",
        "DATABASE_URL",
        "JWT_SECRET",
        "NEON_DATABASE_URL_UNPOOLED",
    ):
        monkeypatch.setenv(key, "private-marker")
    cwd, inherited, path = Path.cwd(), dict(os.environ), sys.path[:]
    with pytest.raises(RuntimeError), gate.sanitized_runtime():
        scratch = Path.cwd()
        assert scratch != cwd and not list(scratch.iterdir())
        assert all(
            os.environ.get(key) is None
            for key in inherited
            if key.upper() not in gate.SYSTEM_KEYS
        )
        assert sys.path[0] == str(gate.API_ROOT)
        raise RuntimeError("fixture")
    assert Path.cwd() == cwd and dict(os.environ) == inherited and sys.path == path
    assert not scratch.exists()


def fake_runtime(
    *,
    identity=("neondb", "fixture"),
    tls=True,
    available=("citext", "vector"),
    lock=True,
    head=HEAD,
    extensions=None,
):
    connection, engine, config = (
        MagicMock(),
        MagicMock(),
        SimpleNamespace(attributes={}),
    )
    engine.connect.return_value.__enter__.return_value = connection
    connection.connection.driver_connection.pgconn.ssl_in_use = tls
    queries = []

    def execute(statement, parameters=None):
        query = str(statement)
        queries.append((query, parameters))
        result = MagicMock()
        if query.startswith("SELECT current_database"):
            result.one.return_value = identity
        elif "pg_available_extensions" in query:
            result.scalars.return_value = available
        elif "pg_try_advisory" in query:
            result.scalar_one.return_value = lock
        elif "alembic_version" in query:
            result.scalars.return_value = head
        elif "pg_extension" in query:
            result.all.return_value = (
                extensions
                if extensions is not None
                else [("citext", "1.8"), ("vector", "0.8.6")]
            )
        return result

    connection.execute.side_effect = execute
    scripts = MagicMock()
    scripts.from_config.return_value.get_heads.return_value = HEAD
    runtime = SimpleNamespace(
        sa=SimpleNamespace(
            engine=sa.engine,
            pool=sa.pool,
            text=sa.text,
            create_engine=MagicMock(return_value=engine),
        ),
        Config=MagicMock(return_value=config),
        command=SimpleNamespace(upgrade=MagicMock()),
        ScriptDirectory=scripts,
    )
    return runtime, connection, engine, config, queries


def test_exact_connection_locked_before_migration_then_readonly_disposed():
    runtime, connection, engine, config, queries = fake_runtime()

    def upgrade(received, revision):
        assert received is config and revision == "head"
        assert received.attributes["connection"] is connection
        assert "pg_try_advisory_xact_lock" in queries[-1][0]
        assert queries[-1][1] == {"key": gate.LOCK_KEY}

    runtime.command.upgrade.side_effect = upgrade
    result = gate.migrate(TARGET, runtime)
    assert result == {
        "status": "PASS",
        "head": HEAD,
        "extensions": {"citext": "1.8", "vector": "0.8.6"},
        "direct_connection": True,
        "tls": "require",
        "tls_active": True,
        "identity_verified": True,
        "serial_lock": True,
        "readonly_verified": True,
    }
    assert "SET TRANSACTION READ ONLY" in [query for query, _ in queries]
    assert connection.begin.call_count == 2
    assert engine.connect.call_count == 1
    assert runtime.sa.create_engine.call_args.kwargs["poolclass"] is sa.pool.NullPool
    assert (
        runtime.sa.create_engine.call_args.kwargs["connect_args"]["prepare_threshold"]
        is None
    )
    engine.dispose.assert_called_once()


@pytest.mark.parametrize(
    "change",
    [
        {"identity": ("other", "fixture")},
        {"identity": ("neondb", "other")},
        {"tls": False},
        {"available": ("citext",)},
        {"lock": False},
    ],
)
def test_identity_tls_extensions_or_busy_lock_refuse_before_upgrade(change):
    runtime, _, engine, _, _ = fake_runtime(**change)
    with pytest.raises(gate.MigrationError):
        gate.migrate(TARGET, runtime)
    runtime.command.upgrade.assert_not_called()
    engine.dispose.assert_called_once()


@pytest.mark.parametrize(
    "change",
    [
        {"head": ["old"]},
        {"extensions": [("citext", "1.8")]},
        {"extensions": [("citext", "private-marker"), ("vector", "0.8.6")]},
    ],
)
def test_proof_mismatch_never_returns_pass(change):
    runtime, _, engine, _, _ = fake_runtime(**change)
    with pytest.raises(gate.MigrationError):
        gate.migrate(TARGET, runtime)
    engine.dispose.assert_called_once()


def test_upgrade_failure_disposes_exact_engine():
    runtime, _, engine, _, _ = fake_runtime()
    runtime.command.upgrade.side_effect = RuntimeError("private-marker")
    with pytest.raises(RuntimeError):
        gate.migrate(TARGET, runtime)
    engine.dispose.assert_called_once()


def test_cli_failure_suppresses_import_output_and_raw_exception(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["neon_migrate.py"])
    monkeypatch.setenv("GANDALF_NEON_MIGRATE", gate.ALLOW)
    monkeypatch.setenv("NEON_DATABASE_URL_UNPOOLED", TARGET)

    def fail():
        print("private-marker")
        print("private-marker", file=sys.stderr)
        raise RuntimeError(TARGET)

    monkeypatch.setattr(gate, "load_runtime", fail)
    assert gate.main() == 1
    output = capsys.readouterr()
    assert output.err == "" and "private-marker" not in output.out
    assert json.loads(output.out) == {
        "status": "NOT_PASSED",
        "stage": "imports",
        "error_class": "MigrationError",
    }
