import os

from sqlalchemy import create_engine, pool

import app.models  # noqa: F401 - registra tabelas no metadata
from alembic import context
from app.core.config import Settings
from app.database.base import Base

config = context.config
target_metadata = Base.metadata


def database_url() -> str:
    url = (
        os.getenv("DATABASE_URL")
        or config.get_main_option("sqlalchemy.url")
        or Settings().database_url
    )
    if not url:
        raise RuntimeError("Defina DATABASE_URL para executar as migrações.")
    return url


def run_migrations_offline() -> None:
    context.configure(
        url=database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connection = config.attributes.get("connection")
    if connection is None:
        engine = create_engine(database_url(), poolclass=pool.NullPool)
        try:
            with engine.connect() as connection:
                context.configure(
                    connection=connection, target_metadata=target_metadata
                )
                with context.begin_transaction():
                    context.run_migrations()
        finally:
            engine.dispose()
    else:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
