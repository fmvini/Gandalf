"""Opt-in disposable fullstack gate. Stdout is one sanitized final JSON.

Run from the checkout with GANDALF_DEPLOYMENT_ALLOW=isolated-coordinated.
Docker/Compose, Node and installed frontend Playwright are prerequisites.
No inherited application environment, existing service or persisted volume is used.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import ssl
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
from uuid import UUID, uuid4

ROOT = Path(__file__).resolve().parents[1]
PG_IMAGE = (
    "pgvector/pgvector@sha256:"
    "2ba9ca5f2e7daa0f0e7723cba1ee9167bab54efd3640516a44ac1a928dd67e7a"
)
LABEL = "com.gandalf.deployment-gate"
SERVICES = {"api": 8000, "frontend": 80, "db": 5432}
FORBIDDEN_PORTS = {5173, 8080, 8000, 8001, 5432, 5433, 55432, 55433}
SYSTEM_ENV = {
    "PATH",
    "PATHEXT",
    "SYSTEMROOT",
    "WINDIR",
    "COMSPEC",
    "TEMP",
    "TMP",
    "HOME",
    "USERPROFILE",
    "APPDATA",
    "LOCALAPPDATA",
    "PROGRAMFILES",
    "PROGRAMFILES(X86)",
    "PROGRAMDATA",
    "PLAYWRIGHT_BROWSERS_PATH",
}


class GateError(RuntimeError):
    """No sensitive values in exception messages."""


class RejectRedirects(HTTPRedirectHandler):
    def redirect_request(self, _request, _response, _code, _message, _headers, _newurl):
        raise GateError("Redirects are forbidden")


def child_diagnostic(item: dict) -> dict:
    """Reconstruct browser diagnostics without messages, inputs or arbitrary JSON."""
    result = {}
    substage = item.get("substage")
    substages = {
        "status-request",
        "start",
        "response-json",
        "memory-only-evaluate",
        "login-destination-evaluate",
        "refresh-clock-evaluate",
        "refresh-clock-restore-evaluate",
        "browser-close-success",
        "browser-close-finally",
        *("response-finished-" + code for code in ("200", "201", "204")),
        "account-profile-ready",
        "account-playlists-ready",
        "login-page-ready",
        "login-fill-email",
        "login-fill-password",
        "login-return-destination",
        "login-open-account-spa",
        "login-account-heading",
        "register-open-link",
        "register-page-ready",
        "register-native-validation",
        "register-login-notice",
        *(
            "register-fill-" + field
            for field in ("email", "username", "password", "confirmation")
        ),
        *(
            "api-post-/auth/" + action
            for action in ("register", "login", "refresh", "logout")
        ),
        *(
            "api-post-/recommendations/" + flow
            for flow in ("music", "books", "read-with-music")
        ),
        "api-post-/users/me/favorites",
        "api-get-/users/me/favorites",
        "api-post-/playlists",
    }
    if isinstance(substage, str) and substage in substages:
        result["substage"] = substage
    locations = item.get("failure_location")
    if isinstance(locations, list):
        result["failure_location"] = [
            {"file": "deployment.mjs", "line": row["line"], "column": row["column"]}
            for row in locations[:3]
            if isinstance(row, dict)
            and row.get("file") == "deployment.mjs"
            and all(
                type(row.get(key)) is int and 0 < row[key] <= 100000
                for key in ("line", "column")
            )
        ]
    auth = item.get("auth_diagnostic")
    if isinstance(auth, dict):
        routes = {
            "/login",
            "/register",
            "/account",
            "/account/favorites",
            "/music",
            "/books",
            "/read-with-music",
            "/other",
        }
        fields = {"auth-email", "auth-username", "auth-password", "auth-confirmation"}
        invalid = auth.get("invalid_fields")
        if (
            isinstance(auth.get("path"), str)
            and auth["path"] in routes
            and all(
                type(auth.get(key)) is bool for key in ("form_present", "form_busy")
            )
            and type(auth.get("alert_count")) is int
            and 0 <= auth["alert_count"] <= 100
            and isinstance(invalid, list)
            and len(invalid) <= 4
            and all(isinstance(field, str) and field in fields for field in invalid)
        ):
            result["auth_diagnostic"] = {
                key: auth[key]
                for key in (
                    "path",
                    "form_present",
                    "form_busy",
                    "alert_count",
                    "invalid_fields",
                )
            }
    traffic = item.get("traffic")
    identity = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
    endpoint = (
        r"/api/v1/(?:system/status|auth/(?:register|login|refresh|logout|me)"
        rf"|users/me/favorites(?:/status|/{identity})?|playlists(?:/{identity})?"
        rf"|recommendations/(?:music|books|read-with-music|{identity}/items/{identity}/explanation)|books/search)"
    )
    if isinstance(traffic, list):
        safe = []
        for row in traffic[:200]:
            if (
                isinstance(row, dict)
                and isinstance(row.get("request"), str)
                and re.fullmatch(
                    r"(?:GET|POST|DELETE) " + endpoint + r" [1-5][0-9]{2}",
                    row["request"],
                )
                and type(row.get("count")) is int
                and 0 < row["count"] <= 10000
            ):
                safe.append({"request": row["request"], "count": row["count"]})
        result["traffic"] = safe
    for field in (
        "browser_errors",
        "console_errors",
        "blocked_external_requests",
        "proven_logout_abort_count",
    ):
        value = item.get(field)
        if type(value) is int and 0 <= value <= 10000:
            result[field] = value
    failures = item.get("failures")
    if isinstance(failures, list):
        result["failures"] = []
        for row in failures[:100]:
            if not isinstance(row, dict) or row.get("kind") not in (
                "http",
                "requestfailed",
            ):
                continue
            if row.get("method") not in ("GET", "POST", "DELETE"):
                continue
            path = row.get("path")
            if not isinstance(path, str):
                continue
            safe_path = path if re.fullmatch(endpoint, path) else "/other"
            safe_row = {"kind": row["kind"], "method": row["method"], "path": safe_path}
            if row.get("error_code") in (
                "net::ERR_ABORTED",
                "net::ERR_FAILED",
                "net::ERR_CONNECTION_REFUSED",
                "other",
            ):
                safe_row["error_code"] = row["error_code"]
            if row["kind"] == "http":
                if (
                    type(row.get("status")) is not int
                    or not 400 <= row["status"] <= 599
                ):
                    continue
                safe_row["status"] = row["status"]
            result["failures"].append(safe_row)
    return result


class CommandFailure(GateError):
    def __init__(self, returncode: int, stderr: str):
        super().__init__("Child command failed")
        self.returncode = returncode
        self.child_stage = None
        self.child_kind = None
        self.child_diagnostic = {}
        child_status = None
        self.reasons = [
            name
            for name, pattern in {
                "build-context-read-denied": r"permission denied|access is denied|acesso negado",
                "tls-verification": r"certificate|x509|sslcertverification",
                "registry-or-network": r"failed to resolve source metadata|failed to fetch|i/o timeout|connection refused|no such host",
                "dockerfile-missing": r"failed to read dockerfile",
                "npm-build": r"npm err|npm error|ts[0-9]{4}",
                "pip-install": r"could not find a version|no matching distribution|pip.*error",
                "compose-build-api-unsupported": r"unknown flag|unknown command|buildx.*not|buildx.*missing",
                "build-dependency-tls-issuer-missing": r"unable to get local issuer certificate",
            }.items()
            if re.search(pattern, stderr, re.IGNORECASE)
        ]
        for line in stderr.splitlines():
            try:
                item = json.loads(line)
            except (ValueError, TypeError):
                continue
            if (
                isinstance(item, dict)
                and item.get("status") in ("FAIL", "PROGRESS")
                and child_status != "FAIL"
            ):
                child_status = item["status"]
                self.child_diagnostic = child_diagnostic(item)
                for key, attribute in (
                    ("stage", "child_stage"),
                    ("error_kind", "child_kind"),
                ):
                    value = item.get(key)
                    if isinstance(value, str) and re.fullmatch(
                        r"[A-Za-z0-9_-]{1,80}", value
                    ):
                        setattr(self, attribute, value)


def require(condition: bool) -> None:
    if not condition:
        raise GateError("Gate check failed")


def clean_environment(source: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in source.items() if key.upper() in SYSTEM_ENV}


def canonical_uuid(value: str) -> str:
    parsed = UUID(value)
    require(str(parsed) == value and parsed.version == 4)
    return value


def browser_artifact(result: dict, phase: str, run: str, origin: str) -> dict:
    require(isinstance(result, dict) and phase in ("create", "verify"))
    allowed = {
        "version",
        "phase",
        "status",
        "run_fingerprint",
        "base_url",
        "checks",
        "user_ids",
        "favorite_ids",
        "playlist_ids",
        "public_snapshot_id",
        "public_snapshot_music_ids",
        "playlist_music_ids",
        "favorites",
        "browser_errors",
        "console_errors",
        "blocked_external_requests",
        "proven_logout_abort_count",
        "traffic",
    }
    require(set(result) <= allowed)
    require(type(result.get("version")) is int and result["version"] == 1)
    require(result.get("status") == "PASS" and result.get("phase") == phase)
    require(result.get("base_url") == origin)
    validate_origin(origin)
    fingerprint = hashlib.sha256(run.encode()).hexdigest()
    require(result.get("run_fingerprint") == fingerprint)
    output = {
        "version": 1,
        "phase": phase,
        "status": "PASS",
        "base_url": origin,
        "run_fingerprint": fingerprint,
    }
    for field, count in (
        ("user_ids", 2),
        ("favorite_ids", 2),
        ("playlist_ids", 1),
        ("public_snapshot_music_ids", None),
        ("playlist_music_ids", None),
    ):
        rows = result.get(field)
        require(isinstance(rows, list) and 0 < len(rows) <= 100)
        require(count is None or len(rows) == count)
        require(
            all(
                isinstance(identifier, str) and str(UUID(identifier)) == identifier
                for identifier in rows
            )
        )
        require(len(set(rows)) == len(rows))
        output[field] = list(rows)
    snapshot = result.get("public_snapshot_id")
    require(isinstance(snapshot, str) and str(UUID(snapshot)) == snapshot)
    output["public_snapshot_id"] = snapshot
    favorites = result.get("favorites")
    require(isinstance(favorites, list) and len(favorites) == 2)
    output["favorites"] = []
    for index, row in enumerate(favorites):
        require(isinstance(row, dict))
        require(row.get("id") == output["favorite_ids"][index])
        require(row.get("type") == ("BOOK" if index else "MUSIC"))
        identifier = row.get("item_id")
        require(isinstance(identifier, str) and str(UUID(identifier)) == identifier)
        output["favorites"].append(
            {
                "id": output["favorite_ids"][index],
                "type": row["type"],
                "item_id": identifier,
            }
        )
    common = {
        "offline-status",
        "real-refresh-via-ui",
        "real-same-origin-api-and-clean-browser",
    }
    expected = common | (
        {
            "nginx-direct-spa-paths",
            "public-music-and-explanation",
            "two-accounts-ownership-and-logout-revocation",
            "saved-snapshots-preserved-for-runner-sql-and-restart",
        }
        if phase == "create"
        else {
            "public-source-survives-restart",
            "browser-relogin-and-snapshot-persistence-after-restart",
            "second-account-relogin-and-preserved-sql-fixtures",
        }
    )
    checks = result.get("checks")
    require(
        isinstance(checks, list) and all(isinstance(check, str) for check in checks)
    )
    require(len(checks) == len(expected) and set(checks) == expected)
    output["checks"] = list(checks)
    for field in ("browser_errors", "console_errors", "blocked_external_requests"):
        require(type(result.get(field)) is int and result[field] == 0)
        output[field] = 0
    count = result.get("proven_logout_abort_count")
    require(type(count) is int and 0 <= count <= (4 if phase == "create" else 2))
    output["proven_logout_abort_count"] = count
    return output


def validate_build_ca(value: str, root: Path = ROOT) -> tuple[Path, str]:
    """Accept an explicit public PEM inside the gate's ignored workspace only."""
    requested = Path(value)
    require(requested.is_absolute())
    path = requested.resolve(strict=True)
    require(path.is_relative_to((root / ".impeccable/runtime").resolve()))
    require(path.is_file() and path.stat().st_size <= 1024 * 1024)
    content = path.read_bytes()
    pem = content.decode("ascii")
    require(
        re.fullmatch(
            r"(?:\s*-----BEGIN CERTIFICATE-----\s+[A-Za-z0-9+/=\s]+"
            r"-----END CERTIFICATE-----\s*)+",
            pem,
        )
        is not None
    )
    ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT).load_verify_locations(cadata=pem)
    return path, hashlib.sha256(content).hexdigest()


def validate_origin(origin: str) -> int:
    value = urlsplit(origin)
    require(value.scheme == "http" and value.hostname == "127.0.0.1")
    require(not value.username and not value.password and not value.query)
    require(not value.fragment and not value.path and value.port is not None)
    require(origin == f"http://127.0.0.1:{value.port}")
    require(1024 <= value.port <= 65535 and value.port not in FORBIDDEN_PORTS)
    return value.port


def labels_match(labels: dict, run: str, project: str, service: str | None = None):
    require(labels.get(LABEL) == canonical_uuid(run))
    require(project == "gandalf_deploy_" + UUID(run).hex)
    require(labels.get("com.docker.compose.project") == project)
    if service is not None:
        require(service in SERVICES)
        require(labels.get("com.docker.compose.service") == service)


def validate_config(config: dict, env: dict, root: Path = ROOT) -> None:
    """Validate merged Compose, including overrides that remove inherited data."""
    run = canonical_uuid(env["GANDALF_GATE_UUID"])
    project = "gandalf_deploy_" + UUID(run).hex
    require(env["GANDALF_GATE_PROJECT"] == project and config["name"] == project)
    require(set(config["services"]) == set(SERVICES))
    require(not config.get("volumes"))
    ca = env.get("GANDALF_BUILD_CA_CERT")
    if ca:
        ca_path, _ = validate_build_ca(ca, root)
        require(
            config.get("secrets")
            == {
                "gandalf_build_ca": {
                    "name": project + "_gandalf_build_ca",
                    "file": str(ca_path),
                }
            }
        )
    else:
        require(not config.get("secrets"))
    require(not config.get("configs"))
    network = config["networks"]
    require(set(network) == {"default"})
    require(network["default"].get("internal", False) is False)
    require(network["default"].get("driver") == "bridge")
    require(not network["default"].get("external"))
    require(network["default"].get("labels", {}).get(LABEL) == run)
    require(network["default"]["name"] == project + "_default")
    for service, target in SERVICES.items():
        value = config["services"][service]
        require(not value.get("env_file") and not value.get("secrets"))
        require(not value.get("configs") and not value.get("container_name"))
        require(not value.get("privileged") and not value.get("network_mode"))
        require(not value.get("devices") and not value.get("cap_add"))
        require(not value.get("external_links") and not value.get("extra_hosts"))
        require(not value.get("volumes_from"))
        require(set(value.get("networks", {})) == {"default"})
        require(value.get("labels", {}).get(LABEL) == run)
        require(value["pull_policy"] == "never")
        ports = value["ports"]
        require(len(ports) == 1)
        port = ports[0]
        require(port["target"] == target and str(port["published"]) == "0")
        require(port["host_ip"] == "127.0.0.1" and port["protocol"] == "tcp")
        if service == "db":
            require(value["image"] == PG_IMAGE and not value.get("build"))
            mounts = value["volumes"]
            require(len(mounts) == 1 and mounts[0]["type"] == "tmpfs")
            require(mounts[0]["target"] == "/var/lib/postgresql")
            require(not mounts[0].get("source"))
            require(str(mounts[0]["tmpfs"]["size"]) == "536870912")
            require(
                value["environment"]
                == {
                    key: env[key]
                    for key in ("POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD")
                }
            )
        else:
            require(not value.get("volumes"))
            require(value["image"] == project + "-" + service + ":gate")
            build = value["build"]
            require(Path(build["context"]).resolve() == root.resolve())
            require(build["dockerfile"] == service + "/Dockerfile")
            require(not build.get("args"))
            if ca:
                require(
                    build.get("secrets")
                    == [{"source": "gandalf_build_ca", "target": "gandalf_build_ca"}]
                )
            else:
                require(not build.get("secrets"))
            require(not build.get("additional_contexts") and not build.get("ssh"))
            require(build.get("labels", {}).get(LABEL) == run)
    api = config["services"]["api"]
    require(api["command"] == ["python", "deploy.py"])
    values = api["environment"]
    require(values["DATABASE_URL"] == env["GANDALF_DEPLOY_DATABASE_URL"])
    require(values["JWT_SECRET"] == env["JWT_SECRET"])
    require(values["ONLINE_CATALOG"] == "false" and values["BOOK_PROVIDER"] == "local")
    require(values["GROQ_API_KEY"] == "" and values["GANDALF_ONLINE"] == "0")
    require(values["CORS_ORIGINS"] == "[]")
    require(len(env["JWT_SECRET"].encode()) >= 32)
    db_name = "gandalf_gate_" + UUID(run).hex
    require(env["POSTGRES_DB"] == db_name and env["POSTGRES_USER"] == db_name)
    require(re.fullmatch(r"[A-Za-z0-9_-]{32,}", env["POSTGRES_PASSWORD"]) is not None)
    require(
        env["GANDALF_DEPLOY_DATABASE_URL"]
        == f"postgresql+psycopg://{db_name}:{env['POSTGRES_PASSWORD']}@db:5432/{db_name}"
    )


def validate_container(item: dict, run: str, project: str, images: dict) -> str:
    """Same guard for live checks and deletion. Never trust a name alone."""
    require(re.fullmatch(r"[0-9a-f]{64}", item["Id"]) is not None)
    config = item["Config"]
    service = config["Labels"].get("com.docker.compose.service")
    labels_match(config["Labels"], run, project, service)
    require(item["Image"] == images[service])
    require(not item["HostConfig"].get("Privileged"))
    require(not item["HostConfig"].get("Binds"))
    mounts = item.get("Mounts", [])
    require(
        all(
            m["Type"] == "tmpfs" and m["Destination"] == "/var/lib/postgresql"
            for m in mounts
        )
        if service == "db"
        else not mounts
    )
    if service == "db":
        # Docker can report tmpfs in HostConfig rather than Mounts.
        tmpfs = item["HostConfig"].get("Tmpfs") or {}
        typed = item["HostConfig"].get("Mounts") or []
        require(
            set(tmpfs) == {"/var/lib/postgresql"}
            or len(typed) == 1
            and typed[0]["Type"] == "tmpfs"
            and typed[0]["Target"] == "/var/lib/postgresql"
        )
    binding = item["HostConfig"]["PortBindings"]
    require(set(binding) == {str(SERVICES[service]) + "/tcp"})
    require(len(next(iter(binding.values()))) == 1)
    bind = next(iter(binding.values()))[0]
    require(bind["HostIp"] == "127.0.0.1")
    require(
        bind["HostPort"] in ("", "0")
        or 1024 <= int(bind["HostPort"]) <= 65535
        and int(bind["HostPort"]) not in FORBIDDEN_PORTS
    )
    require(set(item["NetworkSettings"].get("Networks", {})) <= {project + "_default"})
    if service == "api":
        require(config["Cmd"] == ["python", "deploy.py"])
    return service


def validate_network(item: dict, run: str, project: str, allowed_ids: set[str]) -> None:
    labels_match(item["Labels"], run, project)
    require(item["Name"] == project + "_default" and item["Internal"] is False)
    require(item["Driver"] == "bridge")
    require(re.fullmatch(r"[0-9a-f]{64}", item["Id"]) is not None)
    require(set(item.get("Containers", {})) <= allowed_ids)


def source_snapshot(ca_path: Path | None = None) -> dict[str, str]:
    files = [
        ROOT / "scripts/deployment_gate.py",
        ROOT / "compose.yaml",
        ROOT / "compose.postgres.yaml",
        ROOT / "compose.deployment-test.yaml",
        ROOT / "compose.build-ca.yaml",
        ROOT / "api/Dockerfile",
        ROOT / "api/deploy.py",
        ROOT / "api/local.py",
        ROOT / "api/pyproject.toml",
        ROOT / "api/alembic.ini",
        ROOT / "frontend/Dockerfile",
        ROOT / "frontend/nginx.conf",
        ROOT / "frontend/package.json",
        ROOT / "frontend/package-lock.json",
        ROOT / "frontend/tests/deployment.mjs",
    ]
    for directory in ("api/app", "api/alembic", "frontend/src", "frontend/public"):
        files.extend(
            p
            for p in (ROOT / directory).rglob("*")
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
        )
    snapshot = {
        p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(files)
    }
    if ca_path is not None:
        snapshot["build_ca_certificate"] = hashlib.sha256(
            ca_path.read_bytes()
        ).hexdigest()
    return snapshot


# Runs inside the verified API container: same DATABASE_URL, real SQLAlchemy/psycopg.
# Output deliberately excludes emails, hashes, tokens, queries, DSNs and raw snapshots.
SQL_BODY = r"""
import hashlib, json, os, sys
from sqlalchemy import create_engine, text
from alembic.config import Config
from alembic.script import ScriptDirectory
payload = json.load(sys.stdin)
engine = create_engine(os.environ["DATABASE_URL"], connect_args={"connect_timeout": 5})
proof_stage = "sql-connection-identity"
with engine.connect() as conn:
    conn.execute(text("SET statement_timeout = '5000ms'"))
    conn.execute(text("SET TRANSACTION READ ONLY"))
    identity = conn.execute(text("SELECT current_database(), current_user, version(), current_setting('transaction_isolation')")).one()
    assert identity[0] == identity[1] == payload["database"]
    assert engine.dialect.name == "postgresql" and "PostgreSQL" in identity[2]
    proof_stage = "sql-migration-head-extensions"
    head = conn.execute(text("SELECT version_num FROM alembic_version")).scalars().all()
    expected = list(ScriptDirectory.from_config(Config("alembic.ini")).get_heads())
    assert head == expected
    extensions = dict(conn.execute(text("SELECT extname, extversion FROM pg_extension WHERE extname IN ('vector','citext')")).all())
    assert set(extensions) == {"vector", "citext"}
    proof_stage = "sql-counts-ai-usage"
    counts = {table: conn.execute(text("SELECT count(*) FROM " + table)).scalar_one()
              for table in ("users", "favorites", "playlists", "playlist_tracks", "recommendation_results")}
    usage = conn.execute(text("SELECT coalesce(sum(calls),0) FROM ai_usage")).scalar_one()
    assert usage == 0
    result = {"engine":engine.dialect.name,"database":identity[0],"user":identity[1],
              "version":identity[2].split(' on ')[0],"isolation":identity[3],
              "head":head,"extensions":extensions,"counts":counts,"ai_calls":usage}
    if "artifact" not in payload:
        assert counts["users"] == counts["favorites"] == counts["playlists"] == counts["playlist_tracks"] == 0
    else:
        proof_stage = "sql-fixtures-ownership-snapshots"
        artifact = payload["artifact"]
        users = conn.execute(text("SELECT id::text, is_active, password_hash LIKE '$argon2id$%' FROM users ORDER BY id")).all()
        favorites = conn.execute(text("SELECT id::text,user_id::text,type,item_id::text,md5(item::text),source_recommendation_id::text FROM favorites ORDER BY id")).all()
        playlists = conn.execute(text("SELECT id::text,user_id::text,source,total_duration_ms,duration_estimated,source_recommendation_id::text FROM playlists ORDER BY id")).all()
        tracks = conn.execute(text("SELECT playlist_id::text,position,music_id,md5(item::text) FROM playlist_tracks ORDER BY playlist_id,position")).all()
        assert {r[0] for r in users} == set(artifact["user_ids"]) and all(r[1] and r[2] for r in users)
        assert {r[0] for r in favorites} == set(artifact["favorite_ids"]) and all(r[1] == artifact["user_ids"][0] for r in favorites)
        assert {(r[0],r[2],r[3]) for r in favorites} == {(f["id"],f["type"],f["item_id"]) for f in artifact["favorites"]}
        assert {r[0] for r in playlists} == set(artifact["playlist_ids"]) and all(r[1] == artifact["user_ids"][0] for r in playlists)
        assert [r[2] for r in tracks] == artifact["playlist_music_ids"] and [r[1] for r in tracks] == list(range(1,len(tracks)+1))
        proof_stage = "sql-public-cache-snapshot"
        public = conn.execute(text("SELECT response FROM recommendation_results WHERE id = :id"), {"id": artifact["public_snapshot_id"]}).scalar_one()
        assert [str(row["item"]["id"]) for row in public["items"]] == artifact["public_snapshot_music_ids"]
        snapshot = json.dumps([list(r) for group in (users,favorites,playlists,tracks) for r in group], sort_keys=True,default=str)
        result["snapshot_sha256"] = hashlib.sha256(snapshot.encode()).hexdigest()
        result["public_snapshot_sha256"] = hashlib.sha256(json.dumps(public,sort_keys=True).encode()).hexdigest()
        result["ownership_verified"] = True
    print(json.dumps(result))
engine.dispose()
"""
SQL_PROOF = (
    "import json, sys\nscope = {}\ntry:\n    exec(" + repr(SQL_BODY) + ", scope)\n"
    "except Exception as error:\n"
    "    print(json.dumps({'status':'FAIL','stage':scope.get('proof_stage','sql-start'),"
    "'error_kind':type(error).__name__}), file=sys.stderr)\n    sys.exit(1)\n"
)


class Runner:
    def __init__(self):
        self.run = str(uuid4())
        self.project = "gandalf_deploy_" + UUID(self.run).hex
        self.directory = ROOT / ".impeccable" / "runtime" / self.project
        self.env = clean_environment(dict(os.environ))
        self.ca_input = os.environ.get("GANDALF_BUILD_CA_CERT")
        self.ca_path: Path | None = None
        name = "gandalf_gate_" + UUID(self.run).hex
        password = secrets.token_urlsafe(36)
        self.env.update(
            {
                "GANDALF_GATE_UUID": self.run,
                "GANDALF_GATE_PROJECT": self.project,
                "GANDALF_GATE_API_IMAGE": self.project + "-api:gate",
                "GANDALF_GATE_FRONTEND_IMAGE": self.project + "-frontend:gate",
                "POSTGRES_DB": name,
                "POSTGRES_USER": name,
                "POSTGRES_PASSWORD": password,
                "JWT_SECRET": secrets.token_urlsafe(48),
                "GANDALF_DEPLOY_DATABASE_URL": f"postgresql+psycopg://{name}:{password}@db:5432/{name}",
                "ONLINE_CATALOG": "false",
                "BOOK_PROVIDER": "local",
                "CORS_ORIGINS": "[]",
            }
        )
        self.compose = [
            "docker",
            "compose",
            "--env-file",
            str(self.directory / "empty.env"),
            "--project-name",
            self.project,
        ]
        for file in (
            "compose.yaml",
            "compose.postgres.yaml",
            "compose.deployment-test.yaml",
        ):
            self.compose.extend(["-f", str(ROOT / file)])
        self.stage = "opt-in"
        self.images: dict[str, str] = {}
        self.containers: dict[str, str] = {}
        self.ports: dict[str, int] = {}
        self.network_id: str | None = None
        self.mutated = False
        self.result = {"status": "FAIL", "uuid": self.run, "project": self.project}
        self.result["postgres_image"] = PG_IMAGE

    def progress(self, stage: str):
        self.stage = stage
        print(json.dumps({"stage": stage}), file=sys.stderr, flush=True)

    def command(
        self, args: list[str], *, data: str | None = None, timeout: int = 120
    ) -> str:
        process = subprocess.run(
            args,
            cwd=ROOT,
            env=self.env,
            input=data,
            capture_output=True,
            check=False,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        if process.returncode != 0:
            raise CommandFailure(
                process.returncode, process.stdout + "\n" + process.stderr
            )
        return process.stdout

    def inspect(self, resource: str, identifier: str) -> dict:
        return json.loads(self.command(["docker", resource, "inspect", identifier]))[0]

    def discover(self):
        ids = self.command(
            [
                "docker",
                "ps",
                "-aq",
                "--filter",
                "label=" + LABEL + "=" + self.run,
                "--filter",
                "label=com.docker.compose.project=" + self.project,
            ]
        ).split()
        found = {}
        for identifier in ids:
            item = self.inspect("container", identifier)
            service = validate_container(item, self.run, self.project, self.images)
            require(service not in found)
            found[service] = item["Id"]
        self.containers = found
        networks = self.command(
            [
                "docker",
                "network",
                "ls",
                "-q",
                "--filter",
                "label=" + LABEL + "=" + self.run,
            ]
        ).split()
        require(len(networks) <= 1)
        if networks:
            item = self.inspect("network", networks[0])
            validate_network(item, self.run, self.project, set(found.values()))
            self.network_id = item["Id"]

    def live_identity(self, *, restarted_api: str | None = None):
        previous = dict(self.containers)
        if restarted_api is not None:
            require(
                self.stage == "restart-own-api" and previous.get("api") == restarted_api
            )
        self.discover()
        require(set(self.containers) == set(SERVICES) and self.network_id is not None)
        if previous:
            require(self.containers == previous)
        for service, identifier in self.containers.items():
            item = self.inspect("container", identifier)
            require(item["State"]["Running"] is True)
            require(
                set(item["NetworkSettings"]["Networks"]) == {self.project + "_default"}
            )
            if service != "frontend":
                require(item["State"]["Health"]["Status"] == "healthy")
            bindings = item["NetworkSettings"]["Ports"][str(SERVICES[service]) + "/tcp"]
            require(len(bindings) == 1 and bindings[0]["HostIp"] == "127.0.0.1")
            port = validate_origin("http://127.0.0.1:" + bindings[0]["HostPort"])
            if service in self.ports and not (
                service == "api" and restarted_api is not None
            ):
                require(self.ports[service] == port)
            self.ports[service] = port
        require(len(set(self.ports.values())) == 3)

    def http_json(self, service: str, path: str) -> dict:
        origin = "http://127.0.0.1:" + str(self.ports[service])
        validate_origin(origin)
        require(path.startswith("/") and not path.startswith("//"))
        opener = build_opener(ProxyHandler({}), RejectRedirects())
        with opener.open(Request(origin + path), timeout=10) as response:
            require(response.status == 200 and response.geturl() == origin + path)
            return json.load(response)

    def offline_status(self):
        for service in ("api", "frontend"):
            status = self.http_json(service, "/api/v1/system/status")
            require(status["catalog"] == "local" and status["ai"]["provider"] is None)
            require(status["ai"]["configured"] is False)
        self.http_json("api", "/health/ready")

    def sql(self, artifact: dict | None = None) -> dict:
        identifier = self.containers["api"]
        validate_container(
            self.inspect("container", identifier), self.run, self.project, self.images
        )
        payload = {"database": self.env["POSTGRES_DB"]}
        if artifact is not None:
            payload["artifact"] = artifact
        return json.loads(
            self.command(
                ["docker", "exec", "-i", identifier, "python", "-c", SQL_PROOF],
                data=json.dumps(payload),
            )
        )

    def browser(self, phase: str) -> dict:
        self.offline_status()
        self.env.update(
            {
                "GANDALF_DEPLOYMENT_ALLOW": "isolated-coordinated",
                "GANDALF_DEPLOYMENT_TOKEN": self.run,
                "GANDALF_DEPLOYMENT_BASE_URL": "http://127.0.0.1:"
                + str(self.ports["frontend"]),
                "GANDALF_DEPLOYMENT_PHASE": phase,
                "GANDALF_DEPLOYMENT_ARTIFACT": str(
                    self.directory / "browser-create.json"
                ),
            }
        )
        result = json.loads(
            self.command(
                ["node", str(ROOT / "frontend/tests/deployment.mjs")], timeout=300
            )
        )
        return browser_artifact(
            result, phase, self.run, self.env["GANDALF_DEPLOYMENT_BASE_URL"]
        )

    def cleanup(self) -> dict:
        report = {
            "verified": False,
            "containers_removed": [],
            "network_removed": False,
            "image_tags_removed": [],
            "remaining_containers": [],
        }
        if not self.mutated:
            report["verified"] = True
            return report
        # A failed multi-image build may already have produced one tagged image.
        tagged = self.command(
            [
                "docker",
                "image",
                "ls",
                "--filter",
                "label=" + LABEL + "=" + self.run,
                "--format",
                "{{.Repository}}:{{.Tag}} ",
            ]
        ).split()
        for tag in tagged:
            if tag in (self.project + "-api:gate", self.project + "-frontend:gate"):
                image = self.inspect("image", tag)
                require(image["Config"]["Labels"].get(LABEL) == self.run)
                require(tag in image["RepoTags"])
                service = "api" if tag.endswith("-api:gate") else "frontend"
                self.images.setdefault(service, image["Id"])
        self.discover()
        ids = dict(self.containers)
        # Reinspect immediately before EACH deletion; a label/name alone is insufficient.
        for service, identifier in ids.items():
            item = self.inspect("container", identifier)
            require(
                validate_container(item, self.run, self.project, self.images) == service
            )
            self.command(["docker", "rm", "-f", identifier])
            report["containers_removed"].append(identifier)
        if self.network_id:
            item = self.inspect("network", self.network_id)
            validate_network(item, self.run, self.project, set())
            self.command(["docker", "network", "rm", self.network_id])
            report["network_removed"] = True
        for service in ("api", "frontend"):
            if service in self.images:
                tag = self.project + "-" + service + ":gate"
                image = self.inspect("image", tag)
                require(image["Id"] == self.images[service])
                require(image["Config"]["Labels"].get(LABEL) == self.run)
                require(tag in image["RepoTags"])
                self.command(["docker", "image", "rm", tag])
                report["image_tags_removed"].append(tag)
        remaining = self.command(
            [
                "docker",
                "ps",
                "-aq",
                "--filter",
                "label=com.docker.compose.project=" + self.project,
            ]
        ).split()
        require(not remaining)
        report["verified"] = True
        return report

    def execute(self) -> dict:
        try:
            require(
                os.environ.get("GANDALF_DEPLOYMENT_ALLOW") == "isolated-coordinated"
            )
            self.progress("preflight")
            if self.ca_input is not None:
                self.ca_path, digest = validate_build_ca(self.ca_input)
                self.env["GANDALF_BUILD_CA_CERT"] = str(self.ca_path)
                self.compose.extend(["-f", str(ROOT / "compose.build-ca.yaml")])
                self.result["build_ca_sha256"] = digest
            require(not self.directory.exists())
            self.directory.mkdir(parents=True)
            (self.directory / "empty.env").write_text("", encoding="utf-8")
            snapshot = source_snapshot(self.ca_path)
            self.result["source_start_sha256"] = hashlib.sha256(
                json.dumps(snapshot, sort_keys=True).encode()
            ).hexdigest()
            context = json.loads(self.command(["docker", "context", "inspect"]))[0]
            endpoint = context["Endpoints"]["docker"]["Host"]
            require(endpoint.startswith(("npipe://", "unix://")))
            info = json.loads(
                self.command(["docker", "info", "--format", "{{json .}} "])
            )
            require(info["OSType"] == "linux")
            self.result["docker_version"] = info["ServerVersion"]
            self.result["compose_version"] = self.command(
                ["docker", "compose", "version", "--short"]
            ).strip()
            self.images["db"] = self.inspect("image", PG_IMAGE)["Id"]
            config = json.loads(
                self.command(self.compose + ["config", "--format", "json"])
            )
            validate_config(config, self.env)
            self.progress("build-current-dockerfiles")
            self.mutated = True
            self.command(self.compose + ["build", "api", "frontend"], timeout=900)
            for service in ("api", "frontend"):
                self.images[service] = self.inspect(
                    "image", self.project + "-" + service + ":gate"
                )["Id"]
            self.result["images"] = dict(self.images)
            self.progress("up-isolated-offline")
            self.command(
                self.compose
                + [
                    "up",
                    "-d",
                    "--no-build",
                    "--pull",
                    "never",
                    "--wait",
                    "--wait-timeout",
                    "180",
                ],
                timeout=240,
            )
            self.live_identity()
            self.result["containers"] = dict(self.containers)
            self.result["ports"] = dict(self.ports)
            self.progress("postgres-identity-migrations-offline")
            self.offline_status()
            self.result["postgres_baseline"] = self.sql()
            self.env["GANDALF_DEPLOYMENT_PASSWORD"] = secrets.token_urlsafe(24)
            self.progress("browser-create")
            artifact = self.browser("create")
            self.result["browser_create"] = artifact
            self.progress("postgres-saved-snapshots")
            before = self.sql(artifact)
            self.result["postgres_before_restart"] = before
            self.progress("restart-own-api")
            api_id = self.containers["api"]
            validate_container(
                self.inspect("container", api_id), self.run, self.project, self.images
            )
            started = self.inspect("container", api_id)["State"]["StartedAt"]
            self.command(self.compose + ["restart", "api"])
            deadline = time.monotonic() + 90
            while time.monotonic() < deadline:
                item = self.inspect("container", api_id)
                if item["State"].get("Health", {}).get("Status") == "healthy":
                    break
                time.sleep(1)
            self.live_identity(restarted_api=api_id)
            self.result["ports_after_restart"] = dict(self.ports)
            require(self.containers["api"] == api_id)
            require(self.inspect("container", api_id)["State"]["StartedAt"] != started)
            self.offline_status()
            after = self.sql(artifact)
            require(before == after)
            self.result["postgres_after_restart"] = after
            self.result["restart_verified"] = True
            self.progress("browser-verify-after-restart")
            self.result["browser_verify"] = self.browser("verify")
            final = self.sql(artifact)
            require(final == before)
            self.result["postgres_after_browser_verify"] = final
            require(source_snapshot(self.ca_path) == snapshot)
            self.result["source_unchanged"] = True
            self.result["status"] = "PASS"
        except Exception as error:  # noqa: BLE001 -- failure envelope must never expose child output
            self.result.update(
                status="FAIL", stage=self.stage, error_kind=type(error).__name__
            )
            trace = error.__traceback__
            locations = []
            while trace is not None:
                locations.append(
                    {
                        "file": Path(trace.tb_frame.f_code.co_filename).name,
                        "line": trace.tb_lineno,
                    }
                )
                trace = trace.tb_next
            self.result["failure_location"] = locations[-2:]  # source locations only
            if isinstance(error, CommandFailure):
                self.result["child_failure"] = {
                    "returncode": error.returncode,
                    "stage": error.child_stage,
                    "error_kind": error.child_kind,
                    "safe_categories": error.reasons,
                    **error.child_diagnostic,
                }
            elif isinstance(error, subprocess.TimeoutExpired):
                captured = error.stderr or ""
                if isinstance(captured, bytes):
                    captured = captured.decode("utf-8", errors="replace")
                child = CommandFailure(-1, captured)
                self.result["child_failure"] = {
                    "stage": child.child_stage,
                    "error_kind": child.child_kind,
                    "timeout_seconds": error.timeout,
                    **child.child_diagnostic,
                }
        finally:
            try:
                self.progress("cleanup-own-verified-resources")
                self.result["cleanup"] = self.cleanup()
            except Exception as error:  # noqa: BLE001 -- cleanup failure is also sanitized
                self.result.update(
                    status="FAIL",
                    cleanup={
                        "verified": False,
                        "error_kind": type(error).__name__,
                        "stage": "cleanup-identity-or-removal",
                    },
                )
        return self.result


def main() -> int:
    runner = Runner()
    result = runner.execute()
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
