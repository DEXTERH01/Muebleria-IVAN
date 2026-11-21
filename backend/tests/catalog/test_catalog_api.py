from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.catalog import get_catalog_service
from app.api.v1.catalog import router as catalog_router
from app.api.v1.quotes import get_pricing_service, get_quote_service
from app.api.v1.quotes import router as quote_router
from app.core.security import CurrentUser, get_current_user
from app.schemas.catalog import ProductListData, ProductSummaryData
from app.schemas.pricing import QuoteEstimateData
from app.schemas.quotes import QuoteListData


class FakeCatalogService:
    def __init__(self) -> None:
        self.calls = []

    def list_products(self, **filters):
        self.calls.append(filters)
        return ProductListData(
            items=[
                ProductSummaryData(
                    id=uuid4(),
                    slug="mesa-demo",
                    name="Mesa demo",
                    description="Descripción",
                    category="Comedor",
                    base_price_minor=100_000,
                    min_production_days=7,
                    max_production_days=10,
                    primary_image=None,
                )
            ],
            page=filters["page"],
            page_size=filters["page_size"],
            total=1,
        )


class FakePricingService:
    def estimate(self, _request):
        return QuoteEstimateData(
            subtotal_minor=100_000,
            adjustments_minor=0,
            total_minor=100_000,
            deposit_minor=50_000,
            items=[],
        )


class FakeQuoteListService:
    def __init__(self) -> None:
        self.calls = []

    def list_for_user(self, user, *, page, page_size):
        self.calls.append((user, page, page_size))
        return QuoteListData(items=[], total=0, page=page, page_size=page_size)


def test_public_catalog_and_estimate_contracts_use_camel_case() -> None:
    catalog = FakeCatalogService()
    app = FastAPI()
    app.include_router(catalog_router, prefix="/api/v1")
    app.include_router(quote_router, prefix="/api/v1")
    app.dependency_overrides[get_catalog_service] = lambda: catalog
    app.dependency_overrides[get_pricing_service] = FakePricingService
    client = TestClient(app)

    catalog_response = client.get(
        "/api/v1/products?page=2&pageSize=5&category=Comedor&search=mesa"
    )
    estimate_response = client.post(
        "/api/v1/quotes/estimate",
        json={
            "items": [
                {
                    "productId": str(uuid4()),
                    "widthMm": 1000,
                    "heightMm": 1000,
                    "depthMm": 500,
                }
            ]
        },
    )

    assert catalog_response.status_code == 200
    assert catalog_response.json()["data"]["pageSize"] == 5
    assert catalog_response.json()["data"]["items"][0]["basePriceMinor"] == 100_000
    assert catalog.calls == [
        {"page": 2, "page_size": 5, "category": "Comedor", "search": "mesa"}
    ]
    assert estimate_response.status_code == 200
    assert estimate_response.json()["data"] == {
        "currency": "PEN",
        "subtotalMinor": 100_000,
        "adjustmentsMinor": 0,
        "totalMinor": 100_000,
        "depositMinor": 50_000,
        "items": [],
    }


def test_module_openapi_exposes_expected_routes_without_central_registration() -> None:
    app = FastAPI()
    app.include_router(catalog_router, prefix="/api/v1")
    app.include_router(quote_router, prefix="/api/v1")
    paths = app.openapi()["paths"]

    assert set(paths) == {
        "/api/v1/products",
        "/api/v1/products/{slug}",
        "/api/v1/products/{product_id}",
        "/api/v1/pricing-rules",
        "/api/v1/quotes/estimate",
        "/api/v1/quotes",
        "/api/v1/quotes/{quote_id}",
        "/api/v1/quotes/{quote_id}/status",
    }
    assert "get" in paths["/api/v1/quotes"]
    assert "post" in paths["/api/v1/quotes"]


def test_quote_list_requires_customer_or_admin_and_uses_camel_case_pagination() -> None:
    quote_service = FakeQuoteListService()
    customer = CurrentUser(user_id=uuid4(), role="customer")
    app = FastAPI()
    app.include_router(quote_router, prefix="/api/v1")
    app.dependency_overrides[get_quote_service] = lambda: quote_service
    app.dependency_overrides[get_current_user] = lambda: customer
    client = TestClient(app)

    response = client.get("/api/v1/quotes?page=2&pageSize=5")

    assert response.status_code == 200
    assert response.json()["data"] == {"items": [], "total": 0, "page": 2, "pageSize": 5}
    assert quote_service.calls == [(customer, 2, 5)]

    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        user_id=uuid4(), role="operator"
    )
    forbidden = client.get("/api/v1/quotes")
    assert forbidden.status_code == 403
