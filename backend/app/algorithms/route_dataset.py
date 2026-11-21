"""Small deterministic coordinate set for A* demonstrations and tests.

Coordinates use synthetic units and do not represent real addresses or traffic.
"""

from collections.abc import Mapping
from math import hypot

SAMPLE_COORDINATES: dict[str, tuple[float, float]] = {
    "taller": (0.0, 0.0),
    "parada-a": (2.0, 5.0),
    "parada-b": (5.0, 1.0),
    "parada-c": (6.0, 6.0),
    "parada-d": (1.0, 2.0),
}


def euclidean_distance_matrix(
    coordinates: Mapping[str, tuple[float, float]],
) -> dict[str, dict[str, float]]:
    """Build a symmetric straight-line matrix from synthetic coordinates."""
    if len(coordinates) != len(set(coordinates)) or any(not name for name in coordinates):
        raise ValueError("Cada coordenada necesita un identificador único no vacío.")
    for point in coordinates.values():
        if len(point) != 2 or any(not isinstance(value, (float, int)) for value in point):
            raise ValueError("Cada ubicación debe tener coordenadas numéricas x e y.")

    return {
        origin: {
            destination: hypot(
                coordinates[origin][0] - coordinates[destination][0],
                coordinates[origin][1] - coordinates[destination][1],
            )
            for destination in coordinates
        }
        for origin in coordinates
    }


SAMPLE_DISTANCE_MATRIX = euclidean_distance_matrix(SAMPLE_COORDINATES)
