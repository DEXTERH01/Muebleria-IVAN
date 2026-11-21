"""Read model for roles; the SQL migration remains the source of truth.

Columns must match app.profiles as defined in docs/BASE_DATOS.md.
Do NOT add columns here that are not in the agreed migration contract.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Profile(Base):
    """Maps to app.profiles – identity and application role for auth.users."""

    __tablename__ = "profiles"
    __table_args__ = {"schema": "app"}

    # Primary key – mirrors auth.users.id from Supabase Auth
    user_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="CASCADE"), primary_key=True
    )

    # Role assigned by an admin; default set by DB trigger on first sign-in
    role: Mapped[str] = mapped_column(String(32), nullable=False, server_default="customer")

    # Whether the account is allowed to operate; set false to soft-ban
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))

    # Optional display fields – populated by the user or by the admin
    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Audit timestamps managed by a DB trigger (see migration)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
