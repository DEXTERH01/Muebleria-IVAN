"""A* route ordering over a symmetric distance matrix.

Distances are demonstration inputs, not traffic-aware travel estimates. The
search chooses an order for visiting every stop once, starting at the depot.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import count
from math import isclose, isfinite
from time import perf_counter

MAX_ASTAR_STOPS = 12
DistanceMatrix = Mapping[str, Mapping[str, float]]
SearchState = tuple[str, tuple[str, ...]]


@dataclass(frozen=True)
class AStarRouteResult:
    initial_route: tuple[str, ...]
    recommended_route: tuple[str, ...]
    initial_distance: float
    total_distance: float
    explored_nodes: int
    duration_ms: float
    improvement_percent: float


def _validate_problem(start: str, stops: tuple[str, ...], distances: DistanceMatrix) -> None:
    locations = (start, *stops)
    if not start or any(not location for location in locations):
        raise ValueError("Los identificadores de ubicación no pueden estar vacíos.")
    if len(stops) != len(set(stops)):
        raise ValueError("La lista de paradas contiene ubicaciones duplicadas.")
    if start in stops:
        raise ValueError("El punto de partida no puede repetirse como parada.")
    if len(stops) > MAX_ASTAR_STOPS:
        raise ValueError(f"A* admite como máximo {MAX_ASTAR_STOPS} paradas por ejecución.")
    missing_rows = set(locations) - distances.keys()
    if missing_rows:
        missing = ", ".join(sorted(missing_rows))
        raise ValueError(f"Faltan distancias para las ubicaciones: {missing}.")

    for origin in locations:
        for destination in locations:
            if destination not in distances[origin]:
                raise ValueError(f"Falta la distancia de {origin} a {destination}.")
            value = distances[origin][destination]
            if not isfinite(value) or value < 0:
                raise ValueError("Las distancias deben ser finitas y no negativas.")
            if not isclose(value, distances[destination][origin], rel_tol=1e-9, abs_tol=1e-9):
                raise ValueError("La matriz de distancias debe ser simétrica.")


def _minimum_spanning_tree(nodes: tuple[str, ...], distances: DistanceMatrix) -> float:
    if len(nodes) < 2:
        return 0.0

    connected = {nodes[0]}
    remaining = set(nodes[1:])
    total = 0.0
    while remaining:
        edge_cost, destination = min(
            (distances[origin][candidate], candidate)
            for origin in connected
            for candidate in remaining
        )
        total += edge_cost
        connected.add(destination)
        remaining.remove(destination)
    return total


def _heuristic(current: str, remaining: tuple[str, ...], distances: DistanceMatrix) -> float:
    if not remaining:
        return 0.0
    return min(distances[current][stop] for stop in remaining) + _minimum_spanning_tree(
        remaining, distances
    )


def _route_from_parents(
    goal: SearchState, parents: dict[SearchState, SearchState]
) -> tuple[str, ...]:
    route = [goal[0]]
    state = goal
    while state in parents:
        state = parents[state]
        route.append(state[0])
    route.reverse()
    return tuple(route)


def _route_distance(route: tuple[str, ...], distances: DistanceMatrix) -> float:
    return sum(
        distances[origin][destination]
        for origin, destination in zip(route, route[1:], strict=False)
    )


def optimize_route(
    start: str,
    stops: tuple[str, ...] | list[str],
    distances: DistanceMatrix,
) -> AStarRouteResult:
    """Find the shortest route that visits each requested stop exactly once.

    The input stop order is used as the baseline. Ties are resolved
    deterministically by location identifier.
    """
    ordered_stops = tuple(stops)
    _validate_problem(start, ordered_stops, distances)
    started_at = perf_counter()
    initial_route = (start, *ordered_stops)
    initial_distance = _route_distance(initial_route, distances)
    initial_state: SearchState = (start, tuple(sorted(ordered_stops)))
    frontier: list[tuple[float, float, int, SearchState]] = []
    sequence = count()
    heappush(
        frontier,
        (_heuristic(start, initial_state[1], distances), 0.0, next(sequence), initial_state),
    )
    best_cost: dict[SearchState, float] = {initial_state: 0.0}
    parents: dict[SearchState, SearchState] = {}
    explored_nodes = 0

    while frontier:
        _, cost_so_far, _, state = heappop(frontier)
        if cost_so_far > best_cost.get(state, float("inf")):
            continue
        explored_nodes += 1
        current, remaining = state
        if not remaining:
            recommended_route = _route_from_parents(state, parents)
            total_distance = cost_so_far
            improvement = (
                0.0
                if initial_distance == 0
                else (initial_distance - total_distance) * 100 / initial_distance
            )
            return AStarRouteResult(
                initial_route=initial_route,
                recommended_route=recommended_route,
                initial_distance=initial_distance,
                total_distance=total_distance,
                explored_nodes=explored_nodes,
                duration_ms=(perf_counter() - started_at) * 1000,
                improvement_percent=improvement,
            )

        for next_stop in remaining:
            next_remaining = tuple(stop for stop in remaining if stop != next_stop)
            next_state = (next_stop, next_remaining)
            new_cost = cost_so_far + distances[current][next_stop]
            if new_cost >= best_cost.get(next_state, float("inf")):
                continue
            best_cost[next_state] = new_cost
            parents[next_state] = state
            estimate = new_cost + _heuristic(next_stop, next_remaining, distances)
            heappush(frontier, (estimate, new_cost, next(sequence), next_state))

    raise ValueError("No se encontró una ruta que visite todas las paradas.")
