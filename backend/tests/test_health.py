from starlette.requests import Request

from app.api.routes.health import health_check
from app.api.routes.health import router as health_router
from app.core.config import Settings
from app.main import create_app


def test_health_endpoint_returns_service_metadata() -> None:
    app = create_app(Settings(environment="test"))
    request = Request({"type": "http", "app": app})

    response = health_check(request)

    assert response.model_dump() == {
        "status": "ok",
        "service": "Mueblería Iván API",
        "version": "0.1.0",
        "environment": "test",
    }


def test_health_endpoint_accepts_get_and_head() -> None:
    health_routes = [
        route for route in health_router.routes if getattr(route, "path", None) == "/health"
    ]

    assert {frozenset(route.methods) for route in health_routes} == {
        frozenset({"GET"}),
        frozenset({"HEAD"}),
    }


def test_openapi_and_documentation_are_available() -> None:
    app = create_app(Settings(environment="test"))
    schema = app.openapi()

    assert "/health" in schema["paths"]
    assert set(schema["paths"]["/health"]) == {"get"}
    assert app.docs_url == "/docs"
    assert app.openapi_url == "/openapi.json"
