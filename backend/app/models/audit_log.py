"""SQLAlchemy model for app.audit_logs.

Append-only table. Records sensitive changes: role updates, price changes,
status transitions, payment registrations, reversals, and ML model activations.
IP addresses are masked (last octet removed) before storage.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class AuditLog(Base):
    """Maps to app.audit_logs – immutable change record for sensitive actions."""

    __tablename__ = "audit_logs"
    __table_args__ = {"schema": "app"}

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )

    # Who performed the action (None for automated/system actions)
    actor_user_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("app.profiles.user_id", ondelete="SET NULL"),
        nullable=True,
    )

    # Dot-separated action name e.g. "order.status_changed", "payment.voided"
    action: Mapped[str] = mapped_column(Text, nullable=False)

    # Entity type e.g. "order", "payment", "product", "user_role"
    entity_type: Mapped[str] = mapped_column(Text, nullable=False)
    entity_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)

    # JSON snapshots — keep minimal to avoid storing PII
    old_values: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    new_values: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Correlates with X-Request-ID response header
    request_id: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True), nullable=True)

    # Partial IP for context — last octet masked (e.g. "192.168.1.x")
    ip_hash: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Append-only: set once at insert
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
