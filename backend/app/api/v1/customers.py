"""Customer directory for staff users."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.security import CurrentUser, require_roles
from app.models.customer import Customer
from app.schemas.customer import (
    CustomerCreate,
    CustomerListResponse,
    CustomerOut,
    CustomerResponse,
    CustomerUpdate,
)

router = APIRouter(prefix="/customers", tags=["customers"])


def _normalize_customer_fields(values: dict[str, object]) -> dict[str, object]:
    normalized = dict(values)
    if "full_name" in normalized and isinstance(normalized["full_name"], str):
        normalized["full_name"] = normalized["full_name"].strip()
    if "email" in normalized:
        email = normalized["email"]
        normalized["email"] = email.strip().lower() or None if isinstance(email, str) else None
    if "phone" in normalized:
        phone = normalized["phone"]
        normalized["phone"] = phone.strip() or None if isinstance(phone, str) else None
    for field in ("document_number", "district"):
        value = normalized.get(field)
        if isinstance(value, str):
            normalized[field] = value.strip() or None
    return normalized


def _check_customer_contact(values: dict[str, object]) -> None:
    if not values.get("email") and not values.get("phone"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Se requiere correo electrónico o teléfono.",
        )


def _get_customer(session: Session, customer_id: UUID) -> Customer:
    customer = session.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="No se encontró el cliente.")
    return customer


@router.get("", response_model=CustomerListResponse, summary="Listar clientes")
def list_customers(
    q: str | None = Query(default=None, min_length=1, max_length=100),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, alias="pageSize", ge=1, le=100),
    _user: CurrentUser = Depends(require_roles("operator", "admin")),
    session: Session = Depends(get_session),
) -> CustomerListResponse:
    query = select(Customer)
    count_query = select(func.count()).select_from(Customer)
    if q:
        pattern = f"%{q.strip()}%"
        predicate = or_(
            func.lower(Customer.full_name).like(pattern.lower()),
            func.lower(Customer.email).like(pattern.lower()),
            Customer.phone.ilike(pattern),
        )
        query = query.where(predicate)
        count_query = count_query.where(predicate)

    total = session.scalar(count_query) or 0
    customers = session.scalars(
        query.order_by(Customer.full_name, Customer.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return CustomerListResponse(
        data=[CustomerOut.model_validate(customer) for customer in customers],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{customer_id}", response_model=CustomerResponse, summary="Detalle de cliente")
def get_customer(
    customer_id: UUID,
    _user: CurrentUser = Depends(require_roles("operator", "admin")),
    session: Session = Depends(get_session),
) -> CustomerResponse:
    return CustomerResponse(data=CustomerOut.model_validate(_get_customer(session, customer_id)))


@router.post(
    "", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED,
    summary="Crear cliente",
)
def create_customer(
    payload: CustomerCreate,
    _user: CurrentUser = Depends(require_roles("operator", "admin")),
    session: Session = Depends(get_session),
) -> CustomerResponse:
    fields = _normalize_customer_fields(payload.model_dump())
    _check_customer_contact(fields)
    if not fields.get("full_name"):
        raise HTTPException(status_code=422, detail="El nombre no puede estar vacío.")
    customer = Customer(**fields)
    session.add(customer)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un cliente con ese correo electrónico.",
        ) from exc
    session.refresh(customer)
    return CustomerResponse(data=CustomerOut.model_validate(customer))


@router.patch(
    "/{customer_id}", response_model=CustomerResponse, summary="Actualizar cliente"
)
def update_customer(
    customer_id: UUID,
    payload: CustomerUpdate,
    _user: CurrentUser = Depends(require_roles("operator", "admin")),
    session: Session = Depends(get_session),
) -> CustomerResponse:
    customer = _get_customer(session, customer_id)
    fields = _normalize_customer_fields(payload.model_dump(exclude_unset=True))
    if "full_name" in fields and not fields["full_name"]:
        raise HTTPException(status_code=422, detail="El nombre no puede estar vacío.")
    contact = {
        "email": fields.get("email", customer.email),
        "phone": fields.get("phone", customer.phone),
    }
    _check_customer_contact(contact)
    for field, value in fields.items():
        setattr(customer, field, value)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un cliente con ese correo electrónico.",
        ) from exc
    session.refresh(customer)
    return CustomerResponse(data=CustomerOut.model_validate(customer))
