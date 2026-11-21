"""End-to-end Phase 4 workflow against local Supabase and PostgreSQL.

Run ``supabase db reset`` first, then provide the local database URL, API URL,
and publishable key through the ``SUPABASE_TEST_*`` environment variables.
The test is skipped in the fast unit suite when that local stack is unavailable.
It uses unique users on every run; ``supabase db reset`` removes the resulting
append-only audit, status, and payment evidence from the disposable local stack.
"""

import os
from datetime import date, timedelta
from uuid import UUID, uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.core.config import Settings
from app.main import create_app

DATABASE_URL = os.getenv("SUPABASE_TEST_DATABASE_URL")
SUPABASE_URL = os.getenv("SUPABASE_TEST_URL")
SUPABASE_PUBLISHABLE_KEY = os.getenv("SUPABASE_TEST_PUBLISHABLE_KEY")

pytestmark = pytest.mark.skipif(
    not all((DATABASE_URL, SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY)),
    reason=(
        "Set SUPABASE_TEST_DATABASE_URL, SUPABASE_TEST_URL, and "
        "SUPABASE_TEST_PUBLISHABLE_KEY to run the Phase 4 workflow"
    ),
)


def _create_local_user(label: str) -> tuple[UUID, str, str]:
    assert SUPABASE_URL is not None
    assert SUPABASE_PUBLISHABLE_KEY is not None

    email = f"phase4-{label}-{uuid4().hex}@example.test"
    password = f"Local-{uuid4().hex}!aA1"
    headers = {"apikey": SUPABASE_PUBLISHABLE_KEY}
    with httpx.Client(base_url=SUPABASE_URL, timeout=10) as auth_client:
        signup = auth_client.post(
            "/auth/v1/signup",
            headers=headers,
            json={
                "email": email,
                "password": password,
                "data": {"full_name": f"Phase 4 {label}"},
            },
        )
        assert signup.status_code == 200, signup.text
        signup_data = signup.json()
        user_id = UUID(signup_data["user"]["id"])
        token = signup_data.get("access_token")
        if not token:
            session = auth_client.post(
                "/auth/v1/token?grant_type=password",
                headers=headers,
                json={"email": email, "password": password},
            )
            assert session.status_code == 200, session.text
            token = session.json()["access_token"]

    return user_id, email, token


def _assert_success(response: httpx.Response, expected: int = 200) -> dict:
    assert response.status_code == expected, response.text
    return response.json()


def test_quote_to_installed_order_workflow_with_customer_isolation() -> None:
    assert DATABASE_URL is not None
    assert SUPABASE_URL is not None

    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

    try:
        customer_user_id, customer_email, customer_token = _create_local_user("customer")
        other_user_id, _, other_token = _create_local_user("other-customer")
        admin_user_id, _, admin_token = _create_local_user("admin")

        with engine.begin() as connection:
            result = connection.execute(
                text("update app.profiles set role = 'admin' where user_id = :user_id"),
                {"user_id": admin_user_id},
            )
        assert result.rowcount == 1

        settings = Settings(
            environment="test",
            database_url=DATABASE_URL,
            supabase_url=SUPABASE_URL,
        )
        customer_headers = {"Authorization": f"Bearer {customer_token}"}
        other_headers = {"Authorization": f"Bearer {other_token}"}
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        with TestClient(create_app(settings)) as client:
            catalog = _assert_success(client.get("/api/v1/products?page=1&pageSize=10"))
            assert catalog["data"]["total"] >= 1
            product_summary = catalog["data"]["items"][0]
            product = _assert_success(
                client.get(f"/api/v1/products/{product_summary['slug']}")
            )["data"]

            limits = product["measurementLimits"]
            quote = _assert_success(
                client.post(
                    "/api/v1/quotes",
                    headers=customer_headers,
                    json={
                        "contactName": "Cliente Flujo Fase 4",
                        "contactEmail": customer_email,
                        "items": [
                            {
                                "productId": product["id"],
                                "quantity": 1,
                                "widthMm": limits["minWidthMm"],
                                "heightMm": limits["minHeightMm"],
                                "depthMm": limits["minDepthMm"],
                                "accessoryIds": [],
                                "configuration": {},
                            }
                        ],
                    },
                ),
                201,
            )["data"]
            quote_id = UUID(quote["id"])

            own_quotes = _assert_success(
                client.get("/api/v1/quotes?page=1&pageSize=100", headers=customer_headers)
            )
            assert quote["id"] in {item["id"] for item in own_quotes["data"]["items"]}
            isolated_quote = client.get(
                f"/api/v1/quotes/{quote_id}", headers=other_headers
            )
            assert isolated_quote.status_code == 403
            assert (
                client.patch(
                    f"/api/v1/quotes/{quote_id}/status",
                    headers=customer_headers,
                    json={"status": "reviewing", "expectedVersion": quote["version"]},
                ).status_code
                == 403
            )

            reviewing = _assert_success(
                client.patch(
                    f"/api/v1/quotes/{quote_id}/status",
                    headers=admin_headers,
                    json={"status": "reviewing", "expectedVersion": quote["version"]},
                )
            )["data"]
            approved = _assert_success(
                client.patch(
                    f"/api/v1/quotes/{quote_id}/status",
                    headers=admin_headers,
                    json={"status": "approved", "expectedVersion": reviewing["version"]},
                )
            )["data"]

            conversion_key = f"phase4-convert-{uuid4()}"
            conversion_headers = {
                **admin_headers,
                "Idempotency-Key": conversion_key,
            }
            conversion_payload = {
                "expectedQuoteVersion": approved["version"],
                "deliveryAddress": {
                    "address": "Av. Prueba 456",
                    "district": "Miraflores",
                    "reference": "Frente al parque",
                },
                "promisedDate": (date.today() + timedelta(days=20)).isoformat(),
            }
            order = _assert_success(
                client.post(
                    f"/api/v1/quotes/{quote_id}/convert",
                    headers=conversion_headers,
                    json=conversion_payload,
                ),
                201,
            )["data"]
            replayed = _assert_success(
                client.post(
                    f"/api/v1/quotes/{quote_id}/convert",
                    headers=conversion_headers,
                    json=conversion_payload,
                )
            )["data"]
            assert replayed["id"] == order["id"]
            order_id = UUID(order["id"])

            assert client.get(f"/api/v1/orders/{order_id}").status_code == 401
            isolated_order = client.get(
                f"/api/v1/orders/{order_id}", headers=other_headers
            )
            assert isolated_order.status_code == 404

            payment_date = date.today().isoformat()
            _assert_success(
                client.post(
                    f"/api/v1/orders/{order_id}/payments",
                    headers={
                        **admin_headers,
                        "Idempotency-Key": f"phase4-deposit-{uuid4()}",
                    },
                    json={
                        "amountMinor": order["depositRequiredMinor"],
                        "currency": "PEN",
                        "method": "bank_transfer",
                        "reference": "Prueba local de anticipo",
                        "paymentDate": payment_date,
                    },
                ),
                201,
            )

            version = order["version"]
            for next_status in (
                "materials_pending",
                "cutting",
                "assembly",
                "finishing",
                "ready",
            ):
                moved = _assert_success(
                    client.patch(
                        f"/api/v1/orders/{order_id}/status",
                        headers=admin_headers,
                        json={"newStatus": next_status, "version": version},
                    )
                )["data"]
                version = moved["version"]

            _assert_success(
                client.post(
                    f"/api/v1/orders/{order_id}/payments",
                    headers={
                        **admin_headers,
                        "Idempotency-Key": f"phase4-balance-{uuid4()}",
                    },
                    json={
                        "amountMinor": order["totalMinor"] - order["depositRequiredMinor"],
                        "currency": "PEN",
                        "method": "bank_transfer",
                        "reference": "Prueba local de saldo",
                        "paymentDate": payment_date,
                    },
                ),
                201,
            )

            for next_status in ("delivered", "installed"):
                moved = _assert_success(
                    client.patch(
                        f"/api/v1/orders/{order_id}/status",
                        headers=admin_headers,
                        json={"newStatus": next_status, "version": version},
                    )
                )["data"]
                version = moved["version"]

            own_orders = _assert_success(
                client.get("/api/v1/orders?page=1&pageSize=100", headers=customer_headers)
            )
            detail = _assert_success(
                client.get(f"/api/v1/orders/{order_id}", headers=customer_headers)
            )["data"]
            payments = _assert_success(
                client.get(f"/api/v1/orders/{order_id}/payments", headers=customer_headers)
            )

            assert order["id"] in {item["id"] for item in own_orders["data"]}
            assert detail["status"] == "installed"
            assert detail["balanceMinor"] == 0
            assert len(detail["statusHistory"]) == 8
            assert payments["total"] == 2
    finally:
        engine.dispose()
