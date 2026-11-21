"""Pydantic schemas for Customer API.

Money and measurement conventions from docs/PLAN_MAESTRO.md:
- camelCase in JSON, snake_case in Python
- Envelope: {data: ...} single / {data: [...], total, page, pageSize} list
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


def _camel(s: str) -> str:
    parts = s.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


_cfg = ConfigDict(alias_generator=_camel, populate_by_name=True, from_attributes=True)


class CustomerBase(BaseModel):
    model_config = _cfg

    full_name: str = Field(..., min_length=1, max_length=200)
    email: str | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=30)
    document_number: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None)
    district: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None)


class CustomerCreate(CustomerBase):
    """Customer contact is required by the database contract."""

    @model_validator(mode="after")
    def require_contact(self) -> "CustomerCreate":
        if not (self.email and self.email.strip()) and not (self.phone and self.phone.strip()):
            raise ValueError("Se requiere correo electrónico o teléfono.")
        return self


class CustomerUpdate(BaseModel):
    """All fields optional for PATCH semantics."""

    model_config = _cfg

    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    email: str | None = Field(default=None)
    phone: str | None = Field(default=None)
    document_number: str | None = Field(default=None)
    address: str | None = Field(default=None)
    district: str | None = Field(default=None)
    notes: str | None = Field(default=None)

    @model_validator(mode="after")
    def reject_empty_patch(self) -> "CustomerUpdate":
        if not self.model_fields_set:
            raise ValueError("Debe indicar al menos un campo para actualizar.")
        return self


class CustomerOut(CustomerBase):
    id: UUID
    profile_user_id: UUID | None = Field(default=None)
    created_at: datetime
    updated_at: datetime


class CustomerResponse(BaseModel):
    data: CustomerOut


class CustomerListResponse(BaseModel):
    data: list[CustomerOut]
    total: int
    page: int
    page_size: int = Field(alias="pageSize")

    model_config = ConfigDict(populate_by_name=True)
