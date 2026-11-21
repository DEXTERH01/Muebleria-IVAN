import pytest

from app.algorithms.hill_climbing import (
    ProductionTask,
    ProductionWeights,
    optimize_production_sequence,
    score_sequence,
)


def _tasks() -> list[ProductionTask]:
    return [
        ProductionTask("flexible", "metal", 8, 48),
        ProductionTask("urgente", "madera", 8, 8),
        ProductionTask("madera-2", "madera", 8, 24),
        ProductionTask("metal-2", "metal", 8, 40),
    ]


def test_hill_climbing_improves_delay_and_material_changes() -> None:
    result = optimize_production_sequence(_tasks(), random_seed=17, restarts=8)

    assert set(result.recommended_sequence) == {task.task_id for task in _tasks()}
    assert result.final_score.total < result.initial_score.total
    assert result.improvement_percent > 0
    assert result.iterations > 0
    assert result.stop_reason in {"local_optimum", "max_iterations"}
    assert result.duration_ms >= 0


def test_hill_climbing_is_reproducible_with_a_fixed_seed() -> None:
    first = optimize_production_sequence(_tasks(), random_seed=2026, restarts=5)
    second = optimize_production_sequence(_tasks(), random_seed=2026, restarts=5)

    assert first.recommended_sequence == second.recommended_sequence
    assert first.final_score == second.final_score
    assert first.iterations == second.iterations


def test_objective_uses_documented_default_weights() -> None:
    tasks = [
        ProductionTask("a", "madera", 24, 0),
        ProductionTask("b", "metal", 1, 100, ready_in_hours=30),
    ]

    score = score_sequence(tasks)

    assert score.delay_days == pytest.approx(1)
    assert score.material_changes == 1
    assert score.idle_hours == pytest.approx(6)
    assert score.total == pytest.approx(10 * 1 + 3 * 1 + 2 * 6)


@pytest.mark.parametrize(
    ("tasks", "weights", "message"),
    [
        ([], ProductionWeights(), "al menos un trabajo"),
        (
            [ProductionTask("repetido", "madera", 1, 2)] * 2,
            ProductionWeights(),
            "no pueden repetirse",
        ),
        (
            [ProductionTask("a", "madera", -1, 2)],
            ProductionWeights(),
            "mayor que cero",
        ),
        (
            [ProductionTask("a", "madera", 1, 2)],
            ProductionWeights(delay_days=-1),
            "no pueden ser negativos",
        ),
    ],
)
def test_hill_climbing_rejects_invalid_inputs(
    tasks: list[ProductionTask], weights: ProductionWeights, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        optimize_production_sequence(tasks, weights)
