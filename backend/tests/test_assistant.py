import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.api.v1 import assistant as assistant_route
from app.core.config import Settings
from app.schemas.assistant import AssistantChatRequest


def setup_function() -> None:
    assistant_route._request_times.clear()


def request() -> Request:
    return Request({"type": "http", "client": ("127.0.0.1", 12345), "headers": []})


def test_assistant_chat_uses_groq_without_exposing_its_key(monkeypatch) -> None:
    captured = {}

    def fake_reply(message: str, **kwargs) -> str:
        captured.update(message=message, **kwargs)
        return "La melamina RH es una opción práctica para zonas con humedad."

    monkeypatch.setattr(assistant_route, "groq_reply", fake_reply)
    response = assistant_route.assistant_chat(
        AssistantChatRequest(message="¿Qué material conviene para un mueble de baño?"),
        request(),
        Settings(environment="test", groq_api_key="gsk_test", groq_model="openai/gpt-oss-20b"),
    )

    assert response.model_dump(mode="json", by_alias=True) == {
        "data": {
            "message": "La melamina RH es una opción práctica para zonas con humedad.",
            "provider": "groq",
            "model": "openai/gpt-oss-20b",
        }
    }
    assert captured["api_key"] == "gsk_test"
    assert "gsk_test" not in response.model_dump_json()


def test_assistant_chat_falls_back_when_groq_is_not_configured() -> None:
    with pytest.raises(HTTPException) as raised:
        assistant_route.assistant_chat(
            AssistantChatRequest(message="Ayúdame a elegir un material"),
            request(),
            Settings(environment="test", groq_api_key=None),
        )

    assert raised.value.status_code == 503
    assert raised.value.detail == "El asistente generativo no está configurado."


def test_assistant_chat_limits_public_requests(monkeypatch) -> None:
    monkeypatch.setattr(assistant_route, "groq_reply", lambda *_args, **_kwargs: "Respuesta")
    settings = Settings(
        environment="test",
        groq_api_key="gsk_test",
        assistant_requests_per_minute=1,
    )
    first = assistant_route.assistant_chat(
        AssistantChatRequest(message="Primera consulta"), request(), settings
    )
    with pytest.raises(HTTPException) as raised:
        assistant_route.assistant_chat(
            AssistantChatRequest(message="Segunda consulta"), request(), settings
        )

    assert first.data.message == "Respuesta"
    assert raised.value.status_code == 429
