"""Auth gate safety and reporting boundaries; no database or network access."""

import json
from unittest.mock import MagicMock

import pytest

from scripts import postgres_auth_gate as gate

DATABASE = "gandalf_gate_00000000000000000000000000000001"
TARGET = f"postgresql+psycopg://gandalf_gate:synthetic@127.0.0.1:55432/{DATABASE}"


@pytest.mark.parametrize(
    "target",
    [
        TARGET.replace(":55432", ":5432"),
        TARGET.replace(":55432", ":5433"),
        TARGET.replace(":55432", ":8000"),
        TARGET.replace("127.0.0.1", "remote.example"),
        TARGET.replace(DATABASE, "gandalf"),
        TARGET.replace(DATABASE, "gandalf_gate_short"),
        TARGET.replace("gandalf_gate:synthetic", "postgres:synthetic"),
        TARGET + "?host=remote.example",
        TARGET.replace("postgresql+psycopg", "sqlite"),
    ],
)
def test_auth_gate_unsafe_target_never_creates_engine(monkeypatch, target):
    creator = MagicMock()
    monkeypatch.setattr(gate.base, "create_engine", creator)
    with pytest.raises(ValueError):
        gate.execute(target)
    creator.assert_not_called()


@pytest.mark.parametrize(
    "database,user,objects,extensions",
    [
        (DATABASE, "gandalf_gate", 1, {"citext", "vector"}),
        ("postgres", "gandalf_gate", 0, {"citext", "vector"}),
        (DATABASE, "postgres", 0, {"citext", "vector"}),
        (DATABASE, "gandalf_gate", 0, {"citext"}),
    ],
)
def test_auth_preflight_refuses_before_migration(
    monkeypatch, database, user, objects, extensions
):
    engine = MagicMock()
    connection = engine.connect.return_value.__enter__.return_value
    connection.execute.return_value.one.return_value = (database, user, "synthetic")
    connection.scalar.return_value = objects
    connection.scalars.return_value = extensions
    monkeypatch.setattr(gate.base, "engine_for", lambda _value: engine)
    upgrade = MagicMock()
    monkeypatch.setattr(gate.command, "upgrade", upgrade)
    with pytest.raises(ValueError):
        gate.execute(TARGET)
    upgrade.assert_not_called()
    engine.begin.assert_not_called()
    engine.dispose.assert_called_once()


@pytest.mark.parametrize("port", [55432, 55433])
def test_uuid_loopback_targets_are_accepted(port):
    url = gate.base.validate_target(TARGET.replace(":55432", f":{port}"))
    assert url.database == DATABASE and url.port == port


def test_opt_in_refusal_does_not_execute(monkeypatch, capsys):
    monkeypatch.setattr(gate.sys, "argv", ["postgres_auth_gate.py"])
    monkeypatch.delenv("GANDALF_AUTH_PG_ALLOW", raising=False)
    monkeypatch.setattr(gate, "STAGE", "coordination")
    execute = MagicMock()
    monkeypatch.setattr(gate, "execute", execute)
    assert gate.main() == 1
    execute.assert_not_called()
    output = capsys.readouterr()
    assert len(output.out.splitlines()) == 1
    assert json.loads(output.out) == {
        "status": "NOT_PASSED",
        "stage": "coordination",
        "error_class": "ValueError",
    }


def test_failed_interleaving_cannot_report_success(monkeypatch, capsys):
    monkeypatch.setattr(gate.sys, "argv", ["postgres_auth_gate.py"])
    monkeypatch.setenv("GANDALF_AUTH_PG_ALLOW", "isolated-coordinated-backend-frozen")
    monkeypatch.setenv("GANDALF_AUTH_PG_URL", TARGET)
    outcome = {
        "status": "NOT_PASSED",
        "checks": [{"passed": False, "blocking_observed": False}],
    }
    monkeypatch.setattr(gate, "execute", lambda _value: outcome)
    assert gate.main() == 1
    assert json.loads(capsys.readouterr().out) == outcome


def test_failure_redacts_sql_dsn_and_keeps_stage(monkeypatch, capsys):
    monkeypatch.setattr(gate.sys, "argv", ["postgres_auth_gate.py"])
    monkeypatch.setenv("GANDALF_AUTH_PG_ALLOW", "isolated-coordinated-backend-frozen")
    monkeypatch.setenv("GANDALF_AUTH_PG_URL", TARGET)

    def fail(_value):
        gate.stage("ancestor_replay_descendant_rotation")
        raise RuntimeError("secret-sql-dsn-password")

    monkeypatch.setattr(gate, "execute", fail)
    assert gate.main() == 1
    output = capsys.readouterr()
    assert "secret-sql-dsn-password" not in output.out + output.err
    assert len(output.out.splitlines()) == 1
    assert json.loads(output.out) == {
        "status": "NOT_PASSED",
        "stage": "ancestor_replay_descendant_rotation",
        "error_class": "RuntimeError",
    }
    assert json.loads(output.err) == {"stage": "ancestor_replay_descendant_rotation"}


def test_source_snapshot_accepts_current_revision_without_session_pin(monkeypatch):
    current = {"app/services/auth_service.py": "new-future-revision"}
    monkeypatch.setattr(gate, "hashes", lambda: current.copy())
    gate.ensure_sources_unchanged(current)


def test_source_snapshot_rejects_changes_during_gate(monkeypatch):
    monkeypatch.setattr(gate, "hashes", lambda: {"source": "after"})
    with pytest.raises(RuntimeError):
        gate.ensure_sources_unchanged({"source": "before"})
