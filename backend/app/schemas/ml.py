"""Contracts for advisory ML inference and model metadata."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.schemas.common import ApiModel


class OrderFeatures(ApiModel):
    width_mm: int = Field(ge=100, le=10_000)
    height_mm: int = Field(ge=100, le=10_000)
    depth_mm: int = Field(ge=100, le=5_000)
    accessory_count: int = Field(ge=0, le=100)
    item_count: int = Field(ge=1, le=100)
    complexity_score: int = Field(ge=1, le=5)
    workshop_load: int = Field(ge=0, le=500)
    quoted_total_minor: int = Field(ge=0)
    promised_days: int = Field(ge=1, le=365)
    customer_frequency: int = Field(ge=1)
    category: str = Field(min_length=1, max_length=100)
    material: str = Field(min_length=1, max_length=100)
    district: str = Field(min_length=1, max_length=100)


class OrderInferenceRequest(OrderFeatures):
    order_id: UUID


class InferenceData(ApiModel):
    prediction_id: UUID
    problem: Literal["production_days", "delay_risk"]
    algorithm: str
    model_version: int
    output: dict[str, object]
    confidence: float | None
    fallback_used: bool
    advisory: bool = True
    data_label: Literal["Datos de prueba"] = "Datos de prueba"


class InferenceResponse(ApiModel):
    data: InferenceData


class ModelVersionData(ApiModel):
    id: UUID
    problem: str
    algorithm: str
    version: int
    artifact_hash: str
    parameters: dict[str, object]
    metrics: dict[str, object]
    status: str
    created_at: datetime


class ModelVersionListResponse(ApiModel):
    data: list[ModelVersionData]
