"""SQLAlchemy model for app.customers.

Customers can exist before creating a Supabase Auth account (operator-created).
The migration owns CHECK constraints (email or phone required) and indexes.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base
from app.models.types import ExtensionCITEXT


class Customer(Base):
    """Maps to app.customers – contact data for order and quote owners."""

    __tablename__ = "customers"
    __table_args__ = {"schema": "app"}

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    # Optional link to an authenticated user; nullable for operator-created contacts
    profile_user_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("app.profiles.user_id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
    )
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str | None] = mapped_column(ExtensionCITEXT(), nullable=True)
    phone: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_number: Mapped[str | None] = mapped_column(Text, nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    district: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("timezone('utc', now())")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("timezone('utc', now())")
    )
