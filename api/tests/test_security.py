"""Password/JWT security contracts using only synthetic credentials."""

from datetime import timedelta
from uuid import uuid4

import jwt
import pytest
from pydantic import ValidationError

from app.core.exceptions import AppError
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    new_refresh_token,
    refresh_hash,
    verify_password,
)
from app.schemas.auth import RegisterRequest
from app.services.auth_service import utc_now

SECRET = "test-only-" + "s" * 64


@pytest.mark.parametrize(
    "length,valid", [(9, False), (10, True), (128, True), (129, False)]
)
def test_registration_password_length_contract(length, valid):
    fields = {"email": "ana@example.com", "username": "Ana", "password": "x" * length}
    if valid:
        assert RegisterRequest(**fields).password == fields["password"]
    else:
        with pytest.raises(ValidationError):
            RegisterRequest(**fields)


@pytest.mark.parametrize("stored_hash", [None, "", "invalid-stored-hash"])
def test_missing_or_invalid_password_hash_never_authenticates(stored_hash):
    assert verify_password(stored_hash, "dummy-password-for-timing") is False


def test_password_hash_preserves_unicode_and_whitespace():
    password = "  senha longa com acentuação  "
    encoded = hash_password(password)
    assert encoded.startswith("$argon2id$")
    assert verify_password(encoded, password) is True
    assert verify_password(encoded, password.strip()) is False


def test_refresh_tokens_are_unique_opaque_and_only_hash_matches_storage():
    first, first_hash = new_refresh_token()
    second, second_hash = new_refresh_token()
    assert first != second
    assert len(first) == len(second) == 64
    assert first_hash == refresh_hash(first)
    assert second_hash == refresh_hash(second)
    assert first_hash != second_hash
    assert first not in first_hash


@pytest.mark.parametrize("missing", ["sub", "iat", "exp", "jti", "type"])
def test_access_requires_all_claims(missing):
    token = create_access_token(uuid4(), SECRET, 15)
    claims = jwt.decode(token, SECRET, algorithms=["HS256"])
    del claims[missing]
    malformed = jwt.encode(claims, SECRET, algorithm="HS256")
    with pytest.raises(AppError) as failure:
        decode_access_token(malformed, SECRET)
    assert failure.value.status_code == 401
    assert failure.value.code == "UNAUTHORIZED"


@pytest.mark.parametrize(
    "claim,value",
    [
        ("type", "refresh"),
        ("sub", "not-a-uuid"),
        ("iat", float("inf")),
        ("exp", float("inf")),
        ("iat", float("nan")),
        ("exp", None),
        ("iat", utc_now().timestamp() + 3600),
    ],
)
def test_malformed_or_future_access_claims_fail_closed(claim, value):
    claims = {
        "sub": str(uuid4()),
        "iat": utc_now().timestamp(),
        "exp": (utc_now() + timedelta(minutes=15)).timestamp(),
        "jti": str(uuid4()),
        "type": "access",
    }
    claims[claim] = value
    token = jwt.encode(claims, SECRET, algorithm="HS256")
    with pytest.raises(AppError) as failure:
        decode_access_token(token, SECRET)
    assert failure.value.status_code == 401


def test_unsigned_access_is_rejected():
    valid = create_access_token(uuid4(), SECRET, 15)
    claims = jwt.decode(valid, SECRET, algorithms=["HS256"])
    unsigned = jwt.encode(claims, "", algorithm="none")
    with pytest.raises(AppError) as failure:
        decode_access_token(unsigned, SECRET)
    assert failure.value.status_code == 401
