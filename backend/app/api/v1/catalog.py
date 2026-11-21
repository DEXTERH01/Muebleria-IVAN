"""Public catalog and administrator product endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.security import CurrentUser, require_roles
from app.domain.catalog import DuplicateProductError, ProductNotFoundError
from app.repositories.catalog import CatalogRepository
from app.schemas.catalog import (
    ProductCreateRequest,
    ProductListResponse,
    ProductResponse,
    ProductUpdateRequest,
)
from app.services.catalog import CatalogService

router = APIRouter(tags=["catalog"])


def get_catalog_service(session: Annotated[Session, Depends(get_session)]) -> CatalogService:
    return CatalogService(CatalogRepository(session))


def _catalog_error(error: Exception) -> HTTPException:
    if isinstance(error, ProductNotFoundError):
        return HTTPException(status_code=404, detail=str(error))
    if isinstance(error, DuplicateProductError):
        return HTTPException(status_code=409, detail=str(error))
    if isinstance(error, ValueError):
        return HTTPException(status_code=422, detail=str(error))
    return HTTPException(status_code=500, detail="No se pudo procesar el catálogo.")


@router.get("/products", response_model=ProductListResponse)
def list_products(
    service: Annotated[CatalogService, Depends(get_catalog_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(alias="pageSize", ge=1, le=100)] = 20,
    category: Annotated[str | None, Query(max_length=80)] = None,
    search: Annotated[str | None, Query(min_length=2, max_length=120)] = None,
) -> ProductListResponse:
    return ProductListResponse(
        data=service.list_products(
            page=page,
            page_size=page_size,
            category=category,
            search=search,
        )
    )


@router.get("/products/{slug}", response_model=ProductResponse)
def product_detail(
    slug: str,
    service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> ProductResponse:
    try:
        return ProductResponse(data=service.product_by_slug(slug))
    except ProductNotFoundError as error:
        raise _catalog_error(error) from error


@router.post("/products", response_model=ProductResponse, status_code=201)
def create_product(
    request: ProductCreateRequest,
    _user: Annotated[CurrentUser, Depends(require_roles("admin"))],
    service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> ProductResponse:
    try:
        return ProductResponse(data=service.create_product(request))
    except (DuplicateProductError, ValueError) as error:
        raise _catalog_error(error) from error


@router.patch("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: UUID,
    request: ProductUpdateRequest,
    _user: Annotated[CurrentUser, Depends(require_roles("admin"))],
    service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> ProductResponse:
    try:
        return ProductResponse(data=service.update_product(product_id, request))
    except (ProductNotFoundError, DuplicateProductError, ValueError) as error:
        raise _catalog_error(error) from error


@router.delete("/products/{product_id}", status_code=204)
def deactivate_product(
    product_id: UUID,
    _user: Annotated[CurrentUser, Depends(require_roles("admin"))],
    service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> Response:
    try:
        service.deactivate_product(product_id)
    except ProductNotFoundError as error:
        raise _catalog_error(error) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)
