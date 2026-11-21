from itertools import permutations

import pytest

from app.algorithms.astar import MAX_ASTAR_STOPS, optimize_route
from app.algorithms.route_dataset import SAMPLE_DISTANCE_MATRIX


def test_astar_finds_optimal_route_and_reports_baseline_metrics() -> None:
    stops = ("parada-a", "parada-b", "parada-c", "parada-d")
    result = optimize_route("taller", stops, SAMPLE_DISTANCE_MATRIX)
    expected = min(
        sum(
            SAMPLE_DISTANCE_MATRIX[origin][destination]
            for origin, destination in zip(("taller", *route), route, strict=False)
        )
        for route in permutations(stops)
    )

    assert result.recommended_route[0] == "taller"
    assert set(result.recommended_route[1:]) == set(stops)
    assert result.total_distance == pytest.approx(expected)
    assert result.initial_distance > result.total_distance
    assert result.improvement_percent > 0
    assert result.explored_nodes > 0
    assert result.duration_ms >= 0


def test_astar_is_deterministic_and_handles_no_stops() -> None:
    first = optimize_route("taller", ["parada-a", "parada-b"], SAMPLE_DISTANCE_MATRIX)
    second = optimize_route("taller", ["parada-a", "parada-b"], SAMPLE_DISTANCE_MATRIX)
    empty = optimize_route("taller", [], SAMPLE_DISTANCE_MATRIX)

    assert first.recommended_route == second.recommended_route
    assert empty.recommended_route == ("taller",)
    assert empty.total_distance == 0
    assert empty.improvement_percent == 0


@pytest.mark.parametrize(
    ("start", "stops", "distances", "message"),
    [
        ("missing", [], SAMPLE_DISTANCE_MATRIX, "Faltan distancias"),
        ("taller", ["parada-a", "parada-a"], SAMPLE_DISTANCE_MATRIX, "duplicadas"),
        ("taller", ["taller"], SAMPLE_DISTANCE_MATRIX, "no puede repetirse"),
    ],
)
def test_astar_rejects_invalid_route_inputs(
    start: str, stops: list[str], distances: dict, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        optimize_route(start, stops, distances)


def test_astar_rejects_more_than_the_configured_stop_limit() -> None:
    stops = [f"stop-{index}" for index in range(MAX_ASTAR_STOPS + 1)]
    locations = ["taller", *stops]
    distances = {
        origin: {destination: float(origin != destination) for destination in locations}
        for origin in locations
    }

    with pytest.raises(ValueError, match="como máximo"):
        optimize_route("taller", stops, distances)


def test_astar_rejects_asymmetric_distance_matrix() -> None:
    distances = {origin: row.copy() for origin, row in SAMPLE_DISTANCE_MATRIX.items()}
    distances["taller"]["parada-a"] += 1

    with pytest.raises(ValueError, match="simétrica"):
        optimize_route("taller", ["parada-a"], distances)
