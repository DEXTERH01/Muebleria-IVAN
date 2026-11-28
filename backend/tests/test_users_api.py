import asyncio
from unittest.mock import AsyncMock
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.users import router as users_router
from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.core.security import CurrentUser, get_current_user
from app.services.user_invitation import UserInvitationError, invite_user


class FakeSession:
    def __init__(self) -> None:
        self.profile = type("ProfileStub", (), {"role": "customer", "full_name": None})()
        self.added = []
        self.committed = False

    def get(self, _model, _user_id):
        return self.profile

    def add(self, value):
        self.added.append(value)

    def commit(self):
        self.committed = True


def _client(role: str = "admin") -> TestClient:
    app = FastAPI()
    app.include_router(users_router, prefix="/api/v1")
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        user_id=uuid4(), role=role, full_name="Dexter Peña"
    )
    app.dependency_overrides[get_session] = FakeSession
    app.dependency_overrides[get_settings] = lambda: Settings(_env_file=None)
    return TestClient(app)


def test_invitation_request_normalizes_email_and_name(monkeypatch) -> None:
    invitation = AsyncMock(
        return_value={"email": "dexter@example.com", "full_name": "Dexter Peña", "role": "admin"}
    )
    monkeypatch.setattr("app.api.v1.users.invite_user", invitation)
    response = _client().post(
        "/api/v1/users/invitations",
        json={"email": "  Dexter@Example.com ", "fullName": " Dexter   Peña ", "role": "admin"},
    )

    assert response.status_code == 201
    assert response.json()["data"] == {
        "email": "dexter@example.com",
        "fullName": "Dexter Peña",
        "role": "admin",
    }
    assert invitation.await_args.kwargs["email"] == "dexter@example.com"
    assert invitation.await_args.kwargs["full_name"] == "Dexter Peña"


def test_operator_cannot_invite_team_members() -> None:
    response = _client(role="operator").post(
        "/api/v1/users/invitations",
        json={"email": "ana@example.com", "fullName": "Ana López", "role": "operator"},
    )

    assert response.status_code == 403


def test_invite_requires_supported_role() -> None:
    response = _client().post(
        "/api/v1/users/invitations",
        json={"email": "ana@example.com", "fullName": "Ana López", "role": "owner"},
    )

    assert response.status_code == 422


def test_invite_user_sends_email_and_assigns_role(monkeypatch) -> None:
    invited_id = uuid4()

    class Response:
        status_code = 200

        def json(self):
            return {"id": str(invited_id)}

    class Client:
        def __init__(self, *, timeout):
            assert timeout == 20

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def post(self, url, *, params, headers, json):
            assert url == "https://supabase.example/auth/v1/invite"
            assert params == {"redirect_to": "https://shop.example/restablecer-contrasena"}
            assert headers["apikey"] == "secret-for-test"
            assert json == {"email": "ana@example.com", "data": {"full_name": "Ana López"}}
            return Response()

    monkeypatch.setattr("app.services.user_invitation.httpx.AsyncClient", Client)
    session = FakeSession()
    result = asyncio.run(
        invite_user(
            email="ana@example.com",
            full_name="Ana López",
            role="operator",
            actor_user_id=uuid4(),
            session=session,
            settings=Settings(
                _env_file=None,
                supabase_url="https://supabase.example",
                supabase_secret_key="secret-for-test",
                supabase_invite_redirect_url="https://shop.example/restablecer-contrasena",
            ),
        ),
    )

    assert result == {"email": "ana@example.com", "full_name": "Ana López", "role": "operator"}
    assert session.profile.role == "operator"
    assert session.profile.full_name == "Ana López"
    assert session.committed
    assert session.added[0].action == "user.invited"


def test_invite_user_requires_server_secret_before_network_call(monkeypatch) -> None:
    request = AsyncMock()
    monkeypatch.setattr("app.services.user_invitation.httpx.AsyncClient", request)

    try:
        asyncio.run(
            invite_user(
                email="ana@example.com",
                full_name="Ana López",
                role="customer",
                actor_user_id=uuid4(),
                session=FakeSession(),
                settings=Settings(_env_file=None),
            )
        )
    except UserInvitationError as error:
        assert error.status_code == 503
        assert "no están configuradas" in error.message
    else:
        raise AssertionError("Expected an invitation configuration error")

    request.assert_not_awaited()
