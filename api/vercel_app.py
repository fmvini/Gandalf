"""Environment-only ASGI entrypoint; schema preparation is an external operation."""

import importlib
import re

from sqlalchemy.engine import make_url

from app.core.config import Settings


class VercelConfigurationError(ValueError):
    """Startup errors must not contain connection strings or credentials."""


def vercel_settings() -> Settings:
    try:
        settings = Settings(_env_file=None)
        if not settings.database_url:
            raise ValueError
        url = make_url(settings.database_url)
        if (
            url.drivername not in {"postgresql", "postgresql+psycopg"}
            or not url.host
            or not re.fullmatch(r"[a-z0-9-]+(?:\.[a-z0-9-]+)*\.neon\.tech", url.host)
            or not url.username
            or not url.password
            or not url.database
            or (url.port is not None and url.port != 5432)
            or set(url.query) - {"sslmode", "channel_binding", "connect_timeout"}
            or url.query.get("sslmode") not in {"require", "verify-ca", "verify-full"}
            or len(settings.jwt_secret.strip().encode("utf-8")) < 32
        ):
            raise ValueError
        # Tuple values signal duplicate query parameters; never select one silently.
        if any(not isinstance(value, str) for value in url.query.values()):
            raise ValueError
        if "channel_binding" in url.query and url.query["channel_binding"] not in {
            "disable",
            "prefer",
            "require",
        }:
            raise ValueError
        timeout = url.query.get("connect_timeout")
        if timeout is not None and (
            not timeout.isascii()
            or not timeout.isdecimal()
            or not 1 <= int(timeout) <= 60
        ):
            raise ValueError
        settings.database_url = url.set(
            drivername="postgresql+psycopg"
        ).render_as_string(hide_password=False)
        return settings
    except Exception:  # noqa: BLE001 -- validation errors can contain secrets and input.
        raise VercelConfigurationError("Invalid Vercel configuration.") from None


def create_vercel_app():
    settings = vercel_settings()  # Fail before importing the default application.
    previous = Settings.model_config
    try:
        # main's unused module-level app calls Settings() without _env_file=None.
        # Scope this guard to its cold import, without changing cwd or process env.
        Settings.model_config = {**previous, "env_file": None}
        factory = importlib.import_module("app.main").create_app
    except Exception:  # noqa: BLE001 -- imports may expose environment input in errors.
        raise VercelConfigurationError("Vercel startup failed.") from None
    finally:
        Settings.model_config = previous
    try:
        return factory(settings=settings)
    except Exception:  # noqa: BLE001 -- keep credentials out of startup diagnostics.
        raise VercelConfigurationError("Vercel startup failed.") from None


app = create_vercel_app()
