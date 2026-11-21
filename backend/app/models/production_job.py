"""SQLAlchemy model for app.production_jobs.

Stores scheduling data needed for Hill Climbing optimization and post-facto
performance measurement. One job per order stage.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class ProductionJob(Base):
    """Maps to app.production_jobs – per-stage scheduling and timing data."""

    __tablename__ = "production_jobs"
    __table_args__ = {"schema": "app"}

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    order_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("app.orders.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Stage mirrors order status values used during production
    stage: Mapped[str] = mapped_column(
        ENUM("confirmed", "materials_pending", "cutting", "assembly", "finishing",
             "ready", "delivered", "installed", "cancelled", name="order_status",
             schema="app", create_type=False),
        nullable=False,
    )

    # Priority 0-100: used as input weight for Hill Climbing
    priority: Mapped[int] = mapped_column(Integer, nullable=False, server_default="100")
    complexity: Mapped[Decimal] = mapped_column(
        Numeric(8, 3), nullable=False, server_default="1"
    )

    estimated_hours: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    actual_hours: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)

    planned_start_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    planned_end_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    actual_start_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    actual_end_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
