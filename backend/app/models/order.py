"""SQLAlchemy model for app.orders.

Amounts travel as bigint cents (minor units). Dimension fields use mm.
The API increments version under a row lock during status transitions.
"""

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import CHAR, BigInteger, Computed, Date, DateTime, ForeignKey, Integer, text
from sqlalchemy.dialects.postgresql import ENUM, JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base
from app.models.types import ExtensionCITEXT


class Order(Base):
    """Maps to app.orders – confirmed orders with payment tracking."""

    __tablename__ = "orders"
    __table_args__ = {"schema": "app"}

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    # Human-readable code e.g. PED-2026-0001; unique index in migration
    code: Mapped[str] = mapped_column(ExtensionCITEXT(), nullable=False, unique=True)

    quote_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("app.quotes.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    customer_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("app.customers.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Canonical states from docs/PLAN_MAESTRO.md
    status: Mapped[str] = mapped_column(
        ENUM("confirmed", "materials_pending", "cutting", "assembly", "finishing",
             "ready", "delivered", "installed", "cancelled", name="order_status",
             schema="app", create_type=False),
        nullable=False,
        server_default=text("'confirmed'::app.order_status"),
    )
    currency: Mapped[str] = mapped_column(
        CHAR(3), nullable=False, server_default="'PEN'"
    )

    # Monetary amounts in minor units (PEN céntimos)
    total_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    deposit_required_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    paid_minor: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=text("0")
    )
    balance_minor: Mapped[int] = mapped_column(
        BigInteger, Computed("total_minor - paid_minor", persisted=True)
    )

    # Dates
    promised_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    installed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Snapshot of delivery address at order creation (immutable after)
    delivery_address_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Optimistic concurrency lock; bumped on status change
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("1")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
