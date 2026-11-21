"""Pricing request and response contracts."""

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from app.schemas.common import ApiModel


class EstimateItemRequest(ApiModel):
    product_id: UUID
    quantity: int = Field(default=1, ge=1, le=20)
    width_mm: int = Field(gt=0, le=10000)
    height_mm: int = Field(gt=0, le=10000)
    depth_mm: int = Field(gt=0, le=10000)
    material_id: UUID | None = None
    finish_id: UUID | None = None
    accessory_ids: list[UUID] = Field(default_factory=list, max_length=20)
    configuration: dict[str, object] = Field(default_factory=dict)

    @field_validator("accessory_ids")
    @classmethod
    def accessories_must_be_unique(cls, value: list[UUID]) -> list[UUID]:
        if len(value) != len(set(value)):
            raise ValueError("accessoryIds no puede contener valores duplicados.")
        return value


class QuoteEstimateRequest(ApiModel):
    items: list[EstimateItemRequest] = Field(min_length=1, max_length=20)


class SelectedOptionData(ApiModel):
    id: UUID
    code: str
    name: str
    adjustment_minor: int


class AppliedRuleData(ApiModel):
    id: UUID
    name: str
    version: int
    adjustment_minor: int


class PricingBreakdownData(ApiModel):
    reference_base_minor: int
    size_adjusted_base_minor: int
    material_minor: int
    finish_minor: int
    accessories_minor: int
    rules_minor: int
    unit_total_minor: int


class EstimateItemData(ApiModel):
    product_id: UUID
    product_name: str
    quantity: int
    width_mm: int
    height_mm: int
    depth_mm: int
    material: SelectedOptionData | None
    finish: SelectedOptionData | None
    accessories: list[SelectedOptionData]
    applied_rules: list[AppliedRuleData]
    breakdown: PricingBreakdownData
    line_total_minor: int
    min_production_days: int
    max_production_days: int


class QuoteEstimateData(ApiModel):
    currency: str = "PEN"
    subtotal_minor: int
    adjustments_minor: int
    total_minor: int
    deposit_minor: int
    items: list[EstimateItemData]


class QuoteEstimateResponse(ApiModel):
    data: QuoteEstimateData


class PricingConditionRequest(ApiModel):
    field: Literal["volumeMm3", "quantity", "category", "subtotalMinor"]
    operator: Literal[
        "equals",
        "greater_than",
        "greater_or_equal",
        "less_than",
        "less_or_equal",
        "in",
    ]
    value: int | float | str | list[str]

    @model_validator(mode="after")
    def validate_in_value(self) -> "PricingConditionRequest":
        if self.operator == "in" and not isinstance(self.value, list):
            raise ValueError("La operación in requiere una lista de valores.")
        return self


class PricingOperationRequest(ApiModel):
    type: Literal["percentage", "fixed_minor"]
    value: Decimal


class PricingRuleCreateRequest(ApiModel):
    name: str = Field(min_length=2, max_length=160)
    priority: int = Field(default=100, ge=0, le=10000)
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    condition: PricingConditionRequest
    operation: PricingOperationRequest
    active: bool = True

    @model_validator(mode="after")
    def validate_dates(self) -> "PricingRuleCreateRequest":
        if self.valid_from and self.valid_until and self.valid_until <= self.valid_from:
            raise ValueError("validUntil debe ser posterior a validFrom.")
        return self


class PricingRuleData(ApiModel):
    id: UUID
    name: str
    version: int
    priority: int
    valid_from: datetime
    valid_until: datetime | None
    condition: PricingConditionRequest
    operation: PricingOperationRequest
    active: bool
    created_by: UUID | None
    created_at: datetime


class PricingRuleListResponse(ApiModel):
    data: list[PricingRuleData]


class PricingRuleResponse(ApiModel):
    data: PricingRuleData
