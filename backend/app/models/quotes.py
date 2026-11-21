"""ORM mappings for quote headers and immutable calculation snapshots."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import CITEXT, JSONB
from sqlalchemy.dialects.postgresql import ENUM as PgEnum
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

quote_status_enum = PgEnum(
    "draft",
    "submitted",
    "reviewing",
    "approved",
    "rejected",
    "expired",
    "converted",
    name="quote_status",
    schema="app",
    create_type=False,
)


class Quote(Base):
    __tablename__ = "quotes"
    __table_args__ = {"schema": "app"}

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(CITEXT(), unique=True, nullable=False)
    customer_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True))
    owner_user_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True))
    contact_name: Mapped[str] = mapped_column(Text, nullable=False)
    contact_email: Mapped[str | None] = mapped_column(CITEXT())
    contact_phone: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(quote_status_enum, nullable=False, default="draft")
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="PEN")
    subtotal_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    adjustments_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    total_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    deposit_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class QuoteItem(Base):
    __tablename__ = "quote_items"
    __table_args__ = {"schema": "app"}

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    quote_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("app.quotes.id"), nullable=False
    )
    product_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("app.products.id"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    width_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    height_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    depth_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    material_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("app.materials.id")
    )
    finish_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("app.finishes.id")
    )
    accessories: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    configuration: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    product_name_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    base_price_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    calculation_breakdown: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    line_total_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
