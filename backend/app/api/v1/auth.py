"""Minimal protected endpoint to validate the complete auth dependency chain."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from app.core.security import CurrentUser, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


class MeData(BaseModel):
    model_config = ConfigDict(
        alias_generator=lambda field: "userId" if field == "user_id" else field,
        populate_by_name=True,
    )

    user_id: UUID
    role: str


class MeResponse(BaseModel):
    data: MeData


@router.get("/me", response_model=MeResponse)
def me(user: Annotated[CurrentUser, Depends(get_current_user)]) -> MeResponse:
    return MeResponse(data=MeData(user_id=user.user_id, role=user.role))
