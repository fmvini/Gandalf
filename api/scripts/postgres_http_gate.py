"""Opt-in two-app ASGI gate; PostgreSQL lifecycle belongs to Banco/Maestro."""

import hashlib
import importlib
import json
import os
import re
import secrets
import sys
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid4

ROOT = Path(__file__).resolve().parents[2]
API_ROOT = ROOT / "api"
sys.path.insert(0, str(API_ROOT))
ALLOW = "isolated-coordinated-backend-frozen"
STAGE = "coordination"
STAGES = {
    "coordination",
    "imports",
    "target_validation",
    "empty_database",
    "migrations",
    "schema_identity",
    "http_contract",
    "source_freeze",
    "complete",
}
CHECKS = (
    "independent_apps_offline",
    "cross_app_register_login_headers",
    "cross_app_refresh_replay_family_isolation",
    "logout_current_old_foreign_contract",
    "shared_origin_favorite_snapshot_ownership",
    "shared_origin_playlist_snapshot_ownership",
    "sql_ownership_cache_ai_zero",
    "app_a_shutdown_preserves_b",
    "both_app_engines_disposed",
)
COUNT_FIELDS = (
    "users",
    "favorites",
    "playlists",
    "playlist_tracks",
    "recommendation_results",
    "refresh_tokens",
    "active_refresh_tokens",
    "ai_calls",
)


def require(condition):
    if not condition:
        raise ValueError("Gate check failed")


def stage(value):
    global STAGE
    require(value in STAGES)
    STAGE = value


def load_runtime():
    """Default app import cannot consult a real .env or inherited app settings."""
    directory = ROOT / ".impeccable/runtime" / ("http-import-" + uuid4().hex)
    directory.mkdir(parents=True)
    previous = Path.cwd()
    inherited = dict(os.environ)
    system_keys = {
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
    try:
        os.chdir(directory)
        os.environ.clear()
        os.environ.update(
            {k: v for k, v in inherited.items() if k.upper() in system_keys}
        )
        base = importlib.import_module("scripts.postgres_gate")
        sa = importlib.import_module("sqlalchemy")
        models = importlib.import_module("app.models")
        return SimpleNamespace(
            base=base,
            sa=sa,
            models=models,
            Session=importlib.import_module("sqlalchemy.orm").Session,
            Config=importlib.import_module("alembic.config").Config,
            command=importlib.import_module("alembic.command"),
            ScriptDirectory=importlib.import_module("alembic.script").ScriptDirectory,
            Settings=importlib.import_module("app.core.config").Settings,
            create_app=importlib.import_module("app.main").create_app,
            TestClient=importlib.import_module("fastapi.testclient").TestClient,
            refresh_hash=importlib.import_module("app.core.security").refresh_hash,
            BOOKS=importlib.import_module("app.providers.local_catalog").BOOKS,
        )
    finally:
        os.chdir(previous)
        os.environ.clear()
        os.environ.update(inherited)
        directory.rmdir()  # Only this newly-created empty directory; never recursive.


def source_snapshot():
    files = {
        Path(__file__),
        API_ROOT / "scripts/postgres_gate.py",
        API_ROOT / "tests/test_postgres_http_gate.py",
        API_ROOT / "alembic.ini",
        API_ROOT / "pyproject.toml",
    }
    for directory in ("app", "alembic"):
        files.update((API_ROOT / directory).rglob("*.py"))
    return {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(files)
    }


def http_contract(settings, observer, runtime):
    """Real factory/routes/DB sessions; no overrides, provider calls or service mocks."""
    r, sa, models = runtime, runtime.sa, runtime.models
    a, b = r.create_app(settings=settings), r.create_app(settings=settings.model_copy())
    checks, counts = [], {}
    requests = {"a": 0, "b": 0}
    disposed = {"a": 0, "b": 0}

    def request(client, method, path, status=200, **kwargs):
        requests["a" if client.app is a else "b"] += 1
        response = client.request(method, path, **kwargs)
        require(response.status_code == status)
        request_id = response.headers.get("X-Request-ID", "")
        require(str(UUID(request_id)) == request_id)
        if path.startswith("/api/v1/auth/"):
            require(response.headers.get("Cache-Control") == "no-store")
            require(response.headers.get("Pragma") == "no-cache")
        if status == 204:
            require(response.content == b"")
            return None
        body = response.json()
        if status >= 400:
            require(body["error"]["request_id"] == request_id)
            require(
                body["error"]["code"]
                == {
                    401: "UNAUTHORIZED",
                    404: "NOT_FOUND",
                    409: "CONFLICT",
                    422: "VALIDATION_ERROR",
                }[status]
            )
            return None
        return body

    def headers(tokens):
        return {"Authorization": "Bearer " + tokens["access_token"]}

    def login(client, email, password):
        tokens = request(
            client,
            "POST",
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": password,
            },
        )
        require(tokens["token_type"] == "bearer" and tokens["expires_in"] == 900)
        require(
            all(
                isinstance(tokens[k], str) and tokens[k]
                for k in (
                    "access_token",
                    "refresh_token",
                )
            )
        )
        return tokens

    def rotate(client, tokens, status=200):
        result = request(
            client,
            "POST",
            "/api/v1/auth/refresh",
            status,
            json={
                "refresh_token": tokens["refresh_token"],
            },
        )
        if status == 200:
            require(result["refresh_token"] != tokens["refresh_token"])
        return result

    def family(raw):
        with r.Session(observer) as session:
            record = session.scalar(
                sa.select(models.RefreshToken).where(
                    models.RefreshToken.token_hash == r.refresh_hash(raw),
                )
            )
            require(record is not None)
            return record.family_id

    def active(family_id):
        with r.Session(observer) as session:
            return session.scalar(
                sa.select(sa.func.count())
                .select_from(
                    models.RefreshToken,
                )
                .where(
                    models.RefreshToken.family_id == family_id,
                    models.RefreshToken.revoked_at.is_(None),
                )
            )

    def disposed_listener(name):
        def notice(_engine):
            disposed[name] += 1

        return notice

    with r.TestClient(b, raise_server_exceptions=False) as cb:
        r.sa.event.listen(b.state.engine, "engine_disposed", disposed_listener("b"))
        with r.TestClient(a, raise_server_exceptions=False) as ca:
            r.sa.event.listen(a.state.engine, "engine_disposed", disposed_listener("a"))
            require(a.state.engine is not b.state.engine)
            require(a.state.session_factory is not b.state.session_factory)
            require(a.state.auth_limiter is not b.state.auth_limiter)
            require(not a.dependency_overrides and not b.dependency_overrides)
            for client in (ca, cb):
                with client.app.state.engine.connect() as connection:
                    if connection.dialect.name == "postgresql":
                        require(
                            connection.scalar(sa.text("SHOW transaction_isolation"))
                            == "read committed"
                        )
                status = request(client, "GET", "/api/v1/system/status")
                require(
                    status["catalog"] == "local" and status["ai"]["configured"] is False
                )
                require(status["ai"]["provider"] is None)
                request(client, "GET", "/health/ready")
            checks.append(CHECKS[0])

            suffix, password = uuid4().hex, secrets.token_urlsafe(24)
            owner_body = {
                "email": suffix + "@example.com",
                "username": "a" + suffix[:19],
                "password": password,
            }
            other_body = {
                **owner_body,
                "email": "b" + owner_body["email"],
                "username": "b" + suffix[:19],
            }
            request(
                ca,
                "POST",
                "/api/v1/auth/register",
                422,
                json={
                    **owner_body,
                    "email": suffix + "@example.test",
                },
            )
            owner = request(ca, "POST", "/api/v1/auth/register", 201, json=owner_body)
            other = request(cb, "POST", "/api/v1/auth/register", 201, json=other_body)
            request(cb, "POST", "/api/v1/auth/register", 409, json=owner_body)
            first = login(ca, owner_body["email"], password)
            independent = login(cb, owner_body["email"], password)
            foreign = login(cb, other_body["email"], password)
            require(
                request(cb, "GET", "/api/v1/auth/me", headers=headers(first))["id"]
                == owner["id"]
            )
            require(
                request(ca, "GET", "/api/v1/auth/me", headers=headers(foreign))["id"]
                == other["id"]
            )
            checks.append(CHECKS[1])

            first_family = family(first["refresh_token"])
            independent_family = family(independent["refresh_token"])
            foreign_family = family(foreign["refresh_token"])
            require(len({first_family, independent_family, foreign_family}) == 3)
            child = rotate(cb, first)
            require(
                request(ca, "GET", "/api/v1/auth/me", headers=headers(child))["id"]
                == owner["id"]
            )
            leaf = rotate(ca, child)
            require(
                request(cb, "GET", "/api/v1/auth/me", headers=headers(leaf))["id"]
                == owner["id"]
            )
            rotate(cb, first, 401)
            require(active(first_family) == 0)
            rotate(ca, leaf, 401)
            require(active(independent_family) == active(foreign_family) == 1)
            current = rotate(ca, independent)
            checks.append(CHECKS[2])

            request(
                cb,
                "POST",
                "/api/v1/auth/logout",
                204,
                headers=headers(first),
                json={"refresh_token": foreign["refresh_token"]},
            )
            require(active(foreign_family) == 1)
            rotate(ca, foreign)
            request(
                ca,
                "POST",
                "/api/v1/auth/logout",
                204,
                headers=headers(first),
                json={"refresh_token": independent["refresh_token"]},
            )
            require(active(independent_family) == 1)
            final = rotate(cb, current)
            request(
                ca,
                "POST",
                "/api/v1/auth/logout",
                204,
                headers=headers(first),
                json={"refresh_token": final["refresh_token"]},
            )
            rotate(cb, final, 401)
            require(active(independent_family) == 0)
            require(
                request(cb, "GET", "/api/v1/auth/me", headers=headers(first))["id"]
                == owner["id"]
            )
            checks.append(CHECKS[3])

            source = request(
                ca,
                "POST",
                "/api/v1/recommendations/read-with-music",
                json={
                    "book_id": str(r.BOOKS[1].id),
                    "mode": "CALM",
                    "target_duration_min": 15,
                },
            )
            require(bool(source["items"]))
            origin, item = source["recommendation_id"], source["items"][0]["item"]
            with r.Session(observer) as session:
                cached = session.get(models.RecommendationResult, UUID(origin))
                require(
                    cached is not None and cached.response["items"] == source["items"]
                )
                cached_times = (cached.created_at, cached.expires_at)
            path = f"/api/v1/recommendations/{origin}/items/{item['id']}/explanation"
            require(request(ca, "GET", path) == request(cb, "GET", path))
            favorite_body = {"recommendation_id": origin, "item_id": item["id"]}
            saved = request(
                cb,
                "POST",
                "/api/v1/users/me/favorites",
                201,
                headers=headers(first),
                json=favorite_body,
            )
            repeated = request(
                ca,
                "POST",
                "/api/v1/users/me/favorites",
                headers=headers(first),
                json=favorite_body,
            )
            require(saved == repeated and saved["item"] == item)
            require(
                request(
                    ca, "GET", "/api/v1/users/me/favorites", headers=headers(first)
                )["total"]
                == 1
            )
            require(
                request(
                    cb, "GET", "/api/v1/users/me/favorites", headers=headers(foreign)
                )["total"]
                == 0
            )
            require(
                request(
                    cb,
                    "POST",
                    "/api/v1/users/me/favorites/status",
                    headers=headers(foreign),
                    json={"type": "MUSIC", "item_ids": [item["id"]]},
                )["favorites"]
                == {}
            )
            request(
                ca,
                "DELETE",
                "/api/v1/users/me/favorites/" + saved["id"],
                204,
                headers=headers(foreign),
            )
            require(
                request(
                    cb, "GET", "/api/v1/users/me/favorites", headers=headers(first)
                )["total"]
                == 1
            )
            checks.append(CHECKS[4])

            playlist = request(
                cb,
                "POST",
                "/api/v1/playlists",
                201,
                headers=headers(first),
                json={"name": "Gate ASGI", "source_recommendation_id": origin},
            )
            playlist_path = "/api/v1/playlists/" + playlist["id"]
            require(
                request(ca, "GET", playlist_path, headers=headers(first)) == playlist
            )
            require(
                [row["item"] for row in playlist["tracks"]]
                == [row["item"] for row in source["items"]]
            )
            request(ca, "GET", playlist_path, 404, headers=headers(foreign))
            request(cb, "DELETE", playlist_path, 404, headers=headers(foreign))
            require(
                request(cb, "GET", "/api/v1/playlists", headers=headers(foreign))[
                    "total"
                ]
                == 0
            )
            require(
                request(ca, "GET", "/api/v1/playlists", headers=headers(first))["total"]
                == 1
            )
            checks.append(CHECKS[5])

            with r.Session(observer) as session:
                favorite = session.get(models.Favorite, UUID(saved["id"]))
                persisted = session.get(models.Playlist, UUID(playlist["id"]))
                require(favorite.user_id == persisted.user_id == UUID(owner["id"]))
                require(
                    favorite.item == item
                    and favorite.source_recommendation_id == UUID(origin)
                )
                require(persisted.source_recommendation_id == UUID(origin))
                tracks = list(
                    session.scalars(
                        sa.select(models.PlaylistTrack)
                        .where(
                            models.PlaylistTrack.playlist_id == persisted.id,
                        )
                        .order_by(models.PlaylistTrack.position)
                    )
                )
                require(
                    [row.position for row in tracks] == list(range(1, len(tracks) + 1))
                )
                require(
                    [row.item for row in tracks]
                    == [row["item"] for row in source["items"]]
                )
                cached = session.get(models.RecommendationResult, UUID(origin))
                require((cached.created_at, cached.expires_at) == cached_times)
                require(cached.response["items"] == source["items"])
                for field, model in zip(
                    COUNT_FIELDS[:6],
                    (
                        models.User,
                        models.Favorite,
                        models.Playlist,
                        models.PlaylistTrack,
                        models.RecommendationResult,
                        models.RefreshToken,
                    ),
                    strict=True,
                ):
                    counts[field] = session.scalar(
                        sa.select(sa.func.count()).select_from(model)
                    )
                counts["active_refresh_tokens"] = session.scalar(
                    sa.select(sa.func.count())
                    .select_from(
                        models.RefreshToken,
                    )
                    .where(models.RefreshToken.revoked_at.is_(None))
                )
                counts["ai_calls"] = session.scalar(
                    sa.select(sa.func.coalesce(sa.func.sum(models.AIUsage.calls), 0))
                )
                require(
                    counts
                    == dict(
                        zip(
                            COUNT_FIELDS,
                            (2, 1, 1, len(tracks), 1, 8, 1, 0),
                            strict=True,
                        )
                    )
                )
            checks.append(CHECKS[6])
        require(disposed == {"a": 1, "b": 0})
        require(
            request(cb, "GET", "/api/v1/auth/me", headers=headers(first))["id"]
            == owner["id"]
        )
        checks.append(CHECKS[7])
    require(disposed == {"a": 1, "b": 1})
    checks.append(CHECKS[8])
    return {"checks": checks, "counts": counts, "requests": requests}


def execute(value):
    require(os.environ.get("GANDALF_HTTP_PG_ALLOW") == ALLOW)
    stage("imports")
    r = load_runtime()
    stage("target_validation")
    url = r.base.validate_target(value)
    snapshot = source_snapshot()
    engine = r.base.engine_for(value)
    try:
        stage("empty_database")
        with engine.connect() as connection:
            database, user, version = connection.execute(
                r.sa.text(
                    "SELECT current_database(), current_user, version()",
                )
            ).one()
            occupied = connection.scalar(
                r.sa.text(
                    "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
                    "WHERE n.nspname NOT LIKE 'pg_%' AND n.nspname <> 'information_schema' "
                    "AND c.relkind IN ('r','p','v','m','S','f')",
                )
            )
            available = set(
                connection.scalars(
                    r.sa.text(
                        "SELECT name FROM pg_available_extensions WHERE name IN ('citext','vector')",
                    )
                )
            )
            r.base.validate_database(url, database, user, occupied, available)
            require(
                engine.dialect.name == "postgresql"
                and version.startswith("PostgreSQL ")
            )
        stage("migrations")
        config = r.Config(str(API_ROOT / "alembic.ini"))
        config.set_main_option("script_location", str(API_ROOT / "alembic"))
        with engine.begin() as connection:
            config.attributes["connection"] = connection
            r.command.upgrade(config, "head")
        stage("schema_identity")
        with engine.connect() as connection:
            require(
                connection.scalar(r.sa.text("SHOW transaction_isolation"))
                == "read committed"
            )
            heads = list(
                connection.scalars(r.sa.text("SELECT version_num FROM alembic_version"))
            )
            require(heads == list(r.ScriptDirectory.from_config(config).get_heads()))
            require(
                set(
                    connection.scalars(
                        r.sa.text(
                            "SELECT extname FROM pg_extension WHERE extname IN ('citext','vector')",
                        )
                    )
                )
                == {"citext", "vector"}
            )
        settings = r.Settings(
            _env_file=None,
            database_url=value,
            jwt_secret=secrets.token_hex(32),
            online_catalog=False,
            book_provider="local",
            groq_api_key="",
            cors_origins=[],
            access_token_minutes=15,
            refresh_token_days=7,
            auth_rate_limit_per_minute=10,
        )
        stage("http_contract")
        result = http_contract(settings, engine, r)
        stage("source_freeze")
        require(source_snapshot() == snapshot)
        stage("complete")
        return {
            "status": "PASS",
            "transport": "ASGI_TWO_APPS_SINGLE_PROCESS",
            **result,
            "source_unchanged": True,
            "source_sha256": hashlib.sha256(
                json.dumps(snapshot, sort_keys=True).encode()
            ).hexdigest(),
            "head": heads,
            "observer_disposed": True,
        }
    finally:
        engine.dispose()  # Disposable state remains for Banco's diagnosis/cleanup.


def public_result(result):
    require(
        result.get("status") == "PASS"
        and result.get("transport") == "ASGI_TWO_APPS_SINGLE_PROCESS"
    )
    require(
        result.get("checks") == list(CHECKS) and result.get("source_unchanged") is True
    )
    digest = result.get("source_sha256")
    require(isinstance(digest, str) and re.fullmatch(r"[0-9a-f]{64}", digest))
    counts, requests, heads = (
        result.get("counts"),
        result.get("requests"),
        result.get("head"),
    )
    require(isinstance(counts, dict) and set(counts) == set(COUNT_FIELDS))
    require(all(type(counts[key]) is int and counts[key] >= 0 for key in COUNT_FIELDS))
    require(0 < counts["playlist_tracks"] <= 60)
    require(
        counts
        == dict(
            zip(
                COUNT_FIELDS,
                (
                    2,
                    1,
                    1,
                    counts["playlist_tracks"],
                    1,
                    8,
                    1,
                    0,
                ),
                strict=True,
            )
        )
    )
    require(isinstance(requests, dict) and set(requests) == {"a", "b"})
    require(
        all(type(requests[key]) is int and 0 < requests[key] <= 100 for key in requests)
    )
    require(
        isinstance(heads, list)
        and len(heads) == 1
        and isinstance(heads[0], str)
        and re.fullmatch(r"[0-9a-z_]{1,80}", heads[0])
    )
    require(result.get("observer_disposed") is True)
    return {
        "status": "PASS",
        "transport": "ASGI_TWO_APPS_SINGLE_PROCESS",
        "checks": list(CHECKS),
        "counts": {key: counts[key] for key in COUNT_FIELDS},
        "requests": {key: requests[key] for key in ("a", "b")},
        "head": list(heads),
        "source_unchanged": True,
        "source_sha256": digest,
        "observer_disposed": True,
    }


def main():
    stage("coordination")
    try:
        require(__debug__ and os.environ.get("GANDALF_HTTP_PG_ALLOW") == ALLOW)
        result = public_result(execute(os.environ["GANDALF_HTTP_PG_URL"]))
        code = 0
    except Exception as error:  # noqa: BLE001 -- never reflect messages, DSNs or bodies.
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
                "OSError",
                "TimeoutError",
                "OperationalError",
                "ProgrammingError",
                "IntegrityError",
            }
            else "ExecutionError",
        }
        code = 1
    print(json.dumps(result, sort_keys=True), flush=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
