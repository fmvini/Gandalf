from hashlib import sha256
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.database.session import get_session
from app.models import User
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
bearer = HTTPBearer(auto_error=False)


def auth_service(
    request: Request, session: Annotated[Session, Depends(get_session)]
) -> AuthService:
    return AuthService(session, request.app.state.settings)


def limit_auth(request: Request) -> None:
    address = request.client.host if request.client else "unknown"
    request.app.state.auth_limiter.check(f"{address}:{request.url.path}")


def limit_account(request: Request, email: str) -> None:
    email_hash = sha256(email.casefold().encode("utf-8")).hexdigest()
    request.app.state.auth_limiter.check(f"account:{email_hash}")


def current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    service: Annotated[AuthService, Depends(auth_service)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError(401, "UNAUTHORIZED", "Autenticação necessária.")
    return service.current_user(credentials.credentials)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201,
    dependencies=[Depends(limit_auth)],
)
def register(
    request: Request,
    payload: RegisterRequest,
    service: Annotated[AuthService, Depends(auth_service)],
) -> User:
    limit_account(request, str(payload.email))
    return service.register(str(payload.email), payload.username, payload.password)


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(limit_auth)])
def login(
    request: Request,
    payload: LoginRequest,
    service: Annotated[AuthService, Depends(auth_service)],
) -> TokenResponse:
    limit_account(request, str(payload.email))
    return service.login(str(payload.email), payload.password)


@router.post(
    "/refresh", response_model=TokenResponse, dependencies=[Depends(limit_auth)]
)
def refresh(
    payload: RefreshRequest, service: Annotated[AuthService, Depends(auth_service)]
) -> TokenResponse:
    return service.refresh(payload.refresh_token)


@router.post("/logout", status_code=204)
def logout(
    payload: RefreshRequest,
    user: Annotated[User, Depends(current_user)],
    service: Annotated[AuthService, Depends(auth_service)],
) -> Response:
    service.logout(payload.refresh_token, user.id)
    return Response(status_code=204)


@router.get("/me", response_model=UserResponse)
def me(user: Annotated[User, Depends(current_user)]) -> User:
    return user
