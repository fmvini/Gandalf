"""Opt-in serial migrations for an explicitly owned Neon direct endpoint.

No dotenv, application factory, credential arguments or automatic retries.
"""

import contextlib
import hashlib
import importlib
import io
import json
import logging
import os
import re
import sys
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qsl, urlsplit
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
API_ROOT = ROOT / "api"
ALLOW = "owned-project"
LOCK_KEY = int.from_bytes(
    hashlib.sha256(b"gandalf:neon:migrate:v1").digest()[:8], "big", signed=True
)
STAGE = "coordination"
SYSTEM_KEYS = {
    "PATH",
    "PATHEXT",
    "SYSTEMROOT",
    "WINDIR",
    "COMSPEC",
    "HOME",
    "USERPROFILE",
    "APPDATA",
    "LOCALAPPDATA",
    "TEMP",
    "TMP",
}
HOST = re.compile(
    r"ep-[a-z0-9]+(?:-[a-z0-9]+)*\."
    r"(?:[a-z0-9]+(?:-[a-z0-9]+)*\.){1,2}(?:aws|azure)\.neon\.tech"
)


class MigrationError(ValueError):
    """Contains no input, SQL or connection credentials."""


def require(condition):
    if not condition:
        raise MigrationError("Migration check failed.")


def validate_target(value):
    """Pure stdlib refusal before imports, DNS or opening a connection."""
    try:
        require(isinstance(value, str) and 0 < len(value) <= 8192)
        require(value == value.strip() and not any(ord(c) < 33 for c in value))
        parsed = urlsplit(value)
        require(parsed.scheme in {"postgres", "postgresql", "postgresql+psycopg"})
        require(parsed.hostname is not None and HOST.fullmatch(parsed.hostname))
        require("pooler" not in parsed.hostname.split(".")[0].split("-"))
        require(parsed.port in (None, 5432) and "#" not in value)
        require(parsed.username and parsed.password)
        require(re.fullmatch(r"/[A-Za-z0-9_-]{1,63}", parsed.path))
        pairs = parse_qsl(parsed.query, keep_blank_values=True, strict_parsing=True)
        query = dict(pairs)
        require(len(query) == len(pairs))
        require(not set(query) - {"sslmode", "channel_binding"})
        require(query.get("sslmode") in {"require", "verify-ca", "verify-full"})
        if "channel_binding" in query:
            require(query["channel_binding"] in {"prefer", "require"})
        # Preserve user/password escaping and query; select the existing psycopg driver.
        return "postgresql+psycopg" + value[value.index(":") :]
    except (ValueError, TypeError):
        raise MigrationError("Invalid Neon migration target.") from None


@contextlib.contextmanager
def sanitized_runtime():
    """No PG*/DATABASE_URL/SSL overrides or dotenv can influence this invocation."""
    directory = ROOT / ".impeccable/runtime" / ("neon-migrate-" + uuid4().hex)
    directory.mkdir(parents=True)
    previous_cwd, inherited, previous_path = Path.cwd(), dict(os.environ), sys.path[:]
    previous_logging = logging.root.manager.disable
    try:
        os.chdir(directory)
        os.environ.clear()
        os.environ.update(
            {k: v for k, v in inherited.items() if k.upper() in SYSTEM_KEYS}
        )
        sys.path.insert(0, str(API_ROOT))
        logging.disable(logging.CRITICAL)
        with (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            yield
    finally:
        logging.disable(previous_logging)
        os.chdir(previous_cwd)
        os.environ.clear()
        os.environ.update(inherited)
        sys.path[:] = previous_path
        directory.rmdir()  # Only our new empty directory, never recursive.


def load_runtime():
    return SimpleNamespace(
        sa=importlib.import_module("sqlalchemy"),
        Config=importlib.import_module("alembic.config").Config,
        command=importlib.import_module("alembic.command"),
        ScriptDirectory=importlib.import_module("alembic.script").ScriptDirectory,
    )


def migrate(value, runtime):
    global STAGE
    sa = runtime.sa
    STAGE = "target_validation"
    value = validate_target(value)
    url = sa.engine.make_url(value)
    config = runtime.Config(str(API_ROOT / "alembic.ini"))
    expected = runtime.ScriptDirectory.from_config(config).get_heads()
    require(len(expected) == 1 and re.fullmatch(r"[a-z0-9_]{1,80}", expected[0]))
    STAGE = "connect"
    engine = sa.create_engine(
        url,
        poolclass=sa.pool.NullPool,
        echo=False,
        hide_parameters=True,
        isolation_level="READ COMMITTED",
        connect_args={
            "connect_timeout": 10,
            "options": "-c statement_timeout=60000 -c lock_timeout=10000",
            "prepare_threshold": None,
        },
    )
    try:
        with engine.connect() as connection:
            with connection.begin():
                STAGE = "identity"
                database, user = connection.execute(
                    sa.text("SELECT current_database(), current_user")
                ).one()
                require(database == url.database and user == url.username)
                # Check our client TLS rather than a proxy's backend connection.
                require(
                    connection.connection.driver_connection.pgconn.ssl_in_use is True
                )
                available = set(
                    connection.execute(
                        sa.text(
                            "SELECT name FROM pg_available_extensions WHERE name IN ('citext','vector')"
                        )
                    ).scalars()
                )
                require(available == {"citext", "vector"})
                STAGE = "serialization"
                require(
                    connection.execute(
                        sa.text("SELECT pg_try_advisory_xact_lock(:key)"),
                        {"key": LOCK_KEY},
                    ).scalar_one()
                    is True
                )
                STAGE = "migrations"
                config.attributes["connection"] = connection
                runtime.command.upgrade(config, "head")
                STAGE = "schema_check"
                require(
                    list(
                        connection.execute(
                            sa.text("SELECT version_num FROM alembic_version")
                        ).scalars()
                    )
                    == expected
                )
            STAGE = "readonly_verification"
            with connection.begin():
                connection.execute(sa.text("SET TRANSACTION READ ONLY"))
                database, user = connection.execute(
                    sa.text("SELECT current_database(), current_user")
                ).one()
                require(database == url.database and user == url.username)
                head = list(
                    connection.execute(
                        sa.text("SELECT version_num FROM alembic_version")
                    ).scalars()
                )
                extensions = dict(
                    connection.execute(
                        sa.text(
                            "SELECT extname,extversion FROM pg_extension WHERE extname IN ('citext','vector')"
                        )
                    ).all()
                )
                require(head == expected and set(extensions) == {"citext", "vector"})
                require(
                    all(
                        re.fullmatch(r"[0-9]+(?:\.[0-9]+){1,3}", version)
                        for version in extensions.values()
                    )
                )
        return {
            "status": "PASS",
            "head": head,
            "extensions": extensions,
            "direct_connection": True,
            "tls": url.query["sslmode"],
            "tls_active": True,
            "identity_verified": True,
            "serial_lock": True,
            "readonly_verified": True,
        }
    finally:
        engine.dispose()


def main():
    global STAGE
    STAGE = "coordination"
    try:
        require(not sys.argv[1:])
        require(os.environ.get("GANDALF_NEON_MIGRATE") == ALLOW)
        STAGE = "target_validation"
        value = validate_target(os.environ.get("NEON_DATABASE_URL_UNPOOLED"))
        with sanitized_runtime():
            STAGE = "imports"
            result = migrate(value, load_runtime())
    except Exception:  # noqa: BLE001 -- CLI errors may contain secrets; never dump them.
        result = {
            "status": "NOT_PASSED",
            "stage": STAGE,
            "error_class": "MigrationError",
        }
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
