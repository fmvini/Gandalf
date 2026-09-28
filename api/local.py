"""Run the free local instance with an isolated, persistent SQLite database."""

import os
import secrets
from pathlib import Path

import uvicorn
from alembic.config import Config

from alembic import command
from app.core.config import Settings
from app.main import create_app

ROOT = Path(__file__).resolve().parent


def local_settings(data_dir: Path | None = None) -> Settings:
    directory = (data_dir or ROOT / ".local").resolve()
    directory.mkdir(parents=True, exist_ok=True)
    secret_file = directory / "jwt-secret"
    try:
        with secret_file.open("x", encoding="utf-8") as stream:
            stream.write(secrets.token_urlsafe(48))
    except FileExistsError:
        pass
    return Settings(
        _env_file=None,
        database_url="sqlite:///" + (directory / "gandalf.db").as_posix(),
        jwt_secret=secret_file.read_text(encoding="utf-8").strip(),
        book_provider="local",
        cors_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    )


def prepare(settings: Settings) -> None:
    config = Config(str(ROOT / "alembic.ini"))
    # Pass a connection so Alembic cannot pick up an unrelated DATABASE_URL.
    from app.database.session import make_engine

    engine = make_engine(settings.database_url)
    try:
        with engine.begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
    finally:
        engine.dispose()


if __name__ == "__main__":
    settings = local_settings(
        Path(os.environ["GANDALF_LOCAL_DATA"])
        if os.environ.get("GANDALF_LOCAL_DATA")
        else None
    )
    prepare(settings)
    uvicorn.run(
        create_app(settings=settings),
        host="127.0.0.1",
        port=int(os.environ.get("GANDALF_PORT", "8000")),
    )
