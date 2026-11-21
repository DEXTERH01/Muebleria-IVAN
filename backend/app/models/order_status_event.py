"""SQLAlchemy model for app.order_status_events.

Append-only history of order stage transitions. Never updated or deleted.
Provides the customer-facing timeline and audit trail for production.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class OrderStatusEvent(Base):
    """Maps to app.order_status_events – immutable transition log."""

    __tablename__ = "order_status_events"
    __table_args__ = {"schema": "app"}

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    order_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("app.orders.id", ondelete="RESTRICT"),
        nullable=False,
    )
    previous_status: Mapped[str | None] = mapped_column(
        ENUM("confirmed", "materials_pending", "cutting", "assembly", "finishing",
             "ready", "delivered", "installed", "cancelled", name="order_status",
             schema="app", create_type=False),
        nullable=True,
    )
    new_status: Mapped[str] = mapped_column(
        ENUM("confirmed", "materials_pending", "cutting", "assembly", "finishing",
             "ready", "delivered", "installed", "cancelled", name="order_status",
             schema="app", create_type=False),
        nullable=False,
    )

    # Who made the transition (nullable for system-generated events)
    actor_user_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("app.profiles.user_id", ondelete="SET NULL"),
        nullable=True,
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Append-only: created_at is set once and never modified
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
