import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.exceptions import AppError

password_hasher = PasswordHasher()
dummy_hash = password_hasher.hash("dummy-password-for-timing")
JWT_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password_hash: str | None, password: str) -> bool:
    try:
        valid = password_hasher.verify(password_hash or dummy_hash, password)
        return bool(password_hash) and valid
    except (InvalidHashError, VerificationError):
        return False


def new_refresh_token() -> tuple[str, str]:
    token = secrets.token_urlsafe(48)
    return token, refresh_hash(token)


def refresh_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(user_id: UUID, secret: str, lifetime_minutes: int) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": str(user_id),
            "iat": now,
            "exp": now + timedelta(minutes=lifetime_minutes),
            "jti": str(uuid4()),
            "type": "access",
        },
        secret,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str, secret: str) -> UUID:
    try:
        claims = jwt.decode(
            token,
            secret,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["sub", "iat", "exp", "jti", "type"]},
        )
        if claims["type"] != "access":
            raise ValueError("wrong token type")
        return UUID(claims["sub"])
    except (jwt.PyJWTError, ValueError, KeyError, TypeError) as exc:
        raise AppError(401, "UNAUTHORIZED", "Sessão inválida ou expirada.") from exc
