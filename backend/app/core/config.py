from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
Environment = Literal["local", "test", "preview", "demo", "production"]
CloudinaryAlgorithm = Literal["sha1", "sha256"]
DEMO_SUPABASE_URL = "https://uyntocgzizflkpdlhtgp.supabase.co"


class Settings(BaseSettings):
    app_name: str = "Mueblería Iván API"
    app_version: str = "0.1.0"
    environment: Environment = "local"
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    database_url: str | None = None
    supabase_url: str | None = None
    supabase_secret_key: SecretStr | None = None
    supabase_invite_redirect_url: str = (
        "https://muebleria-ivan.pages.dev/restablecer-contrasena"
    )
    supabase_jwt_audience: str = "authenticated"
    cloudinary_cloud_name: str | None = None
    cloudinary_api_key: str | None = None
    cloudinary_api_secret: str | None = None
    cloudinary_signature_algorithm: CloudinaryAlgorithm = "sha1"
    groq_api_key: str | None = None
    groq_model: str = "openai/gpt-oss-20b"
    groq_timeout_seconds: float = Field(default=12.0, gt=0, le=30)
    assistant_requests_per_minute: int = Field(default=10, ge=1, le=60)

    @model_validator(mode="after")
    def configure_demo_supabase(self) -> "Settings":
        if self.environment == "demo" and not self.supabase_url:
            self.supabase_url = DEMO_SUPABASE_URL
        return self

    @property
    def supabase_issuer(self) -> str | None:
        return f"{self.supabase_url.rstrip('/')}/auth/v1" if self.supabase_url else None

    @property
    def supabase_jwks_url(self) -> str | None:
        return f"{self.supabase_issuer}/.well-known/jwks.json" if self.supabase_issuer else None

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        env_prefix="MUEBLERIA_",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
