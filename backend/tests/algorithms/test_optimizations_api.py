from uuid import uuid4

from app.api.v1.optimizations import optimize_delivery, optimize_production
from app.core.security import CurrentUser
from app.models.optimization_run import OptimizationRun
from app.schemas.optimization import (
    DeliveryOptimizationRequest,
    ProductionOptimizationRequest,
)


class FakeSession:
    def __init__(self) -> None:
        self.added: list[object] = []
        self.commits = 0
        self.rollbacks = 0

    def add(self, value: object) -> None:
        if getattr(value, "id", None) is None:
            value.id = uuid4()
        self.added.append(value)

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1

    def refresh(self, _value: object) -> None:
        return None


def _staff() -> CurrentUser:
    return CurrentUser(user_id=uuid4(), role="operator")


def test_delivery_endpoint_persists_advisory_astar_result() -> None:
    session = FakeSession()
    payload = DeliveryOptimizationRequest(
        start="taller",
        stops=["a", "b", "c"],
        distances={
            "taller": {"taller": 0, "a": 5, "b": 2, "c": 7},
            "a": {"taller": 5, "a": 0, "b": 2, "c": 2},
            "b": {"taller": 2, "a": 2, "b": 0, "c": 5},
            "c": {"taller": 7, "a": 2, "b": 5, "c": 0},
        },
    )

    response = optimize_delivery(payload, _staff(), session)  # type: ignore[arg-type]

    run = next(item for item in session.added if isinstance(item, OptimizationRun))
    assert response.data.advisory is True
    assert response.data.algorithm == "astar"
    assert run.result["route"] == ["taller", "b", "a", "c"]
    assert run.result["exploredNodes"] > 0
    assert session.commits == 1


def test_production_endpoint_persists_seeded_hill_climbing_result() -> None:
    session = FakeSession()
    payload = ProductionOptimizationRequest(
        tasks=[
            {
                "taskId": "flexible",
                "material": "metal",
                "durationHours": 8,
                "dueInHours": 48,
            },
            {
                "taskId": "urgente",
                "material": "madera",
                "durationHours": 8,
                "dueInHours": 8,
            },
            {
                "taskId": "madera-2",
                "material": "madera",
                "durationHours": 8,
                "dueInHours": 24,
            },
        ],
        randomSeed=99,
        restarts=4,
    )

    response = optimize_production(payload, _staff(), session)  # type: ignore[arg-type]

    run = next(item for item in session.added if isinstance(item, OptimizationRun))
    assert response.data.advisory is True
    assert response.data.algorithm == "hill_climbing"
    assert run.random_seed == 99
    assert run.result["sequence"][0] == "urgente"
    assert run.result["stopReason"] in {"local_optimum", "max_iterations"}
    assert session.commits == 1
