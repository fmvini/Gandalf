from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.exceptions import AppError
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    new_refresh_token,
    password_hasher,
    refresh_hash,
    verify_password,
)
from app.models import RefreshToken, User
from app.schemas.auth import TokenResponse


def utc_now() -> datetime:
    return datetime.now(UTC)


def as_utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


class AuthService:
    def __init__(self, session: Session, settings: Settings) -> None:
        if len(settings.jwt_secret.encode("utf-8")) < 32:
            raise AppError(
                503, "SERVICE_UNAVAILABLE", "A autenticação não está configurada."
            )
        self.session = session
        self.settings = settings

    def register(self, email: str, username: str, password: str) -> User:
        with self._database_errors():
            user = User(
                email=email.casefold(),
                username=username.casefold(),
                password_hash=hash_password(password),
            )
            self.session.add(user)
            try:
                self.session.commit()
            except IntegrityError as exc:
                self.session.rollback()
                raise AppError(
                    409, "CONFLICT", "Não foi possível criar a conta com esses dados."
                ) from exc
            self.session.refresh(user)
            return user

    def login(self, email: str, password: str) -> TokenResponse:
        with self._database_errors():
            user = self.session.scalar(
                select(User).where(User.email == email.casefold())
            )
            valid = verify_password(user.password_hash if user else None, password)
            if user is None or not valid or not user.is_active:
                raise AppError(401, "INVALID_CREDENTIALS", "E-mail ou senha inválidos.")
            if password_hasher.check_needs_rehash(user.password_hash):
                user.password_hash = hash_password(password)
            return self._issue_tokens(user, family_id=uuid4())

    def refresh(self, token: str) -> TokenResponse:
        with self._database_errors():
            return self._rotate_refresh(token)

    def _rotate_refresh(self, token: str) -> TokenResponse:
        record = self.session.scalar(
            select(RefreshToken)
            .where(RefreshToken.token_hash == refresh_hash(token))
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if record is None:
            raise AppError(401, "UNAUTHORIZED", "Sessão inválida ou expirada.")
        if record.revoked_at is not None:
            if record.replaced_by_id is not None:
                self._revoke_family(record.family_id)
            raise AppError(401, "UNAUTHORIZED", "Sessão inválida ou expirada.")
        if as_utc(record.expires_at) <= utc_now():
            raise AppError(401, "UNAUTHORIZED", "Sessão inválida ou expirada.")
        user = self.session.get(User, record.user_id)
        if user is None or not user.is_active:
            raise AppError(401, "UNAUTHORIZED", "Sessão inválida ou expirada.")

        raw_token, token_hash = new_refresh_token()
        replacement = RefreshToken(
            id=uuid4(),
            user_id=user.id,
            token_hash=token_hash,
            family_id=record.family_id,
            expires_at=utc_now() + timedelta(days=self.settings.refresh_token_days),
        )
        # SQLite ignores FOR UPDATE. Claim the unconsumed row atomically on
        # either database before adding a successor; never trust a stale read.
        consumed = self.session.execute(
            update(RefreshToken)
            .where(
                RefreshToken.id == record.id,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > utc_now(),
            )
            .values(revoked_at=utc_now(), replaced_by_id=replacement.id)
            .execution_options(synchronize_session=False)
        )
        if consumed.rowcount != 1:
            record_id = record.id
            self.session.rollback()
            current = self.session.get(RefreshToken, record_id)
            if current is not None and current.replaced_by_id is not None:
                self._revoke_family(current.family_id)
            raise AppError(401, "UNAUTHORIZED", "Sessão inválida ou expirada.")
        self.session.add(replacement)
        response = self._token_response(user.id, raw_token)
        self.session.commit()
        return response

    def logout(self, token: str, user_id: UUID) -> None:
        with self._database_errors():
            record = self.session.scalar(
                select(RefreshToken)
                .where(RefreshToken.token_hash == refresh_hash(token))
                .with_for_update()
            )
            if (
                record is not None
                and record.user_id == user_id
                and record.revoked_at is None
            ):
                record.revoked_at = utc_now()
                self.session.commit()

    def current_user(self, access_token: str) -> User:
        user_id = decode_access_token(access_token, self.settings.jwt_secret)
        with self._database_errors():
            user = self.session.get(User, user_id)
            if user is None or not user.is_active:
                raise AppError(401, "UNAUTHORIZED", "Sessão inválida ou expirada.")
            return user

    @contextmanager
    def _database_errors(self):
        try:
            yield
        except SQLAlchemyError as exc:
            self.session.rollback()
            raise AppError(
                503,
                "SERVICE_UNAVAILABLE",
                "A autenticação está indisponível. Tente novamente.",
            ) from exc

    def _issue_tokens(self, user: User, family_id: UUID) -> TokenResponse:
        raw_token, token_hash = new_refresh_token()
        self.session.add(
            RefreshToken(
                id=uuid4(),
                user_id=user.id,
                token_hash=token_hash,
                family_id=family_id,
                expires_at=utc_now() + timedelta(days=self.settings.refresh_token_days),
            )
        )
        response = self._token_response(user.id, raw_token)
        self.session.commit()
        return response

    def _token_response(self, user_id: UUID, refresh_token: str) -> TokenResponse:
        return TokenResponse(
            access_token=create_access_token(
                user_id, self.settings.jwt_secret, self.settings.access_token_minutes
            ),
            refresh_token=refresh_token,
            expires_in=self.settings.access_token_minutes * 60,
        )

    def _revoke_family(self, family_id: UUID) -> None:
        self.session.execute(
            update(RefreshToken)
            .where(
                RefreshToken.family_id == family_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=utc_now())
        )
        self.session.commit()
