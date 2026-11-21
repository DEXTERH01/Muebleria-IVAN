"""Tests for the /api/v1/auth/me endpoint handler.

These tests call the handler function directly with stubbed dependencies
so they run without a live database, Supabase project, or HTTP server.
Integration tests against a real Supabase instance are deferred to
Fase 2 completion (see docs/SEGUIMIENTO.md).
"""

from uuid import uuid4

import pytest

from app.api.v1.auth import MeData, MeResponse, me
from app.core.security import CurrentUser


def _user(role: str, full_name: str | None = None, phone: str | None = None) -> CurrentUser:
    return CurrentUser(user_id=uuid4(), role=role, full_name=full_name, phone=phone)


def test_me_returns_user_id_and_role() -> None:
    uid = uuid4()
    user = CurrentUser(user_id=uid, role="admin")
    result = me(user)
    assert result.data.user_id == uid
    assert result.data.role == "admin"


def test_me_serialises_user_id_as_camel_case() -> None:
    uid = uuid4()
    user = CurrentUser(user_id=uid, role="customer")
    body = me(user).model_dump(mode="json", by_alias=True)
    assert body["data"]["userId"] == str(uid)
    assert "user_id" not in body["data"]


def test_me_includes_full_name_when_set() -> None:
    user = _user("customer", full_name="Ana López")
    result = me(user)
    assert result.data.full_name == "Ana López"


def test_me_includes_phone_when_set() -> None:
    user = _user("operator", phone="+51999000111")
    result = me(user)
    assert result.data.phone == "+51999000111"


def test_me_has_null_optional_fields_when_absent() -> None:
    user = _user("operator")
    result = me(user)
    assert result.data.full_name is None
    assert result.data.phone is None
    assert result.data.created_at is None


@pytest.mark.parametrize("role", ["customer", "operator", "admin"])
def test_me_accepts_all_valid_roles(role: str) -> None:
    result = me(_user(role))
    assert result.data.role == role


def test_me_response_matches_contract_envelope() -> None:
    """The response must follow the {data: {...}} envelope from docs/PLAN_MAESTRO.md."""
    result = me(_user("admin", full_name="Iván"))
    assert isinstance(result, MeResponse)
    assert isinstance(result.data, MeData)
