"""Opt-in disposable PostgreSQL/TCP gate; never targets existing API processes."""

import hashlib
import json
import os
import queue
import re
import secrets
import subprocess
import sys
import sysconfig
import tempfile
import threading
from pathlib import Path
from time import monotonic, sleep
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
from uuid import UUID, uuid4

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))
from scripts import postgres_http_gate as base

ALLOW = "isolated-coordinated-backend-frozen"
WORKER = API_ROOT / "scripts/postgres_tcp_worker.py"
STAGE = "coordination"
CHECKS = [
    "identified_tcp_processes",
    "cross_process_session_rotation",
    "shared_snapshots_ownership",
    "restart_preserves_live_session",
    "cross_process_logout",
    "sql_persistence_ai_zero",
    "owned_process_cleanup",
]
KEEP = {
    "PATH",
    "PATHEXT",
    "SYSTEMROOT",
    "WINDIR",
    "COMSPEC",
    "TEMP",
    "TMP",
    "USERPROFILE",
    "APPDATA",
    "LOCALAPPDATA",
    "HOME",
}


def require(condition):
    if not condition:
        raise ValueError("TCP gate check failed")


def stage(value):
    global STAGE
    STAGE = value
    print(json.dumps({"stage": value}), file=sys.stderr, flush=True)


def failure_location(error):
    line = 1
    traceback = error.__traceback__
    while traceback:
        frame = traceback.tb_frame
        if (
            Path(frame.f_code.co_filename).resolve() == Path(__file__).resolve()
            and frame.f_code.co_name != "require"
        ):
            line = traceback.tb_lineno
        traceback = traceback.tb_next
    return {"source": "postgres_tcp_gate.py", "line": line}


class WorkerFailure(ValueError):
    def __init__(self, value):
        require(isinstance(value, dict) and value.get("status") == "NOT_PASSED")
        require(value.get("stage") in {"coordination", "configuration", "startup"})
        require(type(value.get("line")) is int and 1 <= value["line"] <= 10000)
        super().__init__("Worker failed")
        self.public = {"stage": value["stage"], "line": value["line"]}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        raise ValueError("Redirect refused")


def source_snapshot():
    files = base.source_snapshot()
    for path in (
        Path(__file__),
        WORKER,
        API_ROOT / "tests/test_postgres_tcp_gate.py",
        API_ROOT / "tests/test_postgres_tcp_worker.py",
    ):
        files[path.relative_to(base.ROOT).as_posix()] = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
    return files


def validate_ready(value, pid, run, instance):
    require(
        isinstance(value, dict)
        and set(value) == {"status", "pid", "port", "run", "instance"}
    )
    require(
        value["status"] == "READY" and type(value["pid"]) is int and value["pid"] == pid
    )
    require(value["run"] == run and value["instance"] == instance)
    port = value["port"]
    require(
        type(port) is int
        and 1024 <= port <= 65535
        and port not in {5432, 5433, 55432, 55433, 5173, 8000, 8001, 8080}
    )
    return port


def validate_offline(value):
    require(isinstance(value, dict) and value.get("catalog") == "local")
    ai = value.get("ai")
    require(isinstance(ai, dict) and ai.get("configured") is False)
    require(ai.get("provider") is None and ai.get("model") is None)


class Child:
    def __init__(self, value, secret, run, instance, cwd):
        self.instance, self.run, self.count = instance, run, 0
        self.port, self.process = None, None
        env = {k: v for k, v in os.environ.items() if k.upper() in KEEP}
        env.update(GANDALF_TCP_PG_ALLOW=ALLOW, PYTHONDONTWRITEBYTECODE="1")
        # Windows venv python.exe is a redirector with a different child PID.
        # Invoke the base interpreter directly, with only this environment's packages.
        interpreter = Path(getattr(sys, "_base_executable", sys.executable)).resolve()
        packages = Path(sysconfig.get_path("purelib")).resolve()
        require(interpreter.is_file() and packages.is_dir())
        require(packages.is_relative_to(Path(sys.prefix).resolve()))
        env["PYTHONPATH"] = str(packages)
        self.process = subprocess.Popen(
            [str(interpreter), "-S", str(WORKER)],
            cwd=cwd,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
        )
        try:
            config = {
                "database_url": value,
                "jwt_secret": secret,
                "run": run,
                "instance": instance,
            }
            self.process.stdin.write(json.dumps(config) + "\n")
            self.process.stdin.flush()
            messages = queue.Queue()
            threading.Thread(
                target=lambda: messages.put(self.process.stdout.readline(4097)),
                daemon=True,
            ).start()
            line = messages.get(timeout=15)
            require(0 < len(line) <= 4096)
            payload = json.loads(line)
            if isinstance(payload, dict) and payload.get("status") == "NOT_PASSED":
                raise WorkerFailure(payload)
            self.port = validate_ready(payload, self.process.pid, run, instance)
            deadline = monotonic() + 15
            while True:
                require(self.process.poll() is None)
                try:
                    self.request("GET", "/health/ready")
                    break
                except (URLError, TimeoutError, OSError):
                    require(monotonic() < deadline)
                    sleep(0.05)
            validate_offline(self.request("GET", "/api/v1/system/status"))
        except BaseException:
            self.stop()
            raise

    def request(self, method, path, status=200, *, body=None, tokens=None):
        require(self.process.poll() is None and path.startswith("/"))
        headers = {"Content-Type": "application/json"}
        if tokens:
            headers["Authorization"] = "Bearer " + tokens["access_token"]
        request = Request(
            f"http://127.0.0.1:{self.port}" + path,
            data=json.dumps(body).encode() if body is not None else None,
            headers=headers,
            method=method,
        )
        opener = build_opener(ProxyHandler({}), NoRedirect())
        try:
            response = opener.open(request, timeout=5)
        except HTTPError as error:
            response = error
        with response:
            self.count += 1
            require(response.status == status)
            require(
                response.headers.get("x-gandalf-gate-run") == self.run
                and response.headers.get("x-gandalf-gate-instance") == self.instance
                and response.headers.get("x-gandalf-gate-pid") == str(self.process.pid)
            )
            request_id = response.headers.get("X-Request-ID", "")
            require(str(UUID(request_id)) == request_id)
            if path.startswith("/api/v1/auth/"):
                require(
                    response.headers.get("Cache-Control") == "no-store"
                    and response.headers.get("Pragma") == "no-cache"
                )
            data = response.read(1048577)
            require(len(data) <= 1048576)
            if status == 204:
                require(data == b"")
                return None
            result = json.loads(data)
            if status >= 400:
                require(result["error"]["request_id"] == request_id)
                require(
                    result["error"]["code"]
                    == {401: "UNAUTHORIZED", 404: "NOT_FOUND"}[status]
                )
                return None
            return result

    def stop(self):
        if self.process is None:
            return True
        graceful = True
        if self.process.poll() is None:
            try:
                self.process.stdin.write("STOP\n")
                self.process.stdin.flush()
                self.process.wait(timeout=8)
            except (OSError, subprocess.TimeoutExpired):
                graceful = False
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=5)
        for stream in (self.process.stdin, self.process.stdout):
            if stream:
                stream.close()
        return graceful and self.process.returncode == 0


def sql_snapshot(engine, runtime, owner):
    sa = runtime.sa
    with engine.begin() as connection:
        connection.execute(sa.text("SET TRANSACTION READ ONLY"))
        connection.execute(sa.text("SET LOCAL statement_timeout = '5000ms'"))
        counts = {
            table: connection.scalar(sa.text("SELECT count(*) FROM " + table))
            for table in (
                "users",
                "favorites",
                "playlists",
                "playlist_tracks",
                "recommendation_results",
                "refresh_tokens",
            )
        }
        counts["active_refresh_tokens"] = connection.scalar(
            sa.text("SELECT count(*) FROM refresh_tokens WHERE revoked_at IS NULL")
        )
        counts["ai_calls"] = connection.scalar(
            sa.text("SELECT COALESCE(sum(calls),0) FROM ai_usage")
        )
        fingerprints = {}
        for table in (
            "favorites",
            "playlists",
            "playlist_tracks",
            "recommendation_results",
        ):
            order = "playlist_id, position" if table == "playlist_tracks" else "id"
            rows = (
                connection.execute(
                    sa.text("SELECT * FROM " + table + " ORDER BY " + order)
                )
                .mappings()
                .all()
            )
            fingerprints[table] = hashlib.sha256(
                json.dumps(
                    [dict(row) for row in rows], sort_keys=True, default=str
                ).encode()
            ).hexdigest()
        for table in ("favorites", "playlists"):
            require(
                connection.scalar(
                    sa.text(
                        "SELECT count(*) FROM " + table + " WHERE user_id <> :owner"
                    ),
                    {"owner": UUID(owner)},
                )
                == 0
            )
        require(counts["ai_calls"] == 0)
        return {"counts": counts, "fingerprints": fingerprints}


def execute(value):
    require(os.environ.get("GANDALF_TCP_PG_ALLOW") == ALLOW)
    snapshot = source_snapshot()
    stage("isolated_imports")
    r = base.load_runtime()
    url = r.base.validate_target(value)
    engine = r.base.engine_for(value)
    children = []
    checks = []
    directory = None
    try:
        stage("empty_database")
        with engine.connect() as connection:
            database, user = connection.execute(
                r.sa.text("SELECT current_database(), current_user")
            ).one()
            occupied = connection.scalar(
                r.sa.text(
                    "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname NOT LIKE 'pg_%' AND n.nspname <> 'information_schema' AND c.relkind IN ('r','p','v','m','S','f')"
                )
            )
            available = set(
                connection.scalars(
                    r.sa.text(
                        "SELECT name FROM pg_available_extensions WHERE name IN ('citext','vector')"
                    )
                )
            )
            r.base.validate_database(url, database, user, occupied, available)
        stage("migration_head_once")
        config = r.Config(str(API_ROOT / "alembic.ini"))
        config.set_main_option("script_location", str(API_ROOT / "alembic"))
        with engine.begin() as connection:
            config.attributes["connection"] = connection
            r.command.upgrade(config, "head")
        with engine.connect() as connection:
            require(
                list(
                    connection.scalars(
                        r.sa.text("SELECT version_num FROM alembic_version")
                    )
                )
                == list(r.ScriptDirectory.from_config(config).get_heads())
            )
        directory = tempfile.TemporaryDirectory(
            prefix="tcp-gate-", dir=base.ROOT / ".impeccable/runtime"
        )
        cwd = directory.name
        run, secret = str(uuid4()), secrets.token_hex(32)
        stage("start_owned_api_processes")
        a = Child(value, secret, run, "a", cwd)
        children.append(a)
        b = Child(value, secret, run, "b", cwd)
        children.append(b)
        require(a.process.pid != b.process.pid and a.port != b.port)
        checks.append(CHECKS[0])
        stage("cross_process_session")
        password, suffix = secrets.token_urlsafe(24), uuid4().hex
        owner = a.request(
            "POST",
            "/api/v1/auth/register",
            201,
            body={
                "email": suffix + "@example.com",
                "username": "a" + suffix[:19],
                "password": password,
            },
        )
        b.request(
            "POST",
            "/api/v1/auth/register",
            201,
            body={
                "email": "b" + suffix + "@example.com",
                "username": "b" + suffix[:19],
                "password": password,
            },
        )
        tokens = a.request(
            "POST",
            "/api/v1/auth/login",
            body={"email": suffix + "@example.com", "password": password},
        )
        foreign = b.request(
            "POST",
            "/api/v1/auth/login",
            body={"email": "b" + suffix + "@example.com", "password": password},
        )
        require(b.request("GET", "/api/v1/auth/me", tokens=tokens)["id"] == owner["id"])
        current = b.request(
            "POST",
            "/api/v1/auth/refresh",
            body={"refresh_token": tokens["refresh_token"]},
        )
        require(current["refresh_token"] != tokens["refresh_token"])
        require(
            a.request("GET", "/api/v1/auth/me", tokens=current)["id"] == owner["id"]
        )
        checks.append(CHECKS[1])
        stage("snapshots_ownership")
        source = a.request(
            "POST",
            "/api/v1/recommendations/read-with-music",
            body={
                "book_id": str(r.BOOKS[1].id),
                "mode": "CALM",
                "target_duration_min": 15,
            },
        )
        require(bool(source["items"]))
        favorite = b.request(
            "POST",
            "/api/v1/users/me/favorites",
            201,
            tokens=current,
            body={
                "recommendation_id": source["recommendation_id"],
                "item_id": source["items"][0]["item"]["id"],
            },
        )
        playlist = a.request(
            "POST",
            "/api/v1/playlists",
            201,
            tokens=current,
            body={
                "name": "Gate TCP",
                "source_recommendation_id": source["recommendation_id"],
            },
        )
        path = "/api/v1/playlists/" + playlist["id"]
        require(b.request("GET", path, tokens=current) == playlist)
        require(
            b.request("GET", "/api/v1/users/me/favorites", tokens=foreign)["total"] == 0
        )
        b.request("GET", path, 404, tokens=foreign)
        b.request("DELETE", path, 404, tokens=foreign)
        a.request(
            "DELETE",
            "/api/v1/users/me/favorites/" + favorite["id"],
            204,
            tokens=foreign,
        )
        checks.append(CHECKS[2])
        before = sql_snapshot(engine, r, owner["id"])
        old_pid = b.process.pid
        stage("restart_b_live_session")
        require(b.stop())
        require(
            a.request("GET", "/api/v1/auth/me", tokens=current)["id"] == owner["id"]
        )
        b2 = Child(value, secret, run, "b", cwd)
        children.append(b2)
        require(b2.process.pid not in {old_pid, a.process.pid})
        require(
            b2.request("GET", "/api/v1/auth/me", tokens=current)["id"] == owner["id"]
        )
        require(b2.request("GET", path, tokens=current) == playlist)
        favorites = b2.request("GET", "/api/v1/users/me/favorites", tokens=current)
        require(favorites["total"] == 1 and favorites["items"][0] == favorite)
        after = sql_snapshot(engine, r, owner["id"])
        require(before == after)
        checks.append(CHECKS[3])
        stage("logout_cross_process")
        final = b2.request(
            "POST",
            "/api/v1/auth/refresh",
            body={"refresh_token": current["refresh_token"]},
        )
        require(a.request("GET", "/api/v1/auth/me", tokens=final)["id"] == owner["id"])
        a.request(
            "POST",
            "/api/v1/auth/logout",
            204,
            tokens=final,
            body={"refresh_token": final["refresh_token"]},
        )
        b2.request(
            "POST",
            "/api/v1/auth/refresh",
            401,
            body={"refresh_token": final["refresh_token"]},
        )
        require(b2.request("GET", "/api/v1/auth/me", tokens=final)["id"] == owner["id"])
        checks.append(CHECKS[4])
        observed = sql_snapshot(engine, r, owner["id"])
        require(observed["fingerprints"] == before["fingerprints"])
        require(
            observed["counts"]
            == {
                "users": 2,
                "favorites": 1,
                "playlists": 1,
                "playlist_tracks": len(playlist["tracks"]),
                "recommendation_results": 1,
                "refresh_tokens": 4,
                "active_refresh_tokens": 1,
                "ai_calls": 0,
            }
        )
        checks.append(CHECKS[5])
        stage("owned_process_cleanup")
        stopped = [child.stop() for child in children]
        cleanup = all(stopped)
        require(cleanup and all(child.process.poll() is not None for child in children))
        checks.append(CHECKS[6])
        require(source_snapshot() == snapshot)
        return {
            "head": list(r.ScriptDirectory.from_config(config).get_heads()),
            "status": "PASS",
            "transport": "TCP_TWO_PROCESSES_RESTART",
            "checks": checks,
            "counts": observed["counts"],
            "requests": {"a": a.count, "b": b.count, "b_restarted": b2.count},
            "restart_without_login": True,
            "persistence_verified": True,
            "cleanup_verified": True,
            "source_unchanged": True,
            "source_sha256": hashlib.sha256(
                json.dumps(snapshot, sort_keys=True).encode()
            ).hexdigest(),
        }
    finally:
        # Always attempt every owned child, even if another cleanup failed.
        stopped = []
        for child in children:
            try:
                stopped.append(child.stop())
            except Exception:  # noqa: BLE001 -- attempt every owned process.
                stopped.append(False)
        engine.dispose()
        require(all(stopped))
        if directory is not None:
            target = Path(directory.name).resolve()
            require(
                target.parent == (base.ROOT / ".impeccable/runtime").resolve()
                and target.name.startswith("tcp-gate-")
                and not target.is_symlink()
            )
            directory.cleanup()


def public_result(value):
    require(isinstance(value, dict) and value.get("status") == "PASS")
    require(value.get("transport") == "TCP_TWO_PROCESSES_RESTART")
    require(value.get("checks") == CHECKS)
    fields = base.COUNT_FIELDS
    counts = value.get("counts")
    require(isinstance(counts, dict) and set(counts) == set(fields))
    require(all(type(counts[k]) is int and 0 <= counts[k] <= 100 for k in fields))
    require(
        counts
        == dict(
            zip(fields, (2, 1, 1, counts["playlist_tracks"], 1, 4, 1, 0), strict=True)
        )
    )
    require(1 <= counts["playlist_tracks"] <= 30)
    requests = value.get("requests")
    require(isinstance(requests, dict) and set(requests) == {"a", "b", "b_restarted"})
    require(all(type(v) is int and 1 <= v <= 100 for v in requests.values()))
    flags = (
        "restart_without_login",
        "persistence_verified",
        "cleanup_verified",
        "source_unchanged",
    )
    require(all(value.get(k) is True for k in flags))
    require(value.get("head") == ["0008_favorites"])
    digest = value.get("source_sha256")
    require(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest))
    return {
        "status": "PASS",
        "transport": "TCP_TWO_PROCESSES_RESTART",
        "checks": list(CHECKS),
        "counts": {k: counts[k] for k in fields},
        "requests": {k: requests[k] for k in ("a", "b", "b_restarted")},
        "head": ["0008_favorites"],
        "source_sha256": digest,
        **{k: True for k in flags},
    }


def main():
    try:
        require(os.environ.get("GANDALF_TCP_PG_ALLOW") == ALLOW)
        require(len(sys.argv) == 1)
        result = public_result(execute(os.environ["GANDALF_TCP_PG_URL"]))
        code = 0
    except Exception as error:  # noqa: BLE001 -- never print exception messages or credentials.
        kind = type(error).__name__
        result = {
            "status": "NOT_PASSED",
            "stage": STAGE,
            "error_class": kind
            if kind
            in {
                "ValueError",
                "KeyError",
                "RuntimeError",
                "TimeoutError",
                "OSError",
                "Empty",
            }
            else "ExecutionError",
        }
        result["failure_location"] = failure_location(error)
        if isinstance(error, WorkerFailure):
            result["worker_failure"] = dict(error.public)
        code = 1
    print(json.dumps(result, sort_keys=True), flush=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
