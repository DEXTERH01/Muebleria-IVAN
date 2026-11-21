"""Pydantic schemas for Order API.

Canonical order states from docs/PLAN_MAESTRO.md:
confirmed → materials_pending → cutting → assembly → finishing → ready →
delivered → installed | cancelled

Money in céntimos (bigint); version field for optimistic concurrency.
"""

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

OrderStatus = Literal[
    "confirmed",
    "materials_pending",
    "cutting",
    "assembly",
    "finishing",
    "ready",
    "delivered",
    "installed",
    "cancelled",
]


def _camel(s: str) -> str:
    parts = s.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


_cfg = ConfigDict(alias_generator=_camel, populate_by_name=True, from_attributes=True)


class OrderOut(BaseModel):
    model_config = _cfg

    id: UUID
    code: str
    quote_id: UUID
    customer_id: UUID
    status: OrderStatus
    currency: str = "PEN"

    # Monetary amounts in PEN céntimos
    total_minor: int
    deposit_required_minor: int
    paid_minor: int
    balance_minor: int

    promised_date: date | None = Field(default=None)
    delivered_at: datetime | None = Field(default=None)
    installed_at: datetime | None = Field(default=None)
    version: int = Field(gt=0)
    created_at: datetime
    updated_at: datetime


class OrderStatusPatch(BaseModel):
    """Request body for PATCH /orders/{id}/status."""

    model_config = _cfg

    new_status: OrderStatus
    # Must match current order.version to prevent lost updates
    version: int = Field(gt=0)
    note: str | None = Field(default=None, max_length=500)


class DeliveryAddressSnapshot(BaseModel):
    """Address captured when an approved quote becomes an order."""

    model_config = _cfg

    address: str = Field(min_length=5, max_length=300)
    district: str = Field(min_length=2, max_length=100)
    reference: str | None = Field(default=None, max_length=300)


class QuoteConvertRequest(BaseModel):
    model_config = _cfg

    expected_quote_version: int = Field(gt=0)
    delivery_address: DeliveryAddressSnapshot
    promised_date: date | None = None


class OrderResponse(BaseModel):
    data: OrderOut


class OrderStatusEventOut(BaseModel):
    model_config = _cfg

    previous_status: OrderStatus | None
    new_status: OrderStatus
    note: str | None
    occurred_at: datetime


class OrderDetailOut(OrderOut):
    status_history: list[OrderStatusEventOut]


class OrderDetailResponse(BaseModel):
    data: OrderDetailOut


class OrderListResponse(BaseModel):
    data: list[OrderOut]
    total: int
    page: int
    page_size: int = Field(alias="pageSize")

    model_config = ConfigDict(populate_by_name=True)
