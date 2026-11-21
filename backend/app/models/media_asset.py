"""SQLAlchemy model for app.media_assets.

Tracks Cloudinary identifiers and verified upload metadata. Public image URLs
are derived from the stored identifier; private voucher links are generated
on demand and expire after a short interval.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM, JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class MediaAsset(Base):
    """Maps to app.media_assets – Cloudinary file metadata."""

    __tablename__ = "media_assets"
    __table_args__ = (UniqueConstraint("provider", "external_id"), {"schema": "app"})

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    # Cloudinary public_id (used to build URLs and sign uploads)
    external_id: Mapped[str] = mapped_column(Text, nullable=False)

    # Type values: image / document / video
    media_type: Mapped[str] = mapped_column(Text, nullable=False)

    # Access values: public / private (private = signed URL only)
    access: Mapped[str] = mapped_column(
        ENUM("public", "private", name="asset_access", schema="app", create_type=False),
        nullable=False,
    )

    # Who uploaded the file (nullable for catalog images loaded by scripts)
    owner_user_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("app.profiles.user_id", ondelete="SET NULL"),
        nullable=True,
    )

    # SHA-256 of the original file for deduplication
    content_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(
        "metadata", JSONB, nullable=False, server_default="'{}'::jsonb"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
