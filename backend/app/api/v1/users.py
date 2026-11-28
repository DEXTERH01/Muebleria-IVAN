"""Administrator-only team invitations and role assignment."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.core.security import CurrentUser, require_roles
from app.services.user_invitation import UserInvitationError, invite_user

router = APIRouter(prefix="/users", tags=["users"])


def _camel(field_name: str) -> str:
    first, *rest = field_name.split("_")
    return first + "".join(part.title() for part in rest)


class UserInvitationRequest(BaseModel):
    model_config = ConfigDict(alias_generator=_camel, populate_by_name=True)

    email: str = Field(min_length=5, max_length=254)
    full_name: str = Field(min_length=2, max_length=120)
    role: Literal["customer", "operator", "admin"]

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        email = value.strip().lower()
        local, separator, domain = email.partition("@")
        if not separator or not local or "." not in domain or domain.startswith("."):
            raise ValueError("Ingresa un correo electrónico válido.")
        return email

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, value: str) -> str:
        name = " ".join(value.split())
        if len(name) < 2:
            raise ValueError("Ingresa el nombre completo.")
        return name


class UserInvitationData(BaseModel):
    model_config = ConfigDict(alias_generator=_camel, populate_by_name=True)

    email: str
    full_name: str
    role: str


class UserInvitationResponse(BaseModel):
    data: UserInvitationData
    message: str = "Invitación enviada por correo."


@router.post("/invitations", response_model=UserInvitationResponse, status_code=201)
async def create_user_invitation(
    request: UserInvitationRequest,
    user: Annotated[CurrentUser, Depends(require_roles("admin"))],
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserInvitationResponse:
    try:
        data = await invite_user(
            email=request.email,
            full_name=request.full_name,
            role=request.role,
            actor_user_id=user.user_id,
            session=session,
            settings=settings,
        )
    except UserInvitationError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message) from error
    return UserInvitationResponse(data=UserInvitationData(**data))
