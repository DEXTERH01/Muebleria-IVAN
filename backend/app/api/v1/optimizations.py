"""Optimization endpoints — BE-05 (Hill Climbing and A*).

These endpoints trigger the search algorithms on the current active orders or
deliveries. Results are advisory — they never modify orders automatically (RN-10).
Algorithm implementations are pending; endpoints return 501 until implemented.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.core.security import require_roles

router = APIRouter(prefix="/optimizations", tags=["optimizations"])

_NOT_IMPLEMENTED = JSONResponse(
    status_code=501,
    content={"error": {"code": "NOT_IMPLEMENTED", "message": "Pendiente implementación"}},
)


@router.post(
    "/production",
    summary="Optimizar secuencia de producción (Hill Climbing)",
    status_code=501,
)
def optimize_production(
    _user=Depends(require_roles("operator", "admin")),
):
    """Run Hill Climbing on a selection of active orders.

    Request body: {"orderIds": [...], "weights": {"delayDays": 10, ...}}
    Returns: initial sequence, optimised sequence, score improvement, iterations,
    stop reason, and execution time.
    """
    return _NOT_IMPLEMENTED


@router.post("/delivery", summary="Optimizar ruta de entregas (A*)", status_code=501)
def optimize_delivery(
    _user=Depends(require_roles("operator", "admin")),
):
    """Run A* route optimisation for a set of pending deliveries.

    Request body: {"deliveryIds": [...]}
    Returns: initial route, optimised route, total distance, nodes explored,
    execution time, and improvement vs. baseline.
    """
    return _NOT_IMPLEMENTED
