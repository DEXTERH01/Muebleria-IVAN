"""SQLAlchemy model for app.predictions.

Stores every inference request so actual outcomes can be compared later,
allowing reproducible metric calculations (RN-10, docs/PLAN_MAESTRO.md § ML).
Input features must not contain PII — only derived numeric/categorical values.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class Prediction(Base):
    """Maps to app.predictions – inference log for regression and classification."""

    __tablename__ = "predictions"
    __table_args__ = {"schema": "app"}

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    model_version_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("app.model_versions.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # What entity this prediction is about
    entity_type: Mapped[str] = mapped_column(Text, nullable=False)
    entity_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), nullable=False)

    # Non-PII feature snapshot used as input (for reproducibility)
    input_summary: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Raw prediction output (days, probability, cluster label, etc.)
    output: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Confidence score 0.0–1.0 (optional, model-dependent)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(6, 5), nullable=True)

    # Filled in after the actual outcome is known (for metrics)
    actual_outcome: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    predicted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
