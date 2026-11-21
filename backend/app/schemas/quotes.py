"""Quote persistence and workflow contracts."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from app.schemas.common import ApiModel
from app.schemas.pricing import EstimateItemRequest, PricingBreakdownData, SelectedOptionData

QuoteStatus = Literal[
    "draft",
    "submitted",
    "reviewing",
    "approved",
    "rejected",
    "expired",
    "converted",
]


class QuoteCreateRequest(ApiModel):
    contact_name: str = Field(min_length=2, max_length=160)
    contact_email: str | None = Field(default=None, max_length=320)
    contact_phone: str | None = Field(default=None, min_length=6, max_length=40)
    items: list[EstimateItemRequest] = Field(min_length=1, max_length=20)

    @field_validator("contact_email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
            raise ValueError("contactEmail no tiene un formato válido.")
        return normalized

    @field_validator("contact_phone")
    @classmethod
    def normalize_phone(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

    @model_validator(mode="after")
    def validate_contact(self) -> "QuoteCreateRequest":
        if not self.contact_email and not self.contact_phone:
            raise ValueError("Debe proporcionar contactEmail o contactPhone.")
        return self


class QuoteItemData(ApiModel):
    id: UUID
    product_id: UUID
    product_name: str
    quantity: int
    width_mm: int
    height_mm: int
    depth_mm: int
    material: SelectedOptionData | None
    finish: SelectedOptionData | None
    accessories: list[SelectedOptionData]
    configuration: dict[str, object]
    base_price_minor: int
    breakdown: PricingBreakdownData
    line_total_minor: int


class QuoteData(ApiModel):
    id: UUID
    code: str
    status: QuoteStatus
    currency: str
    contact_name: str
    contact_email: str | None
    contact_phone: str | None
    subtotal_minor: int
    adjustments_minor: int
    total_minor: int
    deposit_minor: int
    expires_at: datetime
    version: int
    created_at: datetime
    updated_at: datetime
    items: list[QuoteItemData]


class QuoteResponse(ApiModel):
    data: QuoteData


class QuoteStatusUpdateRequest(ApiModel):
    status: Literal["reviewing", "approved", "rejected", "expired"]
    expected_version: int = Field(gt=0)
