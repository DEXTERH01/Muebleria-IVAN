"""Supabase JWT verification and database-backed application authorization."""

from dataclasses import dataclass, field
from datetime import datetime
from functools import lru_cache
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from jwt.exceptions import PyJWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.models.profile import Profile

bearer = HTTPBearer(auto_error=False)
ALGORITHMS = ["RS256", "ES256"]


@dataclass(frozen=True)
class CurrentUser:
    user_id: UUID
    role: str
    full_name: str | None = field(default=None)
    phone: str | None = field(default=None)
    created_at: datetime | None = field(default=None)


def unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Se requiere una sesión válida.",
        headers={"WWW-Authenticate": "Bearer"},
    )


@lru_cache(maxsize=8)
def _jwks_client(url: str) -> PyJWKClient:
    return PyJWKClient(url, cache_jwk_set=True, lifespan=300)


def verify_token(token: str, settings: Settings) -> UUID:
    if not settings.supabase_issuer or not settings.supabase_jwks_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase Auth no está configurado.",
        )
    try:
        key = _jwks_client(settings.supabase_jwks_url).get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            key.key,
            algorithms=ALGORITHMS,
            audience=settings.supabase_jwt_audience,
            issuer=settings.supabase_issuer,
            options={"require": ["sub", "exp", "iat", "aud", "iss"]},
        )
        if claims.get("role") != "authenticated":
            raise unauthorized()
        return UUID(claims["sub"])
    except (PyJWTError, ValueError, TypeError) as exc:
        raise unauthorized() from exc


def get_current_identity(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UUID:
    if credentials is None:
        raise unauthorized()
    return verify_token(credentials.credentials, settings)


def get_current_user(
    user_id: Annotated[UUID, Depends(get_current_identity)],
    session: Annotated[Session, Depends(get_session)],
) -> CurrentUser:
    row = session.execute(
        select(
            Profile.role,
            Profile.active,
            Profile.full_name,
            Profile.phone,
            Profile.created_at,
        ).where(Profile.user_id == user_id)
    ).one_or_none()
    if row is None or not row.active:
        raise HTTPException(status_code=403, detail="Perfil deshabilitado o inexistente.")
    return CurrentUser(
        user_id=user_id,
        role=row.role,
        full_name=row.full_name,
        phone=row.phone,
        created_at=row.created_at,
    )


def require_roles(*allowed_roles: str):
    def dependency(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
        if user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="No tienes permiso para esta operación.")
        return user

    return dependency
