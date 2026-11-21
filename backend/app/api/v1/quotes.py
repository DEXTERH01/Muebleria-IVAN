"""Public quote estimation and protected quote workflow endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_session
from app.core.security import (
    CurrentUser,
    bearer,
    get_current_user,
    require_roles,
    verify_token,
)
from app.domain.catalog import (
    InvalidQuoteTransitionError,
    PricingValidationError,
    ProductNotFoundError,
    QuoteAccessError,
    QuoteNotFoundError,
    QuoteVersionConflictError,
)
from app.repositories.catalog import CatalogRepository
from app.repositories.pricing import PricingRepository
from app.repositories.quotes import QuoteRepository
from app.schemas.pricing import (
    PricingRuleCreateRequest,
    PricingRuleListResponse,
    PricingRuleResponse,
    QuoteEstimateRequest,
    QuoteEstimateResponse,
)
from app.schemas.quotes import (
    QuoteCreateRequest,
    QuoteListResponse,
    QuoteResponse,
    QuoteStatusUpdateRequest,
)
from app.services.pricing import PricingService
from app.services.quotes import QuoteService

router = APIRouter(tags=["quotes"])


def get_pricing_service(session: Annotated[Session, Depends(get_session)]) -> PricingService:
    return PricingService(CatalogRepository(session), PricingRepository(session))


def get_quote_service(session: Annotated[Session, Depends(get_session)]) -> QuoteService:
    pricing = PricingService(CatalogRepository(session), PricingRepository(session))
    return QuoteService(QuoteRepository(session), pricing)


def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    settings: Annotated[Settings, Depends(get_settings)],
    session: Annotated[Session, Depends(get_session)],
) -> CurrentUser | None:
    if credentials is None:
        return None
    user_id = verify_token(credentials.credentials, settings)
    return get_current_user(user_id, session)


def _quote_error(error: Exception) -> HTTPException:
    if isinstance(error, (ProductNotFoundError, QuoteNotFoundError)):
        return HTTPException(status_code=404, detail=str(error))
    if isinstance(error, QuoteAccessError):
        return HTTPException(status_code=403, detail=str(error))
    if isinstance(error, PricingValidationError):
        return HTTPException(status_code=422, detail=str(error))
    if isinstance(error, (QuoteVersionConflictError, InvalidQuoteTransitionError)):
        return HTTPException(status_code=409, detail=str(error))
    return HTTPException(status_code=500, detail="No se pudo procesar la cotización.")


@router.post("/quotes/estimate", response_model=QuoteEstimateResponse)
def estimate_quote(
    request: QuoteEstimateRequest,
    service: Annotated[PricingService, Depends(get_pricing_service)],
) -> QuoteEstimateResponse:
    try:
        return QuoteEstimateResponse(data=service.estimate(request))
    except (ProductNotFoundError, PricingValidationError) as error:
        raise _quote_error(error) from error


@router.get("/pricing-rules", response_model=PricingRuleListResponse)
def list_pricing_rules(
    _user: Annotated[CurrentUser, Depends(require_roles("admin"))],
    service: Annotated[PricingService, Depends(get_pricing_service)],
) -> PricingRuleListResponse:
    return PricingRuleListResponse(data=service.list_rules())


@router.post("/pricing-rules", response_model=PricingRuleResponse, status_code=201)
def create_pricing_rule(
    request: PricingRuleCreateRequest,
    user: Annotated[CurrentUser, Depends(require_roles("admin"))],
    service: Annotated[PricingService, Depends(get_pricing_service)],
) -> PricingRuleResponse:
    try:
        return PricingRuleResponse(
            data=service.create_rule(request, created_by=user.user_id)
        )
    except PricingValidationError as error:
        raise _quote_error(error) from error


@router.post("/quotes", response_model=QuoteResponse, status_code=201)
def create_quote(
    request: QuoteCreateRequest,
    service: Annotated[QuoteService, Depends(get_quote_service)],
    owner: Annotated[CurrentUser | None, Depends(get_optional_user)],
) -> QuoteResponse:
    try:
        return QuoteResponse(data=service.create(request, owner))
    except (ProductNotFoundError, PricingValidationError) as error:
        raise _quote_error(error) from error


@router.get("/quotes", response_model=QuoteListResponse)
def list_quotes(
    user: Annotated[CurrentUser, Depends(require_roles("customer", "admin"))],
    service: Annotated[QuoteService, Depends(get_quote_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 20,
) -> QuoteListResponse:
    return QuoteListResponse(data=service.list_for_user(user, page=page, page_size=page_size))


@router.get("/quotes/{quote_id}", response_model=QuoteResponse)
def get_quote(
    quote_id: UUID,
    user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[QuoteService, Depends(get_quote_service)],
) -> QuoteResponse:
    try:
        return QuoteResponse(data=service.get(quote_id, user))
    except (QuoteNotFoundError, QuoteAccessError) as error:
        raise _quote_error(error) from error


@router.patch("/quotes/{quote_id}/status", response_model=QuoteResponse)
def update_quote_status(
    quote_id: UUID,
    request: QuoteStatusUpdateRequest,
    _user: Annotated[CurrentUser, Depends(require_roles("admin"))],
    service: Annotated[QuoteService, Depends(get_quote_service)],
) -> QuoteResponse:
    try:
        return QuoteResponse(data=service.update_status(quote_id, request))
    except (
        QuoteNotFoundError,
        QuoteVersionConflictError,
        InvalidQuoteTransitionError,
    ) as error:
        raise _quote_error(error) from error
