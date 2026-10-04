"""Execute the literal CI bootstrap against a fake connection, never a real DB."""

import sys
import textwrap
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import psycopg
import pytest
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[2]
VARIABLES = {"GANDALF_AUTH_PG_URL", "GANDALF_HTTP_PG_URL", "GANDALF_TCP_PG_URL"}
BOOTSTRAP = "postgresql+psycopg://gandalf_gate:synthetic-private@127.0.0.1:55432/gandalf_gate_00000000000000000000000000000001"


def ci_block():
    lines = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8").splitlines()
    candidates = []
    for index, line in enumerate(lines):
        if line.strip() != "python - <<'PY'":
            continue
        body = []
        for following in lines[index + 1 :]:
            if following.strip() == "PY":
                break
            body.append(following)
        code = textwrap.dedent("\n".join(body)) + "\n"
        if "GANDALF_TCP_PG_URL" in code:
            candidates.append(code)
    assert len(candidates) == 1
    return candidates[0]


def run_bootstrap():
    # Execute only the checked-in CI literal, against the test's fake connection.
    exec(compile(ci_block(), "ci-postgres-bootstrap", "exec"), {})  # noqa: S102


def prepare(monkeypatch, tmp_path, identity):
    target = tmp_path / "github-env"
    monkeypatch.setenv("GANDALF_PG_GATE_URL", BOOTSTRAP)
    monkeypatch.setenv("GITHUB_ENV", str(target))
    connection = MagicMock()
    connection.execute.return_value.fetchone.return_value = identity
    connect = MagicMock()
    connect.return_value.__enter__.return_value = connection
    monkeypatch.setattr(psycopg, "connect", connect)
    # Import the validator only through this fake; app.main/.env must not be loaded.
    monkeypatch.setitem(
        sys.modules,
        "scripts.postgres_gate",
        SimpleNamespace(validate_target=make_url),
    )
    return target, connection, connect


def test_literal_bootstrap_creates_three_distinct_databases(
    monkeypatch, tmp_path, capsys
):
    initial = make_url(BOOTSTRAP)
    path, connection, connect = prepare(
        monkeypatch, tmp_path, (initial.database, "gandalf_gate")
    )
    run_bootstrap()
    assert not capsys.readouterr().out
    values = dict(line.split("=", 1) for line in path.read_text().splitlines())
    assert set(values) == VARIABLES
    databases = set()
    for value in values.values():
        url = make_url(value)
        assert url.set(database=initial.database) == initial
        assert url.database.startswith("gandalf_gate_") and len(url.database) == 45
        assert url.database != initial.database
        databases.add(url.database)
    assert len(databases) == 3
    calls = connection.execute.call_args_list
    assert calls[0].args == ("SELECT current_database(), current_user",)
    assert len(calls) == 4
    assert {call.args[0].as_string() for call in calls[1:]} == {
        f'CREATE DATABASE "{db}"' for db in databases
    }
    assert connect.call_args.kwargs["options"] == "-c statement_timeout=15000"
    assert connect.call_args.kwargs["connect_timeout"] == 5
    assert connect.call_args.kwargs["autocommit"] is True


@pytest.mark.parametrize(
    "identity",
    [("wrong-db", "gandalf_gate"), (make_url(BOOTSTRAP).database, "wrong-role"), None],
)
def test_wrong_identity_does_not_create_databases_or_publish_urls(
    monkeypatch, tmp_path, identity
):
    path, connection, _connect = prepare(monkeypatch, tmp_path, identity)
    with pytest.raises(RuntimeError, match="identity mismatch"):
        run_bootstrap()
    assert connection.execute.call_count == 1 and not path.exists()


def test_creation_failure_does_not_publish_partial_targets(monkeypatch, tmp_path):
    path, connection, _connect = prepare(
        monkeypatch, tmp_path, (make_url(BOOTSTRAP).database, "gandalf_gate")
    )
    cursor = SimpleNamespace(
        fetchone=lambda: (make_url(BOOTSTRAP).database, "gandalf_gate")
    )
    connection.execute.side_effect = [cursor, None, RuntimeError("synthetic-failure")]
    with pytest.raises(RuntimeError):
        run_bootstrap()
    assert not path.exists()


def test_tcp_step_is_optin_and_uploads_only_named_artifact():
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    step = workflow[
        workflow.index("      - name: Testar sess") : workflow.index(
            "      - name: Guardar resultado PostgreSQL"
        )
    ]
    assert "GANDALF_TCP_PG_ALLOW: isolated-coordinated-backend-frozen" in step
    assert (
        "python scripts/postgres_tcp_gate.py | tee ../.impeccable/ci/postgres-tcp-gate.json"
        in step
    )
    assert "shell: bash" in workflow
    upload = workflow[
        workflow.index("      - name: Guardar resultado PostgreSQL") : workflow.index(
            "  frontend:"
        )
    ]
    assert (
        ".impeccable/ci/postgres-tcp-gate.json" in upload and "if: always()" in upload
    )
    assert (
        "DATABASE_URL" not in step and "JWT_SECRET" not in step and ".env" not in step
    )
