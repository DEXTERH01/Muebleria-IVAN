"""Protected auth endpoints: identity and role verification.

/api/v1/auth/me returns the authenticated user's profile fields that the
frontend needs without exposing PII that it does not need.
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from app.core.security import CurrentUser, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


def _camel(field: str) -> str:
    parts = field.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


class MeData(BaseModel):
    model_config = ConfigDict(alias_generator=_camel, populate_by_name=True)

    user_id: UUID
    role: str
    full_name: str | None = Field(default=None)
    phone: str | None = Field(default=None)
    created_at: datetime | None = Field(default=None)


class MeResponse(BaseModel):
    data: MeData


@router.get("/me", response_model=MeResponse, summary="Perfil del usuario autenticado")
def me(user: Annotated[CurrentUser, Depends(get_current_user)]) -> MeResponse:
    """Return the authenticated user's public profile fields.

    All fields are loaded by get_current_user in a single DB query so this
    handler requires no additional database access.
    """
    return MeResponse(
        data=MeData(
            user_id=user.user_id,
            role=user.role,
            full_name=user.full_name,
            phone=user.phone,
            created_at=user.created_at,
        )
    )
