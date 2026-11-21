"""API contracts for advisory search algorithm executions."""

from typing import Literal
from uuid import UUID

from pydantic import Field

from app.schemas.common import ApiModel


class DeliveryOptimizationRequest(ApiModel):
    start: str = Field(min_length=1, max_length=100)
    stops: list[str] = Field(min_length=1, max_length=12)
    distances: dict[str, dict[str, float]]


class ProductionTaskRequest(ApiModel):
    task_id: str = Field(min_length=1, max_length=100)
    material: str = Field(min_length=1, max_length=100)
    duration_hours: float = Field(gt=0)
    due_in_hours: float = Field(ge=0)
    ready_in_hours: float = Field(default=0, ge=0)


class ProductionWeightsRequest(ApiModel):
    delay_days: float = Field(default=10, ge=0)
    material_changes: float = Field(default=3, ge=0)
    idle_hours: float = Field(default=2, ge=0)


class ProductionOptimizationRequest(ApiModel):
    tasks: list[ProductionTaskRequest] = Field(min_length=1, max_length=20)
    weights: ProductionWeightsRequest = Field(default_factory=ProductionWeightsRequest)
    random_seed: int = 2026
    restarts: int = Field(default=5, ge=0, le=50)
    max_iterations: int = Field(default=100, ge=1, le=10_000)


class OptimizationRunData(ApiModel):
    id: UUID
    algorithm: Literal["astar", "hill_climbing"]
    baseline: dict[str, object]
    result: dict[str, object]
    improvement: float
    duration_ms: int
    random_seed: int | None
    advisory: bool = True


class OptimizationRunResponse(ApiModel):
    data: OptimizationRunData
