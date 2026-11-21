"""SQLAlchemy model for app.delivery_locations.

Provides address nodes for A* route optimization demonstrations.
Coordinate range checks are enforced by DB constraints in the migration.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class DeliveryLocation(Base):
    """Maps to app.delivery_locations – delivery addresses linked to customers."""

    __tablename__ = "delivery_locations"
    __table_args__ = {"schema": "app"}

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    customer_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("app.customers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    label: Mapped[str] = mapped_column(Text, nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    district: Mapped[str] = mapped_column(Text, nullable=False)
    reference: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Coordinates validated by CHECK in migration (lat -90..90, lon -180..180)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
