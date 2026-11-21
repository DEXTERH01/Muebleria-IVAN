"""Advisory A* delivery routing and Hill Climbing production sequencing."""

from dataclasses import asdict
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.algorithms.astar import optimize_route
from app.algorithms.hill_climbing import (
    ProductionTask,
    ProductionWeights,
    optimize_production_sequence,
)
from app.core.database import get_session
from app.core.security import CurrentUser, require_roles
from app.models.optimization_run import OptimizationRun
from app.schemas.optimization import (
    DeliveryOptimizationRequest,
    OptimizationRunData,
    OptimizationRunResponse,
    ProductionOptimizationRequest,
)

router = APIRouter(prefix="/optimizations", tags=["optimizations"])


def _persist_run(session: Session, run: OptimizationRun) -> OptimizationRun:
    session.add(run)
    try:
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo guardar la ejecución de optimización.",
        ) from exc
    session.refresh(run)
    return run


def _response(run: OptimizationRun) -> OptimizationRunResponse:
    return OptimizationRunResponse(
        data=OptimizationRunData(
            id=run.id,
            algorithm=run.algorithm,
            baseline=run.baseline,
            result=run.result,
            improvement=float(run.improvement),
            duration_ms=run.duration_ms,
            random_seed=run.random_seed,
        )
    )


@router.post(
    "/production",
    response_model=OptimizationRunResponse,
    summary="Optimizar secuencia de producción con Hill Climbing",
)
def optimize_production(
    payload: ProductionOptimizationRequest,
    user: CurrentUser = Depends(require_roles("operator", "admin")),
    session: Session = Depends(get_session),
) -> OptimizationRunResponse:
    """Suggest a sequence; this endpoint never changes production jobs."""
    tasks = [
        ProductionTask(
            task_id=task.task_id,
            material=task.material,
            duration_hours=task.duration_hours,
            due_in_hours=task.due_in_hours,
            ready_in_hours=task.ready_in_hours,
        )
        for task in payload.tasks
    ]
    weights = ProductionWeights(
        delay_days=payload.weights.delay_days,
        material_changes=payload.weights.material_changes,
        idle_hours=payload.weights.idle_hours,
    )
    try:
        result = optimize_production_sequence(
            tasks,
            weights,
            random_seed=payload.random_seed,
            restarts=payload.restarts,
            max_iterations=payload.max_iterations,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    run = OptimizationRun(
        algorithm="hill_climbing",
        input_data=payload.model_dump(mode="json", by_alias=True),
        baseline={
            "sequence": list(result.initial_sequence),
            "score": asdict(result.initial_score),
        },
        result={
            "sequence": list(result.recommended_sequence),
            "score": asdict(result.final_score),
            "iterations": result.iterations,
            "restarts": result.restarts,
            "stopReason": result.stop_reason,
        },
        improvement=Decimal(str(round(result.improvement_percent, 5))),
        random_seed=result.random_seed,
        duration_ms=max(0, round(result.duration_ms)),
        requested_by=user.user_id,
    )
    return _response(_persist_run(session, run))


@router.post(
    "/delivery",
    response_model=OptimizationRunResponse,
    summary="Optimizar ruta de entregas con A*",
)
def optimize_delivery(
    payload: DeliveryOptimizationRequest,
    user: CurrentUser = Depends(require_roles("operator", "admin")),
    session: Session = Depends(get_session),
) -> OptimizationRunResponse:
    """Suggest a route over provided distances; no delivery is modified."""
    try:
        result = optimize_route(payload.start, payload.stops, payload.distances)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    run = OptimizationRun(
        algorithm="astar",
        input_data=payload.model_dump(mode="json", by_alias=True),
        baseline={
            "route": list(result.initial_route),
            "distance": result.initial_distance,
        },
        result={
            "route": list(result.recommended_route),
            "distance": result.total_distance,
            "exploredNodes": result.explored_nodes,
        },
        improvement=Decimal(str(round(result.improvement_percent, 5))),
        random_seed=None,
        duration_ms=max(0, round(result.duration_ms)),
        requested_by=user.user_id,
    )
    return _response(_persist_run(session, run))
