"""Analytics and ML model endpoints.

Dashboard KPIs are computed from live PostgreSQL data (no hardcoded metrics).
ML model metadata is served from app.model_versions.
Service layer is pending; endpoints return 501 until implemented.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.core.security import require_roles

router = APIRouter(tags=["analytics"])

_NOT_IMPLEMENTED = JSONResponse(
    status_code=501,
    content={"error": {"code": "NOT_IMPLEMENTED", "message": "Pendiente implementación"}},
)


@router.get("/analytics/overview", summary="Indicadores del dashboard", status_code=501)
def analytics_overview(
    _user=Depends(require_roles("operator", "admin")),
):
    """Return real-time KPIs from PostgreSQL.

    Includes: active orders by status, revenue this month, overdue orders,
    top products, average production days, payment recovery rate.
    All values computed from app schema — no hardcoded numbers.
    """
    return _NOT_IMPLEMENTED


@router.get("/analytics/ml/models", summary="Versiones y métricas de modelos ML", status_code=501)
def ml_model_list(
    _user=Depends(require_roles("admin")),
):
    """Return all model versions with their metrics and activation status.

    Metrics are stored in app.model_versions.metrics (JSON) — never hardcoded.
    """
    return _NOT_IMPLEMENTED
