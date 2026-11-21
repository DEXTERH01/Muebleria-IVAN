"""Request-scoped SQLAlchemy sessions; Supabase SQL migrations own the schema."""

from collections.abc import Iterator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings


@lru_cache(maxsize=4)
def _engine(database_url: str) -> Engine:
    return create_engine(database_url, pool_pre_ping=True)


def get_session(settings: Annotated[Settings, Depends(get_settings)]) -> Iterator[Session]:
    database_url = settings.database_url
    if not database_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="La base de datos no está configurada.",
        )
    with Session(_engine(database_url)) as session:
        yield session
