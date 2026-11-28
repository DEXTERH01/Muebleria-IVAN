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
    """In-memory session stub that returns a profile row without DB access."""

    def __init__(
        self,
        role: str,
        active: bool = True,
        full_name: str | None = None,
        phone: str | None = None,
        created_at: datetime | None = None,
    ) -> None:
        self._row = SimpleNamespace(
            role=role,
            active=active,
            full_name=full_name,
            phone=phone,
            created_at=created_at,
        )

    def execute(self, _statement: object) -> "FakeSession":
        return self

    def one_or_none(self) -> SimpleNamespace:
        return self._row


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


def test_require_roles_allows_multiple_roles() -> None:
    """require_roles must accept any role listed in the allow-list."""
    op_user = get_current_user(uuid4(), FakeSession("operator"))
    admin_user = get_current_user(uuid4(), FakeSession("admin"))
    dep = require_roles("operator", "admin")
    assert dep(op_user).role == "operator"
    assert dep(admin_user).role == "admin"
    with pytest.raises(HTTPException) as exc:
        dep(get_current_user(uuid4(), FakeSession("customer")))
    assert exc.value.status_code == 403


def test_missing_bearer_is_rejected() -> None:
    with pytest.raises(HTTPException) as error:
        get_current_identity(None, Settings(environment="test"))
    assert error.value.status_code == 401
    assert error.value.headers == {"WWW-Authenticate": "Bearer"}


def test_disabled_profile_is_rejected() -> None:
    with pytest.raises(HTTPException) as error:
        get_current_user(uuid4(), FakeSession("admin", active=False))
    assert error.value.status_code == 403


def test_missing_profile_is_rejected() -> None:
    """A user_id with no matching profile row must be rejected with 403."""

    class EmptySession(FakeSession):
        def one_or_none(self) -> None:  # type: ignore[override]
            return None

    with pytest.raises(HTTPException) as exc:
        get_current_user(uuid4(), EmptySession("customer"))
    assert exc.value.status_code == 403


def test_me_returns_profile_fields_in_camel_case() -> None:
    user_id = uuid4()
    user = get_current_user(user_id, FakeSession("customer", full_name="Ana López"))
    result = me(user).model_dump(mode="json", by_alias=True)
    assert result["data"]["userId"] == str(user_id)
    assert result["data"]["role"] == "customer"
    assert result["data"]["fullName"] == "Ana López"
    assert result["data"]["phone"] is None


def test_unconfigured_auth_rejects_presented_token() -> None:
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")
    with pytest.raises(HTTPException) as error:
        get_current_identity(credentials, Settings(_env_file=None, environment="test"))
    assert error.value.status_code == 503
