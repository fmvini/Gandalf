import logging
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.exceptions import AppError
from app.main import create_app
from app.models import User
from app.routes.auth import auth_service
from app.schemas.auth import TokenResponse


class SyntheticAuthService:
    def __init__(self, error=None):
        self.error = error
        self.user = User(
            id=uuid4(),
            email="audit@example.com",
            username="audit",
            created_at=datetime.now(UTC),
        )

    def register(self, *_):
        return self.user

    def login(self, *_):
        if self.error:
            raise self.error
        return TokenResponse(
            access_token="synthetic-access",
            refresh_token="synthetic-refresh",
            expires_in=900,
        )

    def refresh(self, *_):
        return self.login()

    def current_user(self, *_):
        return self.user

    def logout(self, *_):
        return None


def client_for(service, limit=10):
    app = create_app(settings=Settings(auth_rate_limit_per_minute=limit))
    app.dependency_overrides[auth_service] = lambda: service
    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize(
    "method,path,body,status",
    [
        (
            "POST",
            "register",
            {
                "email": "audit@example.com",
                "username": "audit",
                "password": "synthetic-password",
            },
            201,
        ),
        (
            "POST",
            "login",
            {"email": "audit@example.com", "password": "synthetic-password"},
            200,
        ),
        ("POST", "refresh", {"refresh_token": "synthetic-refresh"}, 200),
        ("GET", "me", None, 200),
        ("POST", "logout", {"refresh_token": "synthetic-refresh"}, 204),
    ],
)
def test_auth_success_responses_are_not_cacheable(method, path, body, status):
    with client_for(SyntheticAuthService()) as client:
        response = client.request(
            method,
            f"/api/v1/auth/{path}",
            json=body,
            headers={"Authorization": "Bearer synthetic-access"},
        )
    assert response.status_code == status
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Pragma"] == "no-cache"


@pytest.mark.parametrize("status", [401, 503, 500])
def test_auth_errors_are_private_and_logs_do_not_include_exception_input(
    status, caplog
):
    sentinel = "synthetic-secret-must-not-be-logged"
    error = (
        RuntimeError(sentinel)
        if status == 500
        else AppError(status, "AUDIT_ERROR", "Erro genérico.")
    )
    with (
        caplog.at_level(logging.INFO, logger="gandalf.api"),
        client_for(SyntheticAuthService(error)) as client,
    ):
        response = client.post(
            "/api/v1/auth/login?private=" + sentinel,
            json={"email": "audit@example.com", "password": sentinel},
        )
    assert response.status_code == status
    assert response.headers["Cache-Control"] == "no-store"
    assert sentinel not in response.text
    assert sentinel not in caplog.text
    if status == 500:
        records = [
            r
            for r in caplog.records
            if r.name == "gandalf.api" and r.levelno == logging.ERROR
        ]
        assert len(records) == 1
        assert records[0].exc_info is None
        assert "RuntimeError" in records[0].getMessage()


def test_validation_and_rate_limit_errors_are_not_cacheable():
    with client_for(SyntheticAuthService(), limit=2) as client:
        invalid = client.post(
            "/api/v1/auth/login", json={"password": "private-invalid-input"}
        )
        assert invalid.status_code == 422
        assert invalid.headers["Cache-Control"] == "no-store"
        assert "private-invalid-input" not in invalid.text
        body = {"email": "audit@example.com", "password": "synthetic-password"}
        assert client.post("/api/v1/auth/login", json=body).status_code == 200
        limited = client.post("/api/v1/auth/login", json=body)
    assert limited.status_code == 429
    assert limited.headers["Cache-Control"] == "no-store"
    assert int(limited.headers["Retry-After"]) > 0


def test_public_health_response_is_unchanged():
    with client_for(SyntheticAuthService()) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert "Cache-Control" not in response.headers
