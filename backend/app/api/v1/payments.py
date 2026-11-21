"""Idempotent payment recording and audited reversals."""

from datetime import UTC, datetime, time
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.core.security import CurrentUser, get_current_user, require_roles
from app.models.audit_log import AuditLog
from app.models.customer import Customer
from app.models.media_asset import MediaAsset
from app.models.order import Order
from app.models.payment import Payment
from app.schemas.payment import (
    PaymentCreate,
    PaymentListResponse,
    PaymentOut,
    PaymentResponse,
    PaymentVoidRequest,
)

router = APIRouter(tags=["payments"])


def _payment_out(payment: Payment) -> PaymentOut:
    return PaymentOut(
        id=payment.id,
        order_id=payment.order_id,
        amount_minor=payment.amount_minor,
        currency=payment.currency.strip(),
        method=payment.method,
        reference=payment.reference,
        payment_date=payment.paid_at.date(),
        status=payment.status,
        created_at=payment.created_at,
    )


def _same_idempotent_request(
    payment: Payment,
    order_id: UUID,
    payload: PaymentCreate,
) -> bool:
    return (
        payment.order_id == order_id
        and payment.amount_minor == payload.amount_minor
        and payment.currency == payload.currency
        and payment.method == payload.method
        and payment.reference == payload.reference
        and payment.paid_at.date() == payload.payment_date
        and payment.voucher_asset_id == payload.voucher_asset_id
        and payment.reverses_payment_id is None
    )


def _get_order_for_user(session: Session, order_id: UUID, user: CurrentUser) -> Order:
    query = select(Order).where(Order.id == order_id)
    if user.role == "customer":
        query = query.join(Customer, Customer.id == Order.customer_id).where(
            Customer.profile_user_id == user.user_id
        )
    order = session.scalars(query).one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="No se encontró el pedido.")
    return order


@router.post(
    "/orders/{order_id}/payments",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar pago",
)
def create_payment(
    order_id: UUID,
    payload: PaymentCreate,
    response: Response,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=128),
    user: CurrentUser = Depends(require_roles("operator", "admin")),
    session: Session = Depends(get_session),
) -> PaymentResponse:
    existing = session.scalar(
        select(Payment).where(Payment.idempotency_key == idempotency_key)
    )
    if existing is not None:
        if _same_idempotent_request(existing, order_id, payload):
            response.status_code = status.HTTP_200_OK
            return PaymentResponse(data=_payment_out(existing))
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La clave de idempotencia ya se usó para otra solicitud.",
        )

    if payload.currency != "PEN":
        raise HTTPException(status_code=422, detail="La moneda permitida es PEN.")
    order = session.scalars(
        select(Order).where(Order.id == order_id).with_for_update()
    ).one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="No se encontró el pedido.")
    if order.status in {"cancelled", "delivered", "installed"}:
        raise HTTPException(status_code=409, detail="El pedido no acepta nuevos pagos.")
    if payload.amount_minor > order.balance_minor:
        raise HTTPException(status_code=409, detail="El pago excede el saldo pendiente.")
    if payload.voucher_asset_id is not None:
        asset = session.get(MediaAsset, payload.voucher_asset_id)
        if asset is None or asset.access != "private":
            raise HTTPException(
                status_code=422,
                detail="El voucher debe ser un recurso privado válido.",
            )

    payment = Payment(
        order_id=order.id,
        amount_minor=payload.amount_minor,
        currency=payload.currency,
        method=payload.method,
        reference=payload.reference,
        paid_at=datetime.combine(payload.payment_date, time.min, tzinfo=UTC),
        idempotency_key=idempotency_key,
        actor_user_id=user.user_id,
        voucher_asset_id=payload.voucher_asset_id,
    )
    previous_paid = order.paid_minor
    order.paid_minor += payment.amount_minor
    session.add(payment)
    session.add(
        AuditLog(
            actor_user_id=user.user_id,
            action="payment.recorded",
            entity_type="payment",
            entity_id=payment.id,
            old_values={"orderId": str(order.id), "paidMinor": previous_paid},
            new_values={
                "orderId": str(order.id),
                "paidMinor": order.paid_minor,
                "amountMinor": payment.amount_minor,
            },
        )
    )
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raced = session.scalar(
            select(Payment).where(Payment.idempotency_key == idempotency_key)
        )
        if raced is not None and _same_idempotent_request(raced, order_id, payload):
            response.status_code = status.HTTP_200_OK
            return PaymentResponse(data=_payment_out(raced))
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se pudo registrar el pago; revisa el saldo y la clave de idempotencia.",
        ) from exc
    session.refresh(payment)
    return PaymentResponse(data=_payment_out(payment))


@router.get(
    "/orders/{order_id}/payments",
    response_model=PaymentListResponse,
    summary="Listar pagos de un pedido",
)
def list_payments(
    order_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, alias="pageSize", ge=1, le=100),
    user: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> PaymentListResponse:
    _get_order_for_user(session, order_id, user)
    base_query = select(Payment).where(Payment.order_id == order_id)
    total = session.scalar(
        select(func.count()).select_from(Payment).where(Payment.order_id == order_id)
    ) or 0
    payments = session.scalars(
        base_query.order_by(Payment.paid_at.desc(), Payment.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return PaymentListResponse(
        data=[_payment_out(payment) for payment in payments],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/payments/{payment_id}/void",
    response_model=PaymentResponse,
    summary="Revertir pago",
)
def void_payment(
    payment_id: UUID,
    payload: PaymentVoidRequest,
    user: CurrentUser = Depends(require_roles("admin")),
    session: Session = Depends(get_session),
) -> PaymentResponse:
    payment = session.scalars(
        select(Payment).where(Payment.id == payment_id).with_for_update()
    ).one_or_none()
    if payment is None:
        raise HTTPException(status_code=404, detail="No se encontró el pago.")
    if payment.status != "recorded" or payment.reverses_payment_id is not None:
        raise HTTPException(status_code=409, detail="El pago no se puede revertir.")
    prior_reversal = session.scalar(
        select(Payment).where(Payment.reverses_payment_id == payment.id)
    )
    if prior_reversal is not None:
        raise HTTPException(status_code=409, detail="El pago ya tiene una reversión.")

    order = session.scalars(
        select(Order).where(Order.id == payment.order_id).with_for_update()
    ).one_or_none()
    if order is None or order.paid_minor < payment.amount_minor:
        raise HTTPException(
            status_code=409,
            detail="El saldo del pedido no permite revertir el pago.",
        )
    if order.status in {"delivered", "installed"} and (
        order.paid_minor - payment.amount_minor < order.total_minor
    ):
        raise HTTPException(
            status_code=409,
            detail="No se puede revertir un pago que dejaría saldo en un pedido entregado.",
        )

    reversal = Payment(
        order_id=payment.order_id,
        amount_minor=payment.amount_minor,
        currency=payment.currency,
        method=payment.method,
        reference=None,
        paid_at=datetime.now(UTC),
        idempotency_key=f"void:{payment.id}:{uuid4()}",
        actor_user_id=user.user_id,
        reverses_payment_id=payment.id,
    )
    previous_paid = order.paid_minor
    payment.status = "voided"
    order.paid_minor -= payment.amount_minor
    session.add(reversal)
    try:
        session.flush()
        session.add(
            AuditLog(
                actor_user_id=user.user_id,
                action="payment.voided",
                entity_type="payment",
                entity_id=payment.id,
                old_values={"status": "recorded", "paidMinor": previous_paid},
                new_values={
                    "status": "voided",
                    "paidMinor": order.paid_minor,
                    "reversalId": str(reversal.id),
                    "reason": payload.reason,
                },
            )
        )
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=409, detail="El pago ya fue revertido.") from exc
    session.refresh(reversal)
    return PaymentResponse(data=_payment_out(reversal))
