"""Reproducible Hill Climbing for advisory production sequencing."""

from dataclasses import dataclass
from random import Random
from time import perf_counter


@dataclass(frozen=True)
class ProductionTask:
    task_id: str
    material: str
    duration_hours: float
    due_in_hours: float
    ready_in_hours: float = 0.0


@dataclass(frozen=True)
class ProductionWeights:
    delay_days: float = 10.0
    material_changes: float = 3.0
    idle_hours: float = 2.0


@dataclass(frozen=True)
class ProductionScore:
    total: float
    delay_days: float
    material_changes: int
    idle_hours: float


@dataclass(frozen=True)
class HillClimbingResult:
    initial_sequence: tuple[str, ...]
    recommended_sequence: tuple[str, ...]
    initial_score: ProductionScore
    final_score: ProductionScore
    improvement_percent: float
    iterations: int
    restarts: int
    random_seed: int
    stop_reason: str
    duration_ms: float


def _validate(tasks: tuple[ProductionTask, ...], weights: ProductionWeights) -> None:
    if not tasks:
        raise ValueError("Se requiere al menos un trabajo de producción.")
    task_ids = [task.task_id for task in tasks]
    if any(not task_id.strip() for task_id in task_ids):
        raise ValueError("Los identificadores de trabajo no pueden estar vacíos.")
    if len(task_ids) != len(set(task_ids)):
        raise ValueError("Los trabajos de producción no pueden repetirse.")
    if any(not task.material.strip() for task in tasks):
        raise ValueError("Cada trabajo debe indicar su material.")
    if any(task.duration_hours <= 0 for task in tasks):
        raise ValueError("La duración estimada debe ser mayor que cero.")
    if any(task.due_in_hours < 0 or task.ready_in_hours < 0 for task in tasks):
        raise ValueError("Los tiempos de entrega y disponibilidad no pueden ser negativos.")
    if min(weights.delay_days, weights.material_changes, weights.idle_hours) < 0:
        raise ValueError("Los pesos de la función objetivo no pueden ser negativos.")


def score_sequence(
    tasks: tuple[ProductionTask, ...] | list[ProductionTask],
    weights: ProductionWeights = ProductionWeights(),
) -> ProductionScore:
    """Calculate delay, material changes, and idle time for one sequence."""
    ordered = tuple(tasks)
    _validate(ordered, weights)
    elapsed = 0.0
    delay_days = 0.0
    idle_hours = 0.0
    material_changes = 0
    prior_material: str | None = None

    for task in ordered:
        if task.ready_in_hours > elapsed:
            idle_hours += task.ready_in_hours - elapsed
            elapsed = task.ready_in_hours
        if prior_material is not None and task.material != prior_material:
            material_changes += 1
        elapsed += task.duration_hours
        delay_days += max(0.0, elapsed - task.due_in_hours) / 24
        prior_material = task.material

    total = (
        weights.delay_days * delay_days
        + weights.material_changes * material_changes
        + weights.idle_hours * idle_hours
    )
    return ProductionScore(
        total=total,
        delay_days=delay_days,
        material_changes=material_changes,
        idle_hours=idle_hours,
    )


def _climb(
    sequence: tuple[ProductionTask, ...],
    weights: ProductionWeights,
    max_iterations: int,
) -> tuple[tuple[ProductionTask, ...], ProductionScore, int, str]:
    current = sequence
    current_score = score_sequence(current, weights)
    iterations = 0

    while iterations < max_iterations:
        candidates: list[
            tuple[float, tuple[str, ...], tuple[ProductionTask, ...], ProductionScore]
        ] = []
        for left in range(len(current) - 1):
            for right in range(left + 1, len(current)):
                neighbor = list(current)
                neighbor[left], neighbor[right] = neighbor[right], neighbor[left]
                neighbor_tuple = tuple(neighbor)
                neighbor_score = score_sequence(neighbor_tuple, weights)
                candidates.append(
                    (
                        neighbor_score.total,
                        tuple(task.task_id for task in neighbor_tuple),
                        neighbor_tuple,
                        neighbor_score,
                    )
                )
        if not candidates:
            return current, current_score, iterations, "local_optimum"
        _, _, best_neighbor, best_score = min(candidates, key=lambda candidate: candidate[:2])
        if best_score.total >= current_score.total - 1e-9:
            return current, current_score, iterations, "local_optimum"
        current = best_neighbor
        current_score = best_score
        iterations += 1

    return current, current_score, iterations, "max_iterations"


def optimize_production_sequence(
    tasks: tuple[ProductionTask, ...] | list[ProductionTask],
    weights: ProductionWeights = ProductionWeights(),
    *,
    random_seed: int = 2026,
    restarts: int = 5,
    max_iterations: int = 100,
) -> HillClimbingResult:
    """Minimize the documented production score with seeded random restarts."""
    ordered = tuple(tasks)
    _validate(ordered, weights)
    if restarts < 0 or restarts > 50:
        raise ValueError("Los reinicios deben estar entre 0 y 50.")
    if max_iterations < 1 or max_iterations > 10_000:
        raise ValueError("Las iteraciones máximas deben estar entre 1 y 10000.")

    started_at = perf_counter()
    initial_score = score_sequence(ordered, weights)
    best_sequence, best_score, total_iterations, stop_reason = _climb(
        ordered, weights, max_iterations
    )
    random = Random(random_seed)

    for _ in range(restarts):
        candidate = list(ordered)
        random.shuffle(candidate)
        sequence, score, iterations, reason = _climb(
            tuple(candidate), weights, max_iterations
        )
        total_iterations += iterations
        candidate_key = (score.total, tuple(task.task_id for task in sequence))
        best_key = (best_score.total, tuple(task.task_id for task in best_sequence))
        if candidate_key < best_key:
            best_sequence, best_score, stop_reason = sequence, score, reason

    improvement = (
        0.0
        if initial_score.total == 0
        else (initial_score.total - best_score.total) * 100 / initial_score.total
    )
    return HillClimbingResult(
        initial_sequence=tuple(task.task_id for task in ordered),
        recommended_sequence=tuple(task.task_id for task in best_sequence),
        initial_score=initial_score,
        final_score=best_score,
        improvement_percent=improvement,
        iterations=total_iterations,
        restarts=restarts,
        random_seed=random_seed,
        stop_reason=stop_reason,
        duration_ms=(perf_counter() - started_at) * 1000,
    )
