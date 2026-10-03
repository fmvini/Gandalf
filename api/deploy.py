"""Explicit environment-only deployment launcher; local.py remains unchanged."""

import os
import sys
from ipaddress import ip_address

from sqlalchemy.engine import make_url

from app.core.config import Settings


class DeploymentConfigurationError(ValueError):
    """Sanitized configuration failure; never include credentials or DSNs."""


def deployment_settings() -> Settings:
    try:
        settings = Settings(_env_file=None)
        if not settings.database_url or not settings.database_url.strip():
            raise DeploymentConfigurationError
        url = make_url(settings.database_url)
        if url.drivername == "postgresql+psycopg":
            if (
                not url.host
                or not url.database
                or url.port is not None
                and not 1 <= url.port <= 65535
            ):
                raise DeploymentConfigurationError
        elif url.drivername == "sqlite":
            if (
                not url.database
                or url.database == ":memory:"
                or url.query.get("mode") == "memory"
            ):
                raise DeploymentConfigurationError
        else:
            raise DeploymentConfigurationError
        if (
            not settings.jwt_secret.strip()
            or len(settings.jwt_secret.encode("utf-8")) < 32
        ):
            raise DeploymentConfigurationError
        return settings
    except (ValueError, TypeError):
        raise DeploymentConfigurationError(
            "Invalid deployment configuration."
        ) from None


def binding() -> tuple[str, int]:
    host = os.environ.get("GANDALF_HOST", "0.0.0.0")
    raw_port = os.environ.get("GANDALF_PORT", "8000")
    try:
        if host != "localhost":
            ip_address(host)
        if (
            not raw_port.isascii()
            or not raw_port.isdecimal()
            or not 1 <= int(raw_port) <= 65535
        ):
            raise ValueError
        return host, int(raw_port)
    except ValueError:
        raise DeploymentConfigurationError("Invalid deployment binding.") from None


def main() -> int:
    try:
        # No local data directory/secret is created. Validate before migration or bind.
        settings = deployment_settings()
        host, port = binding()

        import uvicorn

        from app.main import create_app
        from local import prepare

        prepare(settings)
        uvicorn.run(create_app(settings=settings), host=host, port=port)
    except Exception:  # noqa: BLE001 - CLI aborts generically; failures may contain credentials.
        print("Deployment startup failed.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
