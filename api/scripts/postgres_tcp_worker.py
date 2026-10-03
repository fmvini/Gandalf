"""Disposable test worker; no migrations, production entrypoint or stored secrets."""

import importlib
import json
import logging
import os
import socket
import sys
import threading
from pathlib import Path
from uuid import UUID

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))
ALLOW = "isolated-coordinated-backend-frozen"
HEADERS = {b"x-gandalf-gate-run", b"x-gandalf-gate-instance", b"x-gandalf-gate-pid"}
MAX_INPUT = 16_384
FIELDS = {"run", "instance", "database_url", "jwt_secret"}


class WorkerError(Exception):
    """Only a generic protocol error crosses the child boundary."""


def require(condition):
    if not condition:
        raise WorkerError("Worker check failed")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result)
        result[key] = value
    return result


def read_config(stream):
    line = stream.readline(MAX_INPUT + 1)
    require(0 < len(line.encode("utf-8")) <= MAX_INPUT)
    value = json.loads(line, object_pairs_hook=unique_object)
    require(isinstance(value, dict) and set(value) == FIELDS)
    identity = value["run"]
    require(isinstance(identity, str))
    parsed = UUID(identity)
    require(str(parsed) == identity and parsed.version == 4)
    require(value["instance"] in ("a", "b"))
    require(
        isinstance(value["database_url"], str)
        and 0 < len(value["database_url"]) <= 2048
    )
    require(
        isinstance(value["jwt_secret"], str)
        and 32 <= len(value["jwt_secret"].encode("utf-8")) <= 4096
    )
    return value


class IdentityMiddleware:
    """Outer test-only ASGI wrapper tags every HTTP response, including errors."""

    def __init__(self, app, config, pid):
        self.app = app
        self.headers = [
            (b"x-gandalf-gate-run", config["run"].encode("ascii")),
            (b"x-gandalf-gate-instance", config["instance"].encode("ascii")),
            (b"x-gandalf-gate-pid", str(pid).encode("ascii")),
        ]

    async def __call__(self, scope, receive, send):
        async def tagged(message):
            if scope["type"] == "http" and message["type"] == "http.response.start":
                headers = [
                    (key, value)
                    for key, value in message.get("headers", [])
                    if key.lower() not in HEADERS
                ]
                message = {**message, "headers": [*headers, *self.headers]}
            await send(message)

        await self.app(scope, receive, tagged)


def serve(
    config,
    emit,
    *,
    runtime=None,
    uvicorn_module=None,
    socket_factory=None,
    control=None,
):
    require(os.environ.get("GANDALF_TCP_PG_ALLOW") == ALLOW)
    # The reused loader imports app.main under an empty cwd and sanitized environment.
    if runtime is None:
        runtime = importlib.import_module("scripts.postgres_http_gate").load_runtime()
    runtime.base.validate_target(config["database_url"])
    settings = runtime.Settings(
        _env_file=None,
        database_url=config["database_url"],
        jwt_secret=config["jwt_secret"],
        online_catalog=False,
        book_provider="local",
        groq_api_key="",
        cors_origins=[],
        access_token_minutes=15,
        refresh_token_days=7,
        auth_rate_limit_per_minute=10,
    )
    app = runtime.create_app(settings=settings)
    uvicorn = uvicorn_module or importlib.import_module("uvicorn")
    pid = os.getpid()
    wrapped = IdentityMiddleware(app, config, pid)
    disposed = False

    def mark_disposed(_engine):
        nonlocal disposed
        disposed = True

    bound = None
    previous_logging = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    try:
        bound = (socket_factory or socket.socket)(socket.AF_INET, socket.SOCK_STREAM)
        bound.bind(("127.0.0.1", 0))
        host, port = bound.getsockname()
        require(host == "127.0.0.1" and type(port) is int and 1024 <= port <= 65535)
        bound.setblocking(False)

        class ReadyServer(uvicorn.Server):
            async def startup(self, sockets=None):
                await super().startup(sockets=sockets)
                require(self.started and not self.should_exit)
                engine = getattr(app.state, "engine", None)
                if engine is not None:
                    runtime.sa.event.listen(engine, "engine_disposed", mark_disposed)
                emit(
                    {
                        "status": "READY",
                        "port": port,
                        "pid": pid,
                        "run": config["run"],
                        "instance": config["instance"],
                    }
                )

        server = ReadyServer(
            uvicorn.Config(
                wrapped,
                host="127.0.0.1",
                port=port,
                workers=1,
                lifespan="on",
                log_config=None,
                log_level="critical",
                access_log=False,
                use_colors=False,
                proxy_headers=False,
                timeout_graceful_shutdown=5,
            )
        )

        def stop_on_input():
            (control or sys.stdin).readline(32)
            server.should_exit = True

        threading.Thread(target=stop_on_input, daemon=True).start()
        server.run(sockets=[bound])
    finally:
        try:
            if bound is not None:
                bound.close()
        finally:
            try:
                engine = getattr(app.state, "engine", None)
                if engine is not None and not disposed:
                    engine.dispose()
            finally:
                logging.disable(previous_logging)


def failure_line(traceback):
    line = 1
    while traceback:
        frame = traceback.tb_frame
        if (
            Path(frame.f_code.co_filename).resolve() == Path(__file__).resolve()
            and frame.f_code.co_name != "require"
        ):
            line = traceback.tb_lineno
        traceback = traceback.tb_next
    return line


def main():
    ready = False
    stage = "coordination"

    def emit(value):
        nonlocal ready
        require(not ready)
        print(json.dumps(value, sort_keys=True), flush=True)
        ready = True

    try:
        require(len(sys.argv) == 1 and os.environ.get("GANDALF_TCP_PG_ALLOW") == ALLOW)
        stage = "configuration"
        config = read_config(sys.stdin)
        stage = "startup"
        serve(config, emit)
        require(ready)
        return 0
    except BaseException:  # noqa: BLE001 -- includes Uvicorn startup SystemExit, no traceback.
        if ready and sys.exc_info()[0] is KeyboardInterrupt:
            return 0
        output = sys.stderr if ready else sys.stdout
        print(
            json.dumps(
                {
                    "status": "NOT_PASSED",
                    "stage": stage,
                    "line": failure_line(sys.exc_info()[2]),
                }
            ),
            file=output,
            flush=True,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
