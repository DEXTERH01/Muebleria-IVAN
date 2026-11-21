"""SQLAlchemy model for app.model_versions.

Tracks trained ML models for regression, classification and clustering.
Only one version per problem may be active at a time (partial unique index
in migration). The app layer loads only the active model on startup.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import ENUM, JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func, text

from app.models.base import Base


class ModelVersion(Base):
    """Maps to app.model_versions – versioned ML model registry."""

    __tablename__ = "model_versions"
    __table_args__ = {"schema": "app"}

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )

    problem: Mapped[str] = mapped_column(Text, nullable=False)

    # Algorithm name: random_forest / knn / svm / kmeans / dbscan / etc.
    algorithm: Mapped[str] = mapped_column(Text, nullable=False)

    version: Mapped[int] = mapped_column(Integer, nullable=False)

    # Filesystem path or hash of the serialised artifact (joblib/pickle)
    artifact_path: Mapped[str] = mapped_column(Text, nullable=False)
    artifact_hash: Mapped[str] = mapped_column(Text, nullable=False)

    # Hyperparameters used for this training run
    parameters: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="'{}'::jsonb")

    # Evaluation metrics: MAE, RMSE, R2, precision, recall, F1, etc.
    metrics: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="'{}'::jsonb")

    # Status: candidate / approved / active / retired
    # Partial unique index in migration: WHERE status = 'active'
    status: Mapped[str] = mapped_column(
        ENUM("candidate", "approved", "active", "retired", name="model_status",
             schema="app", create_type=False),
        nullable=False,
        server_default=text("'candidate'::app.model_status"),
    )

    created_by: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True), ForeignKey("app.profiles.user_id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
