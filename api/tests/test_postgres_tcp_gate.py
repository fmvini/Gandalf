"""Offline guards for the TCP gate; no PostgreSQL or existing services."""

import io
import json
import subprocess
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from scripts import postgres_tcp_gate as gate


def fixture():
    return {
        "status": "PASS",
        "transport": "TCP_TWO_PROCESSES_RESTART",
        "checks": list(gate.CHECKS),
        "head": ["0008_favorites"],
        "counts": dict(
            zip(gate.base.COUNT_FIELDS, (2, 1, 1, 3, 1, 4, 1, 0), strict=True)
        ),
        "requests": {"a": 11, "b": 12, "b_restarted": 8},
        "restart_without_login": True,
        "persistence_verified": True,
        "cleanup_verified": True,
        "source_unchanged": True,
        "source_sha256": "a" * 64,
    }


@pytest.mark.parametrize("allow", [None, "", "true", "isolated-coordinated"])
def test_optin_before_import_or_execution(monkeypatch, capsys, allow):
    monkeypatch.setenv("GANDALF_TCP_PG_ALLOW", allow or "")
    execute = MagicMock()
    monkeypatch.setattr(gate, "execute", execute)
    assert gate.main() == 1
    execute.assert_not_called()
    assert json.loads(capsys.readouterr().out)["status"] == "NOT_PASSED"


def test_execute_refuses_before_snapshot_and_import(monkeypatch):
    monkeypatch.delenv("GANDALF_TCP_PG_ALLOW", raising=False)
    snapshot = MagicMock()
    monkeypatch.setattr(gate, "source_snapshot", snapshot)
    with pytest.raises(ValueError):
        gate.execute("private-marker")
    snapshot.assert_not_called()


def test_missing_url_and_errors_do_not_print_credentials(monkeypatch, capsys):
    monkeypatch.setenv("GANDALF_TCP_PG_ALLOW", gate.ALLOW)
    monkeypatch.setattr(gate.sys, "argv", ["gate"])
    monkeypatch.delenv("GANDALF_TCP_PG_URL", raising=False)
    assert gate.main() == 1
    assert "private-marker" not in capsys.readouterr().out
    monkeypatch.setenv("GANDALF_TCP_PG_URL", "private-marker")
    monkeypatch.setattr(
        gate, "execute", MagicMock(side_effect=RuntimeError("private-marker"))
    )
    assert gate.main() == 1
    output = capsys.readouterr().out
    assert "private-marker" not in output and "RuntimeError" in output


def test_public_output_reconstructed(monkeypatch, capsys):
    value = fixture()
    value["token"] = "private-marker"
    safe = gate.public_result(value)
    assert (
        safe == fixture()
        and safe is not value
        and safe["counts"] is not value["counts"]
    )
    monkeypatch.setenv("GANDALF_TCP_PG_ALLOW", gate.ALLOW)
    monkeypatch.setenv("GANDALF_TCP_PG_URL", "private-marker")
    monkeypatch.setattr(gate.sys, "argv", ["gate"])
    monkeypatch.setattr(gate, "execute", lambda _url: value)
    assert gate.main() == 0
    assert "private-marker" not in capsys.readouterr().out


@pytest.mark.parametrize(
    "key,bad",
    [
        ("checks", [{"token": "private-marker"}]),
        ("head", ["private-marker"]),
        ("cleanup_verified", 1),
        ("source_unchanged", False),
        ("restart_without_login", False),
        ("source_sha256", "secret"),
        ("transport", "ASGI"),
        ("counts", {"token": "private-marker"}),
        ("requests", {"a": True, "b": 3, "b_restarted": 3}),
    ],
)
def test_public_output_rejects_untrusted_values(key, bad):
    value = fixture()
    value[key] = bad
    with pytest.raises(ValueError):
        gate.public_result(value)


@pytest.mark.parametrize(
    "field,value",
    [("ai_calls", 1), ("refresh_tokens", True), ("users", 3), ("playlist_tracks", 0)],
)
def test_counts_are_strict_and_match_proof(field, value):
    result = fixture()
    result["counts"][field] = value
    with pytest.raises(ValueError):
        gate.public_result(result)


@pytest.mark.parametrize(
    "field,bad",
    [
        ("pid", True),
        ("pid", 55),
        ("port", 8000),
        ("port", True),
        ("port", 65536),
        ("run", "other"),
        ("instance", "other"),
        ("status", "PASS"),
    ],
)
def test_ready_requires_owned_identity_and_ephemeral_port(field, bad):
    run = str(uuid4())
    value = {"status": "READY", "pid": 1234, "port": 49152, "run": run, "instance": "a"}
    assert gate.validate_ready(value, 1234, run, "a") == 49152
    value[field] = bad
    with pytest.raises(ValueError):
        gate.validate_ready(value, 1234, run, "a")


def test_redirect_refused_before_follow():
    with pytest.raises(ValueError):
        gate.NoRedirect().redirect_request(
            None, None, 302, "private-marker", {}, "http://other/"
        )


def test_worker_failure_diagnostics_reconstructed():
    value = {
        "status": "NOT_PASSED",
        "stage": "startup",
        "line": 12,
        "token": "private-marker",
    }
    assert gate.WorkerFailure(value).public == {"stage": "startup", "line": 12}
    value["line"] = True
    with pytest.raises(ValueError):
        gate.WorkerFailure(value)


def test_child_environment_and_stdin_only_secrets(monkeypatch):
    run = str(uuid4())
    process = MagicMock(pid=1234)
    process.poll.return_value = None
    process.stdin = io.StringIO()
    process.stdout = io.StringIO(
        json.dumps(
            {"status": "READY", "pid": 1234, "port": 49152, "run": run, "instance": "a"}
        )
        + "\n"
    )
    spawn = MagicMock(return_value=process)
    monkeypatch.setattr(gate.subprocess, "Popen", spawn)
    monkeypatch.setattr(
        gate.Child,
        "request",
        lambda *args, **kwargs: {
            "catalog": "local",
            "ai": {"configured": False, "provider": None, "model": None},
        },
    )
    monkeypatch.setenv("DATABASE_URL", "private-marker")
    monkeypatch.setenv("JWT_SECRET", "private-marker")
    child = gate.Child("synthetic-url", "synthetic-secret", run, "a", "empty-cwd")
    assert child.process is process
    args, kwargs = spawn.call_args
    assert "synthetic" not in str(args)
    assert (
        not {"DATABASE_URL", "JWT_SECRET", "GANDALF_TCP_PG_URL"} & kwargs["env"].keys()
    )
    assert kwargs["stderr"] == subprocess.DEVNULL
    assert json.loads(process.stdin.getvalue())["jwt_secret"] == "synthetic-secret"


@pytest.mark.parametrize(
    "bad",
    [
        {"catalog": "online"},
        {"catalog": "local", "ai": {"configured": True}},
        {"catalog": "local", "ai": {"configured": 0}},
        {"catalog": "local", "ai": {"configured": False, "provider": "groq"}},
    ],
)
def test_actual_worker_status_must_be_offline(bad):
    with pytest.raises(ValueError):
        gate.validate_offline(bad)


@pytest.mark.parametrize("forced", [False, True])
def test_owned_stop_graceful_or_force_is_not_pass(forced):
    child = object.__new__(gate.Child)
    process = MagicMock(returncode=0)
    process.poll.return_value = None
    process.stdin, process.stdout = io.StringIO(), io.StringIO()
    if forced:
        process.wait.side_effect = [subprocess.TimeoutExpired("worker", 8), None]
    child.process = process
    assert child.stop() is (not forced)
    assert process.stdin.closed and process.stdout.closed
    assert process.terminate.called is forced


def test_http_response_requires_process_identity(monkeypatch):
    child = object.__new__(gate.Child)
    child.process = SimpleNamespace(pid=1234, poll=lambda: None)
    child.run, child.instance, child.port, child.count = str(uuid4()), "a", 49152, 0
    response = MagicMock(status=200)
    response.__enter__.return_value = response
    response.headers = {
        "x-gandalf-gate-run": child.run,
        "x-gandalf-gate-instance": "b",
        "x-gandalf-gate-pid": "1234",
    }
    monkeypatch.setattr(
        gate, "build_opener", lambda *_: SimpleNamespace(open=lambda *a, **k: response)
    )
    with pytest.raises(ValueError):
        child.request("GET", "/health")


def test_flow_failure_stops_both_children_before_directory_removal(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("GANDALF_TCP_PG_ALLOW", gate.ALLOW)
    monkeypatch.setattr(gate.base, "ROOT", tmp_path)
    monkeypatch.setattr(gate, "source_snapshot", dict)
    connection = MagicMock()
    connection.execute.return_value.one.return_value = ("database", "role")
    connection.scalar.return_value = 0
    connection.scalars.side_effect = [{"citext", "vector"}, ["head"]]
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value = connection
    runtime = MagicMock()
    runtime.base.engine_for.return_value = engine
    runtime.ScriptDirectory.from_config.return_value.get_heads.return_value = ["head"]
    monkeypatch.setattr(gate.base, "load_runtime", lambda: runtime)
    target = tmp_path / ".impeccable/runtime/tcp-gate-owned"
    target.mkdir(parents=True)
    children = []

    class FakeChild:
        def __init__(self, *_args):
            self.process = SimpleNamespace(pid=100 + len(children))
            self.port = 49000 + len(children)
            self.stopped = False
            children.append(self)

        def request(self, *_args, **_kwargs):
            raise RuntimeError("private-marker")

        def stop(self):
            self.stopped = True
            return True

    class Directory:
        name = str(target)

        def cleanup(self):
            assert len(children) == 2 and all(child.stopped for child in children)
            target.rmdir()

    monkeypatch.setattr(gate, "Child", FakeChild)
    monkeypatch.setattr(gate.tempfile, "TemporaryDirectory", lambda **_kw: Directory())
    with pytest.raises(RuntimeError):
        gate.execute("synthetic-target")
    assert not target.exists()
    engine.dispose.assert_called_once()


def test_sql_fingerprints_use_composite_track_key_and_read_only():
    connection, engine, runtime = MagicMock(), MagicMock(), MagicMock()
    engine.begin.return_value.__enter__.return_value = connection
    runtime.sa.text.side_effect = lambda value: value
    connection.scalar.return_value = 0
    connection.execute.return_value.mappings.return_value.all.return_value = []
    result = gate.sql_snapshot(engine, runtime, str(uuid4()))
    sql = [str(call.args[0]) for call in connection.execute.call_args_list]
    assert sql[0] == "SET TRANSACTION READ ONLY"
    assert "SELECT * FROM playlist_tracks ORDER BY playlist_id, position" in sql
    assert set(result["fingerprints"]) == {
        "favorites",
        "playlists",
        "playlist_tracks",
        "recommendation_results",
    }
