"""Advisory ML inference backed by versioned artifacts and PostgreSQL logs."""

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.security import CurrentUser, require_roles
from app.ml.inference import InferenceResult, predict_delay_risk, predict_production_days
from app.models.model_version import ModelVersion
from app.models.prediction import Prediction
from app.schemas.ml import (
    InferenceData,
    InferenceResponse,
    ModelVersionData,
    ModelVersionListResponse,
    OrderInferenceRequest,
)

router = APIRouter(prefix="/ml", tags=["machine-learning"])


def _record(
    session: Session, payload: OrderInferenceRequest, result: InferenceResult
) -> Prediction:
    model = session.scalar(
        select(ModelVersion).where(
            ModelVersion.problem == result.problem,
            ModelVersion.status == "active",
        )
    )
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"No existe un modelo activo para {result.problem}.",
        )
    prediction = Prediction(
        model_version_id=model.id,
        entity_type="order",
        entity_id=payload.order_id,
        input_summary=payload.model_dump(mode="json", exclude={"order_id"}, by_alias=True),
        output={
            **result.output,
            "algorithm": result.algorithm,
            "modelVersion": result.version,
            "fallbackUsed": result.fallback_used,
            "dataLabel": result.data_label,
        },
        confidence=(
            Decimal(str(round(result.confidence, 5))) if result.confidence is not None else None
        ),
    )
    session.add(prediction)
    try:
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo registrar la predicción.",
        ) from exc
    session.refresh(prediction)
    return prediction


def _response(prediction: Prediction, result: InferenceResult) -> InferenceResponse:
    return InferenceResponse(
        data=InferenceData(
            prediction_id=prediction.id,
            problem=result.problem,
            algorithm=result.algorithm,
            model_version=result.version,
            output=result.output,
            confidence=result.confidence,
            fallback_used=result.fallback_used,
        )
    )


@router.get("/models", response_model=ModelVersionListResponse, summary="Listar modelos ML")
def list_models(
    _user: CurrentUser = Depends(require_roles("admin")),
    session: Session = Depends(get_session),
) -> ModelVersionListResponse:
    models = session.scalars(
        select(ModelVersion).order_by(ModelVersion.problem, ModelVersion.version.desc())
    ).all()
    return ModelVersionListResponse(
        data=[ModelVersionData.model_validate(model) for model in models]
    )


@router.post(
    "/production-days",
    response_model=InferenceResponse,
    summary="Estimar días de producción",
)
def production_days(
    payload: OrderInferenceRequest,
    _user: CurrentUser = Depends(require_roles("operator", "admin")),
    session: Session = Depends(get_session),
) -> InferenceResponse:
    result = predict_production_days(payload.model_dump(exclude={"order_id"}))
    return _response(_record(session, payload, result), result)


@router.post(
    "/delay-risk",
    response_model=InferenceResponse,
    summary="Estimar riesgo de retraso",
)
def delay_risk(
    payload: OrderInferenceRequest,
    _user: CurrentUser = Depends(require_roles("operator", "admin")),
    session: Session = Depends(get_session),
) -> InferenceResponse:
    result = predict_delay_risk(payload.model_dump(exclude={"order_id"}))
    return _response(_record(session, payload, result), result)
