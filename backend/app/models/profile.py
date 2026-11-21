"""Read model for roles; the SQL migration remains the source of truth.

Columns must match app.profiles as defined in docs/BASE_DATOS.md.
Do NOT add columns here that are not in the agreed migration contract.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import ENUM
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

    # This enum is created by the Supabase migration, not by SQLAlchemy.
    role: Mapped[str] = mapped_column(
        ENUM("customer", "operator", "admin", name="user_role", schema="app", create_type=False),
        nullable=False,
        server_default=text("'customer'::app.user_role"),
    )

    # Whether the account is allowed to operate; set false to soft-ban
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))

    # Optional display fields – populated by the user or by the admin
    full_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Audit timestamps managed by a DB trigger (see migration)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("timezone('utc', now())"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("timezone('utc', now())"),
    )
