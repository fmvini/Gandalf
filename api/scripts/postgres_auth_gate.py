"""Opt-in PostgreSQL auth gate for an empty disposable test database."""

import hashlib
import json
import os
import secrets
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from threading import Barrier, Event
from time import monotonic, sleep
from unittest.mock import patch
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "api"))

from alembic.config import Config
from sqlalchemy import event, func, inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from alembic import command
from app.core.config import Settings
from app.core.exceptions import AppError
from app.core.security import password_hasher, refresh_hash
from app.models import RefreshToken, User
from app.services.auth_service import AuthService, utc_now
from scripts import postgres_gate as base

STAGE = "coordination"
FILES = (
    "app/core/security.py",
    "app/services/auth_service.py",
    "tests/test_auth.py",
    "tests/test_security.py",
    "app/models/account.py",
)


def stage(name):
    global STAGE
    STAGE = name
    print(json.dumps({"stage": name}), file=sys.stderr, flush=True)


def hashes():
    return {
        path: hashlib.sha256((ROOT / "api" / path).read_bytes()).hexdigest()
        for path in FILES
    }


def ensure_sources_unchanged(started):
    if started != hashes():
        raise RuntimeError("Auth files changed during gate.")


def execute(value):
    stage("source_snapshot")
    started = hashes()
    stage("target_validation")
    url = base.validate_target(value)
    engine = base.engine_for(value)
    checks = []
    settings = Settings(
        _env_file=None,
        database_url=value,
        jwt_secret=secrets.token_hex(32),
        groq_api_key="",
        online_catalog=False,
        book_provider="local",
    )

    def checked(name, **details):
        checks.append({"check": name, **details})

    def token(raw):
        with Session(engine) as session:
            row = session.scalar(
                select(RefreshToken).where(RefreshToken.token_hash == refresh_hash(raw))
            )
            return row.id, row.family_id, row.revoked_at, row.replaced_by_id

    def active(family):
        with Session(engine) as session:
            return session.scalar(
                select(func.count())
                .select_from(RefreshToken)
                .where(
                    RefreshToken.family_id == family,
                    RefreshToken.revoked_at.is_(None),
                )
            )

    def account():
        suffix = uuid4().hex
        email, username = f"{suffix}@example.test", suffix[:20]
        with Session(engine) as session:
            service = AuthService(session, settings)
            user = service.register(email, username, "Synthetic-gate-password-2026")
            uid = user.id
            result = service.login(email, "Synthetic-gate-password-2026")
        return uid, result.refresh_token

    def refresh(raw, barrier=None, entered=None, release=None, pid_box=None):
        with Session(engine) as session:
            if pid_box is not None:
                pid_box.append(session.scalar(text("SELECT pg_backend_pid()")))
            if entered is not None:

                def hold(_session):
                    entered.set()
                    if not release.wait(8):
                        raise TimeoutError("Controlled interleaving not released.")

                event.listen(session, "before_commit", hold, once=True)
            if barrier is not None:
                barrier.wait(timeout=8)
            try:
                return 200, AuthService(session, settings).refresh(raw).refresh_token
            except AppError as exc:
                return exc.status_code, None

    def blocked(waiter, holder):
        deadline = monotonic() + 6
        while monotonic() < deadline:
            if waiter and holder:
                with engine.connect() as connection:
                    if connection.scalar(
                        text("SELECT :holder = ANY(pg_blocking_pids(:waiter))"),
                        {"holder": holder[0], "waiter": waiter[0]},
                    ):
                        return True
            sleep(0.02)
        return False

    try:
        stage("empty_database_preflight")
        with engine.connect() as connection:
            database, user, version = connection.execute(
                text("SELECT current_database(), current_user, version()")
            ).one()
            occupied = connection.scalar(
                text(
                    "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
                    "WHERE n.nspname NOT LIKE 'pg_%' AND n.nspname <> 'information_schema' "
                    "AND c.relkind IN ('r','p','v','m','S','f')"
                )
            )
            available = set(
                connection.scalars(
                    text(
                        "SELECT name FROM pg_available_extensions WHERE name IN ('citext','vector')"
                    )
                )
            )
            base.validate_database(url, database, user, occupied, available)
        stage("migration_head")
        config = Config(str(ROOT / "api/alembic.ini"))
        config.set_main_option("script_location", str(ROOT / "api/alembic"))
        with engine.begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "head")

        stage("constraints_and_digest")
        uid, raw = account()
        with Session(engine) as session:
            user = session.get(User, uid)
            row = session.scalar(
                select(RefreshToken).where(RefreshToken.user_id == uid)
            )
            digest_ok = (
                user.password_hash.startswith("$argon2id$")
                and password_hasher.verify(
                    user.password_hash, "Synthetic-gate-password-2026"
                )
                and row.token_hash == refresh_hash(raw)
                and row.token_hash != raw
                and len(row.token_hash) == 64
            )
            source_email, source_username, source_hash = (
                user.email,
                user.username,
                row.token_hash,
            )
        definitions = inspect(engine)
        foreign_keys = definitions.get_foreign_keys("refresh_tokens")
        fk_ok = any(
            fk["constrained_columns"] == ["user_id"]
            and fk["referred_table"] == "users"
            and fk["options"].get("ondelete") == "CASCADE"
            for fk in foreign_keys
        )
        negatives = [
            (
                User(
                    email=source_email.upper(),
                    username=uuid4().hex[:20],
                    password_hash="synthetic",
                ),
                "23505",
            ),
            (
                User(
                    email=f"{uuid4().hex}@example.test",
                    username=source_username.upper(),
                    password_hash="synthetic",
                ),
                "23505",
            ),
            (
                User(
                    email=f"{uuid4().hex}@example.test",
                    username="xy",
                    password_hash="synthetic",
                ),
                "23514",
            ),
            (
                User(
                    email=f"{uuid4().hex}@example.test",
                    username=uuid4().hex[:20],
                    password_hash=None,
                ),
                "23502",
            ),
            (
                RefreshToken(
                    user_id=uid,
                    family_id=uuid4(),
                    token_hash=source_hash,
                    expires_at=utc_now() + timedelta(days=1),
                ),
                "23505",
            ),
            (
                RefreshToken(
                    user_id=uuid4(),
                    family_id=uuid4(),
                    token_hash=secrets.token_hex(32),
                    expires_at=utc_now() + timedelta(days=1),
                ),
                "23503",
            ),
        ]
        negatives_ok = True
        for record, expected in negatives:
            with Session(engine) as session:
                session.add(record)
                try:
                    session.flush()
                except IntegrityError as exc:
                    negatives_ok &= getattr(exc.orig, "sqlstate", None) == expected
                else:
                    negatives_ok = False
                finally:
                    session.rollback()
        checked(
            "constraints_digest",
            passed=bool(digest_ok and fk_ok and negatives_ok),
            negative_checks=len(negatives),
            replaced_by_has_fk=any(
                fk["constrained_columns"] == ["replaced_by_id"] for fk in foreign_keys
            ),
        )

        stage("same_token_two_sessions")
        _, raw = account()
        _, family, _, _ = token(raw)
        barrier = Barrier(2)
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(refresh, raw, barrier) for _ in range(2)]
            outcomes = [future.result(timeout=12) for future in futures]
        count = active(family)
        with Session(engine) as session:
            records = list(
                session.scalars(
                    select(RefreshToken).where(RefreshToken.family_id == family)
                )
            )
            old = next(row for row in records if row.token_hash == refresh_hash(raw))
            replacement = next(
                (row for row in records if row.id == old.replaced_by_id), None
            )
            chain_ok = (
                len(records) == 2
                and replacement is not None
                and replacement.user_id == old.user_id
            )
        checked(
            "same_token_two_sessions",
            passed=sorted(x[0] for x in outcomes) == [200, 401] and count == 0,
            statuses=sorted(x[0] for x in outcomes),
            active_tokens=count,
            chain_consistent=chain_ok,
        )
        checks[-1]["passed"] &= chain_ok

        stage("ancestor_replay_descendant_rotation")
        _, original = account()
        _, child = refresh(original)
        _, family, _, _ = token(child)
        entered, release = Event(), Event()
        holder, waiter = [], []
        with ThreadPoolExecutor(max_workers=2) as pool:
            rotation = pool.submit(refresh, child, None, entered, release, holder)
            try:
                if not entered.wait(6):
                    raise TimeoutError("Rotation did not reach commit barrier.")
                replay = pool.submit(refresh, original, None, None, None, waiter)
                observed = blocked(waiter, holder)
            finally:
                release.set()
            rotated, reused = rotation.result(timeout=12), replay.result(timeout=12)
        count = active(family)
        checked(
            "ancestor_replay_descendant_rotation",
            passed=observed and rotated[0] == 200 and reused[0] == 401 and count == 0,
            blocking_observed=observed,
            rotation_status=rotated[0],
            replay_status=reused[0],
            active_tokens=count,
        )

        stage("ownership_expiry_logout_cascade")
        owner, raw = account()
        other, other_raw = account()
        with Session(engine) as session:
            AuthService(session, settings).logout(raw, other)
        ownership_ok = token(raw)[2] is None
        _, child = refresh(raw)
        with Session(engine) as session:
            AuthService(session, settings).logout(raw, owner)
        # Current documented contract: logout revokes the provided token only.
        old_logout_preserves_child = token(child)[2] is None
        with Session(engine) as session:
            AuthService(session, settings).logout(child, owner)
        logout_ok = refresh(child)[0] == 401
        with Session(engine) as session:
            row = session.scalar(
                select(RefreshToken).where(
                    RefreshToken.token_hash == refresh_hash(other_raw)
                )
            )
            row.expires_at = utc_now() - timedelta(seconds=1)
            session.commit()
        expiry_ok = refresh(other_raw)[0] == 401
        with Session(engine) as session:
            session.delete(session.get(User, other))
            session.commit()
            cascade_ok = (
                session.scalar(
                    select(func.count())
                    .select_from(RefreshToken)
                    .where(RefreshToken.user_id == other)
                )
                == 0
            )
        checked(
            "ownership_expiry_logout_cascade",
            passed=ownership_ok
            and logout_ok
            and expiry_ok
            and cascade_ok
            and old_logout_preserves_child,
            logout_old_preserves_child=old_logout_preserves_child,
        )
        stage("source_consistency")
        ensure_sources_unchanged(started)
        return {
            "status": "PASS" if all(c["passed"] for c in checks) else "NOT_PASSED",
            "checks": checks,
            "postgresql": version,
            "source_sha256": started,
            "concurrency": "threads_independent_sessions_read_committed",
        }
    finally:
        engine.dispose()


def guard_checks():
    safe = (
        "postgresql+psycopg://gandalf_gate:synthetic@127.0.0.1:55432/gandalf_gate_"
        + "0" * 31
        + "1"
    )
    unsafe = [safe.replace(":55432", f":{port}") for port in (5432, 5433, 8000)]
    unsafe += [
        safe.replace("127.0.0.1", "remote.example"),
        safe + "?host=remote.example",
        safe.replace("gandalf_gate:synthetic", "postgres:synthetic"),
        safe.rsplit("/", 1)[0] + "/gandalf",
        safe.replace("postgresql+psycopg", "sqlite"),
    ]
    count = 0
    with patch.object(base, "create_engine") as creator:
        for target in unsafe:
            try:
                base.engine_for(target)
            except ValueError:
                count += 1
            else:
                raise AssertionError("Unsafe target accepted.")
        creator.assert_not_called()
    url = base.validate_target(safe)
    for db, user, objects, extensions in (
        (url.database, "gandalf_gate", 1, {"citext", "vector"}),
        ("postgres", "gandalf_gate", 0, {"citext", "vector"}),
        (url.database, "postgres", 0, {"citext", "vector"}),
        (url.database, "gandalf_gate", 0, {"citext"}),
    ):
        try:
            base.validate_database(url, db, user, objects, extensions)
        except ValueError:
            count += 1
        else:
            raise AssertionError("Unsafe database accepted.")
    return {
        "status": "OFFLINE_GUARDS_PASS",
        "refusals": count,
        "integration_executed": False,
    }


def main():
    try:
        if not __debug__:
            raise ValueError("Optimization disables gate assertions.")
        if sys.argv[1:] == ["--guard-checks"]:
            result = guard_checks()
        else:
            if sys.argv[1:]:
                raise ValueError("Unexpected arguments.")
            if (
                os.environ.get("GANDALF_AUTH_PG_ALLOW")
                != "isolated-coordinated-backend-frozen"
            ):
                raise ValueError("Explicit coordination and Backend freeze required.")
            result = execute(os.environ["GANDALF_AUTH_PG_URL"])
        print(json.dumps(result))
        return 0 if result["status"] in {"PASS", "OFFLINE_GUARDS_PASS"} else 1
    except Exception as exc:  # noqa: BLE001 -- CLI boundary emits only safe stage/class.
        print(
            json.dumps(
                {
                    "status": "NOT_PASSED",
                    "stage": STAGE,
                    "error_class": type(exc).__name__,
                }
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
