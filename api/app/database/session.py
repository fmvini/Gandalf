from collections.abc import Iterator

from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.exceptions import AppError


def make_engine(database_url: str) -> Engine:
    return create_engine(database_url, pool_pre_ping=True)


def get_session(request: Request) -> Iterator[Session]:
    factory: sessionmaker[Session] | None = getattr(
        request.app.state, "session_factory", None
    )
    if factory is None:
        raise AppError(
            503, "SERVICE_UNAVAILABLE", "O banco de dados não está configurado."
        )
    with factory() as session:
        yield session
