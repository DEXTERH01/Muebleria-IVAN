"""SQLAlchemy model for app.order_items.

Immutable snapshot of approved product configuration and pricing.
Once created, rows are never updated — the snapshot survives catalog changes.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class OrderItem(Base):
    """Maps to app.order_items – immutable line items for an approved order."""

    __tablename__ = "order_items"
    __table_args__ = {"schema": "app"}

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    order_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("app.orders.id", ondelete="RESTRICT"),
        nullable=False,
    )

    source_quote_item_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("app.quote_items.id", ondelete="RESTRICT"),
        nullable=True,
    )
    product_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("app.products.id", ondelete="RESTRICT"),
        nullable=True,
    )
    product_name_snapshot: Mapped[str] = mapped_column(Text, nullable=False)

    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    # Canonical dimensions in millimeters (RN-04)
    width_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    height_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    depth_mm: Mapped[int] = mapped_column(Integer, nullable=False)

    # Pricing in PEN céntimos
    configuration_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    unit_price_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    line_total_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
