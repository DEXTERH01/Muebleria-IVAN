from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.api.v1.auth import me
from app.core.config import Settings
from app.core.security import (
    get_current_identity,
    get_current_user,
    require_roles,
    verify_token,
)


def test_verify_token_accepts_valid_supabase_access_token(monkeypatch: pytest.MonkeyPatch) -> None:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    monkeypatch.setattr(
        "app.core.security._jwks_client",
        lambda _: SimpleNamespace(
            get_signing_key_from_jwt=lambda _: SimpleNamespace(key=key.public_key())
        ),
    )
    settings = Settings(environment="test", supabase_url="https://project.supabase.co")
    user_id = uuid4()
    now = datetime.now(UTC)
    claims = {
        "sub": str(user_id),
        "aud": "authenticated",
        "iss": settings.supabase_issuer,
        "role": "authenticated",
        "iat": now,
        "exp": now + timedelta(minutes=5),
    }
    token = jwt.encode(claims, key, algorithm="RS256")

    assert verify_token(token, settings) == user_id

    for change in (
        {"aud": "wrong"},
        {"iss": "https://wrong.supabase.co/auth/v1"},
        {"exp": now - timedelta(seconds=1)},
        {"role": "service_role"},
    ):
        invalid = jwt.encode(claims | change, key, algorithm="RS256")
        with pytest.raises(HTTPException) as error:
            verify_token(invalid, settings)
        assert error.value.status_code == 401


class FakeSession:
    def __init__(self, role: str, active: bool = True) -> None:
        self.profile = SimpleNamespace(role=role, active=active)

    def execute(self, _statement: object) -> "FakeSession":
        return self

    def one_or_none(self) -> SimpleNamespace:
        return self.profile


@pytest.mark.parametrize(
    ("role", "allowed"),
    [("admin", True), ("operator", False), ("customer", False)],
)
def test_role_dependency_uses_database_profile(role: str, allowed: bool) -> None:
    user_id = uuid4()
    user = get_current_user(user_id, FakeSession(role))
    dependency = require_roles("admin")
    if allowed:
        assert dependency(user) == user
    else:
        with pytest.raises(HTTPException) as error:
            dependency(user)
        assert error.value.status_code == 403


def test_missing_bearer_is_rejected() -> None:
    with pytest.raises(HTTPException) as error:
        get_current_identity(None, Settings(environment="test"))
    assert error.value.status_code == 401
    assert error.value.headers == {"WWW-Authenticate": "Bearer"}


def test_disabled_profile_is_rejected() -> None:
    with pytest.raises(HTTPException) as error:
        get_current_user(uuid4(), FakeSession("admin", active=False))
    assert error.value.status_code == 403


def test_me_returns_profile_role_and_camel_case_id() -> None:
    user_id = uuid4()
    user = get_current_user(user_id, FakeSession("customer"))
    assert me(user).model_dump(mode="json", by_alias=True) == {
        "data": {"userId": str(user_id), "role": "customer"}
    }


def test_unconfigured_auth_rejects_presented_token() -> None:
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")
    with pytest.raises(HTTPException) as error:
        get_current_identity(credentials, Settings(environment="test"))
    assert error.value.status_code == 503
