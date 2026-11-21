"""Pydantic schemas for Payment API.

Payments are immutable — no update schema. Reversal creates a new record.
Idempotency-Key is required as an HTTP header (not in the body schema).
Money in PEN céntimos (bigint). No floats.
"""

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

PaymentMethod = Literal["cash", "bank_transfer", "card", "other"]
PaymentStatus = Literal["recorded", "voided"]
Currency = Literal["PEN"]


def _camel(s: str) -> str:
    parts = s.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


_cfg = ConfigDict(alias_generator=_camel, populate_by_name=True)


class PaymentCreate(BaseModel):
    """Body for POST /orders/{order_id}/payments.

    Idempotency-Key must be provided as an HTTP header by the client.
    """

    model_config = _cfg

    # Amount in PEN céntimos; must be > 0 (service validates against balance)
    amount_minor: int = Field(..., gt=0)
    currency: Currency = "PEN"
    method: PaymentMethod
    reference: str | None = Field(default=None, max_length=200)
    payment_date: date
    voucher_asset_id: UUID | None = Field(default=None)


class PaymentVoidRequest(BaseModel):
    """Body for POST /payments/{payment_id}/void."""

    model_config = _cfg

    reason: str = Field(..., min_length=5, max_length=500)


class PaymentOut(BaseModel):
    model_config = _cfg

    id: UUID
    order_id: UUID
    amount_minor: int
    currency: Currency
    method: PaymentMethod
    reference: str | None = Field(default=None)
    payment_date: date
    status: PaymentStatus
    created_at: datetime | None = Field(default=None)


class PaymentResponse(BaseModel):
    data: PaymentOut


class PaymentListResponse(BaseModel):
    data: list[PaymentOut]
    total: int
    page: int
    page_size: int = Field(alias="pageSize")

    model_config = ConfigDict(populate_by_name=True)
