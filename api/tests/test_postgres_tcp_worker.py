"""Worker protocol and test-only identity guards without PostgreSQL."""

import asyncio
import io
import json
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from scripts import postgres_tcp_worker as worker


def config():
    return {
        "database_url": "synthetic-url",
        "jwt_secret": "s" * 32,
        "run": str(uuid4()),
        "instance": "a",
    }


def test_protocol_valid_and_duplicate_keys_refused():
    value = config()
    assert worker.read_config(io.StringIO(json.dumps(value))) == value
    with pytest.raises(worker.WorkerError):
        worker.read_config(io.StringIO(json.dumps(value)[:-1] + ',"instance":"a"}'))


@pytest.mark.parametrize(
    "key,bad",
    [
        ("instance", "A"),
        ("instance", True),
        ("run", "private-marker"),
        ("run", str(uuid4()).upper()),
        ("jwt_secret", "s" * 31),
        ("jwt_secret", 123),
        ("database_url", ""),
        ("database_url", 123),
    ],
)
def test_protocol_invalid(key, bad):
    value = config()
    value[key] = bad
    with pytest.raises((worker.WorkerError, ValueError)):
        worker.read_config(io.StringIO(json.dumps(value)))


def test_extra_field_and_oversize_refused():
    value = config()
    value["token"] = "private-marker"
    with pytest.raises(worker.WorkerError):
        worker.read_config(io.StringIO(json.dumps(value)))
    with pytest.raises(worker.WorkerError):
        worker.read_config(io.StringIO("x" * (worker.MAX_INPUT + 1)))


@pytest.mark.parametrize("allowed", [False, True])
def test_main_fails_sanitized_before_runtime(monkeypatch, capsys, allowed):
    monkeypatch.setattr(worker.sys, "argv", ["worker"])
    monkeypatch.setattr(worker.sys, "stdin", io.StringIO("private-marker"))
    monkeypatch.setenv("GANDALF_TCP_PG_ALLOW", worker.ALLOW if allowed else "wrong")
    serve = MagicMock()
    monkeypatch.setattr(worker, "serve", serve)
    assert worker.main() == 1
    serve.assert_not_called()
    output = capsys.readouterr().out
    assert (
        "private-marker" not in output and json.loads(output)["status"] == "NOT_PASSED"
    )


def test_serve_refuses_before_import(monkeypatch):
    monkeypatch.delenv("GANDALF_TCP_PG_ALLOW", raising=False)
    imported = MagicMock()
    monkeypatch.setattr(worker.importlib, "import_module", imported)
    with pytest.raises(worker.WorkerError):
        worker.serve(config(), MagicMock())
    imported.assert_not_called()


@pytest.mark.parametrize("status", [200, 401, 500])
def test_outer_headers_replace_untrusted_identity_in_every_response(status):
    value = config()
    sent = []

    async def app(_scope, _receive, send):
        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": [
                    (b"x-gandalf-gate-pid", b"other"),
                    (b"content-type", b"application/json"),
                ],
            }
        )

    async def send(message):
        sent.append(message)

    asyncio.run(
        worker.IdentityMiddleware(app, value, 1234)({"type": "http"}, None, send)
    )
    headers = dict(sent[0]["headers"])
    assert headers[b"x-gandalf-gate-run"] == value["run"].encode()
    assert headers[b"x-gandalf-gate-instance"] == b"a"
    assert headers[b"x-gandalf-gate-pid"] == b"1234"


def test_socket_closed_and_engine_disposed_on_startup_failure(monkeypatch):
    monkeypatch.setenv("GANDALF_TCP_PG_ALLOW", worker.ALLOW)
    engine = MagicMock()
    app = SimpleNamespace(state=SimpleNamespace(engine=engine))
    runtime = SimpleNamespace(
        base=MagicMock(), Settings=MagicMock(), create_app=lambda **kw: app
    )
    bound = MagicMock()
    bound.getsockname.return_value = ("127.0.0.1", 49152)

    class BrokenServer:
        def __init__(self, _config):
            pass

        def run(self, **_kwargs):
            raise RuntimeError("private-marker")

    uvicorn = SimpleNamespace(Server=BrokenServer, Config=MagicMock())
    with pytest.raises(RuntimeError):
        worker.serve(
            config(),
            MagicMock(),
            runtime=runtime,
            uvicorn_module=uvicorn,
            socket_factory=lambda *_: bound,
            control=io.StringIO("STOP\n"),
        )
    bound.bind.assert_called_once_with(("127.0.0.1", 0))
    bound.close.assert_called_once()
    engine.dispose.assert_called_once()
    settings = runtime.Settings.call_args.kwargs
    assert settings["_env_file"] is None and settings["online_catalog"] is False
    assert settings["groq_api_key"] == "" and settings["book_provider"] == "local"
