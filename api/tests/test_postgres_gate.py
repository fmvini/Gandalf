"""No-network checks for the disposable PostgreSQL gate's refusal boundaries."""

from unittest.mock import MagicMock

import pytest

from scripts import postgres_gate as gate

DATABASE = "gandalf_gate_00000000000000000000000000000001"
TARGET = f"postgresql+psycopg://gandalf_gate:test-only@127.0.0.1:55432/{DATABASE}"


@pytest.mark.parametrize(
    "target",
    [
        TARGET.replace(":55432", ":5432"),
        TARGET.replace(":55432", ":5433"),
        TARGET.replace(":55432", ":8000"),
        TARGET.replace("127.0.0.1", "database.example"),
        TARGET.replace(DATABASE, "gandalf"),
        TARGET.replace(DATABASE, "gandalf_gate_short"),
        TARGET.replace("gandalf_gate:test-only", "postgres:test-only"),
        TARGET + "?host=database.example",
        TARGET.replace("postgresql+psycopg", "sqlite"),
    ],
)
def test_unsafe_target_never_creates_engine(monkeypatch, target):
    create_engine = MagicMock()
    monkeypatch.setattr(gate, "create_engine", create_engine)
    with pytest.raises(ValueError):
        gate.engine_for(target)
    create_engine.assert_not_called()


@pytest.mark.parametrize("port", [55432, 55433])
def test_ci_uuid_database_and_loopback_ports_are_accepted(port):
    url = gate.validate_target(TARGET.replace(":55432", f":{port}"))
    assert url.database == DATABASE and url.port == port


@pytest.mark.parametrize(
    "database,user,occupied,extensions",
    [
        (DATABASE, "gandalf_gate", 1, {"citext", "vector"}),
        ("postgres", "gandalf_gate", 0, {"citext", "vector"}),
        (DATABASE, "postgres", 0, {"citext", "vector"}),
        (DATABASE, "gandalf_gate", 0, {"citext"}),
    ],
)
def test_unsafe_preflight_never_migrates(
    monkeypatch, database, user, occupied, extensions
):
    engine = MagicMock()
    connection = engine.connect.return_value.__enter__.return_value
    connection.execute.return_value.one.return_value = (database, user, "gate")
    connection.scalar.return_value = occupied
    connection.scalars.return_value = extensions
    monkeypatch.setattr(gate, "engine_for", lambda _value: engine)
    upgrade = MagicMock()
    monkeypatch.setattr(gate.command, "upgrade", upgrade)
    with pytest.raises(ValueError):
        gate.run(TARGET)
    upgrade.assert_not_called()
    engine.begin.assert_not_called()


def test_uncoordinated_main_does_not_run(monkeypatch, capsys):
    monkeypatch.delenv("GANDALF_PG_GATE_ALLOW", raising=False)
    run = MagicMock()
    monkeypatch.setattr(gate, "run", run)
    assert gate.main() == 1
    run.assert_not_called()
    assert '"NOT_PASSED"' in capsys.readouterr().out


def test_failure_output_redacts_exception_and_keeps_stage(monkeypatch, capsys):
    monkeypatch.setenv("GANDALF_PG_GATE_ALLOW", "isolated-coordinated")
    monkeypatch.setenv("GANDALF_PG_GATE_URL", TARGET)

    def fail(_value):
        gate.stage("preflight")
        raise RuntimeError("sensitive-dsn-or-password")

    monkeypatch.setattr(gate, "run", fail)
    assert gate.main() == 1
    output = capsys.readouterr()
    assert "sensitive-dsn-or-password" not in output.out + output.err
    assert output.out.count("\n") == 1
    assert '"stage": "preflight"' in output.out
    assert '"error_class": "RuntimeError"' in output.out
    assert '"stage": "preflight"' in output.err
