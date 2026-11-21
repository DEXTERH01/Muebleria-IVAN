from app.core.config import Settings


def test_settings_are_typed() -> None:
    settings = Settings(
        environment="test",
        cors_origins=["http://localhost:4173"],
    )

    assert settings.environment == "test"
    assert settings.cors_origins == ["http://localhost:4173"]
    assert settings.api_v1_prefix == "/api/v1"
