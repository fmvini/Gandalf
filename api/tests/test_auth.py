from datetime import timedelta
from pathlib import Path
from uuid import UUID

import jwt
import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from alembic import command
from app.core.config import Settings
from app.core.security import create_access_token, password_hasher, refresh_hash
from app.main import create_app
from app.models import RefreshToken, User
from app.services.auth_service import utc_now

SECRET = "test-only-" + "s" * 64


@pytest.fixture
def auth_client(tmp_path: Path, monkeypatch):
    database_url = f"sqlite:///{tmp_path / 'auth.db'}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(config, "head")
    settings = Settings(database_url=database_url, jwt_secret=SECRET)
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
        database_url=database_url,
        jwt_secret=SECRET,
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
