from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.core.security import CurrentUser
from app.domain.catalog import (
    InvalidQuoteTransitionError,
    QuoteAccessError,
    QuoteVersionConflictError,
)
from app.repositories.quotes import QuoteAggregate
from app.schemas.pricing import (
    EstimateItemData,
    EstimateItemRequest,
    PricingBreakdownData,
    QuoteEstimateData,
)
from app.schemas.quotes import QuoteCreateRequest, QuoteStatusUpdateRequest
from app.services.quotes import QuoteService


class FakePricing:
    def __init__(self, product_id) -> None:
        self.product_id = product_id

    def estimate(self, request):
        requested = request.items[0]
        item = EstimateItemData(
            product_id=self.product_id,
            product_name="Producto",
            quantity=requested.quantity,
            width_mm=requested.width_mm,
            height_mm=requested.height_mm,
            depth_mm=requested.depth_mm,
            material=None,
            finish=None,
            accessories=[],
            applied_rules=[],
            breakdown=PricingBreakdownData(
                reference_base_minor=100_000,
                size_adjusted_base_minor=100_000,
                material_minor=0,
                finish_minor=0,
                accessories_minor=0,
                rules_minor=0,
                unit_total_minor=100_000,
            ),
            line_total_minor=100_000,
            min_production_days=7,
            max_production_days=10,
        )
        return QuoteEstimateData(
            subtotal_minor=100_000,
            adjustments_minor=0,
            total_minor=100_000,
            deposit_minor=50_000,
            items=[item],
        )


class FakeQuoteRepository:
    def __init__(self) -> None:
        self.aggregate = None
        self.aggregates = []
        self.conflict = False

    def add(self, quote, items):
        self.aggregate = QuoteAggregate(quote, items)
        self.aggregates.append(self.aggregate)

    def get(self, quote_id):
        if self.aggregate and self.aggregate.quote.id == quote_id:
            return self.aggregate
        return None

    def list_for_user(self, *, owner_user_id, include_all, page, page_size):
        matching = self.aggregates if include_all else [
            aggregate
            for aggregate in self.aggregates
            if aggregate.quote.owner_user_id == owner_user_id
        ]
        start = (page - 1) * page_size
        return matching[start : start + page_size], len(matching)

    def update_status(self, quote_id, *, expected_version, new_status):
        if self.conflict or not self.aggregate:
            return None
        quote = self.aggregate.quote
        if quote.id != quote_id or quote.version != expected_version:
            return None
        quote.status = new_status
        quote.version += 1
        return quote

    def commit(self):
        return None

    def rollback(self):
        return None


def request(product_id):
    return QuoteCreateRequest(
        contact_name="Ana Demo",
        contact_email="ANA@EXAMPLE.TEST",
        items=[
            EstimateItemRequest(
                product_id=product_id,
                width_mm=1000,
                height_mm=1000,
                depth_mm=500,
            )
        ],
    )


def test_quote_creation_persists_seven_day_snapshot_for_owner() -> None:
    now = datetime(2026, 11, 21, 15, 0, tzinfo=UTC)
    product_id = uuid4()
    repository = FakeQuoteRepository()
    service = QuoteService(repository, FakePricing(product_id), clock=lambda: now)
    owner = CurrentUser(user_id=uuid4(), role="customer")

    quote = service.create(request(product_id), owner)

    assert quote.status == "submitted"
    assert quote.contact_email == "ana@example.test"
    assert quote.expires_at.isoformat() == "2026-11-28T15:00:00+00:00"
    assert quote.deposit_minor == 50_000
    assert quote.items[0].breakdown.unit_total_minor == 100_000
    assert repository.aggregate.quote.owner_user_id == owner.user_id


def test_quote_access_is_limited_to_owner_or_admin() -> None:
    product_id = uuid4()
    repository = FakeQuoteRepository()
    service = QuoteService(repository, FakePricing(product_id))
    owner = CurrentUser(user_id=uuid4(), role="customer")
    quote = service.create(request(product_id), owner)

    assert service.get(quote.id, owner).id == quote.id
    assert service.get(quote.id, CurrentUser(uuid4(), "admin")).id == quote.id
    with pytest.raises(QuoteAccessError):
        service.get(quote.id, CurrentUser(uuid4(), "customer"))


def test_quote_list_is_owner_scoped_and_paginated() -> None:
    product_id = uuid4()
    repository = FakeQuoteRepository()
    service = QuoteService(repository, FakePricing(product_id))
    owner = CurrentUser(user_id=uuid4(), role="customer")
    other_owner = CurrentUser(user_id=uuid4(), role="customer")
    owned_quote = service.create(request(product_id), owner)
    service.create(request(product_id), other_owner)
    service.create(request(product_id), None)

    first_page = service.list_for_user(owner, page=1, page_size=1)
    admin_page = service.list_for_user(
        CurrentUser(user_id=uuid4(), role="admin"), page=1, page_size=20
    )

    assert first_page.total == 1
    assert first_page.page == 1
    assert first_page.page_size == 1
    assert [quote.id for quote in first_page.items] == [owned_quote.id]
    assert admin_page.total == 3


def test_quote_status_uses_allowed_transitions_and_optimistic_version() -> None:
    product_id = uuid4()
    repository = FakeQuoteRepository()
    service = QuoteService(repository, FakePricing(product_id))
    quote = service.create(request(product_id), None)

    reviewing = service.update_status(
        quote.id,
        QuoteStatusUpdateRequest(status="reviewing", expected_version=1),
    )
    assert reviewing.status == "reviewing"
    assert reviewing.version == 2

    with pytest.raises(InvalidQuoteTransitionError):
        service.update_status(
            quote.id,
            QuoteStatusUpdateRequest(status="reviewing", expected_version=2),
        )

    repository.aggregate.quote.status = "submitted"
    repository.aggregate.quote.version = 1
    repository.conflict = True
    with pytest.raises(QuoteVersionConflictError):
        service.update_status(
            quote.id,
            QuoteStatusUpdateRequest(status="reviewing", expected_version=1),
        )
