"""SQLAlchemy model for app.payments.

Payments are immutable financial records. A reversal creates a new row linked
to the original through reverses_payment_id. amount_minor > 0 is enforced by DB CHECK.
Idempotency is enforced by the unique index on idempotency_key.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import BigInteger, DateTime, ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import CHAR, ENUM
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class Payment(Base):
    """Maps to app.payments – immutable payment records for orders."""

    __tablename__ = "payments"
    __table_args__ = {"schema": "app"}

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    order_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("app.orders.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Amount in PEN céntimos; CHECK amount_minor > 0 in migration
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(CHAR(3), nullable=False, server_default="'PEN'")

    # Method values: cash / bank_transfer / card / other
    method: Mapped[str] = mapped_column(
        ENUM("cash", "bank_transfer", "card", "other", name="payment_method",
             schema="app", create_type=False),
        nullable=False,
    )
    reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Status values: recorded / voided
    status: Mapped[str] = mapped_column(
        ENUM("recorded", "voided", name="payment_status", schema="app", create_type=False),
        nullable=False,
        server_default=text("'recorded'::app.payment_status"),
    )

    # Unique key to prevent duplicate registrations (RN-07, RN-08)
    idempotency_key: Mapped[str] = mapped_column(
        Text, nullable=False, unique=True
    )

    # Who registered the payment
    actor_user_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("app.profiles.user_id", ondelete="SET NULL"),
        nullable=True,
    )
    reverses_payment_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("app.payments.id", ondelete="RESTRICT"),
        nullable=True,
        unique=True,
    )
    # Private voucher asset (Cloudinary)
    voucher_asset_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("app.media_assets.id", ondelete="RESTRICT"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
