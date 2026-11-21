"""SQLAlchemy model for app.optimization_runs.

Records every execution of A* (delivery routing) and Hill Climbing (production
scheduling). Results are advisory — they never automatically change orders or
payments (RN-10, docs/PLAN_MAESTRO.md § Restricciones).
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.models.base import Base


class OptimizationRun(Base):
    """Maps to app.optimization_runs – algorithm execution log."""

    __tablename__ = "optimization_runs"
    __table_args__ = {"schema": "app"}

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )

    # Algorithm values: astar / hill_climbing
    algorithm: Mapped[str] = mapped_column(Text, nullable=False)

    # Input and output stored as JSON for display in the UI
    input_data: Mapped[dict] = mapped_column("input", JSONB, nullable=False)
    baseline: Mapped[dict] = mapped_column(JSONB, nullable=False)
    result: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Improvement percentage vs. baseline (shown in UI comparison)
    improvement: Mapped[Decimal] = mapped_column(Numeric(12, 5), nullable=False)

    # Random seed used (for Hill Climbing restarts reproducibility)
    random_seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)

    requested_by: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("app.profiles.user_id", ondelete="SET NULL"),
        nullable=True,
    )
    accepted: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
