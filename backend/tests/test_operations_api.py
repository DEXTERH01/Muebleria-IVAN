from datetime import UTC, date, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException, Response
from starlette.requests import Request

from app.api.v1.customers import _normalize_customer_fields, create_customer
from app.api.v1.media import (
    _private_download_url,
    cloudinary_signature,
    confirm_upload,
    get_asset,
    get_upload_signature,
    verify_cloudinary_upload_signature,
)
from app.api.v1.orders import convert_quote_to_order, update_order_status
from app.api.v1.payments import create_payment, list_payments, void_payment
from app.core.config import Settings
from app.core.security import CurrentUser
from app.models.audit_log import AuditLog
from app.models.customer import Customer
from app.models.media_asset import MediaAsset
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.order_status_event import OrderStatusEvent
from app.models.payment import Payment
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.schemas.media import MediaAssetConfirm, MediaSignatureRequest
from app.schemas.order import OrderStatusPatch, QuoteConvertRequest
from app.schemas.payment import PaymentCreate, PaymentVoidRequest


class Result:
    def __init__(self, value: object) -> None:
        self.value = value

    def one_or_none(self) -> object:
        return self.value

    def all(self) -> list[object]:
        if self.value is None:
            return []
        return self.value if isinstance(self.value, list) else [self.value]


class FakeSession:
    def __init__(
        self,
        *,
        scalars: list[object] | None = None,
        scalar: list[object] | None = None,
        gets: list[object] | None = None,
    ):
        self._scalars = list(scalars or [])
        self._scalar = list(scalar or [])
        self._gets = list(gets or [])
        self.added: list[object] = []
        self.commits = 0
        self.rollbacks = 0

    def scalar(self, _statement: object) -> object:
        return self._scalar.pop(0) if self._scalar else None

    def scalars(self, _statement: object) -> Result:
        return Result(self._scalars.pop(0) if self._scalars else None)

    def get(self, _model: type, _identity: object) -> object:
        return self._gets.pop(0) if self._gets else None

    def add(self, value: object) -> None:
        if hasattr(value, "id") and value.id is None:
            value.id = uuid4()
        if isinstance(value, Payment) and value.status is None:
            value.status = "recorded"
        self.added.append(value)

    def add_all(self, values: list[object]) -> None:
        for value in values:
            self.add(value)

    def flush(self) -> None:
        for value in self.added:
            if hasattr(value, "id") and value.id is None:
                value.id = uuid4()

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1

    def refresh(self, value: object) -> None:
        if hasattr(value, "id") and value.id is None:
            value.id = uuid4()
        if isinstance(value, Customer):
            value.created_at = datetime.now(UTC)
            value.updated_at = value.created_at
        if isinstance(value, MediaAsset):
            value.created_at = datetime.now(UTC)
        if isinstance(value, Payment) and value.created_at is None:
            value.created_at = datetime.now(UTC)
        if isinstance(value, SimpleNamespace):
            if hasattr(value, "delivered_at") and not isinstance(value.delivered_at, datetime):
                value.delivered_at = datetime.now(UTC)
            if hasattr(value, "installed_at") and not isinstance(value.installed_at, datetime):
                value.installed_at = datetime.now(UTC)
        if isinstance(value, Order):
            value.balance_minor = value.total_minor - value.paid_minor


def _staff(role: str = "operator") -> CurrentUser:
    return CurrentUser(user_id=uuid4(), role=role)


def _order(**changes: object) -> SimpleNamespace:
    now = datetime.now(UTC)
    values: dict[str, object] = {
        "id": uuid4(),
        "code": "PED-2026-0001",
        "quote_id": uuid4(),
        "customer_id": uuid4(),
        "status": "confirmed",
        "currency": "PEN",
        "total_minor": 10000,
        "deposit_required_minor": 5000,
        "paid_minor": 5000,
        "balance_minor": 5000,
        "promised_date": None,
        "delivered_at": None,
        "installed_at": None,
        "version": 1,
        "created_at": now,
        "updated_at": now,
    }
    values.update(changes)
    return SimpleNamespace(**values)


def _request() -> Request:
    request = Request(
        {
            "type": "http",
            "method": "PATCH",
            "path": "/api/v1/orders/test/status",
            "headers": [],
            "query_string": b"",
            "server": ("test", 80),
            "client": ("127.0.0.1", 1234),
            "scheme": "http",
            "http_version": "1.1",
        }
    )
    request.state.request_id = str(uuid4())
    return request


def test_customer_requires_contact_and_normalizes_values() -> None:
    with pytest.raises(ValueError, match="correo electrónico o teléfono"):
        CustomerCreate(full_name="Ana")

    fields = _normalize_customer_fields(
        {"full_name": " Ana López ", "email": " ANA@EXAMPLE.TEST ", "phone": " +51999 "}
    )
    assert fields == {
        "full_name": "Ana López",
        "email": "ana@example.test",
        "phone": "+51999",
    }

    with pytest.raises(ValueError, match="al menos un campo"):
        CustomerUpdate()


def test_approved_quote_converts_to_order_with_immutable_item_snapshot() -> None:
    quote_id = uuid4()
    quote_item = SimpleNamespace(
        id=uuid4(),
        product_id=uuid4(),
        quantity=2,
        width_mm=1200,
        height_mm=800,
        depth_mm=500,
        configuration={"drawerCount": 3},
        calculation_breakdown={"material": {"name": "Melamina"}},
        accessories=[{"name": "Corredera"}],
        product_name_snapshot="Cómoda clásica",
        line_total_minor=240_000,
        created_at=datetime.now(UTC),
    )
    quote = SimpleNamespace(
        id=quote_id,
        code="COT-2026-TEST1234",
        customer_id=None,
        owner_user_id=None,
        contact_name="Ana López",
        contact_email="ana@example.test",
        contact_phone=None,
        status="approved",
        currency="PEN",
        total_minor=240_000,
        deposit_minor=120_000,
        version=1,
    )
    session = FakeSession(
        scalars=[quote, [quote_item]],
        scalar=[None, None, None],
    )

    result = convert_quote_to_order(
        quote_id,
        QuoteConvertRequest(
            expectedQuoteVersion=1,
            deliveryAddress={"address": "Av. Los Robles 123", "district": "San Miguel"},
        ),
        _request(),
        Response(),
        "convert-key-001",
        _staff("admin"),
        session,  # type: ignore[arg-type]
    )

    next(item for item in session.added if isinstance(item, Order))
    order_item = next(item for item in session.added if isinstance(item, OrderItem))
    audit = next(item for item in session.added if isinstance(item, AuditLog))
    assert result.data.status == "confirmed"
    assert result.data.total_minor == quote.total_minor
    assert result.data.deposit_required_minor == quote.deposit_minor
    assert result.data.paid_minor == 0
    assert quote.status == "converted"
    assert quote.version == 2
    assert order_item.source_quote_item_id == quote_item.id
    assert order_item.unit_price_minor == 120_000
    assert order_item.line_total_minor == 240_000
    assert order_item.configuration_snapshot["configuration"] == {"drawerCount": 3}
    assert audit.action == "quote.converted"
    assert audit.new_values["idempotencyKey"] == "convert-key-001"
    assert session.commits == 1


def test_cloudinary_upload_signature_matches_provider_algorithm() -> None:
    assert cloudinary_signature({"timestamp": 1315060510}, "abcd", "sha1") == (
        "a21ad0f63beb4de2e5575204b79ab90bffb02c10"
    )
    response_signature = cloudinary_signature(
        {"public_id": "sample", "version": 1315060510}, "abcd", "sha1"
    )
    assert verify_cloudinary_upload_signature(
        "sample", 1315060510, response_signature, "abcd", "sha1"
    )
    assert not verify_cloudinary_upload_signature(
        "sample", 1315060510, "0" * 40, "abcd", "sha1"
    )


def test_upload_signature_scopes_asset_to_user_and_purpose() -> None:
    user = _staff()
    settings = Settings(
        environment="test",
        cloudinary_cloud_name="demo-cloud",
        cloudinary_api_key="demo-key",
        cloudinary_api_secret="abcd",
    )

    result = get_upload_signature(
        MediaSignatureRequest(purpose="payment_voucher", format="pdf"), user, settings
    )

    data = result.data
    assert data.public_id.startswith(f"muebleria-ivan/vouchers/{user.user_id}/")
    assert data.public_id.endswith(".pdf")
    assert data.delivery_type == "private"
    assert data.resource_type == "raw"
    assert data.signature == cloudinary_signature(
        {
            "public_id": data.public_id,
            "timestamp": data.timestamp,
            "type": "private",
        },
        "abcd",
        "sha1",
    )


def test_confirm_upload_verifies_provider_response_and_stores_private_access() -> None:
    user = _staff()
    settings = Settings(
        environment="test",
        cloudinary_cloud_name="demo-cloud",
        cloudinary_api_key="demo-key",
        cloudinary_api_secret="abcd",
    )
    public_id = f"muebleria-ivan/vouchers/{user.user_id}/{uuid4()}.pdf"
    version = 1315060510
    payload = MediaAssetConfirm(
        purpose="payment_voucher",
        publicId=public_id,
        version=version,
        signature=cloudinary_signature(
            {"public_id": public_id, "version": version}, "abcd", "sha1"
        ),
        format="pdf",
        resourceType="raw",
        bytes=1000,
    )
    session = FakeSession()

    result = confirm_upload(payload, user, settings, session)  # type: ignore[arg-type]

    saved = next(item for item in session.added if isinstance(item, MediaAsset))
    assert result.data.access == "private"
    assert result.data.url is None
    assert saved.owner_user_id == user.user_id
    assert saved.metadata_json["delivery_type"] == "private"


def test_private_cloudinary_download_url_expires_after_ten_minutes() -> None:
    settings = Settings(
        environment="test",
        cloudinary_cloud_name="demo-cloud",
        cloudinary_api_key="demo-key",
        cloudinary_api_secret="abcd",
    )
    media = SimpleNamespace(
        external_id="muebleria-ivan/vouchers/user/file.pdf",
        metadata_json={"format": "pdf", "resource_type": "raw"},
    )

    url = _private_download_url(settings, media)
    from urllib.parse import parse_qs, urlparse

    query = parse_qs(urlparse(url).query)
    timestamp = int(query["timestamp"][0])
    expires_at = int(query["expires_at"][0])
    signed_values = {
        "public_id": query["public_id"][0],
        "format": query["format"][0],
        "timestamp": timestamp,
        "expires_at": expires_at,
    }
    assert expires_at - timestamp == 600
    assert query["signature"][0] == cloudinary_signature(signed_values, "abcd", "sha1")
    assert "/raw/download?" in url


def test_private_voucher_is_hidden_from_another_customer() -> None:
    user = CurrentUser(user_id=uuid4(), role="customer")
    asset = SimpleNamespace(
        id=uuid4(),
        access="private",
        owner_user_id=uuid4(),
        external_id="muebleria-ivan/vouchers/other-user/file.pdf",
        media_type="application/pdf",
        created_at=datetime.now(UTC),
        metadata_json={"format": "pdf", "resource_type": "raw"},
    )
    settings = Settings(
        environment="test",
        cloudinary_cloud_name="demo-cloud",
        cloudinary_api_key="demo-key",
        cloudinary_api_secret="abcd",
    )

    with pytest.raises(HTTPException) as error:
        get_asset(asset.id, user, settings, FakeSession(gets=[asset]))  # type: ignore[arg-type]

    assert error.value.status_code == 404


def test_voucher_owner_receives_a_temporary_private_link() -> None:
    user = CurrentUser(user_id=uuid4(), role="customer")
    asset = SimpleNamespace(
        id=uuid4(),
        access="private",
        owner_user_id=user.user_id,
        external_id=f"muebleria-ivan/vouchers/{user.user_id}/file.pdf",
        media_type="application/pdf",
        created_at=datetime.now(UTC),
        metadata_json={"format": "pdf", "resource_type": "raw"},
    )
    settings = Settings(
        environment="test",
        cloudinary_cloud_name="demo-cloud",
        cloudinary_api_key="demo-key",
        cloudinary_api_secret="abcd",
    )

    result = get_asset(asset.id, user, settings, FakeSession(gets=[asset]))  # type: ignore[arg-type]

    assert result.data.url is None
    assert result.data.download_url is not None
    assert "/raw/download?" in result.data.download_url


def test_customer_cannot_list_payments_for_another_customers_order() -> None:
    user = CurrentUser(user_id=uuid4(), role="customer")
    session = FakeSession(scalars=[None])

    with pytest.raises(HTTPException) as error:
        list_payments(uuid4(), user=user, session=session)  # type: ignore[arg-type]

    assert error.value.status_code == 404
    assert not session._scalars


def test_create_customer_persists_only_normalized_contact() -> None:
    session = FakeSession()
    payload = CustomerCreate(full_name=" Ana L\u00f3pez ", email=" ANA@EXAMPLE.TEST ")

    result = create_customer(payload, _staff(), session)  # type: ignore[arg-type]

    assert result.data.full_name == "Ana L\u00f3pez"
    assert result.data.email == "ana@example.test"
    assert session.commits == 1


def test_production_status_requires_deposit_before_start() -> None:
    order = _order(paid_minor=0, balance_minor=10000)
    session = FakeSession(scalars=[order])
    payload = OrderStatusPatch(newStatus="materials_pending", version=1)

    with pytest.raises(HTTPException) as error:
        update_order_status(uuid4(), payload, _request(), _staff(), session)  # type: ignore[arg-type]

    assert error.value.status_code == 409
    assert session.commits == 0


def test_production_status_records_event_and_audit() -> None:
    order = _order()
    session = FakeSession(scalars=[order])
    payload = OrderStatusPatch(newStatus="materials_pending", version=1, note="Madera lista")

    result = update_order_status(
        order.id, payload, _request(), _staff(), session  # type: ignore[arg-type]
    )

    assert result.data.status == "materials_pending"
    assert result.data.version == 2
    assert session.commits == 1
    event = next(item for item in session.added if isinstance(item, OrderStatusEvent))
    assert event.actor_user_id is not None
    assert any(isinstance(item, AuditLog) for item in session.added)


@pytest.mark.parametrize(
    ("role", "note"),
    [("operator", "Cliente solicitó excepción"), ("admin", "   ")],
)
def test_install_with_balance_requires_admin_and_nonempty_reason(
    role: str, note: str
) -> None:
    order = _order(status="delivered", paid_minor=7000, balance_minor=3000)
    session = FakeSession(scalars=[order])
    payload = OrderStatusPatch(newStatus="installed", version=1, note=note)

    with pytest.raises(HTTPException) as error:
        update_order_status(
            order.id, payload, _request(), _staff(role), session  # type: ignore[arg-type]
        )

    assert error.value.status_code == 409
    assert session.commits == 0


def test_admin_installation_with_balance_records_exception_reason() -> None:
    order = _order(status="delivered", paid_minor=7000, balance_minor=3000)
    session = FakeSession(scalars=[order])
    payload = OrderStatusPatch(
        newStatus="installed", version=1, note="Cliente pagará al finalizar la semana"
    )

    result = update_order_status(
        order.id, payload, _request(), _staff("admin"), session  # type: ignore[arg-type]
    )

    audit = next(item for item in session.added if isinstance(item, AuditLog))
    assert result.data.status == "installed"
    assert audit.new_values["exception"] == "installed_with_balance"
    assert audit.new_values["reason"] == "Cliente pagará al finalizar la semana"
    assert session.commits == 1


def test_payment_is_idempotent_and_updates_order_balance() -> None:
    order = _order(balance_minor=5000)
    session = FakeSession(scalars=[order], scalar=[None])
    payload = PaymentCreate(
        amountMinor=3000,
        method="cash",
        paymentDate=date(2026, 11, 21),
    )
    response = Response()

    result = create_payment(
        order.id,
        payload,
        response,
        "payment-key-001",
        _staff(),
        session,  # type: ignore[arg-type]
    )

    assert result.data.amount_minor == 3000
    assert order.paid_minor == 8000
    assert session.commits == 1
    assert any(isinstance(item, AuditLog) for item in session.added)


def test_payment_rejects_amount_above_remaining_balance() -> None:
    order = _order(balance_minor=1000)
    session = FakeSession(scalars=[order], scalar=[None])
    payload = PaymentCreate(
        amountMinor=1001,
        method="cash",
        paymentDate=date(2026, 11, 21),
    )

    with pytest.raises(HTTPException) as error:
        create_payment(
            order.id,
            payload,
            Response(),
            "payment-key-002",
            _staff(),
            session,  # type: ignore[arg-type]
        )

    assert error.value.status_code == 409
    assert session.commits == 0


def test_same_payment_idempotency_key_returns_existing_record() -> None:
    order_id = uuid4()
    existing = Payment(
        id=uuid4(),
        order_id=order_id,
        amount_minor=3000,
        currency="PEN",
        method="cash",
        reference="recibo-1",
        paid_at=datetime(2026, 11, 21, tzinfo=UTC),
        status="recorded",
        idempotency_key="payment-key-004",
        actor_user_id=uuid4(),
        created_at=datetime.now(UTC),
    )
    session = FakeSession(scalar=[existing])
    payload = PaymentCreate(
        amountMinor=3000,
        method="cash",
        reference="recibo-1",
        paymentDate=date(2026, 11, 21),
    )
    response = Response()

    result = create_payment(
        order_id,
        payload,
        response,
        "payment-key-004",
        _staff(),
        session,  # type: ignore[arg-type]
    )

    assert result.data.id == existing.id
    assert response.status_code == 200
    assert session.commits == 0


def test_idempotency_key_cannot_be_reused_for_different_payment() -> None:
    existing = Payment(
        id=uuid4(),
        order_id=uuid4(),
        amount_minor=3000,
        currency="PEN",
        method="cash",
        reference=None,
        paid_at=datetime(2026, 11, 21, tzinfo=UTC),
        status="recorded",
        idempotency_key="payment-key-005",
        actor_user_id=uuid4(),
    )
    session = FakeSession(scalar=[existing])
    payload = PaymentCreate(
        amountMinor=2000,
        method="cash",
        paymentDate=date(2026, 11, 21),
    )

    with pytest.raises(HTTPException) as error:
        create_payment(
            uuid4(),
            payload,
            Response(),
            "payment-key-005",
            _staff(),
            session,  # type: ignore[arg-type]
        )

    assert error.value.status_code == 409
    assert session.commits == 0


def test_payment_reversal_creates_a_linked_record_and_updates_balance() -> None:
    original = Payment(
        id=uuid4(),
        order_id=uuid4(),
        amount_minor=2000,
        currency="PEN",
        method="cash",
        reference=None,
        paid_at=datetime(2026, 11, 21, tzinfo=UTC),
        status="recorded",
        idempotency_key="payment-key-003",
        actor_user_id=uuid4(),
    )
    order = _order(paid_minor=7000, balance_minor=3000)
    session = FakeSession(scalars=[original, order], scalar=[None])

    result = void_payment(
        original.id,
        PaymentVoidRequest(reason="Registro duplicado"),
        _staff("admin"),
        session,  # type: ignore[arg-type]
    )

    reversal = next(item for item in session.added if isinstance(item, Payment))
    assert original.status == "voided"
    assert order.paid_minor == 5000
    assert reversal.reverses_payment_id == original.id
    assert result.data.amount_minor == 2000
    assert session.commits == 1
