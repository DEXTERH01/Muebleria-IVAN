"""ORM mappings for catalog and versioned pricing rules."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import CITEXT, JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Product(Base):
    __tablename__ = "products"
    __table_args__ = {"schema": "app"}

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    slug: Mapped[str] = mapped_column(CITEXT(), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    category: Mapped[str] = mapped_column(Text, nullable=False)
    base_price_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    min_production_days: Mapped[int] = mapped_column(Integer, nullable=False)
    max_production_days: Mapped[int] = mapped_column(Integer, nullable=False)
    min_width_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    max_width_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    min_height_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    max_height_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    min_depth_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    max_depth_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProductImage(Base):
    __tablename__ = "product_images"
    __table_args__ = {"schema": "app"}

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    product_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("app.products.id"), nullable=False
    )
    public_id: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    secure_url: Mapped[str] = mapped_column(Text, nullable=False)
    alt_text: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Material(Base):
    __tablename__ = "materials"
    __table_args__ = {"schema": "app"}

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(CITEXT(), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    price_adjustment_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    price_adjustment_percent: Mapped[Decimal] = mapped_column(
        Numeric(7, 4), nullable=False, default=Decimal(0)
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Finish(Base):
    __tablename__ = "finishes"
    __table_args__ = {"schema": "app"}

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(CITEXT(), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    price_adjustment_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    price_adjustment_percent: Mapped[Decimal] = mapped_column(
        Numeric(7, 4), nullable=False, default=Decimal(0)
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Accessory(Base):
    __tablename__ = "accessories"
    __table_args__ = {"schema": "app"}

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(CITEXT(), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    price_adjustment_minor: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    price_adjustment_percent: Mapped[Decimal] = mapped_column(
        Numeric(7, 4), nullable=False, default=Decimal(0)
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProductMaterial(Base):
    __tablename__ = "product_materials"
    __table_args__ = {"schema": "app"}

    product_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("app.products.id"), primary_key=True
    )
    material_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("app.materials.id"), primary_key=True
    )
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProductFinish(Base):
    __tablename__ = "product_finishes"
    __table_args__ = {"schema": "app"}

    product_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("app.products.id"), primary_key=True
    )
    finish_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("app.finishes.id"), primary_key=True
    )
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProductAccessory(Base):
    __tablename__ = "product_accessories"
    __table_args__ = {"schema": "app"}

    product_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("app.products.id"), primary_key=True
    )
    accessory_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("app.accessories.id"), primary_key=True
    )
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PricingRule(Base):
    __tablename__ = "pricing_rules"
    __table_args__ = {"schema": "app"}

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    conditions: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    operation: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[UUID | None] = mapped_column(PgUUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
