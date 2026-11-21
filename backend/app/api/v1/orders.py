"""Order lookup and production state transitions."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.security import CurrentUser, get_current_user, require_roles
from app.models.audit_log import AuditLog
from app.models.customer import Customer
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.order_status_event import OrderStatusEvent
from app.models.quotes import Quote, QuoteItem
from app.schemas.order import (
    OrderDetailOut,
    OrderDetailResponse,
    OrderListResponse,
    OrderOut,
    OrderResponse,
    OrderStatus,
    OrderStatusEventOut,
    OrderStatusPatch,
    QuoteConvertRequest,
)

router = APIRouter(prefix="/orders", tags=["orders"])
quote_conversion_router = APIRouter(prefix="/quotes", tags=["orders"])

NEXT_STATES: dict[OrderStatus, set[OrderStatus]] = {
    "confirmed": {"materials_pending", "cancelled"},
    "materials_pending": {"cutting", "cancelled"},
    "cutting": {"assembly"},
    "assembly": {"finishing"},
    "finishing": {"ready"},
    "ready": {"delivered"},
    "delivered": {"installed"},
    "installed": set(),
    "cancelled": set(),
}


def transition_allowed(current: str, target: str) -> bool:
    return target in NEXT_STATES.get(current, set())


def _find_or_create_customer(session: Session, quote: Quote) -> Customer:
    if quote.customer_id is not None:
        customer = session.get(Customer, quote.customer_id)
        if customer is None:
            raise HTTPException(status_code=409, detail="La cotización tiene un cliente inválido.")
        return customer

    if quote.owner_user_id is not None:
        customer = session.scalar(
            select(Customer).where(Customer.profile_user_id == quote.owner_user_id)
        )
        if customer is not None:
            return customer

    if quote.contact_email:
        customer = session.scalar(
            select(Customer).where(func.lower(Customer.email) == quote.contact_email.lower())
        )
        if customer is not None:
            if quote.owner_user_id is not None and customer.profile_user_id is None:
                customer.profile_user_id = quote.owner_user_id
            return customer
    if quote.contact_phone:
        customer = session.scalar(select(Customer).where(Customer.phone == quote.contact_phone))
        if customer is not None:
            if quote.owner_user_id is not None and customer.profile_user_id is None:
                customer.profile_user_id = quote.owner_user_id
            return customer

    customer = Customer(
        full_name=quote.contact_name.strip(),
        email=quote.contact_email,
        phone=quote.contact_phone,
        profile_user_id=quote.owner_user_id,
    )
    session.add(customer)
    session.flush()
    return customer


def _order_items_from_quote(order_id: UUID, items: list[QuoteItem]) -> list[OrderItem]:
    return [
        OrderItem(
            order_id=order_id,
            source_quote_item_id=item.id,
            product_id=item.product_id,
            product_name_snapshot=item.product_name_snapshot,
            quantity=item.quantity,
            width_mm=item.width_mm,
            height_mm=item.height_mm,
            depth_mm=item.depth_mm,
            configuration_snapshot={
                "configuration": item.configuration,
                "material": item.calculation_breakdown.get("material"),
                "finish": item.calculation_breakdown.get("finish"),
                "accessories": item.accessories,
                "calculationBreakdown": item.calculation_breakdown,
            },
            unit_price_minor=item.line_total_minor // item.quantity,
            line_total_minor=item.line_total_minor,
        )
        for item in items
    ]


@quote_conversion_router.post(
    "/{quote_id}/convert",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Convertir cotización aprobada en pedido",
)
def convert_quote_to_order(
    quote_id: UUID,
    payload: QuoteConvertRequest,
    request: Request,
    response: Response,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=128),
    user: CurrentUser = Depends(require_roles("admin")),
    session: Session = Depends(get_session),
) -> OrderResponse:
    quote = session.scalars(
        select(Quote).where(Quote.id == quote_id).with_for_update()
    ).one_or_none()
    if quote is None:
        raise HTTPException(status_code=404, detail="No se encontró la cotización.")

    address_snapshot = payload.delivery_address.model_dump(mode="json", exclude_none=True)
    existing = session.scalar(select(Order).where(Order.quote_id == quote_id))
    if existing is not None:
        prior_conversion = session.scalar(
            select(AuditLog).where(
                AuditLog.action == "quote.converted",
                AuditLog.entity_id == existing.id,
            )
        )
        is_replay = (
            prior_conversion is not None
            and (prior_conversion.new_values or {}).get("idempotencyKey") == idempotency_key
            and existing.delivery_address_snapshot == address_snapshot
            and existing.promised_date == payload.promised_date
        )
        if is_replay:
            response.status_code = status.HTTP_200_OK
            return OrderResponse(data=OrderOut.model_validate(existing))
        raise HTTPException(
            status_code=409,
            detail="La cotización ya se convirtió con otra solicitud.",
        )

    if quote.status != "approved":
        raise HTTPException(
            status_code=409,
            detail="Solo se pueden convertir cotizaciones aprobadas.",
        )
    if quote.version != payload.expected_quote_version:
        raise HTTPException(
            status_code=409,
            detail="La cotización cambió; vuelve a cargarla antes de convertirla.",
        )
    if quote.currency != "PEN":
        raise HTTPException(status_code=409, detail="La moneda de la cotización no es válida.")

    items = session.scalars(
        select(QuoteItem)
        .where(QuoteItem.quote_id == quote_id)
        .order_by(QuoteItem.created_at, QuoteItem.id)
    ).all()
    if not items:
        raise HTTPException(status_code=409, detail="La cotización no tiene artículos.")

    now = datetime.now(UTC)
    order_id = uuid4()
    customer = _find_or_create_customer(session, quote)
    order = Order(
        id=order_id,
        code=f"PED-{now.year}-{order_id.hex[:8].upper()}",
        quote_id=quote.id,
        customer_id=customer.id,
        status="confirmed",
        currency="PEN",
        total_minor=quote.total_minor,
        deposit_required_minor=quote.deposit_minor,
        paid_minor=0,
        promised_date=payload.promised_date,
        delivery_address_snapshot=address_snapshot,
        version=1,
        created_at=now,
        updated_at=now,
    )
    quote.status = "converted"
    quote.version += 1
    session.add(order)
    session.add_all(_order_items_from_quote(order.id, items))
    session.add(
        OrderStatusEvent(
            order_id=order.id,
            previous_status=None,
            new_status="confirmed",
            actor_user_id=user.user_id,
            note=f"Creado desde la cotización {quote.code}",
        )
    )
    session.add(
        AuditLog(
            actor_user_id=user.user_id,
            action="quote.converted",
            entity_type="order",
            entity_id=order.id,
            old_values={"quoteId": str(quote.id), "quoteStatus": "approved"},
            new_values={
                "orderId": str(order.id),
                "quoteStatus": "converted",
                "idempotencyKey": idempotency_key,
            },
            request_id=UUID(request.state.request_id),
        )
    )
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="No se pudo convertir la cotización; revisa si ya fue procesada.",
        ) from exc
    session.refresh(order)
    return OrderResponse(data=OrderOut.model_validate(order))


def _order_query_for_user(user: CurrentUser):
    query = select(Order)
    if user.role == "customer":
        query = query.join(Customer, Customer.id == Order.customer_id).where(
            Customer.profile_user_id == user.user_id
        )
    return query


@router.get("", response_model=OrderListResponse, summary="Listar pedidos")
def list_orders(
    order_status: OrderStatus | None = Query(default=None, alias="status"),
    customer_id: UUID | None = Query(default=None, alias="customerId"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, alias="pageSize", ge=1, le=100),
    user: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> OrderListResponse:
    query = _order_query_for_user(user)
    count_query = select(func.count()).select_from(Order)
    if user.role == "customer":
        count_query = count_query.join(Customer, Customer.id == Order.customer_id).where(
            Customer.profile_user_id == user.user_id
        )
    if order_status:
        query = query.where(Order.status == order_status)
        count_query = count_query.where(Order.status == order_status)
    if customer_id and user.role in {"operator", "admin"}:
        query = query.where(Order.customer_id == customer_id)
        count_query = count_query.where(Order.customer_id == customer_id)

    total = session.scalar(count_query) or 0
    orders = session.scalars(
        query.order_by(Order.created_at.desc(), Order.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return OrderListResponse(
        data=[OrderOut.model_validate(order) for order in orders],
        total=total,
        page=page,
        page_size=page_size,
    )


def _get_order_for_user(session: Session, order_id: UUID, user: CurrentUser) -> Order:
    order = session.scalars(_order_query_for_user(user).where(Order.id == order_id)).one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="No se encontró el pedido.")
    return order


@router.get("/{order_id}", response_model=OrderDetailResponse, summary="Detalle de pedido")
def get_order(
    order_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> OrderDetailResponse:
    order = _get_order_for_user(session, order_id, user)
    events = session.scalars(
        select(OrderStatusEvent)
        .where(OrderStatusEvent.order_id == order_id)
        .order_by(OrderStatusEvent.occurred_at, OrderStatusEvent.id)
    ).all()
    details = OrderDetailOut(
        **OrderOut.model_validate(order).model_dump(),
        status_history=[OrderStatusEventOut.model_validate(event) for event in events],
    )
    return OrderDetailResponse(data=details)


@router.patch(
    "/{order_id}/status",
    response_model=OrderResponse,
    summary="Cambiar etapa de producción",
)
def update_order_status(
    order_id: UUID,
    payload: OrderStatusPatch,
    request: Request,
    user: CurrentUser = Depends(require_roles("operator", "admin")),
    session: Session = Depends(get_session),
) -> OrderResponse:
    order = session.scalars(
        select(Order).where(Order.id == order_id).with_for_update()
    ).one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="No se encontró el pedido.")
    if order.version != payload.version:
        raise HTTPException(status_code=409, detail="El pedido cambió; vuelve a cargarlo.")
    if not transition_allowed(order.status, payload.new_status):
        raise HTTPException(
            status_code=409,
            detail=f"No se permite pasar de {order.status} a {payload.new_status}.",
        )
    if (
        payload.new_status == "materials_pending"
        and order.paid_minor < order.deposit_required_minor
    ):
        raise HTTPException(
            status_code=409,
            detail="Se requiere el anticipo acordado antes de iniciar la producción.",
        )
    if payload.new_status == "delivered" and order.balance_minor > 0:
        raise HTTPException(
            status_code=409,
            detail="No se puede entregar un pedido con saldo pendiente.",
        )
    installation_payment_exception = (
        payload.new_status == "installed" and order.balance_minor > 0
    )
    if installation_payment_exception and (
        user.role != "admin" or not payload.note or not payload.note.strip()
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                "Solo un administrador puede instalar con saldo pendiente "
                "y debe registrar el motivo."
            ),
        )

    previous_status = order.status
    order.status = payload.new_status
    order.version += 1
    if payload.new_status == "delivered":
        order.delivered_at = func.now()
    elif payload.new_status == "installed":
        order.installed_at = func.now()

    session.add(
        OrderStatusEvent(
            order_id=order.id,
            previous_status=previous_status,
            new_status=payload.new_status,
            actor_user_id=user.user_id,
            note=payload.note,
        )
    )
    session.add(
        AuditLog(
            actor_user_id=user.user_id,
            action="order.status_changed",
            entity_type="order",
            entity_id=order.id,
            old_values={"status": previous_status, "version": payload.version},
            new_values={
                "status": payload.new_status,
                "version": payload.version + 1,
                **(
                    {
                        "exception": "installed_with_balance",
                        "reason": payload.note.strip(),
                    }
                    if installation_payment_exception
                    else {}
                ),
            },
            request_id=UUID(request.state.request_id),
        )
    )
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=409, detail="No se pudo guardar el cambio de etapa."
        ) from exc
    session.refresh(order)
    return OrderResponse(data=OrderOut.model_validate(order))
