from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from threading import Barrier
from uuid import UUID

import jwt
import pytest
from alembic.config import Config
from argon2 import PasswordHasher
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from alembic import command
from app.core.config import Settings
from app.core.exceptions import AppError
from app.core.security import create_access_token, password_hasher, refresh_hash
from app.main import create_app
from app.models import RefreshToken, User
from app.services.auth_service import AuthService, utc_now

SECRET = "test-only-" + "s" * 64


@pytest.fixture
def auth_client(tmp_path: Path, monkeypatch):
    database_url = f"sqlite:///{tmp_path / 'auth.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(config, "head")
    settings = Settings(
        _env_file=None,
        database_url=database_url,
        jwt_secret=SECRET,
        online_catalog=False,
        book_provider="local",
    )
    with TestClient(create_app(settings=settings)) as client:
        yield client, database_url


def register(client: TestClient, email: str = "ana@example.com", username: str = "Ana"):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "username": username, "password": "senha-longa-segura"},
    )


def login(client: TestClient, email: str = "ana@example.com"):
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "senha-longa-segura"},
    )


def test_register_login_and_me(auth_client) -> None:
    client, database_url = auth_client
    created = register(client, "ANA@EXAMPLE.COM")
    assert created.status_code == 201
    assert created.json()["email"] == "ana@example.com"
    assert created.json()["username"] == "ana"
    assert "password" not in created.json()
    user_id = UUID(created.json()["id"])

    engine = create_engine(database_url)
    with Session(engine) as session:
        user = session.get(User, user_id)
        assert user is not None
        assert user.password_hash.startswith("$argon2id$")
        assert password_hasher.verify(user.password_hash, "senha-longa-segura")
    engine.dispose()

    assert client.get("/api/v1/auth/me").status_code == 401
    logged_in = login(client)
    assert logged_in.status_code == 200
    tokens = logged_in.json()
    assert tokens["token_type"] == "bearer"
    assert tokens["expires_in"] == 900
    claims = jwt.decode(tokens["access_token"], SECRET, algorithms=["HS256"])
    assert claims["sub"] == str(user_id)
    assert claims["type"] == "access"
    assert {"iat", "exp", "jti"} <= claims.keys()
    me = client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer " + tokens["access_token"]}
    )
    assert me.status_code == 200
    assert me.json()["id"] == str(user_id)


def test_registration_validation_duplicates_and_generic_login_error(
    auth_client,
) -> None:
    client, _ = auth_client
    assert register(client).status_code == 201
    duplicate = register(client, "ana@example.com", "outra")
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "CONFLICT"
    invalid = client.post(
        "/api/v1/auth/register",
        json={"email": "invalido", "username": "x", "password": "curta"},
    )
    assert invalid.status_code == 422
    wrong_password = client.post(
        "/api/v1/auth/login",
        json={"email": "ana@example.com", "password": "senha-errada"},
    )
    unknown_email = client.post(
        "/api/v1/auth/login",
        json={"email": "outro@example.com", "password": "senha-errada"},
    )
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert (
        wrong_password.json()["error"]["message"]
        == unknown_email.json()["error"]["message"]
    )


def test_access_token_rejects_expired_and_tampered_values(auth_client) -> None:
    client, _ = auth_client
    user_id = UUID(register(client).json()["id"])
    expired = create_access_token(user_id, SECRET, -1)
    assert (
        client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer " + expired}
        ).status_code
        == 401
    )
    valid = login(client).json()["access_token"]
    header, payload, signature = valid.split(".")
    tampered = ".".join(
        (header, payload, ("A" if signature[0] != "A" else "B") + signature[1:])
    )
    assert (
        client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer " + tampered}
        ).status_code
        == 401
    )
    claims = jwt.decode(valid, SECRET, algorithms=["HS256"])
    wrong_algorithm = jwt.encode(claims, SECRET, algorithm="HS512")
    assert (
        client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer " + wrong_algorithm}
        ).status_code
        == 401
    )


def test_argon2_uses_distinct_salts(auth_client) -> None:
    client, database_url = auth_client
    first_id = UUID(register(client).json()["id"])
    second_id = UUID(register(client, "bia@example.com", "Bia").json()["id"])
    engine = create_engine(database_url)
    with Session(engine) as session:
        first = session.get(User, first_id)
        second = session.get(User, second_id)
        assert first is not None and second is not None
        assert first.password_hash != second.password_hash
    engine.dispose()


def test_refresh_rotates_and_reuse_revokes_family(auth_client) -> None:
    client, database_url = auth_client
    register(client)
    first = login(client).json()
    rotated = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]}
    )
    assert rotated.status_code == 200
    second = rotated.json()
    assert second["refresh_token"] != first["refresh_token"]
    assert second["access_token"] != first["access_token"]

    reused = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]}
    )
    assert reused.status_code == 401
    assert (
        client.post(
            "/api/v1/auth/refresh", json={"refresh_token": second["refresh_token"]}
        ).status_code
        == 401
    )
    engine = create_engine(database_url)
    with Session(engine) as session:
        record = session.scalar(
            select(RefreshToken).where(
                RefreshToken.token_hash == refresh_hash(second["refresh_token"])
            )
        )
        assert record is not None and record.revoked_at is not None
    engine.dispose()


def test_expired_refresh_and_logout(auth_client) -> None:
    client, database_url = auth_client
    register(client)
    tokens = login(client).json()
    engine = create_engine(database_url)
    with Session(engine) as session:
        record = session.scalar(
            select(RefreshToken).where(
                RefreshToken.token_hash == refresh_hash(tokens["refresh_token"])
            )
        )
        assert record is not None
        record.expires_at = utc_now() - timedelta(days=1)
        session.commit()
    assert (
        client.post(
            "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        ).status_code
        == 401
    )
    engine.dispose()

    fresh = login(client).json()
    logged_out = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": fresh["refresh_token"]},
        headers={"Authorization": "Bearer " + fresh["access_token"]},
    )
    assert logged_out.status_code == 204
    assert (
        client.post(
            "/api/v1/auth/refresh", json={"refresh_token": fresh["refresh_token"]}
        ).status_code
        == 401
    )


def test_auth_rate_limit_returns_429_and_retry_after(auth_client) -> None:
    _, database_url = auth_client
    settings = Settings(
        _env_file=None,
        database_url=database_url,
        jwt_secret=SECRET,
        online_catalog=False,
        book_provider="local",
        auth_rate_limit_per_minute=2,
    )
    with TestClient(create_app(settings=settings)) as client:
        for _ in range(2):
            assert (
                client.post(
                    "/api/v1/auth/login",
                    json={"email": "missing@example.com", "password": "wrong"},
                ).status_code
                == 401
            )
        limited = client.post(
            "/api/v1/auth/login",
            json={"email": "missing@example.com", "password": "wrong"},
        )
    assert limited.status_code == 429
    assert limited.json()["error"]["code"] == "RATE_LIMITED"
    assert int(limited.headers["Retry-After"]) > 0


def test_logout_cannot_revoke_another_users_refresh(auth_client) -> None:
    client, _ = auth_client
    register(client)
    register(client, "bia@example.com", "Bia")
    ana = login(client).json()
    bia = login(client, "bia@example.com").json()
    response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": bia["refresh_token"]},
        headers={"Authorization": "Bearer " + ana["access_token"]},
    )
    assert response.status_code == 204
    assert (
        client.post(
            "/api/v1/auth/refresh", json={"refresh_token": bia["refresh_token"]}
        ).status_code
        == 200
    )


@pytest.mark.parametrize("stored_hash", ["", "invalid-stored-hash"])
def test_corrupt_password_hash_fails_as_generic_credentials(
    auth_client, stored_hash
) -> None:
    client, database_url = auth_client
    user_id = UUID(register(client).json()["id"])
    engine = create_engine(database_url)
    try:
        with Session(engine) as session:
            session.get(User, user_id).password_hash = stored_hash
            session.commit()
        response = login(client)
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"
    finally:
        engine.dispose()


def test_concurrent_refresh_has_one_winner_and_replay_revokes_family(
    auth_client, monkeypatch
) -> None:
    client, database_url = auth_client
    register(client)
    first = login(client).json()
    engine = create_engine(database_url)
    barrier = Barrier(2)
    from app.services import auth_service

    original_new_token = auth_service.new_refresh_token

    def synchronized_new_token():
        # Both independent sessions have validated the same unconsumed token.
        barrier.wait(timeout=10)
        return original_new_token()

    monkeypatch.setattr(auth_service, "new_refresh_token", synchronized_new_token)

    def rotate():
        with Session(engine) as session:
            try:
                response = AuthService(session, client.app.state.settings).refresh(
                    first["refresh_token"]
                )
                return 200, response
            except AppError as error:
                return error.status_code, None

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(rotate) for _ in range(2)]
            results = [future.result(timeout=20) for future in futures]
        assert sorted(status for status, _ in results) == [200, 401]
        with Session(engine) as session:
            original = session.scalar(
                select(RefreshToken).where(
                    RefreshToken.token_hash == refresh_hash(first["refresh_token"])
                )
            )
            family = session.scalars(
                select(RefreshToken).where(RefreshToken.family_id == original.family_id)
            ).all()
            assert len(family) == 2
            assert all(record.revoked_at is not None for record in family)
        winner = next(response for status, response in results if status == 200)
        assert (
            client.post(
                "/api/v1/auth/refresh", json={"refresh_token": winner.refresh_token}
            ).status_code
            == 401
        )
    finally:
        engine.dispose()


@pytest.mark.parametrize(
    "operation", ["register", "login", "refresh", "logout", "replay"]
)
def test_auth_write_failure_rolls_back_without_sensitive_logging(
    auth_client, monkeypatch, caplog, operation
) -> None:
    client, database_url = auth_client
    register(client)
    tokens = login(client).json()
    live_token = tokens["refresh_token"]
    if operation == "replay":
        live_token = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        ).json()["refresh_token"]
    original_rollback = Session.rollback
    rollbacks = []

    def fail_commit(session):
        raise OperationalError(
            "INSERT auth", ("sensitive-hash-fixture",), Exception("db unavailable")
        )

    def record_rollback(session):
        rollbacks.append(session)
        original_rollback(session)

    monkeypatch.setattr(Session, "commit", fail_commit)
    monkeypatch.setattr(Session, "rollback", record_rollback)
    if operation == "register":
        response = register(client, "bia@example.com", "Bia")
    elif operation == "login":
        response = login(client)
    else:
        response = client.post(
            "/api/v1/auth/" + ("refresh" if operation == "replay" else operation),
            json={"refresh_token": tokens["refresh_token"]},
            headers={"Authorization": "Bearer " + tokens["access_token"]},
        )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert rollbacks
    assert "sensitive-hash-fixture" not in response.text
    assert "sensitive-hash-fixture" not in caplog.text
    engine = create_engine(database_url)
    try:
        with Session(engine) as session:
            assert len(session.scalars(select(User)).all()) == 1
            records = session.scalars(select(RefreshToken)).all()
            assert len(records) == (2 if operation == "replay" else 1)
            live = next(
                record
                for record in records
                if record.token_hash == refresh_hash(live_token)
            )
            assert live.revoked_at is None
            assert live.replaced_by_id is None
    finally:
        engine.dispose()


@pytest.mark.parametrize("operation", ["login", "refresh", "logout", "me"])
def test_auth_read_failure_is_generic_unavailable(
    auth_client, monkeypatch, caplog, operation
):
    client, _ = auth_client
    register(client)
    tokens = login(client).json()

    def fail_query(*args, **kwargs):
        raise OperationalError(
            "SELECT auth", ("private-fixture-parameter",), Exception("db unavailable")
        )

    monkeypatch.setattr(Session, "_execute_internal", fail_query)
    if operation == "login":
        response = login(client)
    elif operation == "me":
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer " + tokens["access_token"]},
        )
    else:
        response = client.post(
            "/api/v1/auth/" + operation,
            json={"refresh_token": tokens["refresh_token"]},
            headers={"Authorization": "Bearer " + tokens["access_token"]},
        )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert "private-fixture-parameter" not in response.text
    assert "private-fixture-parameter" not in caplog.text


@pytest.mark.parametrize("commit_fails", [False, True])
def test_password_rehash_is_atomic_with_login(auth_client, monkeypatch, commit_fails):
    client, database_url = auth_client
    user_id = UUID(register(client).json()["id"])
    old_hash = PasswordHasher(time_cost=1, memory_cost=8192, parallelism=1).hash(
        "senha-longa-segura"
    )
    engine = create_engine(database_url)
    try:
        with Session(engine) as session:
            session.get(User, user_id).password_hash = old_hash
            session.commit()
        assert password_hasher.check_needs_rehash(old_hash)
        if commit_fails:

            def fail_commit(session):
                raise OperationalError("INSERT auth", (), Exception("db unavailable"))

            monkeypatch.setattr(Session, "commit", fail_commit)
        response = login(client)
        assert response.status_code == (503 if commit_fails else 200)
        with Session(engine) as session:
            current_hash = session.get(User, user_id).password_hash
            records = session.scalars(select(RefreshToken)).all()
            if commit_fails:
                assert current_hash == old_hash
                assert not records
            else:
                assert current_hash != old_hash
                assert not password_hasher.check_needs_rehash(current_hash)
                assert password_hasher.verify(current_hash, "senha-longa-segura")
                assert len(records) == 1
    finally:
        engine.dispose()


def test_inactive_user_cannot_login_refresh_or_use_access(auth_client):
    client, database_url = auth_client
    user_id = UUID(register(client).json()["id"])
    tokens = login(client).json()
    engine = create_engine(database_url)
    try:
        with Session(engine) as session:
            session.get(User, user_id).is_active = False
            session.commit()
        assert login(client).status_code == 401
        assert (
            client.get(
                "/api/v1/auth/me",
                headers={"Authorization": "Bearer " + tokens["access_token"]},
            ).status_code
            == 401
        )
        assert (
            client.post(
                "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
            ).status_code
            == 401
        )
    finally:
        engine.dispose()


def test_logout_old_refresh_is_noop_and_access_expires_naturally(auth_client):
    client, _ = auth_client
    register(client)
    first = login(client).json()
    second = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]}
    ).json()
    headers = {"Authorization": "Bearer " + first["access_token"]}
    assert (
        client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": first["refresh_token"]},
            headers=headers,
        ).status_code
        == 204
    )
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200
    assert (
        client.post(
            "/api/v1/auth/refresh", json={"refresh_token": second["refresh_token"]}
        ).status_code
        == 200
    )


def test_replay_does_not_revoke_another_login_family(auth_client):
    client, _ = auth_client
    register(client)
    first, independent = login(client).json(), login(client).json()
    successor = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]}
    ).json()
    assert (
        client.post(
            "/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]}
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/auth/refresh", json={"refresh_token": successor["refresh_token"]}
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/auth/refresh", json={"refresh_token": independent["refresh_token"]}
        ).status_code
        == 200
    )


def test_username_duplicate_is_generic_and_failed_insert_does_not_persist(auth_client):
    client, database_url = auth_client
    assert register(client).status_code == 201
    conflict = register(client, "bia@example.com", "ANA")
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "CONFLICT"
    assert "username" not in conflict.json()["error"]["message"]
    assert register(client, "bia@example.com", "Bia").status_code == 201
    engine = create_engine(database_url)
    try:
        with Session(engine) as session:
            assert len(session.scalars(select(User)).all()) == 2
    finally:
        engine.dispose()
